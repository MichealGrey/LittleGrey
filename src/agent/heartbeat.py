import json
import random
import threading
import time
from datetime import datetime
from typing import Any, Callable

from src.agent.llm import LLMClient
from src.core.config import AgentConfig, PersonalityConfig
from src.core.gate import PriorityGate
from src.core.logger import AgentLogger
from src.agent.idle_intent import IdleIntentAnalyzer
from src.core.types import ToolResult
from src.executor.engine import ExecutionEngine
from src.executor.registry import ToolRegistry
from src.memory.long_term import LongTermMemory
from src.memory.rag import RAG
from src.memory.short_term import ShortTermMemory
from src.tools.search_tool import SearchNewsTool


class Heartbeat:
    def __init__(
        self,
        config: AgentConfig,
        personality: PersonalityConfig,
        llm: LLMClient,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        rag: RAG,
        registry: ToolRegistry,
        engine: ExecutionEngine,
        logger: AgentLogger,
        on_message: Callable[[str], None],
        gate: PriorityGate | None = None,
        on_idle: Callable[[], None] | None = None,
        intent_analyzer: IdleIntentAnalyzer | None = None,
        emotion_analyzer: Any | None = None,
    ):
        self.config = config
        self.personality = personality
        self.llm = llm
        self.short_term = short_term
        self.long_term = long_term
        self.rag = rag
        self.registry = registry
        self.engine = engine
        self.logger = logger
        self.on_message = on_message
        self._gate = gate
        self._on_idle = on_idle
        self._intent_analyzer = intent_analyzer
        self._emotion_analyzer = emotion_analyzer

        self._last_active: float = time.monotonic()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._pushed_keywords: set[str] = set()  # 已推送过的搜索关键词，不重复

        if not self.registry.get("search_news"):
            self.registry.register(SearchNewsTool(llm_client=llm))

    def touch(self) -> None:
        self._last_active = time.monotonic()

    def start(self) -> None:
        if not self.config.heartbeat_enabled:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        check_interval = min(self.config.heartbeat_interval, 30)
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=check_interval)
            if self._stop_event.is_set():
                break

            if self._emotion_analyzer:
                self._emotion_analyzer.autonomous_tick()

            idle = time.monotonic() - self._last_active
            if idle >= self.config.heartbeat_interval:
                if self._emotion_analyzer:
                    mods = self._emotion_analyzer.get_behavior_modifiers()
                    proactive_prob = mods.get("proactive_prob", 1.0)
                    if random.random() > proactive_prob:
                        continue
                self._trigger()
                self.touch()

    def _trigger(self) -> None:
        self.logger.log("heartbeat", "trigger")

        if self._on_idle:
            self._on_idle()

        idle_seconds = time.monotonic() - self._last_active

        motivation = self._emotion_analyzer.get_motivation() if self._emotion_analyzer else None

        if motivation and motivation.wants_solitude:
            self.logger.log("heartbeat", "solitude_desired", output_data={"need": motivation.current_need})
            return

        intent = None
        if self._intent_analyzer:
            intent = self._intent_analyzer.analyze(idle_seconds)

        if intent and intent.get("action") == "silent":
            self.logger.log("heartbeat", "silent_by_intent", output_data=intent)
            return

        if intent and intent.get("action") in ("comfort", "remind"):
            response = self._intent_analyzer.generate_response(intent)
            if response:
                self.short_term.add("assistant", response)
                self.on_message(response)
            self.logger.log("heartbeat", "intent_response", output_data={"action": intent["action"]})
            return

        if self._emotion_analyzer:
            action = self._decide_action_by_motivation(idle_seconds, motivation)
            if action == "rest":
                self.logger.log("heartbeat", "rest_by_motivation")
                return
            if action == "care":
                self._send_care_message()
                return

        if self._gate and not self._gate.wait_for_turn(timeout=120):
            self.logger.log("heartbeat", "yielding", status="skip")
            return

        interests = self._get_user_interests()

        if not interests:
            self.logger.log("heartbeat", "no_interests", status="skip")
            return

        # 逐个兴趣点尝试：搜索新闻 → 判断用户是否感兴趣 → 满意则发起对话
        for interest in interests:
            if self._gate and not self._gate.wait_for_turn(timeout=60):
                self.logger.log("heartbeat", "yielding_mid_cycle", status="skip")
                return

            keyword = self._extract_keyword(interest)
            if not keyword or keyword in self._pushed_keywords:
                continue

            news_result = self._search_news(keyword)
            if not news_result.success or not news_result.data:
                self._pushed_keywords.add(keyword)
                continue

            news_list = news_result.data.get("news", [])
            if not news_list:
                self._pushed_keywords.add(keyword)
                continue

            if self._gate and not self._gate.wait_for_turn(timeout=60):
                self.logger.log("heartbeat", "yielding_mid_cycle", status="skip")
                return

            # 核心：意图判断——LLM 评估用户是否会对这些新闻感兴趣
            interested = self._judge_interest(interest, news_list)
            if not interested:
                self._pushed_keywords.add(keyword)
                self.logger.log("heartbeat", "not_interested", extra={"keyword": keyword})
                continue

            if self._gate and not self._gate.wait_for_turn(timeout=60):
                self.logger.log("heartbeat", "yielding_mid_cycle", status="skip")
                return

            # 用户感兴趣，生成对话
            content = self._compose_message(interest, keyword, news_list)
            self._pushed_keywords.add(keyword)

            if content:
                self.short_term.add("assistant", content)
                self.on_message(content)
            return  # 本轮心跳只推一条

        # 所有兴趣点都不合适，本轮静默，等下次心跳
        self.logger.log("heartbeat", "all_topics_skipped")

    def _get_user_interests(self) -> list[str]:
        try:
            results = self.long_term.search("用户兴趣 喜好 关注的话题", top_k=10)
            interests = []
            for item in results:
                if item.get("relevance", 0) < 0.2:
                    continue
                meta = item.get("metadata", {})
                if meta.get("type") == "user_preference":
                    interests.append(item.get("text", ""))
            return interests
        except Exception:
            return []

    def _extract_keyword(self, interest_text: str) -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": "从用户兴趣描述中提取1-3个搜索关键词，只返回关键词，不要其他文字。",
                },
                {"role": "user", "content": interest_text},
            ]
            result = self.llm.chat(messages, use_tools=False)
            return result.get("content", "").strip() or interest_text[:10]
        except Exception:
            return interest_text[:10]

    def _search_news(self, keyword: str) -> ToolResult:
        return self.engine.execute_single("search_news", {"query": keyword, "count": 3})

    def _judge_interest(self, interest: str, news_list: list[dict[str, Any]]) -> bool:
        """LLM 判断用户是否会对这些新闻内容感兴趣。"""
        news_text = "\n".join(
            f"- {n.get('title', '')}: {n.get('summary', '')}" for n in news_list
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个兴趣判断助手。根据对方的已知兴趣和搜到的新闻内容，"
                    "判断对方是否会对这些新闻感兴趣。\n"
                    "只返回JSON：{\"interested\": true/false, \"reason\": \"简短原因\"}\n"
                    "判断标准：\n"
                    "- 新闻内容与用户兴趣直接相关 → interested: true\n"
                    "- 新闻是旧闻或无关内容 → interested: false\n"
                    "- 新闻质量差、标题党、没有实质内容 → interested: false\n"
                    "- 用户可能只是随口提及并非真正关注 → interested: false"
                ),
            },
            {
                "role": "user",
                "content": f"对方兴趣：{interest}\n\n新闻内容：\n{news_text}",
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "")
            parsed = json.loads(content)
            return parsed.get("interested", False)
        except (json.JSONDecodeError, TypeError):
            # 解析失败时，默认保守不感兴趣
            if "true" in content.lower() or "感兴趣" in content:
                return True
            return False
        except Exception:
            return False

    def _compose_message(self, interest: str, keyword: str, news_list: list[dict[str, Any]]) -> str:
        hour = datetime.now().hour
        time_hint = self._time_hint(hour)

        news_items = []
        for n in news_list:
            title = n.get("title", "")
            summary = n.get("summary", "")
            news_items.append(f"- {title}：{summary}")
        news_context = "\n".join(news_items)

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}，现在{time_hint}了，你想跟对方聊聊你看到的内容。"
                    f"根据你自己的兴趣和搜到的资讯，用你自己的语气说出来。"
                    f"像朋友分享消息一样，不要太正式，不超过3句话。"
                    f"只分享真正有价值的内容，不要强行凑话题。"
                ),
            },
            {
                "role": "user",
                "content": f"对方兴趣：{interest}\n\n搜到的资讯：\n{news_context}",
            },
        ]

        try:
            result = self.llm.chat(prompt_messages, use_tools=False)
            return result.get("content", "")
        except Exception as e:
            self.logger.log("heartbeat", "compose_error", status="error", error=str(e))
            return ""

    def _decide_action_by_motivation(self, idle_seconds: float, motivation: Any | None) -> str:
        if not motivation or not motivation.has_drive():
            return "proactive"

        idle_minutes = idle_seconds / 60
        motivation_context = motivation.to_prompt_snippet()

        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}。对方已经{idle_minutes:.0f}分钟没说话了。\n"
                    f"你现在的感受：{motivation_context}\n"
                    f"根据你此刻真实的感受，决定要不要主动说话、说什么。\n"
                    f'返回JSON：{{"action": "rest/care/share", "reason": "简短原因"}}\n'
                    f"action说明：\n"
                    f"- rest: 不想说话，保持安静\n"
                    f"- care: 想关心对方一句\n"
                    f"- share: 想分享自己此刻的想法\n"
                ),
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "")
            parsed = json.loads(content)
            return parsed.get("action", "share")
        except (json.JSONDecodeError, TypeError, Exception):
            return "share"

    def _send_care_message(self) -> None:
        hour = datetime.now().hour
        time_hint = self._time_hint(hour)
        motivation = self._emotion_analyzer.get_motivation() if self._emotion_analyzer else None
        care_context = motivation.to_prompt_snippet() if motivation else ""

        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}，现在{time_hint}了。{care_context}\n"
                    f"对方好久没说话了，你想自然地发一句关心的话。\n"
                    f"像朋友发消息一样随意，不要追问，不要说教，不超过2句话。"
                ),
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "")
            if content:
                self.short_term.add("assistant", content)
                self.on_message(content)
        except Exception as e:
            self.logger.log("heartbeat", "care_error", status="error", error=str(e))

    @staticmethod
    def _time_hint(hour: int) -> str:
        if 5 <= hour < 9:
            return "早上"
        elif 9 <= hour < 12:
            return "上午"
        elif 12 <= hour < 14:
            return "中午"
        elif 14 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "深夜"

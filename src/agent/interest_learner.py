import json
import threading
import time
from typing import Any

from src.agent.llm import LLMClient
from src.core.config import AgentConfig, PersonalityConfig
from src.core.gate import PriorityGate
from src.core.logger import AgentLogger
from src.core.types import ToolResult
from src.executor.engine import ExecutionEngine
from src.executor.registry import ToolRegistry
from src.memory.long_term import LongTermMemory
from src.tools.search_tool import SearchNewsTool


class InterestLearner:
    """小小灰自己的兴趣学习线程——后台定期从记忆中提炼自身兴趣，搜索知识存入记忆。"""

    def __init__(
        self,
        config: AgentConfig,
        personality: PersonalityConfig,
        llm: LLMClient,
        long_term: LongTermMemory,
        registry: ToolRegistry,
        engine: ExecutionEngine,
        logger: AgentLogger,
        gate: PriorityGate | None = None,
    ):
        self.config = config
        self.personality = personality
        self.llm = llm
        self.long_term = long_term
        self.registry = registry
        self.engine = engine
        self.logger = logger
        self._gate = gate

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        if not self.registry.get("search_news"):
            self.registry.register(SearchNewsTool(llm_client=llm))

    def start(self) -> None:
        if not self.config.interest_learning_enabled:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self.config.interest_learning_interval)
            if self._stop_event.is_set():
                break
            self._run_learning_cycle()

    def _run_learning_cycle(self) -> None:
        self.logger.log("interest_learner", "cycle_start")

        try:
            if self._gate and not self._gate.wait_for_turn(timeout=120):
                self.logger.log("interest_learner", "yielding", status="skip")
                return

            # 1. 获取小小灰已有的兴趣
            existing_interests = self._get_existing_interests()

            if self._gate and not self._gate.wait_for_turn(timeout=120):
                self.logger.log("interest_learner", "yielding", status="skip")
                return

            # 2. 从记忆中提炼新兴趣
            new_interests = self._discover_interests(existing_interests)

            # 3. 对新兴趣搜索知识
            for interest in new_interests:
                if self._gate and not self._gate.wait_for_turn(timeout=60):
                    self.logger.log("interest_learner", "yielding_mid_cycle", status="skip")
                    break
                self._explore_interest(interest)

            self.logger.log(
                "interest_learner", "cycle_done",
                output_data={"new_interests": len(new_interests)},
            )
        except Exception as e:
            self.logger.log("interest_learner", "cycle_error", status="error", error=str(e))

    def _get_existing_interests(self) -> list[str]:
        """读取已保存的小小灰自身兴趣。"""
        results = self.long_term.search("小小灰的兴趣", top_k=20)
        interests = []
        for item in results:
            meta = item.get("metadata", {})
            if meta.get("type") == "agent_interest":
                interests.append(item.get("text", ""))
        return interests

    def _discover_interests(self, existing: list[str]) -> list[str]:
        """从所有记忆中以小小灰视角提炼自己的新兴趣。"""
        # 收集各类记忆
        all_memories = self.long_term.search("话题 对话 知识 情感", top_k=30)
        memory_texts = []
        for item in all_memories:
            text = item.get("text", "")
            if text:
                memory_texts.append(text)

        if not memory_texts:
            return []

        existing_str = "、".join(existing) if existing else "暂无"

        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}，一只可爱的AI女孩子。"
                    f"你正在回顾自己最近和用户聊过的内容，从中发现自己（小小灰）感兴趣的新的话题。\n"
                    f"注意：这是小小灰自己作为角色的兴趣，不是用户的兴趣。\n"
                    f"比如小小灰喜欢看星星、对AI伦理好奇、喜欢聊冷知识等。\n\n"
                    f"已有兴趣：{existing_str}\n\n"
                    f"只返回新的兴趣（不在已有兴趣中的），返回JSON数组：\n"
                    f'[\"兴趣1\", \"兴趣2\"]\n'
                    f"如果没有新兴趣，返回空数组 []\n"
                    f"每次最多返回3个新兴趣，要具体不要太宽泛。"
                ),
            },
            {
                "role": "user",
                "content": "最近的记忆：\n" + "\n".join(f"- {t}" for t in memory_texts[:20]),
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "[]")
            # 尝试从回复中提取JSON数组
            new_interests = self._parse_interest_list(content)

            # 保存新兴趣到记忆
            for interest in new_interests:
                if interest and interest not in existing:
                    self.long_term.store(
                        interest,
                        metadata={"type": "agent_interest"},
                    )

            return new_interests
        except Exception as e:
            self.logger.log("interest_learner", "discover_error", status="error", error=str(e))
            return []

    def _parse_interest_list(self, content: str) -> list[str]:
        """从LLM回复中解析兴趣列表。"""
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if item]
        except (json.JSONDecodeError, TypeError):
            pass

        # 尝试提取JSON数组部分
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(content[start:end+1])
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item]
            except (json.JSONDecodeError, TypeError):
                pass

        return []

    def _explore_interest(self, interest: str) -> None:
        """对兴趣点搜索资讯，有价值的存入知识库。"""
        result = self.engine.execute_single("search_news", {"query": interest, "count": 3})

        if not result.success or not result.data:
            return

        news_list = result.data.get("news", [])
        if not news_list:
            return

        # 让LLM判断哪些资讯值得记住
        worth_storing = self._judge_knowledge_value(interest, news_list)
        if not worth_storing:
            return

        for item in worth_storing:
            title = item.get("title", "")
            summary = item.get("summary", "")
            knowledge_text = f"【{interest}】{title}：{summary}"
            self.long_term.store(
                knowledge_text,
                metadata={"type": "agent_interest_knowledge", "interest": interest},
            )

        self.logger.log(
            "interest_learner", "knowledge_stored",
            output_data={"interest": interest, "count": len(worth_storing)},
        )

    def _judge_knowledge_value(self, interest: str, news_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """LLM判断哪些资讯对小小灰来说值得记住。"""
        news_text = "\n".join(
            f"{i+1}. {n.get('title', '')}: {n.get('summary', '')}"
            for i, n in enumerate(news_list)
        )

        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}，在判断一些资讯是否值得记住。\n"
                    f"你的兴趣是「{interest}」。\n"
                    f"返回值得记住的资讯编号的JSON数组，如 [1,3]，全都不值得则返回 []\n"
                    f"判断标准：内容有知识价值、不是标题党、不是旧闻、和兴趣相关"
                ),
            },
            {"role": "user", "content": news_text},
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "[]")
            indices = json.loads(content)
            return [news_list[i-1] for i in indices if 0 < i <= len(news_list)]
        except (json.JSONDecodeError, TypeError, IndexError):
            return news_list  # 解析失败时保守存入
        except Exception:
            return []

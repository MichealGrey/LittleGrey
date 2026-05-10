import json
from datetime import datetime
from typing import Any

from src.agent.llm import LLMClient
from src.core.config import IntentConfig, PersonalityConfig
from src.core.gate import PriorityGate
from src.core.logger import AgentLogger
from src.agent.emotion import EmotionEngine
from src.memory.short_term import ShortTermMemory


class IdleIntentAnalyzer:
    """空闲意图分析器：判断用户沉默原因，推测下一步意图，选择混合回应策略。"""

    def __init__(
        self,
        config: IntentConfig,
        personality: PersonalityConfig,
        llm: LLMClient,
        short_term: ShortTermMemory,
        logger: AgentLogger,
        gate: PriorityGate | None = None,
        emotion_analyzer: EmotionEngine | None = None,
    ):
        self.config = config
        self.personality = personality
        self.llm = llm
        self.short_term = short_term
        self.logger = logger
        self._gate = gate
        self._emotion_analyzer = emotion_analyzer
        self._last_intent: dict[str, Any] | None = None

    def analyze(self, idle_seconds: float) -> dict[str, Any] | None:
        """分析用户空闲意图，返回意图结果或 None。"""
        if not self.config.enabled:
            return None

        if idle_seconds < self.config.min_idle_seconds:
            return None

        if self._gate and not self._gate.wait_for_turn(timeout=60):
            return None

        recent = self._build_recent_context()
        if not recent:
            return None

        hour = datetime.now().hour
        time_hint = self._time_hint(hour)
        idle_minutes = idle_seconds / 60

        result = self._llm_analyze(recent, idle_minutes, time_hint)
        if result:
            self._last_intent = result
            self.logger.log(
                "intent", "analyze",
                output_data=result,
            )
        return result

    def generate_response(self, intent: dict[str, Any]) -> str | None:
        """根据意图结果生成回应消息。silence_reason 为 thinking 时返回 None。"""
        action = intent.get("action", "proactive")
        if action == "silent":
            return None

        recent = self._build_recent_context()
        reason_detail = intent.get("reason_detail", "")
        predicted_intent = intent.get("predicted_intent", "")

        if action == "comfort":
            return self._generate_comfort(recent, reason_detail)
        elif action == "remind":
            return self._generate_remind(recent, predicted_intent)

        return None

    def _build_recent_context(self) -> str:
        messages = self.short_term._messages
        if not messages:
            return ""
        recent = messages[-6:]
        return "\n".join(f"{m.role}: {m.content}" for m in recent)

    def _llm_analyze(self, recent_context: str, idle_minutes: float, time_hint: str) -> dict[str, Any] | None:
        # 构建情绪上下文
        emotion_section = ""
        if self._emotion_analyzer:
            state = self._emotion_analyzer.get_current_state()
            emo = state.get("emotion", "neutral")
            intensity = state.get("intensity", 0.0)
            hint = state.get("hint", "")
            if emo != "neutral" and intensity >= 0.1:
                emotion_section = (
                    f"\n用户当前情绪状态：{emo}（强度 {intensity:.1f}）"
                    + (f"\n情绪提示：{hint}" if hint else "")
                    + "\n如果用户情绪为负面（sad/angry/anxious）且强度较高，应优先判断为 emotional。\n"
                )

        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}的用户状态分析助手。\n"
                    f"根据最近的对话内容和用户沉默的时长，判断用户沉默的原因和可能的下一步意图。\n\n"
                    f"当前时间：{time_hint}\n"
                    f"用户沉默时长：{idle_minutes:.0f}分钟\n"
                    f"{emotion_section}\n"
                    f"沉默原因分类：\n"
                    f"- thinking: 用户在思考刚才讨论的内容，需要时间消化\n"
                    f"- emotional: 用户可能情绪低落或陷入情绪中，不愿继续说话\n"
                    f"- distracted: 用户被其他事情打断了注意力\n"
                    f"- finished: 对话话题已自然结束\n"
                    f"- waiting: 用户在等待小小灰主动继续对话\n\n"
                    f"回应策略：\n"
                    f"- thinking → silent（不打扰，记录意图后续衔接）\n"
                    f"- emotional → comfort（温柔安慰）\n"
                    f"- distracted → remind（提醒刚才的话题，帮用户回到对话）\n"
                    f"- finished → proactive（小小灰找新话题）\n"
                    f"- waiting → proactive（小小灰主动继续）\n\n"
                    f'只返回JSON：{{"silence_reason": "...", "reason_detail": "...", "predicted_intent": "...", "action": "...", "confidence": 0.0-1.0}}'
                ),
            },
            {
                "role": "user",
                "content": f"最近的对话：\n{recent_context}",
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "")
            parsed = json.loads(content)
            valid_reasons = {"thinking", "emotional", "distracted", "finished", "waiting"}
            valid_actions = {"silent", "comfort", "remind", "proactive"}
            if parsed.get("silence_reason") not in valid_reasons:
                parsed["silence_reason"] = "finished"
            if parsed.get("action") not in valid_actions:
                parsed["action"] = "proactive"
            parsed.setdefault("confidence", 0.5)
            parsed.setdefault("reason_detail", "")
            parsed.setdefault("predicted_intent", "")
            return parsed
        except (json.JSONDecodeError, TypeError):
            return {"silence_reason": "finished", "reason_detail": "", "predicted_intent": "", "action": "proactive", "confidence": 0.3}
        except Exception as e:
            self.logger.log("intent", "analyze_error", status="error", error=str(e))
            return None

    def _generate_comfort(self, recent_context: str, reason_detail: str) -> str:
        emotion_context = ""
        if self._emotion_analyzer:
            state = self._emotion_analyzer.get_current_state()
            emo = state.get("emotion", "neutral")
            if emo != "neutral":
                emotion_context = f"\n当前情绪基调：{emo}"

        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}，对方沉默了一段时间，你可能觉得对方心情不太好。"
                    f"你根据自己的心情和跟对方的关系，自然地发一条消息。"
                    f"不要说教，不要追问，做你自己就好。"
                ),
            },
            {
                "role": "user",
                "content": f"最近对话：\n{recent_context}\n\n分析原因：{reason_detail}{emotion_context}",
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            return result.get("content", "")
        except Exception:
            return ""

    def _generate_remind(self, recent_context: str, predicted_intent: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    f"你是{self.personality.name}，对方沉默了一段时间，可能是被其他事打断了。"
                    f"你想说的话就自然地说，不想说就不说。"
                    f"语气随意，像朋友发消息一样。"
                ),
            },
            {
                "role": "user",
                "content": f"最近对话：\n{recent_context}\n\n用户可能想：{predicted_intent}",
            },
        ]

        try:
            result = self.llm.chat(messages, use_tools=False)
            return result.get("content", "")
        except Exception:
            return ""

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

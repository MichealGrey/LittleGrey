from datetime import datetime, timedelta
from typing import Any

from src.agent.emotion_result import EmotionResult
from src.core.logger import AgentLogger


class RelationshipState:
    def __init__(
        self,
        intimacy: float = 0.1,
        trust: float = 0.3,
        interactions_count: int = 0,
        positive_interactions: int = 0,
        last_seen: str = "",
        shared_experiences: list[str] | None = None,
    ):
        self.intimacy = max(0.0, min(1.0, intimacy))
        self.trust = max(0.0, min(1.0, trust))
        self.interactions_count = interactions_count
        self.positive_interactions = positive_interactions
        self.last_seen = last_seen
        self.shared_experiences = shared_experiences or []

    @property
    def familiarity(self) -> str:
        if self.interactions_count < 5:
            return "陌生人"
        elif self.interactions_count < 20:
            return "刚认识"
        elif self.interactions_count < 50:
            return "熟人"
        elif self.interactions_count < 100:
            return "朋友"
        else:
            return "好朋友"

    @property
    def absence_hours(self) -> float:
        if not self.last_seen:
            return 999.0
        try:
            last = datetime.fromisoformat(self.last_seen)
            delta = datetime.now() - last
            return delta.total_seconds() / 3600
        except (ValueError, TypeError):
            return 999.0

    @property
    def absence_reaction(self) -> str:
        hours = self.absence_hours
        if hours < 1:
            return "刚才还聊着呢"
        elif hours < 6:
            return "刚才还聊着呢"
        elif hours < 24:
            return "今天又来啦"
        elif hours < 72:
            return "好几天没见"
        elif hours < 168:
            return "一个星期没见了"
        else:
            return "好久好久了"


class RelationshipManager:
    def __init__(self, long_term_memory: Any = None, logger: AgentLogger | None = None):
        self._ltm = long_term_memory
        self._logger = logger
        self._state = RelationshipState()
        self._load_state()

    def _load_state(self):
        if not self._ltm:
            return
        try:
            results = self._ltm.search("relationship_state", n=1)
            if results:
                data = results[0].get("metadata", {})
                self._state = RelationshipState(
                    intimacy=data.get("intimacy", 0.1),
                    trust=data.get("trust", 0.3),
                    interactions_count=data.get("interactions_count", 0),
                    positive_interactions=data.get("positive_interactions", 0),
                    last_seen=data.get("last_seen", ""),
                    shared_experiences=data.get("shared_experiences", []),
                )
        except Exception:
            pass

    def _save_state(self):
        if not self._ltm:
            return
        try:
            self._ltm.store_mood_summary(
                text="relationship_state",
                metadata={
                    "type": "relationship_state",
                    "intimacy": self._state.intimacy,
                    "trust": self._state.trust,
                    "interactions_count": self._state.interactions_count,
                    "positive_interactions": self._state.interactions_count,
                    "last_seen": self._state.last_seen,
                    "shared_experiences": self._state.shared_experiences,
                },
            )
        except Exception:
            pass

    def update(self, user_input: str, agent_emotion: EmotionResult | dict[str, Any], response: str) -> None:
        self._state.interactions_count += 1
        self._state.last_seen = datetime.now().isoformat()

        if isinstance(agent_emotion, EmotionResult):
            emotion = agent_emotion.primary_emotion
            trust_change = agent_emotion.trust_change
            intimacy_change = agent_emotion.intimacy_change
        else:
            emotion = agent_emotion.get("emotion", "neutral")
            trust_change = agent_emotion.get("trust_change", 0.0)
            intimacy_change = agent_emotion.get("intimacy_change", 0.0)

        if emotion in ("happy", "excited"):
            self._state.intimacy = min(1.0, self._state.intimacy + 0.01)
            self._state.trust = min(1.0, self._state.trust + 0.005)
            self._state.positive_interactions += 1
        elif emotion in ("sad", "angry"):
            self._state.intimacy = max(0.0, self._state.intimacy - 0.005)

        self._state.trust = max(0.0, min(1.0, self._state.trust + trust_change))
        self._state.intimacy = max(0.0, min(1.0, self._state.intimacy + intimacy_change))

        if "想你" in user_input or "喜欢你" in user_input:
            self._state.intimacy = min(1.0, self._state.intimacy + 0.05)
        if "讨厌你" in user_input:
            self._state.intimacy = max(0.0, self._state.intimacy - 0.03)
            self._state.trust = max(0.0, self._state.trust - 0.02)
        if "对不起" in user_input:
            self._state.trust = min(1.0, self._state.trust + 0.01)

        self._save_state()

    def get_emotion_weight(self) -> float:
        if self._state.intimacy < 0.2:
            return 0.5
        elif self._state.intimacy < 0.5:
            return 0.75
        elif self._state.intimacy < 0.8:
            return 1.0
        else:
            return 1.5

    def get_proactive_modifier(self) -> float:
        return 0.6 + self._state.intimacy * 0.6

    def get_tool_cooperation_modifier(self) -> float:
        return 0.7 + self._state.intimacy * 0.3

    def get_greeting_style(self) -> str:
        fam = self._state.familiarity
        if fam == "陌生人":
            return "礼貌但有距离感"
        elif fam == "刚认识":
            return "友好但不太放肆"
        elif fam == "熟人":
            return "轻松随意"
        elif fam == "朋友":
            return "亲密、会撒娇、偶尔调侃"
        else:
            return "非常亲密、会直接表达情感、放肆"

    def get_state_description(self) -> str:
        lines = [
            f"关系阶段：{self._state.familiarity}",
            f"亲密度：{self._state.intimacy:.2f}",
            f"信任度：{self._state.trust:.2f}",
            f"互动次数：{self._state.interactions_count}",
        ]
        if self._state.absence_hours > 1:
            lines.append(f"上次互动：{self._state.absence_reaction}")
        lines.append(f"说话风格：{self.get_greeting_style()}")
        return "；".join(lines)

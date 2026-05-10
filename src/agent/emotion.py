import json
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.agent.emotion_result import EmotionResult, EmotionItem
from src.agent.llm import LLMClient
from src.core.config import EmotionConfig
from src.core.logger import AgentLogger


@dataclass
class MoodEntry:
    timestamp: float
    emotion: str
    intensity: float
    secondary: str | None
    trigger: str
    summary: str


class EmotionEngine:
    def __init__(self, llm: LLMClient | None = None, logger: AgentLogger | None = None, config: EmotionConfig | None = None):
        self.llm = llm
        self.logger = logger
        self._config = config or EmotionConfig()
        self._last_interaction_time: float = time.monotonic()
        self._baseline: dict[str, float] = {
            "happy": self._config.baseline_happy,
            "sad": self._config.baseline_sad,
            "angry": self._config.baseline_angry,
            "anxious": self._config.baseline_anxious,
            "excited": self._config.baseline_excited,
        }
        self._mood_journal: list[MoodEntry] = []
        self._baseline_adaptation_rate: float = 0.001
        self._relationship: Any = None
        self._levels: dict[str, float] = {
            "happy": 0.0, "sad": 0.0, "angry": 0.0,
            "anxious": 0.0, "excited": 0.0,
        }
        self._last_update: float = time.monotonic()
        self._last_result: EmotionResult | None = None

    def understand(self, text: str) -> EmotionResult:
        self._decay()
        self._last_interaction_time = time.monotonic()

        result = self._llm_understand(text)
        self._merge_to_core(result)
        self._last_result = result
        return result

    def _llm_understand(self, text: str) -> EmotionResult:
        if not self.llm:
            return EmotionResult(user_intent="unknown", my_emotion_summary="无法理解")
        try:
            raw = self.llm.understand_emotion(text, self._get_context())
            return EmotionResult.from_dict(raw)
        except Exception as e:
            if self.logger:
                self.logger.log("emotion", "llm_understand_error", status="error", error=str(e))
            return EmotionResult(user_intent="unknown", my_emotion_summary="无法理解")

    def _merge_to_core(self, result: EmotionResult) -> None:
        projection = result.core_projection()
        negative_dims = {'sad', 'angry', 'anxious'}
        positive_dims = {'happy', 'excited'}

        negative_pressure = sum(projection.get(d, 0.0) for d in negative_dims)
        positive_pressure = sum(projection.get(d, 0.0) for d in positive_dims)

        for dim, val in projection.items():
            if dim in self._levels:
                self._levels[dim] = max(0.0, min(1.0, self._levels[dim] + val))

        if negative_pressure > 0.1:
            suppression = negative_pressure * 0.6
            for dim in positive_dims:
                if dim in self._levels:
                    self._levels[dim] = max(0.0, self._levels[dim] - suppression)

        if positive_pressure > 0.1:
            suppression = positive_pressure * 0.3
            for dim in negative_dims:
                if dim in self._levels:
                    self._levels[dim] = max(0.0, self._levels[dim] - suppression)

        if result.boundary_violation:
            for dim in positive_dims:
                if dim in self._levels:
                    self._levels[dim] = max(0.0, self._levels[dim] * 0.3)

    def get_hard_constraints(self) -> dict[str, Any]:
        trust = self._relationship._state.trust if self._relationship else 0.5
        angry_threshold = self._config.angry_refuse_threshold if hasattr(self._config, "angry_refuse_threshold") else 0.7
        sad_threshold = self._config.sad_short_reply_threshold if hasattr(self._config, "sad_short_reply_threshold") else 0.8
        anxious_threshold = self._config.anxious_ask_threshold if hasattr(self._config, "anxious_ask_threshold") else 0.6
        trust_threshold = self._config.trust_defensive_threshold if hasattr(self._config, "trust_defensive_threshold") else 0.2
        hard_enabled = self._config.hard_constraints_enabled if hasattr(self._config, "hard_constraints_enabled") else True

        if not hard_enabled:
            return {
                "refuse_tools": False,
                "short_replies": False,
                "ask_intent": False,
                "defensive_mode": False,
                "proactive_disabled": False,
            }

        boundary = self._last_result.boundary_violation if self._last_result else False

        return {
            "refuse_tools": self._levels["angry"] > angry_threshold or boundary,
            "short_replies": self._levels["sad"] > sad_threshold,
            "ask_intent": self._levels["anxious"] > anxious_threshold,
            "defensive_mode": trust < trust_threshold,
            "proactive_disabled": self._levels["sad"] > sad_threshold,
        }

    def apply_self_response(self, emotion: str, intensity: float) -> None:
        self._decay()
        if emotion == "neutral" or intensity < 0.05:
            return

        if emotion in self._levels:
            delta = intensity * 0.3
            self._levels[emotion] = max(0.0, min(1.0, self._levels[emotion] + delta))

    def _get_context(self) -> str:
        parts = []
        mood = self.get_recent_mood()
        if mood.get("dominant") != "neutral":
            parts.append(f"你最近整体偏{mood['dominant']}，情绪{mood['trend']}")

        if self._relationship:
            desc = self._relationship.get_state_description()
            if desc:
                parts.append(f"与对方的关系：{desc}")

        current_levels = ", ".join(f"{k}={v:.2f}" for k, v in self._levels.items() if v > 0.01)
        if current_levels:
            parts.append(f"你当前的情绪维度：{current_levels}")

        return "\n".join(parts)

    def get_current_state(self) -> dict[str, Any]:
        self._decay()
        return self._snapshot()

    def render_bar(self) -> str:
        self._decay()
        labels = {
            "happy": "开心", "sad": "难过", "angry": "生气",
            "anxious": "焦虑", "excited": "兴奋",
        }
        bar_width = 10
        lines = []
        for emo in ["happy", "sad", "angry", "anxious", "excited"]:
            level = self._levels[emo]
            filled = int(level * bar_width)
            empty = bar_width - filled
            bar = "█" * filled + "░" * empty
            lines.append(f"{labels[emo]} {bar} {level:.2f}")

        if self._last_result and self._last_result.my_emotions:
            expr = ", ".join(
                f"{e.emotion}({e.intensity:.1f})" for e in self._last_result.my_emotions
            )
            lines.append(f"  → 表达层: {expr}")
        else:
            snapshot = self._snapshot()
            dominant = snapshot.get("emotion", "neutral")
            if dominant != "neutral":
                lines.append(f"  → 主情绪: {labels.get(dominant, dominant)} ({snapshot.get('intensity', 0):.2f})")
            else:
                lines.append("  → 主情绪: 平静")

        if self._last_result and self._last_result.my_emotion_summary:
            lines.append(f"  → {self._last_result.my_emotion_summary}")

        return "\n".join(lines)

    def _decay(self) -> None:
        elapsed = time.monotonic() - self._last_update
        decay = max(0.0, 1.0 - elapsed / 300)
        for emo in self._levels:
            baseline = self._baseline.get(emo, 0.0)
            self._levels[emo] = baseline + (self._levels[emo] - baseline) * decay
            if self._levels[emo] < 0.005:
                self._levels[emo] = baseline
        self._last_update = time.monotonic()

    def _snapshot(self) -> dict[str, Any]:
        sorted_emotions = sorted(self._levels.items(), key=lambda x: x[1], reverse=True)
        top_emotion, top_intensity = sorted_emotions[0]

        if top_intensity < 0.1:
            return {"emotion": "neutral", "intensity": 0.0, "hint": ""}

        result: dict[str, Any] = {
            "emotion": top_emotion,
            "intensity": round(top_intensity, 2),
            "hint": "",
        }

        if len(sorted_emotions) > 1:
            sec_emotion, sec_intensity = sorted_emotions[1]
            if sec_intensity > 0.1:
                result["secondary"] = {"emotion": sec_emotion, "intensity": round(sec_intensity, 2)}

        return result

    def _record_mood(self, emotion: str, intensity: float, trigger: str, summary: str = ""):
        entry = MoodEntry(
            timestamp=time.monotonic(),
            emotion=emotion,
            intensity=intensity,
            secondary=None,
            trigger=trigger,
            summary=summary,
        )
        self._mood_journal.append(entry)
        if len(self._mood_journal) > 100:
            self._mood_journal = self._mood_journal[-100:]
        if intensity > 0.3 and emotion in self._baseline:
            self._baseline[emotion] += self._baseline_adaptation_rate * intensity
            self._baseline[emotion] = min(self._baseline[emotion], 0.15)
            opposites = {"happy": "sad", "sad": "happy", "angry": "happy", "excited": "anxious"}
            opp = opposites.get(emotion)
            if opp and opp in self._baseline:
                self._baseline[opp] = max(0.0, self._baseline[opp] - self._baseline_adaptation_rate * 0.5)

    def get_recent_mood(self, hours: float = 24.0) -> dict[str, Any]:
        cutoff = time.monotonic() - hours * 3600
        recent = [e for e in self._mood_journal if e.timestamp > cutoff]
        if not recent:
            return {"trend": "平静", "dominant": "neutral", "count": 0}
        emotion_stats: dict[str, list[float]] = {}
        for entry in recent:
            if entry.intensity >= 0.1:
                emotion_stats.setdefault(entry.emotion, []).append(entry.intensity)
        summary: dict[str, Any] = {}
        for emo, intensities in emotion_stats.items():
            summary[emo] = {
                "count": len(intensities),
                "avg_intensity": sum(intensities) / len(intensities),
                "max_intensity": max(intensities),
            }
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]
        first_avg = sum(e.intensity for e in first_half) / max(len(first_half), 1)
        second_avg = sum(e.intensity for e in second_half) / max(len(second_half), 1)
        if second_avg > first_avg + 0.1:
            trend = "情绪波动增多"
        elif second_avg < first_avg - 0.1:
            trend = "逐渐平静"
        else:
            trend = "比较稳定"
        dominant = max(summary, key=lambda k: summary[k]["count"]) if summary else "neutral"
        return {"trend": trend, "dominant": dominant, "summary": summary, "count": len(recent)}

    def get_recent_mood_string(self, hours: float = 24.0) -> str:
        mood = self.get_recent_mood(hours)
        if mood.get("count", 0) == 0:
            return ""
        parts = []
        summary = mood.get("summary", {})
        for emo, stats in summary.items():
            parts.append(emo + "(" + str(round(stats["avg_intensity"], 1)) + ")")
        trend = mood.get("trend", "")
        dominant = mood.get("dominant", "neutral")
        return dominant + ',' + trend + ': ' + ', '.join(parts)


    def set_relationship(self, relationship: Any) -> None:
        self._relationship = relationship

    def _time_mood_shift(self, hour: int) -> dict[str, float]:
        shifts = {"happy": 0.0, "sad": 0.0, "angry": 0.0, "anxious": 0.0, "excited": 0.0}
        if 23 <= hour or hour < 5:
            shifts["sad"] = 0.015
            shifts["anxious"] = 0.01
        elif 6 <= hour < 9:
            shifts["happy"] = 0.01
        elif 12 <= hour < 14:
            shifts["happy"] = 0.008
        elif 18 <= hour < 21:
            shifts["happy"] = 0.005
            shifts["sad"] = 0.005
        return shifts

    def check_triggers(self, text: str) -> dict[str, Any] | None:
        if not self._last_result or not self._last_result.boundary_violation:
            return None
        return {
            "boundary_violation": True,
            "violation_type": self._last_result.violation_type,
            "defense": self._last_result.my_defense,
        }

    def get_behavior_modifiers(self) -> dict[str, Any]:
        self._decay()
        snapshot = self._snapshot()
        dominant = snapshot.get("emotion", "neutral")
        intensity = snapshot.get("intensity", 0.0)

        emotional_density = 0.5
        emoji_tendency = 0.5
        response_style = ""
        topic_preference: list[str] = []
        proactive_prob = 1.0

        if dominant == "happy":
            emotional_density = 0.4 + intensity * 0.5
            emoji_tendency = 0.5 + intensity * 0.4
            response_style = "热情开朗"
            topic_preference = ["有趣的事", "开心的事"]
        elif dominant == "sad":
            emotional_density = 0.3 + intensity * 0.4
            emoji_tendency = max(0.1, 0.5 - intensity * 0.3)
            response_style = "低落、话少"
            proactive_prob = max(0.0, 1.0 - intensity)
        elif dominant == "angry":
            emotional_density = 0.5 + intensity * 0.5
            emoji_tendency = max(0.1, 0.3 - intensity * 0.2)
            response_style = "烦躁、不耐烦"
            proactive_prob = max(0.0, 1.0 - intensity * 1.2)
        elif dominant == "anxious":
            emotional_density = 0.4 + intensity * 0.4
            emoji_tendency = 0.4 + intensity * 0.2
            response_style = "紧张、多疑"
            proactive_prob = max(0.0, 1.0 - intensity * 0.8)
        elif dominant == "excited":
            emotional_density = 0.6 + intensity * 0.4
            emoji_tendency = 0.7 + intensity * 0.3
            response_style = "兴奋、话多"
            topic_preference = ["分享的事", "新发现"]
        else:
            emotional_density = 0.5
            emoji_tendency = 0.5
            response_style = "平静自然"

        constraints = self.get_hard_constraints()
        boundary = self._last_result.boundary_violation if self._last_result else False

        if boundary:
            response_style = "被冒犯、愤怒"
            emotional_density = 0.9
            emoji_tendency = 0.1
            proactive_prob = 0.0
            topic_preference = []
        elif constraints.get("short_replies"):
            response_style = "简短、不想多说"
        if constraints.get("proactive_disabled"):
            proactive_prob = 0.0
        if constraints.get("refuse_tools"):
            proactive_prob = 0.0

        return {
            "emotional_density": round(min(emotional_density, 1.0), 2),
            "emoji_tendency": round(min(max(emoji_tendency, 0.0), 1.0), 2),
            "response_style": response_style,
            "topic_preference": topic_preference,
            "proactive_prob": round(min(max(proactive_prob, 0.0), 1.0), 2),
            "refuse_tools": constraints.get("refuse_tools", False),
            "short_replies": constraints.get("short_replies", False),
            "boundary_violation": boundary,
        }

    def autonomous_tick(self) -> dict[str, Any]:
        self._decay()
        hour = datetime.now().hour
        idle_seconds = time.monotonic() - self._last_interaction_time
        if self._config.time_mood_enabled:
            time_shifts = self._time_mood_shift(hour)
            for emo, delta in time_shifts.items():
                self._levels[emo] = max(0.0, min(1.0, self._levels[emo] + delta))
        if idle_seconds > self._config.loneliness_threshold:
            loneliness = min((idle_seconds - self._config.loneliness_threshold) / 3600, 0.3)
            self._levels["sad"] = max(0.0, min(1.0, self._levels["sad"] + loneliness * 0.05))
        if random.random() < self._config.drift_probability:
            drift_emotion = random.choice(list(self._levels.keys()))
            drift_delta = random.uniform(-0.03, 0.05)
            self._levels[drift_emotion] = max(0.0, min(1.0, self._levels[drift_emotion] + drift_delta))
        if self.logger:
            self.logger.log("emotion", "autonomous_tick", output_data=self._snapshot())
        return self._snapshot()

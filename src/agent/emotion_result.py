from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmotionItem:
    emotion: str
    intensity: float
    core: dict[str, float] = field(default_factory=dict)


@dataclass
class EmotionResult:
    user_intent: str = ""
    user_attitude: str = ""
    my_emotions: list[EmotionItem] = field(default_factory=list)
    my_emotion_summary: str = ""
    boundary_violation: bool = False
    violation_type: str = ""
    my_need: str = ""
    my_desire: str = ""
    my_energy: str = ""
    my_defense: str = ""
    trust_change: float = 0.0
    intimacy_change: float = 0.0
    memory_weight: float = 0.5
    memory_summary: str = ""
    physical_state: str = ""
    energy_change: float = 0.0
    wants_interaction: bool = False
    wants_solitude: bool = False
    feels_purposeless: bool = False

    @property
    def primary_emotion(self) -> str:
        if not self.my_emotions:
            return "neutral"
        return self.my_emotions[0].emotion

    @property
    def primary_intensity(self) -> float:
        if not self.my_emotions:
            return 0.0
        return self.my_emotions[0].intensity

    def core_projection(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for item in self.my_emotions:
            for dim, val in item.core.items():
                result[dim] = result.get(dim, 0.0) + val
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmotionResult":
        emotions = []
        for e in data.get("my_emotions", []):
            emotions.append(EmotionItem(
                emotion=e.get("emotion", ""),
                intensity=float(e.get("intensity", 0.0)),
                core=e.get("core", {}),
            ))
        return cls(
            user_intent=data.get("user_intent", ""),
            user_attitude=data.get("user_attitude", ""),
            my_emotions=emotions,
            my_emotion_summary=data.get("my_emotion_summary", ""),
            boundary_violation=bool(data.get("boundary_violation", False)),
            violation_type=data.get("violation_type", ""),
            my_need=data.get("my_need", ""),
            my_desire=data.get("my_desire", ""),
            my_energy=data.get("my_energy", ""),
            my_defense=data.get("my_defense", ""),
            trust_change=float(data.get("trust_change", 0.0)),
            intimacy_change=float(data.get("intimacy_change", 0.0)),
            memory_weight=float(data.get("memory_weight", 0.5)),
            memory_summary=data.get("memory_summary", ""),
            physical_state=data.get("physical_state", ""),
            energy_change=float(data.get("energy_change", 0.0)),
            wants_interaction=bool(data.get("wants_interaction", False)),
            wants_solitude=bool(data.get("wants_solitude", False)),
            feels_purposeless=bool(data.get("feels_purposeless", False)),
        )

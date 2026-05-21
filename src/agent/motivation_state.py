from dataclasses import dataclass, field


@dataclass
class MotivationState:
    current_need: str = ""
    current_desire: str = ""
    current_energy: str = ""
    wants_interaction: bool = False
    wants_solitude: bool = False
    feels_purposeless: bool = False

    def has_drive(self) -> bool:
        return bool(self.current_need or self.current_desire)

    def to_prompt_snippet(self) -> str:
        parts = []
        if self.current_need:
            parts.append(f"内心需要：{self.current_need}")
        if self.current_desire:
            parts.append(f"此刻想做：{self.current_desire}")
        if self.current_energy:
            parts.append(f"精力感受：{self.current_energy}")
        return "；".join(parts)

    @classmethod
    def from_dict(cls, data: dict) -> "MotivationState":
        return cls(
            current_need=data.get("my_need", "")[:30],
            current_desire=data.get("my_desire", "")[:30],
            current_energy=data.get("my_energy", "")[:10],
            wants_interaction=bool(data.get("wants_interaction", False)),
            wants_solitude=bool(data.get("wants_solitude", False)),
            feels_purposeless=bool(data.get("feels_purposeless", False)),
        )

import os

content = '''from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class TokenType(str, Enum):
    COT = "COT"
    NARR = "NARR"
    DIALOG = "DIALOG"
    CHOICE = "CHOICE"
    STAT = "STAT"


@dataclass
class DialogToken:
    type: TokenType
    text: str
    character: Optional[str] = None
    options: list[str] = field(default_factory=list)
    stat_changes: dict[str, float] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "text": self.text,
            "character": self.character,
            "options": self.options,
            "stat_changes": self.stat_changes,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DialogToken":
        return class(
            type=TokenType(data.get("type", "DIALOG")),
            text=data.get("text", ""),
            character=data.get("character"),
            options=data.get("options", []),
            stat_changes=data.get("stat_changes", {}),
            metadata=data.get("metadata", {})
        )
'''

os.makedirs('extensions/dialog', exist_ok=True)
with open('extensions/dialog/tokens.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('tokens.py created')

from abc import ABC, abstractmethod
from typing import Any

from jsonschema import validate, ValidationError

from src.core.types import ToolResult


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    input_schema: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    is_risky: bool = False

    @abstractmethod
    def execute(self, params: dict[str, Any]) -> ToolResult:
        ...

    def validate_input(self, params: dict[str, Any]) -> tuple[bool, str]:
        if not self.input_schema:
            return True, ""
        try:
            validate(instance=params, schema=self.input_schema)
            return True, ""
        except ValidationError as e:
            return False, str(e.message)

    def check_risky(self, params: dict[str, Any]) -> tuple[bool, str]:
        if not self.is_risky:
            return False, ""
        return self._risk_check(params)

    def _risk_check(self, params: dict[str, Any]) -> tuple[bool, str]:
        return False, ""

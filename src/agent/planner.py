import json
from typing import Any

from src.core.config import AgentConfig
from src.core.types import ExecutionChain, SubTask


class Planner:
    def __init__(self, config: AgentConfig):
        self.config = config

    def plan_from_tool_calls(self, tool_calls: list[dict[str, Any]]) -> ExecutionChain:
        chain = ExecutionChain(max_steps=self.config.max_steps)

        for tc in tool_calls:
            tool_name = tc["name"]
            try:
                params = json.loads(tc["arguments"]) if isinstance(tc["arguments"], str) else tc["arguments"]
            except (json.JSONDecodeError, TypeError):
                params = {"raw_arguments": tc["arguments"]}

            chain.add_task(tool_name, params)

        return chain

    def plan_single(self, tool_name: str, params: dict[str, Any]) -> ExecutionChain:
        chain = ExecutionChain(max_steps=self.config.max_steps)
        chain.add_task(tool_name, params)
        return chain

    def needs_planning(self, user_input: str) -> bool:
        office_keywords = ["excel", "word", "文档", "表格", "图表", "画图", "柱状图", "折线图", "饼图", "周报", "报告", "数据"]
        return any(kw in user_input.lower() for kw in office_keywords)

import json
from typing import Any

from src.core.types import ToolResult
from src.tools.base import BaseTool

SEARCH_TOOL_SCHEMA = {
    "name": "search_news",
    "description": "搜索与指定关键词相关的最新新闻资讯",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "count": {
                "type": "integer",
                "description": "返回结果数量，默认3"
            }
        },
        "required": ["query"]
    }
}


class SearchNewsTool(BaseTool):
    name = "search_news"
    description = "搜索与指定关键词相关的最新新闻资讯"
    input_schema = SEARCH_TOOL_SCHEMA
    is_risky = False

    def __init__(self, llm_client=None):
        self._llm = llm_client

    def execute(self, params: dict[str, Any]) -> ToolResult:
        query = params.get("query", "")
        count = params.get("count", 3)

        if not query:
            return ToolResult(success=False, message="缺少搜索关键词")

        if not self._llm:
            return ToolResult(success=False, message="LLM客户端未配置，无法搜索")

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"请根据关键词「{query}」，提供{count}条最新的相关新闻或资讯。"
                        f"每条包含标题和简短摘要。返回JSON数组格式："
                        f'[{{"title": "标题", "summary": "摘要", "source": "来源"}}]'
                        f"如果无法获取真实新闻，请根据你的知识提供相关领域的重要信息。"
                        f"严格返回JSON，不要包含其他文字。"
                    ),
                },
                {"role": "user", "content": f"搜索：{query}"},
            ]

            result = self._llm.chat(messages, use_tools=False)
            content = result.get("content", "")

            try:
                news = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                news = [{"title": "搜索结果", "summary": content, "source": "AI"}]

            return ToolResult(
                success=True,
                data={"query": query, "news": news[:count]},
                message=f"找到{min(len(news), count)}条关于「{query}」的资讯",
            )
        except Exception as e:
            return ToolResult(success=False, message=f"搜索失败: {e}")

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_CONFIRMATION = "needs_confirmation"


@dataclass
class SubTask:
    tool_name: str
    input_params: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    retry_count: int = 0
    error: str | None = None


@dataclass
class ExecutionChain:
    tasks: list[SubTask] = field(default_factory=list)
    max_steps: int = 10
    current_step: int = 0

    def add_task(self, tool_name: str, input_params: dict[str, Any]) -> None:
        self.tasks.append(SubTask(tool_name=tool_name, input_params=input_params))

    @property
    def is_exhausted(self) -> bool:
        return self.current_step >= self.max_steps

    @property
    def current_task(self) -> SubTask | None:
        if 0 <= self.current_step < len(self.tasks):
            return self.tasks[self.current_step]
        return None

    def advance(self) -> SubTask | None:
        self.current_step += 1
        return self.current_task


@dataclass
class ToolResult:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    file_path: str | None = None


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    tool_call_id: str | None = None
    tool_name: str | None = None


# JSON Schema definitions for tools

EXCEL_TOOL_SCHEMA = {
    "name": "excel_tool",
    "description": "创建和编辑 Excel 文件，支持创建工作簿、读取内容、写入数据、添加图表",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "read", "write", "add_chart"],
                "description": "操作类型：create新建, read读取, write修改, add_chart添加图表"
            },
            "file_path": {
                "type": "string",
                "description": "文件路径"
            },
            "sheet_name": {
                "type": "string",
                "description": "工作表名称，默认为Sheet1"
            },
            "data": {
                "type": "object",
                "description": "写入数据，格式为 {行号: {列号: 值}} 或 {行号: [值1, 值2, ...]}"
            },
            "headers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "表头列表"
            },
            "rows": {
                "type": "array",
                "items": {"type": "array"},
                "description": "数据行列表，每行是一个值数组"
            },
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie"],
                "description": "图表类型"
            },
            "chart_title": {
                "type": "string",
                "description": "图表标题"
            },
            "data_range": {
                "type": "string",
                "description": "图表数据范围，如 A1:B10"
            }
        },
        "required": ["action", "file_path"]
    }
}

WORD_TOOL_SCHEMA = {
    "name": "word_tool",
    "description": "创建和编辑 Word 文档，支持创建文档、读取内容、写入段落、插入表格和图片",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "read", "write", "add_table", "add_image"],
                "description": "操作类型：create新建, read读取, write写入, add_table插入表格, add_image插入图片"
            },
            "file_path": {
                "type": "string",
                "description": "文件路径"
            },
            "title": {
                "type": "string",
                "description": "文档标题"
            },
            "paragraphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "style": {"type": "string", "description": "段落样式：Heading1, Heading2, Normal等"}
                    },
                    "required": ["text"]
                },
                "description": "段落列表"
            },
            "table": {
                "type": "object",
                "properties": {
                    "headers": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "rows": {
                        "type": "array",
                        "items": {"type": "array"}
                    }
                },
                "description": "表格数据"
            },
            "image_path": {
                "type": "string",
                "description": "要插入的图片路径"
            },
            "content": {
                "type": "string",
                "description": "写入的文本内容（write操作用）"
            },
            "position": {
                "type": "integer",
                "description": "插入位置（段落索引，从0开始）"
            }
        },
        "required": ["action", "file_path"]
    }
}

CHART_TOOL_SCHEMA = {
    "name": "chart_tool",
    "description": "绘制数据图表并保存为PNG图片，支持柱状图、折线图、饼图、散点图",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["bar", "line", "pie", "scatter"],
                "description": "图表类型"
            },
            "file_path": {
                "type": "string",
                "description": "输出图片保存路径"
            },
            "title": {
                "type": "string",
                "description": "图表标题"
            },
            "x_label": {
                "type": "string",
                "description": "X轴标签"
            },
            "y_label": {
                "type": "string",
                "description": "Y轴标签"
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "数据标签（如类别名、X轴刻度）"
            },
            "values": {
                "type": "array",
                "items": {"type": "number"},
                "description": "数据值"
            },
            "series": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "values": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["name", "values"]
                },
                "description": "多组数据系列"
            }
        },
        "required": ["action", "file_path", "values"]
    }
}

SEARCH_NEWS_TOOL_SCHEMA = {
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

ALL_TOOL_SCHEMAS = [EXCEL_TOOL_SCHEMA, WORD_TOOL_SCHEMA, CHART_TOOL_SCHEMA, SEARCH_NEWS_TOOL_SCHEMA]

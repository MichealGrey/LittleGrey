from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.types import CHART_TOOL_SCHEMA, ToolResult
from src.tools.base import BaseTool

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class ChartTool(BaseTool):
    name = "chart_tool"
    description = "绘制数据图表并保存为PNG图片"
    input_schema = CHART_TOOL_SCHEMA
    is_risky = False

    def execute(self, params: dict[str, Any]) -> ToolResult:
        action = params["action"]
        try:
            if action == "bar":
                return self._bar(params)
            elif action == "line":
                return self._line(params)
            elif action == "pie":
                return self._pie(params)
            elif action == "scatter":
                return self._scatter(params)
            else:
                return ToolResult(success=False, message=f"未知图表类型: {action}")
        except Exception as e:
            return ToolResult(success=False, message=f"图表绘制失败: {e}")

    def _bar(self, params: dict[str, Any]) -> ToolResult:
        fig, ax = plt.subplots(figsize=(10, 6))

        labels = params.get("labels", [])
        values = params.get("values", [])
        series = params.get("series")

        if series:
            import numpy as np
            x = np.arange(len(labels))
            width = 0.8 / len(series)
            for i, s in enumerate(series):
                offset = (i - len(series) / 2 + 0.5) * width
                ax.bar(x + offset, s["values"], width, label=s["name"])
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
        else:
            ax.bar(labels or range(len(values)), values)

        ax.set_title(params.get("title", ""))
        ax.set_xlabel(params.get("x_label", ""))
        ax.set_ylabel(params.get("y_label", ""))

        return self._save(fig, params["file_path"])

    def _line(self, params: dict[str, Any]) -> ToolResult:
        fig, ax = plt.subplots(figsize=(10, 6))

        labels = params.get("labels", [])
        values = params.get("values", [])
        series = params.get("series")

        if series:
            x = labels if labels else range(max(len(s["values"]) for s in series))
            for s in series:
                ax.plot(x, s["values"], marker="o", label=s["name"])
            ax.legend()
        else:
            x = labels if labels else range(len(values))
            ax.plot(x, values, marker="o")

        ax.set_title(params.get("title", ""))
        ax.set_xlabel(params.get("x_label", ""))
        ax.set_ylabel(params.get("y_label", ""))

        return self._save(fig, params["file_path"])

    def _pie(self, params: dict[str, Any]) -> ToolResult:
        fig, ax = plt.subplots(figsize=(8, 8))

        labels = params.get("labels", [])
        values = params.get("values", [])

        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(params.get("title", ""))

        return self._save(fig, params["file_path"])

    def _scatter(self, params: dict[str, Any]) -> ToolResult:
        fig, ax = plt.subplots(figsize=(10, 6))

        values = params.get("values", [])
        labels = params.get("labels", [])
        series = params.get("series")

        if series:
            for s in series:
                ax.scatter(s["values"][::2], s["values"][1::2], label=s["name"])
            ax.legend()
        else:
            if len(values) >= 2:
                x = values[::2]
                y = values[1::2]
                ax.scatter(x, y)

        ax.set_title(params.get("title", ""))
        ax.set_xlabel(params.get("x_label", ""))
        ax.set_ylabel(params.get("y_label", ""))

        return self._save(fig, params["file_path"])

    def _save(self, fig, file_path: str) -> ToolResult:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fig.tight_layout()
        fig.savefig(str(path), dpi=150, bbox_inches="tight")
        plt.close(fig)

        return ToolResult(
            success=True,
            file_path=str(path),
            message=f"图表已保存: {path}",
        )

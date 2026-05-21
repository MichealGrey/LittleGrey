import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from threading import Lock


class ThoughtLogger:
    """
    零 token 消耗的 LLM 思考过程记录器。
    记录 reasoning_content、完整请求/响应、调用元数据。
    """

    def __init__(self, log_dir: str | Path, max_file_size_mb: int = 50):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self._lock = Lock()
        self._current_file_size = 0
        self._current_file: Path | None = None

    def _get_log_file(self) -> Path:
        if self._current_file is None or self._current_file_size >= self.max_file_size:
            date_str = datetime.now().strftime("%Y-%m-%d")
            self._current_file = self.log_dir / f"thought_{date_str}.jsonl"
            self._current_file_size = self._current_file.stat().st_size if self._current_file.exists() else 0
        return self._current_file

    def log_thought(
        self,
        model: str,
        messages: list[dict[str, Any]],
        response_content: str,
        reasoning_content: str = "",
        tool_calls: list[dict] | None = None,
        duration_ms: float = 0,
        trace_id: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        """记录一次 LLM 思考过程"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "trace_id": trace_id,
            "duration_ms": round(duration_ms, 2),
        }
        if reasoning_content:
            entry["reasoning"] = reasoning_content
        entry["response"] = response_content
        if tool_calls:
            entry["tool_calls"] = tool_calls
        if extra:
            entry.update({k: _safe_serialize(v) for k, v in extra.items()})
        entry["context"] = {
            "system_prompt": messages[0]["content"] if messages and messages[0].get("role") == "system" else "",
            "user_message": _extract_last_user_message(messages),
        }
        with self._lock:
            log_file = self._get_log_file()
            line = json.dumps(entry, ensure_ascii=False) + "\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line)
            self._current_file_size += len(line.encode("utf-8"))

    def get_recent_thoughts(self, limit: int = 10, trace_id: str = "") -> list[dict]:
        """获取最近的思考记录"""
        results = []
        log_files = sorted(self.log_dir.glob("thought_*.jsonl"), reverse=True)
        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in reversed(list(f)):
                    entry = json.loads(line.strip())
                    if trace_id and entry.get("trace_id") != trace_id:
                        continue
                    results.append(entry)
                    if len(results) >= limit:
                        return results
        return results


def _extract_last_user_message(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")[:500]
    return ""


def _safe_serialize(obj: Any) -> Any:
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(v) for v in obj]
    return str(obj)
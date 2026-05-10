import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class AgentLogger:
    def __init__(self, log_dir: str | Path, level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = level
        self._trace_id: str | None = None

    def new_trace(self) -> str:
        self._trace_id = uuid.uuid4().hex[:12]
        return self._trace_id

    @property
    def trace_id(self) -> str | None:
        return self._trace_id

    def _log_file(self) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"agent_{date_str}.jsonl"

    def log(
        self,
        module: str,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        duration: float | None = None,
        status: str = "ok",
        error: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "trace_id": self._trace_id,
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "action": action,
            "status": status,
        }
        if input_data is not None:
            entry["input"] = _safe_serialize(input_data)
        if output_data is not None:
            entry["output"] = _safe_serialize(output_data)
        if duration is not None:
            entry["duration_ms"] = round(duration * 1000, 2)
        if error is not None:
            entry["error"] = error
        if extra:
            entry.update({k: _safe_serialize(v) for k, v in extra.items()})

        line = json.dumps(entry, ensure_ascii=False)
        with open(self._log_file(), "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def trace_query(self, trace_id: str) -> list[dict]:
        results = []
        for log_file in sorted(self.log_dir.glob("agent_*.jsonl")):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("trace_id") == trace_id:
                        results.append(entry)
        return results


class StepTimer:
    def __init__(self, logger: AgentLogger, module: str, action: str):
        self.logger = logger
        self.module = module
        self.action = action
        self.input_data: Any = None

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.monotonic() - self.start
        if exc_type:
            self.logger.log(
                self.module, self.action,
                input_data=self.input_data,
                duration=duration,
                status="error",
                error=str(exc_val),
            )
        else:
            self.logger.log(
                self.module, self.action,
                input_data=self.input_data,
                duration=duration,
                status="ok",
            )
        return False


def _safe_serialize(obj: Any) -> Any:
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return [_safe_serialize(v) for v in obj]
    return str(obj)

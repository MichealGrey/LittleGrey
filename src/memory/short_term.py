import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.config import MemoryConfig
from src.core.types import ChatMessage


class ShortTermMemory:
    def __init__(self, config: MemoryConfig, summary_fn=None, gate=None):
        self.max_messages = config.short_term_max
        self.summary_threshold = config.summary_threshold
        self._messages: list[ChatMessage] = []
        self._summary: str = ""
        self._summary_fn = summary_fn
        self._gate = gate
        self._compress_lock = threading.Lock()

    def add(self, role: str, content: str, **kwargs: Any) -> None:
        msg = ChatMessage(role=role, content=content, **kwargs)
        self._messages.append(msg)

        if len(self._messages) >= self.summary_threshold and self._summary_fn:
            self._schedule_compress()

    def get_messages(self) -> list[dict[str, Any]]:
        result = []
        if self._summary:
            result.append({"role": "system", "content": f"[之前的对话摘要]\n{self._summary}"})
        for msg in self._messages:
            entry: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_name:
                entry["tool_name"] = msg.tool_name
            result.append(entry)
        return result

    def _schedule_compress(self) -> None:
        thread = threading.Thread(target=self._compress_async, daemon=True)
        thread.start()

    def _compress_async(self) -> None:
        if not self._compress_lock.acquire(blocking=False):
            return
        try:
            if self._gate:
                self._gate.wait_for_turn(timeout=120)
            self._compress()
        finally:
            self._compress_lock.release()

    def _compress(self) -> None:
        """将旧消息压缩为摘要，释放消息槽位。"""
        compress_count = len(self._messages) - self.max_messages + 5
        if compress_count <= 0:
            return

        old_messages = self._messages[:compress_count]
        self._messages = self._messages[compress_count:]

        if self._summary_fn:
            old_text = "\n".join(f"{m.role}: {m.content}" for m in old_messages)
            self._summary = self._summary_fn(old_text, self._summary)
        else:
            old_text = "\n".join(f"{m.role}: {m.content}" for m in old_messages)
            self._summary = (self._summary + "\n" + old_text).strip()[-2000:]

    def merge_messages(self, idx_a: int, idx_b: int, merged_content: str) -> None:
        self._messages[idx_a].content = merged_content
        self._messages.pop(idx_b)

    def clear(self) -> None:
        self._messages = []
        self._summary = ""

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "summary": self._summary,
            "messages": [
                {"role": m.role, "content": m.content, "tool_name": m.tool_name}
                for m in self._messages
            ],
            "saved_at": datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: Path) -> None:
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._summary = data.get("summary", "")
        self._messages = [
            ChatMessage(role=m["role"], content=m["content"], tool_name=m.get("tool_name"))
            for m in data.get("messages", [])
        ]

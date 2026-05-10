from typing import Any

from src.memory.long_term import LongTermMemory


class RAG:
    def __init__(self, long_term_memory: LongTermMemory, top_k: int = 5):
        self.long_term = long_term_memory
        self.top_k = top_k

    def retrieve(self, query: str) -> str:
        results = self.long_term.search(query, top_k=self.top_k)
        if not results:
            return ""

        context_parts = []
        for item in results:
            text = item["text"]
            meta = item.get("metadata", {})
            mem_type = meta.get("type", "")
            relevance = item.get("relevance", 0)
            if relevance < 0.3:
                continue
            context_parts.append(f"[{mem_type}] {text}")

        return "\n".join(context_parts)

    def build_context(self, current_query: str) -> str:
        retrieved = self.retrieve(current_query)
        if not retrieved:
            return ""
        return f"以下是与当前对话相关的历史记忆：\n{retrieved}"

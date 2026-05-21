from typing import Any

from src.memory.long_term import LongTermMemory
from src.memory.rag_cache import RAGCache


class RAG:
    def __init__(self, long_term_memory: LongTermMemory, top_k: int = 3):
        self.long_term = long_term_memory
        self.top_k = top_k
        self._cache = RAGCache(max_size=64, ttl_seconds=300)

    def retrieve(self, query: str) -> str:
        cached = self._cache.get(query)
        if cached is not None:
            return cached
        results = self.long_term.search(query, top_k=self.top_k * 2)
        if not results:
            return ""

        for item in results:
            meta = item.get("metadata", {})
            importance = meta.get("importance", 0.5)
            base_relevance = item.get("relevance", 0)
            item["relevance"] = base_relevance * (0.5 + importance * 0.5)

        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        results = results[:self.top_k]

        context_parts = []
        for item in results:
            text = item["text"]
            meta = item.get("metadata", {})
            mem_type = meta.get("type", "")
            relevance = item.get("relevance", 0)
            if relevance < 0.3:
                continue
            context_parts.append(f"[{mem_type}] {text}")

        result = "\n".join(context_parts)
        self._cache.put(query, result)
        return result

    def build_context(self, current_query: str) -> str:
        retrieved = self.retrieve(current_query)
        if not retrieved:
            return ""
        return f"以下是与当前对话相关的历史记忆：\n{retrieved}"

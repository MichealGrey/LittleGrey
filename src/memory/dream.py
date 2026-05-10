import json
import random
from datetime import datetime
from typing import Any

from src.agent.llm import LLMClient
from src.core.config import DreamConfig
from src.core.gate import PriorityGate
from src.core.logger import AgentLogger
from src.memory.long_term import LongTermMemory
from src.memory.short_term import ShortTermMemory


class DreamEngine:
    """做梦引擎：在空闲时合并相似记忆，越久远的记忆越容易被归一化。"""

    def __init__(
        self,
        config: DreamConfig,
        llm: LLMClient,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        logger: AgentLogger,
        gate: PriorityGate | None = None,
    ):
        self.config = config
        self.llm = llm
        self.short_term = short_term
        self.long_term = long_term
        self.logger = logger
        self._gate = gate

    def dream(self) -> None:
        if not self.config.enabled:
            return

        if self._gate and not self._gate.wait_for_turn(timeout=60):
            return

        self.logger.log("dream", "start")
        self._dream_short_term()

        if self._gate and not self._gate.wait_for_turn(timeout=60):
            return

        self._dream_long_term()
        self.logger.log("dream", "done")

    def _dream_short_term(self) -> None:
        messages = self.short_term._messages
        if len(messages) < 4:
            return

        pairs = self._find_similar_message_pairs(messages)
        if not pairs:
            return

        merged_count = 0
        removed_indices: set[int] = set()

        for idx_a, idx_b in pairs:
            if idx_a in removed_indices or idx_b in removed_indices:
                continue

            age_ratio = 1.0 - idx_a / len(messages)
            prob = self.config.short_term_dream_base_prob * (1 + age_ratio)
            if random.random() > prob:
                continue

            merged_content = self._llm_merge(
                messages[idx_a].content, messages[idx_b].content, "消息"
            )
            if merged_content is None:
                continue

            self.short_term.merge_messages(idx_a, idx_b, merged_content)
            removed_indices.add(idx_b)
            merged_count += 1

        if merged_count:
            self.logger.log("dream", "short_term_merged", output_data={"count": merged_count})

    def _find_similar_message_pairs(self, messages: list) -> list[tuple[int, int]]:
        pairs = []
        n = len(messages)
        for i in range(n):
            for j in range(i + 1, n):
                if messages[i].role != messages[j].role:
                    continue
                if self._keyword_overlap(messages[i].content, messages[j].content) < 0.3:
                    continue
                pairs.append((i, j))
        return pairs

    @staticmethod
    def _keyword_overlap(text_a: str, text_b: str) -> float:
        set_a = set(text_a)
        set_b = set(text_b)
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def _dream_long_term(self) -> None:
        all_docs = self.long_term.get_all()
        if len(all_docs) < 4:
            return

        sample = random.sample(all_docs, min(20, len(all_docs)))

        to_delete: list[str] = []
        to_store: list[tuple[str, dict[str, Any]]] = []
        now = datetime.now()

        for doc in sample:
            if doc["id"] in to_delete:
                continue

            similar = self.long_term.search(doc["text"], top_k=5)
            for hit in similar:
                if hit["id"] == doc["id"] or hit["id"] in to_delete:
                    continue
                if hit["relevance"] < self.config.similarity_threshold:
                    continue

                age_days = self._age_days(doc["metadata"].get("stored_at", ""), now)
                prob = self.config.long_term_dream_base_prob * (1 + min(age_days, 7) / 7)
                if random.random() > prob:
                    continue

                merged_content = self._llm_merge(doc["text"], hit["text"], "记忆")
                if merged_content is None:
                    continue

                to_delete.append(doc["id"])
                to_delete.append(hit["id"])
                merged_meta = doc["metadata"].copy()
                merged_meta["merged_from"] = f"{doc['id']}+{hit['id']}"
                to_store.append((merged_content, merged_meta))
                break

        if to_delete:
            self.long_term.delete(to_delete)
            for content, meta in to_store:
                self.long_term.store(content, meta)
            self.logger.log(
                "dream", "long_term_merged",
                output_data={"deleted": len(to_delete), "stored": len(to_store)},
            )

    @staticmethod
    def _age_days(stored_at: str, now: datetime) -> float:
        if not stored_at:
            return 0.0
        try:
            stored = datetime.fromisoformat(stored_at)
            return max(0, (now - stored).total_seconds() / 86400)
        except (ValueError, TypeError):
            return 0.0

    def _llm_merge(self, text_a: str, text_b: str, label: str) -> str | None:
        messages = [
            {
                "role": "system",
                "content": (
                    f"以下两段{label}是否在说同一件事或表达相似含义？\n"
                    f"如果是，合并为一条精简的表述，保留两者的关键信息，去除重复。\n"
                    f"如果不是同件事，返回 merged: false。\n"
                    f'只返回JSON：{{"merged": true/false, "content": "合并后内容"}}'
                ),
            },
            {
                "role": "user",
                "content": f"{label}A：{text_a}\n\n{label}B：{text_b}",
            },
        ]

        try:
            if self._gate:
                self._gate.wait_for_turn(timeout=60)
            result = self.llm.chat(messages, use_tools=False)
            content = result.get("content", "")
            parsed = json.loads(content)
            if parsed.get("merged"):
                return parsed.get("content")
            return None
        except (json.JSONDecodeError, TypeError):
            if "false" in content.lower() or "不是" in content:
                return None
            if "merged" not in content.lower() and len(content) < max(len(text_a), len(text_b)):
                return content
            return None
        except Exception as e:
            self.logger.log("dream", "merge_error", status="error", error=str(e))
            return None

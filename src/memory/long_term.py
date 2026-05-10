import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb


class LongTermMemory:
    def __init__(self, db_path: str, embedding_model: str):
        self._client = chromadb.PersistentClient(path=db_path)
        self._collection = self._client.get_or_create_collection(
            name="agent_memory",
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_model = embedding_model
        self._lock = threading.Lock()
        self._id_counter = self._init_id_counter()

    def _init_id_counter(self) -> int:
        existing = self._collection.get()
        ids = existing.get("ids", [])
        if not ids:
            return 0
        max_id = 0
        for doc_id in ids:
            if doc_id.startswith("mem_"):
                try:
                    num = int(doc_id[4:])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
        return max_id

    def store(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        with self._lock:
            self._id_counter += 1
            doc_id = f"mem_{self._id_counter}"
            meta = metadata or {}
            if "stored_at" not in meta:
                meta["stored_at"] = datetime.now().isoformat()
            self._collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[meta],
            )
            return doc_id

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, self._collection.count() or 1),
            )

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            items = []
            for doc, meta, dist, doc_id in zip(documents, metadatas, distances, ids):
                items.append({
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta,
                    "relevance": 1.0 - dist,
                })
            return items

    def delete(self, ids: list[str]) -> None:
        with self._lock:
            try:
                self._collection.delete(ids=ids)
            except Exception:
                pass

    def get_all(self) -> list[dict[str, Any]]:
        with self._lock:
            count = self._collection.count()
            if count == 0:
                return []
            results = self._collection.get(include=["documents", "metadatas"])
            ids = results.get("ids", [])
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            items = []
            for doc_id, doc, meta in zip(ids, documents, metadatas):
                items.append({
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta,
                })
            return items

    def store_conversation_summary(self, summary: str, session_id: str = "") -> str:
        return self.store(summary, {"type": "conversation_summary", "session_id": session_id})

    def store_user_preference(self, preference: str) -> str:
        return self.store(preference, {"type": "user_preference"})

    def store_knowledge(self, knowledge: str, topic: str = "") -> str:
        return self.store(knowledge, {"type": "knowledge", "topic": topic})

    def store_agent_interest(self, interest: str) -> str:
        return self.store(interest, {"type": "agent_interest"})

    def store_agent_knowledge(self, knowledge: str, interest: str = "") -> str:
        return self.store(knowledge, {"type": "agent_interest_knowledge", "interest": interest})

    def store_mood_summary(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        meta = metadata or {}
        if "type" not in meta:
            meta["type"] = "mood_summary"
        return self.store(text, meta)

    def count(self) -> int:
        return self._collection.count()

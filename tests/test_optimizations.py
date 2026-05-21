import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

for mod in ["volcenginesdkarkruntime", "volcengine", "chromadb"]:
    sys.modules.setdefault(mod, MagicMock())

import pytest
import time
from src.agent.emotion_cache import EmotionCache
from src.memory.rag_cache import RAGCache


class TestEmotionCache:
    def test_basic_put_get(self):
        cache = EmotionCache(max_size=10)
        mock_result = MagicMock()
        cache.put("test text", mock_result)
        assert cache.get("test text") is mock_result

    def test_cache_miss(self):
        cache = EmotionCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        cache = EmotionCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_access_updates_order(self):
        cache = EmotionCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")
        cache.put("c", 3)
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_stats(self):
        cache = EmotionCache(max_size=10)
        cache.put("a", 1)
        cache.get("a")
        cache.get("b")
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_normalization(self):
        cache = EmotionCache(max_size=10)
        mock_result = MagicMock()
        cache.put("  Hello World  ", mock_result)
        assert cache.get("hello world") is mock_result

    def test_similarity_match(self):
        cache = EmotionCache(max_size=10, threshold=0.7)
        mock_result = MagicMock()
        cache.put("hello world test", mock_result)
        result = cache.get("hello world testing")
        assert result is mock_result


class TestRAGCache:
    def test_basic_put_get(self):
        cache = RAGCache(max_size=10, ttl_seconds=60)
        cache.put("query", "result")
        assert cache.get("query") == "result"

    def test_cache_miss(self):
        cache = RAGCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        cache = RAGCache(max_size=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_stats(self):
        cache = RAGCache(max_size=10)
        cache.put("a", 1)
        cache.get("a")
        cache.get("b")
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


class TestConfigOptimization:
    def test_settings_yaml_values(self):
        content = Path("config/settings.yaml").read_text(encoding="utf-8")
        assert "max_tokens: 1000" in content
        assert "short_term_max: 10" in content
        assert "summary_threshold: 8" in content
        assert "max_steps: 5" in content
        assert "max_retries: 1" in content


class TestEmotionEngineWithCache:
    def test_understand_uses_cache(self):
        from src.agent.emotion import EmotionEngine
        from src.core.config import EmotionConfig

        config = EmotionConfig()
        mock_llm = MagicMock()
        mock_llm.understand_emotion.return_value = {
            "user_intent": "happy",
            "my_emotion_summary": "user is happy",
            "my_emotions": [],
            "boundary_violation": False,
            "core_projection": {"happy": 0.8}
        }

        engine = EmotionEngine(llm=mock_llm, config=config)
        result1 = engine.understand("test text")
        result2 = engine.understand("test text")

        assert result1.user_intent == "happy"
        assert result2.user_intent == "happy"
        assert engine._emotion_cache._hits >= 1

    def test_cache_miss_calls_llm(self):
        from src.agent.emotion import EmotionEngine
        from src.core.config import EmotionConfig

        config = EmotionConfig()
        mock_llm = MagicMock()
        mock_llm.understand_emotion.return_value = {
            "user_intent": "unknown",
            "my_emotion_summary": "unknown",
            "my_emotions": [],
            "boundary_violation": False,
            "core_projection": {}
        }

        engine = EmotionEngine(llm=mock_llm, config=config)
        engine.understand("text1")
        engine.understand("text2")

        assert mock_llm.understand_emotion.call_count == 2


class TestRAGWithCache:
    def test_retrieve_uses_cache(self):
        from src.memory.rag import RAG

        mock_long_term = MagicMock()
        mock_long_term.search.return_value = [
            {"text": "result1", "metadata": {"type": "chat"}, "relevance": 0.8}
        ]

        rag = RAG(long_term_memory=mock_long_term, top_k=3)
        result1 = rag.retrieve("test query")
        result2 = rag.retrieve("test query")

        assert result1 == "[chat] result1"
        assert result2 == "[chat] result1"
        assert rag._cache._hits >= 1
        assert mock_long_term.search.call_count == 1

    def test_top_k_optimization(self):
        from src.memory.rag import RAG

        mock_long_term = MagicMock()
        mock_long_term.search.return_value = []

        rag = RAG(long_term_memory=mock_long_term, top_k=3)
        rag.retrieve("test")

        mock_long_term.search.assert_called_once_with("test", top_k=6)


class TestRelationshipOptimization:
    def test_familiarity_caching(self):
        from src.agent.relationship import RelationshipState

        state = RelationshipState(interactions_count=10)
        fam1 = state.familiarity
        fam2 = state.familiarity

        assert fam1 == "刚认识"
        assert fam2 == "刚认识"
        assert state._familiarity_cache is not None

    def test_absence_hours_caching(self):
        from src.agent.relationship import RelationshipState
        from datetime import datetime

        state = RelationshipState(last_seen=datetime.now().isoformat())
        hours1 = state.absence_hours
        hours2 = state.absence_hours

        assert hours1 == hours2
        assert state._absence_hours_cache is not None

    def test_absence_reaction_caching(self):
        from src.agent.relationship import RelationshipState

        state = RelationshipState()
        reaction1 = state.absence_reaction
        reaction2 = state.absence_reaction

        assert reaction1 == reaction2
        assert state._absence_reaction_cache is not None

    def test_cache_invalidation_on_update(self):
        from src.agent.relationship import RelationshipState

        state = RelationshipState(interactions_count=10)
        _ = state.familiarity
        assert state._familiarity_cache is not None

        state.interactions_count = 60
        state._invalidate_cache()

        assert state._familiarity_cache is None
        assert state.familiarity == "朋友"

    def test_state_description_caching(self):
        from src.agent.relationship import RelationshipManager

        manager = RelationshipManager()
        desc1 = manager.get_state_description()
        desc2 = manager.get_state_description()

        assert desc1 == desc2
        assert manager._state_description_cache is not None


class TestParallelProcessing:
    def test_thread_pool_executor_import(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        assert ThreadPoolExecutor is not None
        assert as_completed is not None

    def test_parallel_emotion_and_rag(self):
        from concurrent.futures import ThreadPoolExecutor
        from unittest.mock import MagicMock

        mock_emotion = MagicMock()
        mock_emotion.understand.return_value = MagicMock(user_intent="test")

        mock_rag = MagicMock()
        mock_rag.build_context.return_value = "test context"

        with ThreadPoolExecutor(max_workers=2) as executor:
            emotion_future = executor.submit(mock_emotion.understand, "test")
            rag_future = executor.submit(mock_rag.build_context, "test")

            emotion_result = emotion_future.result()
            rag_context = rag_future.result()

        assert emotion_result.user_intent == "test"
        assert rag_context == "test context"


class TestStreamingResponse:
    def test_llm_chat_has_stream_parameter(self):
        import inspect
        from src.agent.llm import LLMClient

        sig = inspect.signature(LLMClient.chat)
        params = sig.parameters
        assert "stream" in params
        assert params["stream"].default == False


class TestEmotionStatePersistence:
    def test_save_emotion_state(self, tmp_path):
        from src.agent.emotion import EmotionEngine, MoodEntry
        from src.agent.emotion_storage import EmotionStateStorage
        import tempfile

        storage_dir = str(tmp_path / "storage")
        engine = EmotionEngine()
        engine._storage = EmotionStateStorage(storage_dir=storage_dir)
        engine._levels["happy"] = 0.8
        engine._levels["angry"] = 0.6
        engine._baseline["happy"] = 0.08

        mood_entry = MoodEntry(
            timestamp=100.0,
            emotion="happy",
            intensity=0.8,
            secondary=None,
            trigger="test",
            summary="test mood",
        )
        engine._mood_journal.append(mood_entry)

        engine._save_emotion_state()

        loaded_data = engine._storage.load()
        assert loaded_data is not None
        assert loaded_data["levels"]["happy"] == 0.8
        assert loaded_data["baseline"]["happy"] == 0.08
        assert len(loaded_data["recent_journal"]) == 1

    def test_load_emotion_state(self, tmp_path):
        from src.agent.emotion import EmotionEngine
        from src.agent.emotion_storage import EmotionStateStorage
        import time

        storage_dir = str(tmp_path / "storage")
        engine = EmotionEngine()
        engine._storage = EmotionStateStorage(storage_dir=storage_dir)

        state_data = {
            "levels": {"happy": 0.7, "sad": 0.0, "angry": 0.0, "anxious": 0.0, "excited": 0.0},
            "baseline": {"happy": 0.08, "sad": 0.0, "angry": 0.0, "anxious": 0.0, "excited": 0.0},
            "recent_journal": [
                {
                    "timestamp": 100.0,
                    "emotion": "happy",
                    "intensity": 0.7,
                    "secondary": None,
                    "trigger": "test",
                    "summary": "test mood",
                }
            ],
            "last_interaction_time": 0,
            "saved_at": time.time() - 3600,
        }
        engine._storage.save(state_data)

        engine._load_emotion_state()

        assert engine._levels["happy"] > 0.6
        assert engine._levels["happy"] <= 0.7
        assert engine._baseline["happy"] == 0.08
        assert len(engine._mood_journal) == 1
        assert engine._mood_journal[0].emotion == "happy"

    def test_load_emotion_state_decay_over_time(self, tmp_path):
        from src.agent.emotion import EmotionEngine
        from src.agent.emotion_storage import EmotionStateStorage
        import time

        storage_dir = str(tmp_path / "storage")
        engine = EmotionEngine()
        engine._storage = EmotionStateStorage(storage_dir=storage_dir)
        engine._levels["happy"] = 0.0

        state_data = {
            "levels": {"happy": 0.8, "sad": 0.0, "angry": 0.0, "anxious": 0.0, "excited": 0.0},
            "baseline": {"happy": 0.0, "sad": 0.0, "angry": 0.0, "anxious": 0.0, "excited": 0.0},
            "recent_journal": [],
            "last_interaction_time": 0,
            "saved_at": time.time() - 43200,
        }
        engine._storage.save(state_data)

        engine._load_emotion_state()

        assert engine._levels["happy"] < 0.8, "Emotion should decay after 12 hours"
        assert engine._levels["happy"] > 0.0, "Emotion should not be zero"

    def test_load_emotion_state_no_memory(self, tmp_path):
        from src.agent.emotion import EmotionEngine
        from src.agent.emotion_storage import EmotionStateStorage

        storage_dir = str(tmp_path / "storage")
        engine = EmotionEngine()
        engine._storage = EmotionStateStorage(storage_dir=storage_dir)
        engine._load_emotion_state()
        assert engine._levels["happy"] == 0.0

    def test_save_emotion_state_no_memory(self, tmp_path):
        from src.agent.emotion import EmotionEngine
        from src.agent.emotion_storage import EmotionStateStorage

        storage_dir = str(tmp_path / "storage")
        engine = EmotionEngine()
        engine._storage = EmotionStateStorage(storage_dir=storage_dir)
        engine._save_emotion_state()
        assert True

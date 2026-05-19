import pathlib

f = pathlib.Path("e:/Proj/AIProj/LittleGrey/tests/test_optimizations.py")
c = f.read_text(encoding="utf-8")

new_tests = ''''

class TestEmotionStatePersistence:
    def test_save_emotion_state(self):
        from src.agent.emotion import EmotionEngine, MoodEntry
        from unittest.mock import MagicMock

        engine = EmotionEngine()
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

        mock_ltm = MagicMock()
        engine._save_emotion_state(mock_ltm)

        mock_ltm.store.assert_called()
        call_args = mock_ltm.store.call_args
        assert call_args[0] == "emotion_state"
        metadata = call_args[1]["metadata"]
        assert metadata["type"] == "emotion_state"
        assert metadata["levels"]["happy"] == 0.8
        assert metadata["baseline"]["happy"] == 0.08
        assert len(metadata["recent_journal"]) == 1

    def test_load_emotion_state(self):
        from src.agent.emotion import EmotionEngine
        from unittest.mock import MagicMock
        import time

        engine = EmotionEngine()

        mock_result = MagicMock()
        mock_result.get.return_value = {
            "metadata": {
                "type": "emotion_state",
                "levels": {"happy": 0.7, "ang": 0.5},
                "baseline": {"happy": 0.08, "ang": 0.06},
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
                "saved_at": time.time() - 3600,  # 1 hour ago
            }
        }

        mock_ltm = MagMock()
        mock_ltm.search.return_value = [mock_result]

        engine._load_emotion_state(mock_ltm)

        assert engine._levels["happy"] == 0.7
        assert engine._baseline["happy"] == 0.08
        assert len(engine._mood_journal) == 1
        assert engine._mood_journal[0].emotion == "happy"

    def test_load_emotion_state_decay_over_time(self):
        from src.agent.emotion import EmotionEngine
        from unittest.mock import MagicMock
        import time

        engine = EmotionEngine()
        engine._levels["happy"] = 0.0

        mock_result = MagMock()
        mock_result.get.return_value = {
            "metadata": {
                "type": "emotion_state",
                "levels": {"happy": 0.8},
                "baseline": {},
                "recent_journal": [],
                "last_interaction_time": 0,
                "saved_at": time.time() - 172800, # 2 days ago
            }
        }

        mock_ltm = MagMock()
        mock_ltm.search.return_value = [mock_result]

        engine._load_emotion_state(mock_ltm)

        assert engine._levels["happy"] < 0.8, "Emotion should decay after 2 days"
        assert engine._levels["happy"] > 0.0, "Emotion should not be zero"

    def test_load_emotion_state_no_memory(self):
        from src.agent.emotion import EmotionEngine

        engine = EmotionEngine()
        engine._load_emotion_state(None)
        assert engine._levels["happy"] == 0.0

    def test_save_emotion_state_no_memory(self):
        from src.agent.emotion import EmotionEngine

        engine = EmotionEngine()
        engine._save_emotion_state(None)
        assert True
'''

c = c + '\n' + new_tests
f.write_text(c, encoding="utf-8")
print("OK")

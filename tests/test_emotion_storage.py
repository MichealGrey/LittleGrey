import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.agent.emotion_storage import EmotionStateStorage


class TestEmotionStateStorage:
    """Test cases for EmotionStateStorage class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_dir):
        """Create an EmotionStateStorage instance with temp directory."""
        return EmotionStateStorage(storage_dir=temp_dir)

    def test_init_with_custom_dir(self, temp_dir):
        """Test initialization with custom storage directory."""
        storage = EmotionStateStorage(storage_dir=temp_dir)
        assert storage.storage_dir == Path(temp_dir)
        assert storage.state_file == Path(temp_dir) / "emotion_state.json"

    def test_init_creates_directory(self, temp_dir):
        """Test that initialization creates the storage directory."""
        custom_dir = Path(temp_dir) / "custom_storage"
        storage = EmotionStateStorage(storage_dir=str(custom_dir))
        assert custom_dir.exists()
        assert custom_dir.is_dir()

    def test_init_with_default_path(self):
        """Test initialization with default path uses project root."""
        storage = EmotionStateStorage()
        # emotion_storage.py is in src/agent/, so parent.parent.parent = project root
        # tests are in tests/, so we need to compute the correct project root
        project_root = Path(__file__).resolve().parent.parent
        expected_dir = project_root / "storage"
        assert storage.storage_dir == expected_dir

    def test_save_and_load(self, storage):
        """Test basic save and load functionality."""
        test_data = {
            "levels": {"happy": 0.8, "sad": 0.2, "angry": 0.5},
            "baseline": {"happy": 0.1, "sad": 0.1, "angry": 0.1},
            "recent_journal": [],
            "last_interaction_time": time.time(),
        }

        result = storage.save(test_data)
        assert result is True
        assert storage.state_file.exists()

        loaded_data = storage.load()
        assert loaded_data is not None
        assert "saved_at" in loaded_data
        assert loaded_data["levels"] == test_data["levels"]
        assert loaded_data["baseline"] == test_data["baseline"]

    def test_save_adds_timestamp(self, storage):
        """Test that save adds saved_at timestamp."""
        test_data = {"test": "value"}
        before_save = time.time()

        storage.save(test_data)
        loaded_data = storage.load()

        assert loaded_data is not None
        assert "saved_at" in loaded_data
        assert loaded_data["saved_at"] >= before_save
        assert loaded_data["test"] == "value"

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading when file doesn't exist returns None."""
        storage = EmotionStateStorage(storage_dir=temp_dir)
        result = storage.load()
        assert result is None

    def test_load_invalid_json(self, storage):
        """Test loading invalid JSON file returns None."""
        with open(storage.state_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        result = storage.load()
        assert result is None

    def test_clear_existing_file(self, storage):
        """Test clearing an existing file."""
        storage.save({"test": "value"})
        assert storage.state_file.exists()

        result = storage.clear()
        assert result is True
        assert not storage.state_file.exists()

    def test_clear_nonexistent_file(self, temp_dir):
        """Test clearing when file doesn't exist returns True."""
        storage = EmotionStateStorage(storage_dir=temp_dir)
        result = storage.clear()
        assert result is True

    def test_save_overwrite(self, storage):
        """Test that save overwrites existing file."""
        storage.save({"version": 1})
        storage.save({"version": 2})

        loaded_data = storage.load()
        assert loaded_data is not None
        assert loaded_data["version"] == 2

    def test_save_and_load_complex_data(self, storage):
        """Test saving and loading complex nested data."""
        complex_data = {
            "levels": {"happy": 0.7, "sad": 0.3, "angry": 0.9, "anxious": 0.4, "excited": 0.6},
            "baseline": {"happy": 0.1, "sad": 0.1, "angry": 0.1, "anxious": 0.1, "excited": 0.1},
            "recent_journal": [
                {
                    "timestamp": time.time(),
                    "emotion": "angry",
                    "intensity": 0.8,
                    "secondary": "sad",
                    "trigger": "user_input",
                    "summary": "用户说了冒犯的话",
                },
                {
                    "timestamp": time.time() - 3600,
                    "emotion": "happy",
                    "intensity": 0.6,
                    "secondary": None,
                    "trigger": "self_response",
                    "summary": "帮助用户解决问题",
                },
            ],
            "last_interaction_time": time.time(),
        }

        storage.save(complex_data)
        loaded_data = storage.load()

        assert loaded_data is not None
        assert loaded_data["levels"] == complex_data["levels"]
        assert loaded_data["baseline"] == complex_data["baseline"]
        assert len(loaded_data["recent_journal"]) == 2
        assert loaded_data["recent_journal"][0]["emotion"] == "angry"
        assert loaded_data["recent_journal"][1]["emotion"] == "happy"

    def test_unicode_content(self, storage):
        """Test saving and loading Unicode content."""
        unicode_data = {
            "summary": "用户你好，这是一段测试内容",
            "emotion": "平静",
            "trend": "情绪波动增多",
        }

        storage.save(unicode_data)
        loaded_data = storage.load()

        assert loaded_data is not None
        assert loaded_data["summary"] == unicode_data["summary"]
        assert loaded_data["emotion"] == unicode_data["emotion"]

    def test_save_exception_handling(self, storage):
        """Test that save handles exceptions gracefully."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = storage.save({"test": "value"})
            assert result is False

    def test_load_exception_handling(self, storage):
        """Test that load handles exceptions gracefully."""
        storage.save({"test": "value"})

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = storage.load()
            assert result is None

    def test_file_encoding(self, storage):
        """Test that file is saved with UTF-8 encoding."""
        data = {"chinese": "中文测试", "emoji": "😊"}
        storage.save(data)

        with open(storage.state_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        assert content["chinese"] == "中文测试"

    def test_state_file_path(self, temp_dir):
        """Test that state file path is correct."""
        storage = EmotionStateStorage(storage_dir=temp_dir)
        expected_path = Path(temp_dir) / "emotion_state.json"
        assert storage.state_file == expected_path


class TestEmotionStatePersistence:
    """Integration tests for emotion state persistence."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_dir):
        """Create an EmotionStateStorage instance."""
        return EmotionStateStorage(storage_dir=temp_dir)

    def test_persistence_round_trip(self, storage):
        """Test complete round-trip persistence."""
        original_state = {
            "levels": {"happy": 0.2, "sad": 0.8, "angry": 0.6, "anxious": 0.4, "excited": 0.1},
            "baseline": {"happy": 0.1, "sad": 0.1, "angry": 0.1, "anxious": 0.1, "excited": 0.1},
            "recent_journal": [
                {
                    "timestamp": time.time(),
                    "emotion": "sad",
                    "intensity": 0.8,
                    "secondary": "angry",
                    "trigger": "conflict",
                    "summary": "用户侵犯了边界",
                }
            ],
            "last_interaction_time": time.time(),
        }

        storage.save(original_state)
        loaded_state = storage.load()

        assert loaded_state is not None
        assert loaded_state["levels"] == original_state["levels"]
        assert loaded_state["baseline"] == original_state["baseline"]
        assert len(loaded_state["recent_journal"]) == 1
        assert loaded_state["recent_journal"][0]["emotion"] == "sad"

    def test_multiple_saves(self, storage):
        """Test multiple consecutive saves."""
        for i in range(5):
            storage.save({"iteration": i, "timestamp": time.time()})
            time.sleep(0.01)

        loaded_state = storage.load()
        assert loaded_state is not None
        assert loaded_state["iteration"] == 4

    def test_data_integrity(self, storage):
        """Test that data integrity is maintained after save/load."""
        test_data = {
            "float_values": {"happy": 0.123456, "sad": 0.654321},
            "string_values": {"dominant": "sad", "trend": "波动"},
            "list_values": [1, 2, 3, "a", "b", "c"],
            "nested": {"a": {"b": {"c": "deep"}}},
        }

        storage.save(test_data)
        loaded_data = storage.load()

        assert loaded_data is not None
        assert loaded_data["float_values"]["happy"] == pytest.approx(0.123456, rel=1e-5)
        assert loaded_data["string_values"]["dominant"] == "sad"
        assert loaded_data["list_values"] == [1, 2, 3, "a", "b", "c"]
        assert loaded_data["nested"]["a"]["b"]["c"] == "deep"

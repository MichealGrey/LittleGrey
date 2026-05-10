import sys
from pathlib import Path
from unittest.mock import MagicMock as _MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

for _mod in ["volcenginesdkarkruntime", "volcengine", "chromadb"]:
    sys.modules.setdefault(_mod, _MagicMock())

import time
import pytest
from src.agent.emotion import EmotionEngine
from src.core.config import EmotionConfig


class TestEmotionJournal:
    def test_journal_starts_empty(self, emotion):
        assert emotion._mood_journal == []

    def test_record_mood_appends_entry(self, emotion):
        emotion._record_mood("happy", 0.5, "user_input", "用户说了开心的话")
        assert len(emotion._mood_journal) == 1
        assert emotion._mood_journal[0].emotion == "happy"

    def test_journal_capped_at_100(self, emotion):
        for i in range(120):
            emotion._record_mood("happy", 0.3, "user_input", f"entry {i}")
        assert len(emotion._mood_journal) <= 100


class TestBaseline:
    def test_baseline_initialized_from_config(self, emotion, emotion_config):
        assert emotion._baseline["happy"] == emotion_config.baseline_happy
        assert emotion._baseline["sad"] == emotion_config.baseline_sad

    def test_baseline_adaptation_on_high_intensity(self, emotion):
        initial_happy = emotion._baseline["happy"]
        emotion._record_mood("happy", 0.8, "user_input", "very happy")
        assert emotion._baseline["happy"] >= initial_happy

    def test_baseline_capped_at_max(self, emotion):
        emotion._baseline["happy"] = 0.14
        emotion._record_mood("happy", 0.9, "user_input", "overjoyed")
        assert emotion._baseline["happy"] <= 0.15

    def test_baseline_opposite_decreases(self, emotion):
        emotion._baseline["sad"] = 0.05
        emotion._record_mood("happy", 0.8, "user_input", "overjoyed")
        assert emotion._baseline["sad"] < 0.05

    def test_low_intensity_no_baseline_change(self, emotion):
        initial = emotion._baseline["happy"]
        emotion._record_mood("happy", 0.2, "user_input", "mildly happy")
        assert emotion._baseline["happy"] == initial


class TestDecayToBaseline:
    def test_decay_toward_baseline_not_zero(self, emotion):
        emotion._baseline["happy"] = 0.05
        emotion._levels["happy"] = 0.6
        emotion._last_update = time.monotonic() - 400
        emotion._decay()
        assert emotion._levels["happy"] >= emotion._baseline["happy"]

    def test_decay_from_below_baseline_rises(self, emotion):
        emotion._baseline["happy"] = 0.05
        emotion._levels["happy"] = 0.0
        emotion._last_update = time.monotonic() - 400
        emotion._decay()
        assert emotion._levels["happy"] > 0.0


class TestGetRecentMood:
    def test_empty_journal_returns_calm(self, emotion):
        result = emotion.get_recent_mood()
        assert result["trend"] == "平静"
        assert result["dominant"] == "neutral"
        assert result["count"] == 0

    def test_recent_entries_counted(self, emotion):
        emotion._record_mood("happy", 0.5, "user_input", "test")
        emotion._record_mood("happy", 0.3, "user_input", "test2")
        result = emotion.get_recent_mood()
        assert result["count"] == 2
        assert result["dominant"] == "happy"

    def test_trend_escalating(self, emotion):
        emotion._record_mood("happy", 0.1, "user_input", "mild")
        emotion._record_mood("happy", 0.3, "user_input", "more")
        emotion._record_mood("happy", 0.5, "user_input", "strong")
        emotion._record_mood("happy", 0.7, "user_input", "stronger")
        result = emotion.get_recent_mood()
        assert result["count"] == 4
        assert result["dominant"] == "happy"
        assert result["trend"] in ["情绪波动增多", "比较稳定", "逐渐平静"]

    def test_trend_stable(self, emotion):
        for _ in range(6):
            emotion._record_mood("happy", 0.4, "user_input", "steady")
        result = emotion.get_recent_mood()
        assert result["trend"] == "比较稳定"


class TestUnderstandUpdatesInteractionTime:
    def test_understand_updates_interaction_time(self, emotion):
        before = emotion._last_interaction_time
        time.sleep(0.01)
        emotion.understand("你好")
        assert emotion._last_interaction_time > before

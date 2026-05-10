import sys
from pathlib import Path
from unittest.mock import MagicMock as _MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

for _mod in ["volcenginesdkarkruntime", "volcengine", "chromadb"]:
    sys.modules.setdefault(_mod, _MagicMock())

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


class TestRelationshipState:
    def _make_state(self, **kwargs):
        from src.agent.relationship import RelationshipState
        defaults = {"intimacy": 0.1, "trust": 0.3, "interactions_count": 0,
                     "positive_interactions": 0, "last_seen": "", "shared_experiences": []}
        defaults.update(kwargs)
        return RelationshipState(**defaults)

    def test_familiarity_stranger(self):
        state = self._make_state(interactions_count=3)
        assert state.familiarity == "陌生人"

    def test_familiarity_just_met(self):
        state = self._make_state(interactions_count=10)
        assert state.familiarity == "刚认识"

    def test_familiarity_acquaintance(self):
        state = self._make_state(interactions_count=30)
        assert state.familiarity == "熟人"

    def test_familiarity_friend(self):
        state = self._make_state(interactions_count=60)
        assert state.familiarity == "朋友"

    def test_familiarity_close_friend(self):
        state = self._make_state(interactions_count=150)
        assert state.familiarity == "好朋友"

    def test_absence_just_now(self):
        state = self._make_state(last_seen=datetime.now().isoformat())
        assert state.absence_hours < 1

    def test_absence_hours_ago(self):
        state = self._make_state(last_seen=(datetime.now() - timedelta(hours=3)).isoformat())
        assert 2 < state.absence_hours < 5

    def test_absence_days(self):
        state = self._make_state(last_seen=(datetime.now() - timedelta(days=2)).isoformat())
        assert state.absence_hours > 24

    def test_absence_no_last_seen(self):
        state = self._make_state(last_seen="")
        assert state.absence_hours == 999.0

    def test_absence_reaction_labels(self):
        state = self._make_state(last_seen=(datetime.now() - timedelta(hours=4)).isoformat())
        assert state.absence_reaction == "刚才还聊着呢"

    def test_absence_reaction_today(self):
        state = self._make_state(last_seen=(datetime.now() - timedelta(hours=10)).isoformat())
        assert state.absence_reaction == "今天又来啦"

    def test_absence_reaction_week(self):
        state = self._make_state(last_seen=(datetime.now() - timedelta(days=5)).isoformat())
        assert state.absence_reaction == "一个星期没见了"


class TestRelationshipManager:
    def _make_manager(self):
        from src.agent.relationship import RelationshipManager
        mock_lt = MagicMock()
        mock_lt.search.return_value = []
        return RelationshipManager(long_term_memory=mock_lt, logger=None)

    def test_init_default_state(self):
        mgr = self._make_manager()
        assert mgr._state.intimacy == 0.1
        assert mgr._state.trust == 0.3
        assert mgr._state.interactions_count == 0

    def test_update_increments_count(self):
        mgr = self._make_manager()
        mgr.update("你好", {"emotion": "neutral", "intensity": 0.0}, "你好呀")
        assert mgr._state.interactions_count == 1

    def test_update_sets_last_seen(self):
        mgr = self._make_manager()
        mgr.update("你好", {"emotion": "neutral", "intensity": 0.0}, "你好呀")
        assert mgr._state.last_seen != ""

    def test_positive_emotion_increases_intimacy(self):
        mgr = self._make_manager()
        initial = mgr._state.intimacy
        mgr.update("你好", {"emotion": "happy", "intensity": 0.5}, "嗨～")
        assert mgr._state.intimacy > initial

    def test_negative_emotion_decreases_intimacy(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.3
        initial = mgr._state.intimacy
        mgr.update("烦死了", {"emotion": "angry", "intensity": 0.5}, "怎么了")
        assert mgr._state.intimacy < initial

    def test_miss_keyword_boosts_intimacy(self):
        mgr = self._make_manager()
        initial = mgr._state.intimacy
        mgr.update("我想你了", {"emotion": "happy", "intensity": 0.3}, "我也是")
        assert mgr._state.intimacy >= initial + 0.03

    def test_dislike_keyword_decreases_intimacy(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.4
        initial = mgr._state.intimacy
        mgr.update("我讨厌你", {"emotion": "angry", "intensity": 0.5}, "qwq")
        assert mgr._state.intimacy < initial

    def test_apology_increases_trust(self):
        mgr = self._make_manager()
        initial = mgr._state.trust
        mgr.update("对不起", {"emotion": "sad", "intensity": 0.3}, "没关系")
        assert mgr._state.trust > initial


class TestRelationshipEmotionWeight:
    def _make_manager(self):
        from src.agent.relationship import RelationshipManager
        mock_lt = MagicMock()
        mock_lt.search.return_value = []
        return RelationshipManager(long_term_memory=mock_lt, logger=None)

    def test_stranger_low_weight(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.1
        weight = mgr.get_emotion_weight()
        assert weight < 1.0

    def test_close_friend_high_weight(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.9
        weight = mgr.get_emotion_weight()
        assert weight > 1.0

    def test_weight_increases_with_intimacy(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.2
        w1 = mgr.get_emotion_weight()
        mgr._state.intimacy = 0.8
        w2 = mgr.get_emotion_weight()
        assert w2 > w1


class TestRelationshipProactiveModifier:
    def _make_manager(self):
        from src.agent.relationship import RelationshipManager
        mock_lt = MagicMock()
        mock_lt.search.return_value = []
        return RelationshipManager(long_term_memory=mock_lt, logger=None)

    def test_stranger_low_proactive(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.1
        mod = mgr.get_proactive_modifier()
        assert mod < 1.0

    def test_close_friend_high_proactive(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.9
        mod = mgr.get_proactive_modifier()
        assert mod > 1.0


class TestRelationshipToolWillingness:
    def _make_manager(self):
        from src.agent.relationship import RelationshipManager
        mock_lt = MagicMock()
        mock_lt.search.return_value = []
        return RelationshipManager(long_term_memory=mock_lt, logger=None)

    def test_stranger_reluctant(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.1
        mod = mgr.get_tool_cooperation_modifier()
        assert mod < 1.0

    def test_close_friend_cooperative(self):
        mgr = self._make_manager()
        mgr._state.intimacy = 0.9
        mod = mgr.get_tool_cooperation_modifier()
        assert mod >= 0.9


class TestRelationshipStateDescription:
    def _make_manager(self):
        from src.agent.relationship import RelationshipManager
        mock_lt = MagicMock()
        mock_lt.search.return_value = []
        return RelationshipManager(long_term_memory=mock_lt, logger=None)

    def test_description_includes_familiarity(self):
        mgr = self._make_manager()
        desc = mgr.get_state_description()
        assert "陌生人" in desc or "刚认识" in desc

    def test_description_includes_interactions_count(self):
        mgr = self._make_manager()
        mgr._state.interactions_count = 42
        desc = mgr.get_state_description()
        assert "42" in desc

    def test_description_includes_intimacy(self):
        mgr = self._make_manager()
        desc = mgr.get_state_description()
        assert "亲密度" in desc

    def test_description_includes_style(self):
        mgr = self._make_manager()
        desc = mgr.get_state_description()
        assert "说话风格" in desc


class TestRelationshipManagerEmotionResult:
    def _make_manager(self):
        from src.agent.relationship import RelationshipManager
        mock_lt = MagicMock()
        mock_lt.search.return_value = []
        return RelationshipManager(long_term_memory=mock_lt, logger=None)

    def test_update_with_emotion_result_positive(self):
        from src.agent.emotion_result import EmotionResult, EmotionItem
        mgr = self._make_manager()
        initial_intimacy = mgr._state.intimacy
        emotion_result = EmotionResult(
            my_emotions=[EmotionItem("happy", 0.8, {"happy": 0.8})],
            trust_change=0.05,
            intimacy_change=0.03,
        )
        mgr.update("你好呀", emotion_result, "嗨～")
        assert mgr._state.intimacy > initial_intimacy
        assert mgr._state.interactions_count == 1

    def test_update_with_emotion_result_negative(self):
        from src.agent.emotion_result import EmotionResult, EmotionItem
        mgr = self._make_manager()
        mgr._state.intimacy = 0.3
        initial_intimacy = mgr._state.intimacy
        emotion_result = EmotionResult(
            my_emotions=[EmotionItem("sad", 0.7, {"sad": 0.7})],
            trust_change=-0.1,
            intimacy_change=-0.05,
        )
        mgr.update("烦死了", emotion_result, "怎么了")
        assert mgr._state.intimacy < initial_intimacy

    def test_update_with_emotion_result_applies_trust_change(self):
        from src.agent.emotion_result import EmotionResult, EmotionItem
        mgr = self._make_manager()
        initial_trust = mgr._state.trust
        emotion_result = EmotionResult(
            my_emotions=[EmotionItem("happy", 0.5, {"happy": 0.5})],
            trust_change=0.1,
            intimacy_change=0.0,
        )
        mgr.update("你好", emotion_result, "嗨～")
        assert mgr._state.trust > initial_trust

    def test_update_with_emotion_result_boundary_violation(self):
        from src.agent.emotion_result import EmotionResult, EmotionItem
        mgr = self._make_manager()
        initial_trust = mgr._state.trust
        emotion_result = EmotionResult(
            my_emotions=[EmotionItem("angry", 0.8, {"angry": 0.8})],
            trust_change=-0.3,
            intimacy_change=-0.2,
            boundary_violation=True,
        )
        mgr.update("打你好开心", emotion_result, "不要这样...")
        assert mgr._state.trust < initial_trust

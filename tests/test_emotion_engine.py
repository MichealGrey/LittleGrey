import sys
from pathlib import Path
from unittest.mock import MagicMock as _MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

for _mod in ["volcenginesdkarkruntime", "volcengine", "chromadb"]:
    sys.modules.setdefault(_mod, _MagicMock())

import time
from unittest.mock import MagicMock, patch

from src.agent.emotion import EmotionEngine
from src.agent.emotion_result import EmotionResult, EmotionItem
from src.core.config import EmotionConfig


def _make_engine(config=None, llm=None):
    return EmotionEngine(llm=llm, logger=None, config=config or EmotionConfig())


def test_understand_calls_llm():
    mock_llm = MagicMock()
    mock_llm.understand_emotion.return_value = {
        "user_intent": "care",
        "my_emotions": [{"emotion": "touched", "intensity": 0.6, "core": {"happy": 0.4}}],
        "my_emotion_summary": "I feel touched",
        "boundary_violation": False,
        "trust_change": 0.1,
    }
    engine = _make_engine(llm=mock_llm)
    result = engine.understand("你好吗？")
    mock_llm.understand_emotion.assert_called_once()
    assert result.user_intent == "care"
    assert result.primary_emotion == "touched"


def test_merge_to_core_accumulates():
    engine = _make_engine()
    result = EmotionResult(
        my_emotions=[
            EmotionItem("happy", 0.8, {"happy": 0.5}),
            EmotionItem("excited", 0.3, {"excited": 0.3}),
        ]
    )
    engine._merge_to_core(result)
    assert engine._levels["happy"] > 0.0
    assert engine._levels["excited"] > 0.0


def test_hard_constraints_boundary_violation():
    engine = _make_engine()
    engine._last_result = EmotionResult(boundary_violation=True)
    constraints = engine.get_hard_constraints()
    assert constraints["refuse_tools"] is True


def test_hard_constraints_angry_threshold():
    engine = _make_engine()
    engine._levels["angry"] = 0.8
    engine._last_result = EmotionResult()
    constraints = engine.get_hard_constraints()
    assert constraints["refuse_tools"] is True


def test_hard_constraints_sad_threshold():
    engine = _make_engine()
    engine._levels["sad"] = 0.85
    engine._last_result = EmotionResult()
    constraints = engine.get_hard_constraints()
    assert constraints["short_replies"] is True
    assert constraints["proactive_disabled"] is True


def test_decay_works():
    engine = _make_engine()
    engine._levels["happy"] = 0.8
    engine._last_update = time.monotonic() - 100
    engine._decay()
    assert engine._levels["happy"] < 0.8


def test_understand_fallback_on_error():
    mock_llm = MagicMock()
    mock_llm.understand_emotion.side_effect = Exception("LLM error")
    engine = _make_engine(llm=mock_llm)
    result = engine.understand("你好")
    assert result.user_intent == "unknown"
    assert result.my_emotion_summary == "无法理解"


def test_understand_no_llm():
    engine = _make_engine(llm=None)
    result = engine.understand("你好")
    assert result.user_intent == "unknown"
    assert result.my_emotion_summary == "无法理解"


def test_apply_self_response():
    engine = _make_engine()
    engine.apply_self_response("happy", 0.6)
    assert engine._levels["happy"] > 0.0


def test_apply_self_response_neutral_no_effect():
    engine = _make_engine()
    engine._levels["happy"] = 0.2
    engine._last_update = time.monotonic()
    engine.apply_self_response("neutral", 0.5)
    assert abs(engine._levels["happy"] - 0.2) < 0.01


def test_get_context_includes_levels():
    engine = _make_engine()
    engine._levels["happy"] = 0.3
    ctx = engine._get_context()
    assert "happy" in ctx


def test_render_bar_shows_expression_layer():
    engine = _make_engine()
    engine._last_result = EmotionResult(
        my_emotions=[EmotionItem("touched", 0.6)],
        my_emotion_summary="I feel touched",
    )
    bar = engine.render_bar()
    assert "表达层" in bar
    assert "touched" in bar


def test_check_triggers_no_violation():
    engine = _make_engine()
    engine._last_result = EmotionResult(boundary_violation=False)
    result = engine.check_triggers("你好")
    assert result is None


def test_check_triggers_with_violation():
    engine = _make_engine()
    engine._last_result = EmotionResult(
        boundary_violation=True,
        violation_type="人身攻击",
        my_defense="拒绝配合",
    )
    result = engine.check_triggers("打你")
    assert result is not None
    assert result["boundary_violation"] is True
    assert result["violation_type"] == "人身攻击"
    assert result["defense"] == "拒绝配合"


def test_check_triggers_no_last_result():
    engine = _make_engine()
    engine._last_result = None
    result = engine.check_triggers("你好")
    assert result is None


def test_get_behavior_modifiers_neutral():
    engine = _make_engine()
    mods = engine.get_behavior_modifiers()
    assert mods["response_style"] == "平静自然"
    assert mods["emotional_density"] == 0.5
    assert mods["emoji_tendency"] == 0.5
    assert mods["proactive_prob"] == 1.0


def test_get_behavior_modifiers_happy():
    engine = _make_engine()
    engine._levels["happy"] = 0.6
    mods = engine.get_behavior_modifiers()
    assert mods["response_style"] == "热情开朗"
    assert mods["emotional_density"] > 0.5
    assert mods["emoji_tendency"] > 0.5


def test_get_behavior_modifiers_sad():
    engine = _make_engine()
    engine._levels["sad"] = 0.5
    mods = engine.get_behavior_modifiers()
    assert "低落" in mods["response_style"]
    assert mods["proactive_prob"] < 1.0


def test_get_behavior_modifiers_angry():
    engine = _make_engine()
    engine._levels["angry"] = 0.8
    mods = engine.get_behavior_modifiers()
    assert "烦躁" in mods["response_style"]


def test_get_behavior_modifiers_excited():
    engine = _make_engine()
    engine._levels["excited"] = 0.7
    mods = engine.get_behavior_modifiers()
    assert mods["response_style"] == "兴奋、话多"
    assert len(mods["topic_preference"]) > 0


def test_get_behavior_modifiers_anxious():
    engine = _make_engine()
    engine._levels["anxious"] = 0.7
    mods = engine.get_behavior_modifiers()
    assert "紧张" in mods["response_style"]


def test_get_behavior_modifiers_hard_constraint_sad():
    engine = _make_engine()
    engine._levels["sad"] = 0.9
    mods = engine.get_behavior_modifiers()
    assert mods["proactive_prob"] == 0.0
    assert "简短" in mods["response_style"]


class TestAppContractWithEmotionEngine:
    """Verify that EmotionEngine provides all methods that app.py calls.

    This test class exists because the original bug (AttributeError: 'EmotionEngine'
    object has no attribute 'detect') was caused by a mismatch between what app.py
    expected and what EmotionEngine actually implemented. Unit tests only tested
    EmotionEngine in isolation, never verifying that the caller's expectations
    matched the implementation.
    """

    def _make_engine(self):
        return _make_engine()

    def test_app_calls_understand_not_detect(self):
        engine = self._make_engine()
        assert hasattr(engine, "understand"), "app.py should call engine.understand(), not engine.detect()"
        result = engine.understand("你好")
        assert isinstance(result, EmotionResult), "understand() must return EmotionResult"

    def test_app_calls_check_triggers(self):
        engine = self._make_engine()
        assert hasattr(engine, "check_triggers"), "app.py calls engine.check_triggers()"
        result = engine.check_triggers("你好")
        assert result is None or isinstance(result, dict)

    def test_app_calls_get_behavior_modifiers(self):
        engine = self._make_engine()
        assert hasattr(engine, "get_behavior_modifiers"), "app.py calls engine.get_behavior_modifiers()"
        mods = engine.get_behavior_modifiers()
        assert isinstance(mods, dict)
        for key in ["emotional_density", "emoji_tendency", "response_style", "topic_preference", "proactive_prob"]:
            assert key in mods, f"get_behavior_modifiers() must include '{key}'"

    def test_app_calls_get_recent_mood(self):
        engine = self._make_engine()
        assert hasattr(engine, "get_recent_mood"), "app.py calls engine.get_recent_mood()"
        mood = engine.get_recent_mood()
        assert isinstance(mood, dict)
        assert "dominant" in mood
        assert "trend" in mood

    def test_app_calls_apply_self_response(self):
        engine = self._make_engine()
        assert hasattr(engine, "apply_self_response"), "app.py calls engine.apply_self_response()"

    def test_app_calls_record_mood(self):
        engine = self._make_engine()
        assert hasattr(engine, "_record_mood"), "app.py calls engine._record_mood()"

    def test_app_calls_get_hard_constraints(self):
        engine = self._make_engine()
        assert hasattr(engine, "get_hard_constraints"), "app.py may use engine.get_hard_constraints()"

    def test_app_calls_render_bar(self):
        engine = self._make_engine()
        assert hasattr(engine, "render_bar"), "app.py calls engine.render_bar()"

    def test_emotion_result_has_primary_emotion_attribute(self):
        result = EmotionResult()
        assert hasattr(result, "primary_emotion"), "app.py accesses result.primary_emotion"
        assert hasattr(result, "primary_intensity"), "app.py accesses result.primary_intensity"
        assert hasattr(result, "user_intent"), "app.py may access result.user_intent"
        assert hasattr(result, "boundary_violation"), "app.py may access result.boundary_violation"
        assert hasattr(result, "trust_change"), "RelationshipManager uses result.trust_change"
        assert hasattr(result, "intimacy_change"), "RelationshipManager uses result.intimacy_change"

    def test_emotion_result_is_not_dict(self):
        result = EmotionResult()
        assert not isinstance(result, dict), "EmotionResult is a dataclass, not a dict. app.py must use attributes, not .get()"

    def test_heartbeat_calls_get_behavior_modifiers(self):
        engine = self._make_engine()
        mods = engine.get_behavior_modifiers()
        assert "proactive_prob" in mods, "heartbeat.py reads mods['proactive_prob']"

    def test_heartbeat_calls_autonomous_tick(self):
        engine = self._make_engine()
        assert hasattr(engine, "autonomous_tick"), "heartbeat.py calls engine.autonomous_tick()"

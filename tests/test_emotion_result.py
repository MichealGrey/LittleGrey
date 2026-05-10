import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.emotion_result import EmotionResult, EmotionItem


def test_emotion_result_from_dict():
    data = {
        "user_intent": "care",
        "user_attitude": "warm",
        "my_emotions": [
            {"emotion": "touched", "intensity": 0.6, "core": {"happy": 0.5}},
        ],
        "my_emotion_summary": "I feel touched",
        "boundary_violation": False,
        "trust_change": 0.1,
    }
    r = EmotionResult.from_dict(data)
    assert r.user_intent == "care"
    assert len(r.my_emotions) == 1
    assert r.my_emotions[0].emotion == "touched"
    assert r.boundary_violation is False


def test_core_projection_accumulates():
    r = EmotionResult(
        my_emotions=[
            EmotionItem("sad", 0.7, {"sad": 0.6, "angry": 0.3}),
            EmotionItem("angry", 0.5, {"angry": 0.5}),
        ]
    )
    proj = r.core_projection()
    assert abs(proj["sad"] - 0.6) < 0.01
    assert abs(proj["angry"] - 0.8) < 0.01


def test_primary_emotion():
    r = EmotionResult(my_emotions=[EmotionItem("happy", 0.8)])
    assert r.primary_emotion == "happy"
    assert r.primary_intensity == 0.8


def test_empty_emotion_result():
    r = EmotionResult()
    assert r.primary_emotion == "neutral"
    assert r.primary_intensity == 0.0
    assert r.core_projection() == {}

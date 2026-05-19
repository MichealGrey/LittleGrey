import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.emotion import EmotionEngine, EmotionConfig


class TestRecallTrigger:
    @pytest.fixture
    def engine(self):
        return EmotionEngine(config=EmotionConfig())

    def test_conflict_recall(self, engine):
        engine._levels['happy'] = 0.8
        engine._levels['sad'] = 0.5
        engine._levels['angry'] = 0.0
        engine.recall_trigger({
            'type': 'conflict',
            'emotion_impact': {'angry': 0.7}
        })
        assert engine._levels['angry'] >= 0.4
        assert engine._levels['sad'] >= 0.2

    def test_threat_recall(self, engine):
        engine._levels['happy'] = 0.8
        engine._levels['angry'] = 0.0
        engine._levels['anxious'] = 0.0
        engine.recall_trigger({
            'type': 'threat',
            'emotion_impact': {'anxious': 0.5}
        })
        assert engine._levels['angry'] >= 0.5
        assert engine._levels['anxious'] >= 0.3

    def test_insult_recall(self, engine):
        engine._levels['happy'] = 0.8
        engine._levels['angry'] = 0.0
        engine._levels['sad'] = 0.0
        engine.recall_trigger({
            'type': 'insult',
            'emotion_impact': {}
        })
        assert engine._levels['angry'] >= 0.6
        assert engine._levels['sad'] >= 0.3

    def test_caring_recall(self, engine):
        engine._levels['happy'] = 0.1
        engine._levels['excited'] = 0.0
        engine.recall_trigger({
            'type': 'caring',
            'emotion_impact': {}
        })
        assert engine._levels['happy'] >= 0.3
        assert engine._levels['excited'] >= 0.1

    def test_apology_recall(self, engine):
        engine._levels['happy'] = 0.1
        engine._levels['sad'] = 0.5
        engine.recall_trigger({
            'type': 'apology',
            'emotion_impact': {}
        })
        assert engine._levels['happy'] >= 0.2
        assert engine._levels['sad'] >= 0.1

    def test_unknown_type_no_effect(self, engine):
        engine._levels['happy'] = 0.5
        engine._levels['angry'] = 0.0
        engine.recall_trigger({
            'type': 'unknown_event',
            'emotion_impact': {}
        })
        assert engine._levels['happy'] == 0.5
        assert engine._levels['angry'] == 0.0

    def test_emotion_impact_applied(self, engine):
        engine._levels['happy'] = 0.0
        engine._levels['sad'] = 0.0
        engine.recall_trigger({
            'type': 'custom',
            'emotion_impact': {'happy': 0.8, 'sad': 0.3}
        })
        assert engine._levels['happy'] >= 0.5
        assert engine._levels['sad'] >= 0.3

    def test_respects_existing_higher_emotion(self, engine):
        engine._levels['happy'] = 0.5
        engine._levels['angry'] = 0.7
        engine.recall_trigger({
            'type': 'conflict',
            'emotion_impact': {'angry': 0.3}
        })
        assert engine._levels['angry'] == 0.7

    def test_max_intensity_capped_at_05(self, engine):
        engine._levels['happy'] = 0.0
        engine._levels['angry'] = 0.0
        engine.recall_trigger({
            'type': 'custom',
            'emotion_impact': {'angry': 0.9}
        })
        assert engine._levels['angry'] <= 0.5

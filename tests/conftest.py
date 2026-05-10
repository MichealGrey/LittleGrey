import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

for mod in ["volcenginesdkarkruntime", "volcengine", "chromadb"]:
    sys.modules.setdefault(mod, MagicMock())

import pytest
from src.agent.emotion import EmotionEngine
from src.core.config import EmotionConfig


@pytest.fixture
def emotion_config():
    return EmotionConfig(
        autonomous_drift_enabled=True,
        loneliness_threshold=600,
        drift_probability=0.15,
        time_mood_enabled=True,
        baseline_happy=0.05,
        baseline_sad=0.0,
        baseline_angry=0.0,
        baseline_anxious=0.0,
        baseline_excited=0.0,
        llm_understand_enabled=True,
        hard_constraints_enabled=True,
        angry_refuse_threshold=0.7,
        sad_short_reply_threshold=0.8,
        anxious_ask_threshold=0.6,
        trust_defensive_threshold=0.2,
    )


@pytest.fixture
def emotion(emotion_config):
    return EmotionEngine(llm=None, logger=None, config=emotion_config)

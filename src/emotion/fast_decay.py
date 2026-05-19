import math
from typing import Dict, Any

from src.emotion.registry import BaseEmotionStrategy, StrategyRegistry


@StrategyRegistry.register
class FastDecayStrategy(BaseEmotionStrategy):
    """Strategy A: Fast emotion decay based on time offline."""
    
    name = "fast_decay"
    
    def __init__(self, decay_rate: float = 0.02, happy_multiplier: float = 1.5):
        self.decay_rate = decay_rate
        self.happy_multiplier = happy_multiplier
    
    def calculate(self, current_emotion: Dict[str, float], memory_context: Any) -> Dict[str, float]:
        offline_minutes = getattr(memory_context, 'offline_minutes', 0)
        
        decayed = {}
        for emotion, value in current_emotion.items():
            if emotion == 'happy':
                decayed[emotion] = value * math.exp(-self.decay_rate * self.happy_multiplier * offline_minutes)
            else:
                decayed[emotion] = value * math.exp(-self.decay_rate * offline_minutes)
            
            decayed[emotion] = max(0.0, min(1.0, decayed[emotion]))
        
        return decayed

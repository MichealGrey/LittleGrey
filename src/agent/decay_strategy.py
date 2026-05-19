from abc import ABC, abstractmethod
import math


class DecayStrategy(ABC):
    """Base class for emotion decay strategies."""
    
    name: str = ""
    
    @abstractmethod
    def calculate(self, value: float, baseline: float, elapsed_hours: float) -> float:
        """Calculate decayed emotion value.
        
        Args:
            value: Current emotion value (0.0 - 1.0)
            baseline: Basemotion value to regress toward
            elapsed_hours: Hours since last update
            
        Returns:
            Decayed emotion value (0.0 - 1.0)
        """
        pass


class ExponentialDecay(DecayStrategy):
    """Exponential decay: value = baseline + (value - baseline) * e^(-rate * hours)"""
    
    name = "exponential"
    
    def __init__(self, rate: float = 0.02):
        self.rate = rate
    
    def calculate(self, value: float, baseline: float, elapsed_hours: float) -> float:
        decay = math.exp(-self.rate * elapsed_hours)
        return baseline + (value - baseline) * decay


class LinearDecay(DecayStrategy):
    """Linear decay: value = baseline + (value - baseline) * max(0, 1 - hours/duration)"""
    
    name = "linear"
    
    def __init__(self, duration_hours: float = 5.0):
        self.duration_hours = duration_hours
    
    def calculate(self, value: float, baseline: float, elapsed_hours: float) -> float:
        decay = max(0.0, 1.0 - elapsed_hours / self.duration_hours)
        return baseline + (value - baseline) * decay


class StepDecay(DecayStrategy):
    """Step decay: value drops by factor every interval hours."""
    
    name = "step"
    
    def __init__(self, interval_hours: float = 1.0, decay_factor: float = 0.5):
        self.interval_hours = interval_hours
        self.decay_factor = decay_factor
    
    def calculate(self, value: float, baseline: float, elapsed_hours: float) -> float:
        steps = int(elapsed_hours / self.interval_hours)
        decay = self.decay_factor ** steps
        return baseline + (value - baseline) * decay


class SlowNegativeDecay(DecayStrategy):
    """Slow decay for negative emotions: very gradual regression to baseline."""
    
    name = "slow_negative"
    
    def __init__(self, rate: float = 0.005):
        self.rate = rate
    
    def calculate(self, value: float, baseline: float, elapsed_hours: float) -> float:
        decay = math.exp(-self.rate * elapsed_hours)
        return baseline + (value - baseline) * decay

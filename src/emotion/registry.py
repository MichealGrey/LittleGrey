from abc import ABC, abstractmethod
from typing import Dict, Type, Any, List


class BaseEmotionStrategy(ABC):
    """Base class for all emotion strategies."""
    
    name: str = ""
    
    @abstractmethod
    def calculate(self, current_emotion: Dict[str, float], memory_context: Any) -> Dict[str, float]:
        """Calculate emotion based on current state and memory context."""
        pass


class StrategyRegistry:
    """Registry for emotion strategies using decorator pattern."""
    
    _strategies: Dict[str, Type[BaseEmotionStrategy]] = {}
    
    @classmethod
    def register(cls, strategy_cls: Type[BaseEmotionStrategy]) -> Type[BaseEmotionStrategy]:
        """Register a strategy class."""
        if not strategy_cls.name:
            raise ValueError(f"Strategy {strategy_cls.__name__} must have a 'name' attribute")
        cls._strategies[strategy_cls.name] = strategy_cls
        return strategy_cls
    
    @classmethod
    def get(cls, name: str) -> BaseEmotionStrategy:
        """Get a strategy instance by name."""
        strategy_cls = cls._strategies.get(name)
        if not strategy_cls:
            raise ValueError(f"Unknown strategy: {name}. Available: {list(cls._strategies.keys())}")
        return strategy_cls()
    
    @classmethod
    def available(cls) -> List[str]:
        """Get list of available strategy names."""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_class(cls, name: str) -> Type[BaseEmotionStrategy]:
        """Get a strategy class by name."""
        return cls._strategies.get(name)

from typing import Dict, Any

from src.emotion.registry import BaseEmotionStrategy, StrategyRegistry


@StrategyRegistry.register
class MemoryGraphStrategy(BaseEmotionStrategy):
    """Strategy B: Emotion recalculation based on memory context."""
    
    name = "memory_graph"
    
    def __init__(self, memory_weight: float = 0.3):
        self.memory_weight = memory_weight
    
    def calculate(self, current_emotion: Dict[str, float], memory_context: Any) -> Dict[str, float]:
        memory_impact = self._assess_memory_impact(memory_context)
        result = self._blend(current_emotion, memory_impact)
        return result
    
    def _assess_memory_impact(self, memory_context: Any) -> Dict[str, float]:
        impact = {}
        if hasattr(memory_context, 'emotion_context'):
            ctx = memory_context.emotion_context
            if ctx and 'trigger_event' in ctx:
                related_ids = ctx.get('related_memory_ids', [])
                for mem_id in related_ids:
                    mem = self._get_memory(mem_id, memory_context)
                    if mem:
                        for emo, val in mem.get('emotion_impact', {}).items():
                            impact[emo] = impact.get(emo, 0.0) + val
        
        if impact:
            max_val = max(impact.values()) if impact else 1.0
            impact = {k: v / max_val for k, v in impact.items()}
        
        return impact
    
    def _get_memory(self, mem_id: str, memory_context: Any) -> Any:
        if hasattr(memory_context, 'memories'):
            for mem in memory_context.memories:
                if mem.get('id') == mem_id:
                    return mem
        return None
    
    def _blend(self, current: Dict[str, float], memory_impact: Dict[str, float]) -> Dict[str, float]:
        result = {}
        all_keys = set(list(current.keys()) + list(memory_impact.keys()))
        for key in all_keys:
            current_val = current.get(key, 0.0)
            memory_val = memory_impact.get(key, 0.0)
            result[key] = current_val * (1 - self.memory_weight) + memory_val * self.memory_weight
            result[key] = max(0.0, min(1.0, result[key]))
        return result

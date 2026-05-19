import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.emotion.registry import BaseEmotionStrategy, StrategyRegistry
from src.emotion.fast_decay import FastDecayStrategy
from src.emotion.memory_graph import MemoryGraphStrategy
from src.emotion.fusion import EmotionFusion


class TestStrategyRegistry:
    def test_register_returns_class(self):
        assert StrategyRegistry.get_class('fast_decay') is FastDecayStrategy
    
    def test_register_returns_memory_graph(self):
        assert StrategyRegistry.get_class('memory_graph') is MemoryGraphStrategy
    
    def test_available_returns_both(self):
        available = StrategyRegistry.available()
        assert 'fast_decay' in available
        assert 'memory_graph' in available
    
    def test_get_returns_instance(self):
        instance = StrategyRegistry.get('fast_decay')
        assert isinstance(instance, FastDecayStrategy)
    
    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            StrategyRegistry.get('unknown_strategy')
    
    def test_strategy_without_name_raises(self):
        class BadStrategy(BaseEmotionStrategy):
            def calculate(self, current_emotion, memory_context):
                return current_emotion
        
        with pytest.raises(ValueError, match="must have a 'name' attribute"):
            StrategyRegistry.register(BadStrategy)


class TestFastDecayStrategy:
    def test_decay_with_time(self):
        strategy = FastDecayStrategy(decay_rate=0.1, happy_multiplier=1.5)
        current = {'happy': 0.8, 'sad': 0.5, 'angry': 0.6}
        
        ctx = type('MockContext', (), {'offline_minutes': 10})()
        result = strategy.calculate(current, ctx)
        
        assert result['happy'] < 0.8
        assert result['sad'] < 0.5
        assert result['angry'] < 0.6
    
    def test_no_decay_zero_time(self):
        strategy = FastDecayStrategy(decay_rate=0.1, happy_multiplier=1.5)
        current = {'happy': 0.8, 'sad': 0.5}
        
        ctx = type('MockContext', (), {'offline_minutes': 0})()
        result = strategy.calculate(current, ctx)
        
        assert abs(result['happy'] - 0.8) < 0.01
        assert abs(result['sad'] - 0.5) < 0.01
    
    def test_values_bounded(self):
        strategy = FastDecayStrategy(decay_rate=0.01, happy_multiplier=1.0)
        current = {'happy': 0.0, 'sad': 1.0}
        
        ctx = type('MockContext', (), {'offline_minutes': 100})()
        result = strategy.calculate(current, ctx)
        
        assert 0.0 <= result['happy'] <= 1.0
        assert 0.0 <= result['sad'] <= 1.0
    
    def test_happy_decays_faster(self):
        strategy = FastDecayStrategy(decay_rate=0.1, happy_multiplier=2.0)
        current = {'happy': 0.5, 'angry': 0.5}
        
        ctx = type('MockContext', (), {'offline_minutes': 5})()
        result = strategy.calculate(current, ctx)
        
        assert result['happy'] < result['angry']


class TestMemoryGraphStrategy:
    def test_blend_with_memory(self):
        strategy = MemoryGraphStrategy(memory_weight=0.5)
        current = {'happy': 0.2, 'sad': 0.8, 'angry': 0.9}
        
        class MockContext:
            emotion_context = {
                'trigger_event': 'conflict',
                'related_memory_ids': ['mem1', 'mem2']
            }
            memories = [
                {'id': 'mem1', 'emotion_impact': {'sad': 0.6, 'angry': 0.7}},
                {'id': 'mem2', 'emotion_impact': {'sad': 0.4, 'angry': 0.3}},
            ]
        
        result = strategy.calculate(current, MockContext())
        
        assert result['sad'] > 0.2
        assert result['angry'] > 0.2
    
    def test_no_memory_returns_decayed(self):
        strategy = MemoryGraphStrategy(memory_weight=0.3)
        current = {'happy': 0.5, 'sad': 0.3}
        
        ctx = type('MockContext', (), {'emotion_context': None})()
        result = strategy.calculate(current, ctx)
        
        expected_happy = 0.5 * 0.7
        expected_sad = 0.3 * 0.7
        assert abs(result['happy'] - expected_happy) < 0.01
        assert abs(result['sad'] - expected_sad) < 0.01
    
    def test_values_bounded(self):
        strategy = MemoryGraphStrategy(memory_weight=0.8)
        current = {'happy': 0.1, 'sad': 0.9}
        
        class MockContext:
            emotion_context = {
                'trigger_event': 'test',
                'related_memory_ids': ['mem1']
            }
            memories = [
                {'id': 'mem1', 'emotion_impact': {'happy': 1.0, 'sad': 1.0}},
            ]
        
        result = strategy.calculate(current, MockContext())
        
        assert 0.0 <= result['happy'] <= 1.0
        assert 0.0 <= result['sad'] <= 1.0


class TestEmotionFusion:
    def test_weighted_average(self):
        results = [{'happy': 0.8, 'sad': 0.2}, {'happy': 0.4, 'sad': 0.6}]
        weights = [0.7, 0.3]
        
        fused = EmotionFusion.weighted_average(results, weights)
        
        expected_happy = 0.8 * 0.7 + 0.4 * 0.3
        assert abs(fused['happy'] - expected_happy) < 0.01
    
    def test_max_pool(self):
        results = [{'happy': 0.3, 'sad': 0.7}, {'happy': 0.8, 'sad': 0.2}]
        
        fused = EmotionFusion.max_pool(results)
        
        assert fused['happy'] == 0.8
        assert fused['sad'] == 0.7
    
    def test_threshold_select(self):
        results = [{'happy': 0.3, 'sad': 0.8}, {'happy': 0.7, 'sad': 0.2}]
        
        fused = EmotionFusion.threshold_select(results, threshold=0.5)
        
        assert fused['happy'] == 0.7
        assert fused['sad'] == 0.8
    
    def test_empty_results_returns_empty(self):
        assert EmotionFusion.weighted_average([], []) == {}
        assert EmotionFusion.max_pool([]) == {}
        assert EmotionFusion.threshold_select([]) == {}
    
    def test_fusion_bounded(self):
        results = [{'happy': 1.5, 'sad': -0.5}, {'happy': 0.5, 'sad': 0.5}]
        weights = [0.5, 0.5]
        
        fused = EmotionFusion.weighted_average(results, weights)
        
        assert 0.0 <= fused['happy'] <= 1.0
        assert 0.0 <= fused['sad'] <= 1.0
    
    def test_mixed_keys(self):
        results = [{'happy': 0.5, 'sad': 0.3}, {'happy': 0.4, 'angry': 0.6}]
        weights = [0.5, 0.5]
        
        fused = EmotionFusion.weighted_average(results, weights)
        
        assert 'happy' in fused
        assert 'sad' in fused
        assert 'angry' in fused

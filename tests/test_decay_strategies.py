import pytest
import math
from src.agent.decay_strategy import ExponentialDecay, LinearDecay, StepDecay, SlowNegativeDecay


class TestExponentialDecay:
    def test_basic_decay(self):
        strategy = ExponentialDecay(rate=0.05)
        result = strategy.calculate(1.0, 0.0, 1.0)
        expected = math.exp(-0.05)
        assert abs(result - expected) < 0.001
    
    def test_zero_time(self):
        strategy = ExponentialDecay(rate=0.05)
        result = strategy.calculate(1.0, 0.0, 0.0)
        assert abs(result - 1.0) < 0.001
    
    def test_with_baseline(self):
        strategy = ExponentialDecay(rate=0.1)
        result = strategy.calculate(1.0, 0.5, 1.0)
        expected = 0.5 + (1.0 - 0.5) * math.exp(-0.1)
        assert abs(result - expected) < 0.001
    
    def test_long_time(self):
        strategy = ExponentialDecay(rate=0.05)
        result = strategy.calculate(1.0, 0.0, 100.0)
        assert result < 0.01
    
    def test_different_rates(self):
        fast = ExponentialDecay(rate=0.1)
        slow = ExponentialDecay(rate=0.01)
        
        fast_result = fast.calculate(1.0, 0.0, 1.0)
        slow_result = slow.calculate(1.0, 0.0, 1.0)
        
        assert fast_result < slow_result


class TestLinearDecay:
    def test_basic_decay(self):
        strategy = LinearDecay(duration_hours=5.0)
        result = strategy.calculate(1.0, 0.0, 2.5)
        expected = 1.0 * (1.0 - 2.5/5.0)
        assert abs(result - expected) < 0.001
    
    def test_zero_time(self):
        strategy = LinearDecay(duration_hours=5.0)
        result = strategy.calculate(1.0, 0.0, 0.0)
        assert abs(result - 1.0) < 0.001
    
    def test_full_duration(self):
        strategy = LinearDecay(duration_hours=5.0)
        result = strategy.calculate(1.0, 0.0, 5.0)
        assert abs(result) < 0.001
    
    def test_over_duration(self):
        strategy = LinearDecay(duration_hours=5.0)
        result = strategy.calculate(1.0, 0.0, 10.0)
        assert abs(result) < 0.001
    
    def test_with_baseline(self):
        strategy = LinearDecay(duration_hours=5.0)
        result = strategy.calculate(1.0, 0.5, 2.5)
        expected = 0.5 + (1.0 - 0.5) * 0.5
        assert abs(result - expected) < 0.001


class TestStepDecay:
    def test_one_step(self):
        strategy = StepDecay(interval_hours=1.0, decay_factor=0.5)
        result = strategy.calculate(1.0, 0.0, 1.0)
        assert abs(result - 0.5) < 0.001
    
    def test_two_steps(self):
        strategy = StepDecay(interval_hours=1.0, decay_factor=0.5)
        result = strategy.calculate(1.0, 0.0, 2.0)
        assert abs(result - 0.25) < 0.001
    
    def test_zero_time(self):
        strategy = StepDecay(interval_hours=1.0, decay_factor=0.5)
        result = strategy.calculate(1.0, 0.0, 0.0)
        assert abs(result - 1.0) < 0.001
    
    def test_partial_interval(self):
        strategy = StepDecay(interval_hours=1.0, decay_factor=0.5)
        result = strategy.calculate(1.0, 0.0, 0.5)
        assert abs(result - 1.0) < 0.001
    
    def test_with_baseline(self):
        strategy = StepDecay(interval_hours=1.0, decay_factor=0.5)
        result = strategy.calculate(1.0, 0.5, 1.0)
        expected = 0.5 + (1.0 - 0.5) * 0.5
        assert abs(result - expected) < 0.001


class TestSlowNegativeDecay:
    def test_basic_decay(self):
        strategy = SlowNegativeDecay(rate=0.005)
        result = strategy.calculate(1.0, 0.0, 1.0)
        expected = math.exp(-0.005)
        assert abs(result - expected) < 0.001
    
    def test_slower_than_normal(self):
        slow = SlowNegativeDecay(rate=0.005)
        normal = ExponentialDecay(rate=0.02)
        
        slow_result = slow.calculate(1.0, 0.0, 1.0)
        normal_result = normal.calculate(1.0, 0.0, 1.0)
        
        assert slow_result > normal_result


class TestStrategyNames:
    def test_exponential_name(self):
        assert ExponentialDecay().name == "exponential"
    
    def test_linear_name(self):
        assert LinearDecay().name == "linear"
    
    def test_step_name(self):
        assert StepDecay().name == "step"
    
    def test_slow_negative_name(self):
        assert SlowNegativeDecay().name == "slow_negative"

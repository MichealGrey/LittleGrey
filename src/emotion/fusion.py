from typing import Dict, List


class EmotionFusion:
    """Fusion module for combining multiple strategy results."""
    
    @staticmethod
    def weighted_average(strategy_results: List[Dict[str, float]], weights: List[float]) -> Dict[str, float]:
        """Weighted average fusion."""
        if not strategy_results or not weights:
            return {}
        
        all_keys = set()
        for result in strategy_results:
            all_keys.update(result.keys())
        
        fused = {}
        for key in all_keys:
            weighted_sum = 0.0
            weight_total = 0.0
            for i, result in enumerate(strategy_results):
                if key in result:
                    weighted_sum += result[key] * weights[i]
                    weight_total += weights[i]
            
            fused[key] = weighted_sum / weight_total if weight_total > 0 else 0.0
            fused[key] = max(0.0, min(1.0, fused[key]))
        
        return fused
    
    @staticmethod
    def max_pool(strategy_results: List[Dict[str, float]]) -> Dict[str, float]:
        """Max pool fusion."""
        if not strategy_results:
            return {}
        
        all_keys = set()
        for result in strategy_results:
            all_keys.update(result.keys())
        
        fused = {}
        for key in all_keys:
            values = [r.get(key, 0.0) for r in strategy_results]
            fused[key] = max(values) if values else 0.0
        
        return fused
    
    @staticmethod
    def threshold_select(strategy_results: List[Dict[str, float]], threshold: float = 0.5) -> Dict[str, float]:
        """Threshold-based selection fusion."""
        if not strategy_results:
            return {}
        
        all_keys = set()
        for result in strategy_results:
            all_keys.update(result.keys())
        
        fused = {}
        for key in all_keys:
            values = [r.get(key, 0.0) for r in strategy_results]
            above_threshold = [v for v in values if v >= threshold]
            fused[key] = max(above_threshold) if above_threshold else (max(values) if values else 0.0)
        
        return fused

update = '''

---

## 14. Generalization Assessment

### 14.1 Evaluation Dimensions

#### Architecture Level
**Score**: 4/5

**Pros**:
- Clear architecture, well-separated modules
- Extensible: new strategies only need to implement `calculate()` interface
- Configuration-driven: strategies, weights, decay rates are configurable

**Cons**:
- Hardcoded context types: `conflict|caring|probing|normal` are hardcoded

---

#### Strategy Level
**Score**: 4/5

**Pros**:
- Dual strategies decoupled (FastDecay and MemoryGraph)
- Unified strategy interface
- Fusion is independent

**Cons**:
- Fixed number of strategies (only A and B)

---

#### Context Classification Level
**Score**: 3/5

**Pros**:
- LLM-driven, no keyword matching
- Prompt is tweakable
- reason field for explainability

**Cons**:
- Hardcoded context types in Prompt
- Hardcoded rules

---

#### Emotion Model Level
**Score**: 2/5

**Pros**:
- 5 emotion dimensions cover basic emotions

**Cons**:
- Not extensible: adding new emotions requires code changes
- Emotion list hardcoded in fusion

---

#### Memory Model Level
**Score**: 3/5

**Pros**:
- Memory summarizer depends on external system
- Memory ID association

**Cons**:
- Assumes memory has `event_type` and `emotion_impact` fields

---

#### Configuration Level
**Score**: 4/5

**Pros**:
- decay_rate, fusion_weights, summary are configurable

**Cons**:
- Configuration structure is not very flexible

---

### 14.2 Comprehensive Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Architecture | 4/5 | Good |
| Strategy | 4/5 | Good |
| Context Classification | 3/5 | Medium |
| Emotion Model | 2/5 | Weak |
| Memory Model | 3/5 | Medium |
| Configuration | 4/5 | Good |
| **Overall** | **3.2/5** | **Acceptable, recommend optimizing emotion model and context classification** |

---

## 15. Generalization Improvement Suggestions

### 15.1 Suggestion 1: Emotion Model Abstraction

**Problem**: Emotion dimensions are hardcoded

**Solution**:
```python
# Current (problem)
for emotion in ['happy', 'sad', 'angry', 'anxious', 'excited']:

# Suggested
class EmotionConfig:
    DIMENSIONS = ['happy', 'sad', 'angry', 'anxious', 'excited']
    
    @classmethod
    def add_emotion(cls, name):
        if name not in cls.DIMENSIONS:
            cls.DIMENSIONS.append(name)

# Usage
for emotion in EmotionConfig.DIMENSIONS:
```

---

### 15.2 Suggestion 2: Strategy Registry Mechanism

**Problem**: Fixed number of strategies

**Solution**:
```python
from abc import ABC, abstractmethod

class BaseEmotionStrategy(ABC):
    name = ""
    
    @abstractmethod
    def calculate(self, current_emotion, memory_context):
        pass

class StrategyRegistry:
    _strategies = {}
    
    @classmethod
    def register(cls, strategy_class):
        cls._strategies[strategy_class.name] = strategy_class
        return strategy_class
    
    @classmethod
    def get(cls, name):
        return cls._strategies.get(name)
    
    @classmethod
    def all(cls):
        return list(cls._strategies.keys())

@StrategyRegistry.register
class FastDecayStrategy(BaseEmotionStrategy):
    name = "fast_decay"
    def calculate(self, current_emotion, memory_context):
        pass

@StrategyRegistry.register
class MemoryGraphStrategy(BaseEmotionStrategy):
    name = "memory_graph"
    def calculate(self, current_emotion, memory_context):
        pass
```

---

### 15.3 Suggestion 3: Prompt Template

**Problem**: Rules are hardcoded in Prompt

**Solution**:
```python
from dataclasses import dataclass
from typing import List

@dataclass
class ContextRule:
    context_type: str
    description: str
    recommended_strategy: str

class PromptTemplate:
    def __init__(self, rules):
        self.rules = rules
    
    def build(self, user_input, current_emotion, memory_summary):
        rule_text = "\n".join([
            f"- {r.description} -> {r.recommended_strategy}"
            for r in self.rules
        ])
        
        return f'''Based on following info, determine context type and recommended strategy:

User input: {user_input}
Current emotion: {current_emotion}
Recent memory: {memory_summary}

Return JSON:
{{
  "context_type": "descriptive string",
  "strategy": "strategy name",
  "reason": "brief reason"
}}

Rules:
{rule_text}
'''

template = PromptTemplate([
    ContextRule("conflict", "Conflict/Attack", "memory_graph"),
    ContextRule("caring", "Caring/Comfort", "fusion"),
    ContextRule("probing", "Probing/Asking history", "memory_graph"),
    ContextRule("normal", "Daily conversation", "fast_decay"),
])
```

---

### 15.4 Suggestion 4: Fusion Abstraction

**Problem**: Fusion only supports 2 strategies

**Solution**:
```python
from typing import List, Dict

class EmotionFusion:
    @staticmethod
    def weighted_average(strategy_results, weights):
        pass
    
    @staticmethod
    def max_pool(strategy_results):
        pass
    
    @staticmethod
    def threshold_select(strategy_results, threshold=0.5):
        pass
```

---

### 15.5 Suggestion 5: Dynamic Context Types

**Problem**: context_type is hardcoded enum

**Solution**: Let LLM decide freely, return descriptive string

```python
# Current
context_type: conflict|caring|probing|normal

# Suggested
context_type: descriptive string (e.g., "apology_and_reconciliation")
```

---

## 16. Improvement Priority

| Priority | Suggestion | Benefit | Complexity | Recommended Phase |
|----------|------------|---------|------------|------------------|
| P0 | Emotion Model Abstraction | High | Medium | First implementation |
| P1 | Strategy Registry | High | Low | First implementation |
| P2 | Prompt Template | Medium | Low | First implementation |
| P3 | Fusion Abstraction | Medium | Medium | Later iteration |
| P4 | Dynamic Context Types | High | High | Later iteration |

---
'''

with open('docs/emotion_persistence_plan.md', 'a', encoding='utf-8') as f:
    f.write(update)

import os
os.remove(__file__)

print('Plan updated: docs/emotion_persistence_plan.md')

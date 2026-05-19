import base64

update_content = '''

---

## 十四、泛化性评估

### 14.1 评估维度

#### 架构层面
**评分**: ⭐⭐⭐⭐ (4/5)

**优点**:
- 核心架构清晰，模块划分合理，逻辑分离
- 可扩展，新增策略只需实现 `calculate()` 接口
- 配置驱动，策略、权重、衰减率均可配置

**问题**:
- 硬编码场景类型：`conflict|caring|probing|normal` 这 4 种场景类型是硬编码的，没有通过配置扩展

---

#### 策略层面
**评分**: ⭐⭐⭐⭐ (4/5)

**优点**:
- 双策略设计解耦，方案 A（快速衰减）和方案 B（记忆图谱）各自独立
- 策略接口统一，都实现 `calculate(current_emotion, memory_context)`
- 融合器独立，可以扩展为任意策略组合

**问题**:
- 策略数量固定，只有 A、B 两种，没有更多策略选择

---

#### 情境分类层面
**评分**: ⭐⭐⭐ (3/5)

**优点**:
- LLM 驱动，没有关键词，减少硬编码规则
- Prompt 可微调，改 Prompt 就能扩展识别新情境
- reason 字段可解释、可记录

**问题**:
- 场景类型硬编码：Prompt 中 `context_type` 还是硬编码枚举
- 规则硬编码：规则部分还是硬编码的（conflict→B, caring→fusion 等）

---

#### 情绪模型层面
**评分**: ⭐⭐ (2/5)

**优点**:
- 5 种情绪维度（happy, sad, angry, anxious, excited）覆盖基本情绪

**问题**:
- 情绪维度不支持扩展：如果要新增"嫉妒"、"无聊"等情绪，需要改多处代码
- 融合器硬编码：`for emotion in ['happy', 'sad', 'angry', 'anxious', 'excited']`

---

#### 记忆模型层面
**评分**: ⭐⭐⭐ (3/5)

**优点**:
- 记忆摘要器依赖外部记忆系统
- 记忆 ID 关联：`related_memory_ids`

**问题**:
- 记忆格式假设：假设记忆有 `event_type` 和 `emotion_impact` 字段

---

#### 配置层面
**评分**: ⭐⭐⭐⭐ (4/5)

**优点**:
- decay_rate、fusion_weights、summary 等参数可配置

**问题**:
- 配置结构不够灵活：`smart_config` 是固定的子配置

---

### 14.2 综合评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构层面 | ⭐⭐⭐⭐ | 好 |
| 策略层面 | ⭐⭐⭐⭐ | 好 |
| 情境分类 | ⭐⭐⭐ | 中 |
| 情绪模型 | ⭐⭐ | 弱 |
| 记忆模型 | ⭐⭐⭐ | 中 |
| 配置层面 | ⭐⭐⭐⭐ | 好 |
| **综合** | **⭐⭐⭐** | **可接受，建议优化情绪模型和情境分类** |

---

## 十五、泛化性优化建议

### 15.1 建议 1：情绪模型抽象化

**问题**: 情绪维度硬编码在多处代码中

**优化方案**:

```python
# 当前（问题）
for emotion in ['happy', 'sad', 'angry', 'anxious', 'excited']:

# 建议优化
class EmotionConfig:
    DIMENSIONS = ['happy', 'sad', 'angry', 'anxious', 'excited']
    
    @classmethod
    def add_emotion(cls, name: str):
        if name not in cls.DIMENSIONS:
            cls.DIMENSIONS.append(name)

# 使用
for emotion in EmotionConfig.DIMENSIONS:
```

**配置化**:
```yaml
emotion:
  dimensions:
    - happy
    - sad
    - angry
    - anxious
    - excited
    # 可新增
    # - envy
    # - bored
```

---

### 15.2 建议 2：情境类型动态化

**问题**: Prompt 中 `context_type` 硬编码枚举

**优化方案**:

```python
# 当前
context_type: conflict|caring|probing|normal

# 建议优化（让LLM自行决定）
Prompt: 请判断当前对话情境类型，并返回一个描述性的字符串

# 返回示例
{"context_type": "apology_and_reconciliation", "strategy": "fusion", ...}
```

**或者半动态化**:
```python
class ContextTypeRegistry:
    TYPES = ['conflict', 'caring', 'probing', 'normal']
    
    @classmethod
    def register(cls, context_type: str, default_strategy: str):
        cls.TYPES.append(context_type)
        # 同时注册默认策略映射
        cls.STRATEGY_MAPPING[context_type] = default_strategy
```

---

### 15.3 建议 3：策略注册机制

**问题**: 策略数量固定（A、B）

**优化方案**:

```python
from abc import ABC, abstractmethod

class BaseEmotionStrategy(ABC):
    name: str = ""
    
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
    def get(cls, name: str):
        return cls._strategies.get(name)
    
    @classmethod
    def all(cls):
        return list(cls._strategies.keys())

# 使用装饰器注册
@StrategyRegistry.register
class FastDecayStrategy(BaseEmotionStrategy):
    name = "fast_decay"  # 替代 "A"
    def calculate(self, current_emotion, memory_context):
        pass

@StrategyRegistry.register
class MemoryGraphStrategy(BaseEmotionStrategy):
    name = "memory_graph"  # 替代 "B"
    def calculate(self, current_emotion, memory_context):
        pass

# 新增策略只需注册
@StrategyRegistry.register
class HybridStrategy(BaseEmotionStrategy):
    name = "hybrid"
    def calculate(self, current_emotion, memory_context):
        pass
```

**配置化**:
```yaml
emotion:
  strategies:
    enabled:
      - fast_decay
      - memory_graph
      # - hybrid  # 可新增
```

---

### 15.4 建议 4：融合器抽象化

**问题**: 融合器只支持两种策略加权融合

**优化方案**:

```python
from typing import List, Dict

class EmotionFusion:
    @staticmethod
    def weighted_average(strategy_results: List[Dict], weights: List[float]):
        """加权平均融合"""
        pass
    
    @staticmethod
    def max_pool(strategy_results: List[Dict]):
        """取最大值融合"""
        pass
    
    @staticmethod
    def threshold_select(strategy_results: List[Dict], threshold: float = 0.5):
        """阈值选择融合"""
        pass

# 可配置融合策略
fusion_config:
  method: "weighted_average"  # weighted_average | max_pool | threshold_select
  weights:
    fast_decay: 0.6
    memory_graph: 0.4
```

---

### 15.5 建议 5：Prompt 模板化

**问题**: 规则部分硬编码在 Prompt 中

**优化方案**:

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class ContextRule:
    context_type: str
    description: str
    recommended_strategy: str

class PromptTemplate:
    def __init__(self, rules: List[ContextRule]):
        self.rules = rules
    
    def build(self, user_input, current_emotion, memory_summary):
        rule_text = "\\n".join([
            f"- {r.description} → {r.recommended_strategy}"
            for r in self.rules
        ])
        
        return f'''根据以下信息判断情境类型和推荐策略：

用户输入：{user_input}
当前情绪：{current_emotion}
近期记忆：{memory_summary}

返回 JSON：
{{
  "context_type": "描述性字符串",
  "strategy": "策略名称",
  "reason": "简短原因"
}}

规则：
{rule_text}
'''

# 使用
template = PromptTemplate([
    ContextRule("conflict", "冲突/攻击", "memory_graph"),
    ContextRule("caring", "关怀/安抚", "fusion"),
    ContextRule("probing", "试探/询问历史", "memory_graph"),
    ContextRule("normal", "日常对话", "fast_decay"),
])
```

---

## 十六、优化优先级

| 优先级 | 建议 | 收益 | 复杂度 | 建议阶段 |
|--------|------|------|--------|---------|
| P0 | 情绪模型抽象化 | 高 | 中 | 第一版实现时就做 |
| P1 | 策略注册机制 | 高 | 低 | 第一版实现时就做 |
| P2 | Prompt 模板化 | 中 | 低 | 第一版实现时就做 |
| P3 | 融合器抽象化 | 中 | 中 | 后续迭代 |
| P4 | 情境类型动态化 | 高 | 高 | 后续迭代 |

---
'''

with open('docs/emotion_persistence_plan.md', 'a', encoding='utf-8') as f:
    f.write(update_content)

import os
os.remove(__file__)

print('方案文件已更新: docs/emotion_persistence_plan.md')

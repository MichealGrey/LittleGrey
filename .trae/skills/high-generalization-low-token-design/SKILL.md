---
name: "high-generalization-low-token-design"
description: "Design principles for high generalization and minimal token consumption. Invoke when designing system architecture, writing prompts, or implementing features to ensure extensibility and token efficiency."
---

# High Generalization + Low Token Design Principles

## Core Principles

### Principle 1: Configuration Over Hardcoding

**Rule:** Never hardcode values, types, or rules that might need extension.

**Bad:**
```python
# Hardcoded emotion types
for emotion in ['happy', 'sad', 'angry', 'anxious', 'excited']:
```

**Good:**
```python
# Configurable, extensible
for emotion in config.emotion_dimensions:
```

**Token Impact:** Configuration adds ~10 tokens once, saves 50-100 tokens per future extension.

---

### Principle 2: LLM-Driven Over Rule-Based

**Rule:** Let LLM make decisions based on context, not hardcoded rules or keyword matching.

**Bad:**
```python
if '打' in text or '骂' in text:
    return 'conflict'
```

**Good:**
```python
# Let LLM decide based on full context
decision = llm.classify_context(user_input, emotion, memory_summary)
```

**Token Impact:** +50-100 tokens per call, but eliminates maintenance cost and improves accuracy.

---

### Principle 3: Abstract Interfaces

**Rule:** Use abstract base classes or interfaces for pluggable components.

**Bad:**
```python
def process(self, user_input, strategy):
    if strategy == 'A':
        return strategy_a.calculate(...)
    elif strategy == 'B':
        return strategy_b.calculate(...)
```

**Good:**
```python
# Registry pattern, open-closed principle
strategy = StrategyRegistry.get(decision['strategy_name'])
return strategy.calculate(...)
```

**Token Impact:** 0 (all local computation)

---

### Principle 4: Minimal Context Transfer

**Rule:** Only pass necessary information to LLM. Summarize, don't dump.

**Bad:**
```python
# Pass full memory history
context = {
    'all_memories': memory.get_all(),  # 500-1000+ tokens
    'emotion_history': emotion.all_history()
}
```

**Good:**
```python
# Pass only summary
context = {
    'recent_summary': memory.summarize(limit=3, max_tokens=50),  # <50 tokens
    'current_emotion': emotion.current()
}
```

**Token Impact:** Reduces from 500-1000+ to <50 tokens per call.

---

### Principle 5: Local Computation Over LLM Calls

**Rule:** Do math, logic, and transformations locally. Only call LLM for judgment, creativity, or understanding.

**Bad:**
```python
# Unnecessary LLM call for simple math
decay_result = llm.calculate_decay(emotion, time_passed)
```

**Good:**
```python
# Local computation, 0 tokens
decay_result = emotion * math.exp(-decay_rate * time_passed)
```

**Token Impact:** Saves 100-500 tokens per avoided call.

---

### Principle 6: Template Over Inline

**Rule:** Use templated prompts that can be configured, not hardcoded inline strings.

**Bad:**
```python
prompt = "判断情境：冲突->B, 关怀->fusion, 试探->B, 日常->A"
```

**Good:**
```python
prompt = PromptTemplate(rules=config.context_rules).build(context)
```

**Token Impact:** Same token cost, but enables configuration changes without code changes.

---

## Design Checklist

Before implementing any feature, ask:

| Question | Yes | No |
|----------|-----|-----|
| Can this be configured instead of hardcoded? | Good | Fix needed |
| Is LLM only called for judgment/understanding? | Good | Fix needed |
| Is context transfer minimal (summary, not dump)? | Good | Fix needed |
| Are interfaces abstract (not tied to specific impl)? | Good | Fix needed |
| Can new types be added without code changes? | Good | Fix needed |

---

## Token Budget Guidelines

| Component | Budget | Notes |
|-----------|--------|-------|
| Context Summary | <50 tokens | Recent memories only |
| Prompt Template | <100 tokens | Include rules |
| LLM Decision Call | 50-150 tokens | One call per user input |
| Local Computation | 0 tokens | Decay, fusion, etc. |
| **Total Per Request** | **<200 tokens** | Target |

---

## When to Invoke

Invoke this skill when:
- Designing new system architecture
- Writing prompts for LLM
- Implementing features that might be extended
- Reviewing code for hardcoded values
- Optimizing token consumption
- Adding new strategies, emotions, or context types

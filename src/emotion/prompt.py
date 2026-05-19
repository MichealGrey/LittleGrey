from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ContextRule:
    type: str
    description: str
    strategy: str


class PromptTemplate:
    def __init__(self, rules: List[ContextRule]):
        self.rules = rules
    
    def build(self, user_input: str, current_emotion: Dict[str, float], memory_summary: str) -> str:
        rule_lines = [
            f"- {r.description} -> {r.strategy}"
            for r in self.rules
        ]
        rule_text = "\n".join(rule_lines)
        
        return (
            "根据以下信息判断情境类型和推荐策略：\n\n"
            f"用户输入：{user_input}\n"
            f"当前情绪：{current_emotion}\n"
            f"近期记忆：{memory_summary}\n\n"
            '返回 JSON：\n'
            '{\n'
            '  "context_type": "描述性字符串",\n'
            '  "strategy": "策略名称",\n'
            '  "reason": "简短原因"\n'
            '}\n\n'
            f"规则：\n{rule_text}"
        )
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "PromptTemplate":
        rules = [
            ContextRule(
                type=r.get('type', ''),
                description=r.get('description', ''),
                strategy=r.get('strategy', '')
            )
            for r in config.get('context_rules', [])
        ]
        return cls(rules)

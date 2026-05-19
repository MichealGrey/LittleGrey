import json
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class StructuredOutputAdapter:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def chat_with_structured_output(
        self,
        messages: list[dict],
        response_format: dict,
        use_tools: bool = False,
        behavior_modifiers: dict[str, Any] | None = None,
        relationship_desc: str = "",
        mood_description: str = "",
        emotion_system_addition: str = "",
    ) -> dict:
        system_prompt = self.llm_client._build_system_prompt(
            behavior_modifiers=behavior_modifiers,
            relationship_desc=relationship_desc,
            mood_description=mood_description,
            emotion_system_addition=emotion_system_addition,
        )

        structured_instruction = (
            "\n\n[{structured Output Requirement}]\n"
            "Please return your response as a JSON object with the following fields:\n"
            f"{json.dumps(response_format, ensure_ascii=False, indent=2)}\n"
            "Return ONLY the JSON object, no extra text.\n"
            "[{End of Structured Output }]\n"
        )

        modified_system = system_prompt + structured_instruction

        full_messages = [{"role": "system", "content": modified_system}] + messages

        result = self.llm_client.chat(
            messages=full_messages,
            use_tools=use_tools,
        )

        content = result.get("content", "")
        return self._parse_structured_response(content)

    def _parse_structured_response(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.error(f"Failed to parse structured response: {content[:100]}")
        return {"raw": content}

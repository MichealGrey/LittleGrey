import json
import logging
from .tokens import DialogToken

logger = logging.getLogger(__name__)


class DialogParser:
    @staticmethod
    def parse(llm_output: str) -> list[DialogToken]:
        try:
            data = json.loads(llm_output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM output as JSON: {e}")
            return []

        dialog_list = data.get("dialog", [])
        if not isinstance(dialog_list, list):
            logger.error("LLM output missing 'dialog' array")
            return []

        tokens = []
        for item in dialog_list:
            try:
                token = DialogToken.from_dict(item)
                tokens.append(token)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid dialog token: {e}")
                continue

        return tokens

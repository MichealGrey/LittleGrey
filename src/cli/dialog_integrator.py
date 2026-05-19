import json
import logging
from typing import Any

from extensions.dialog import DialogParser, HandlerChain
from extensions.memory_enhanced import CompactMemoryManager
from extensions.dialog.structured_llm import StructuredOutputAdapter

logger = logging.getLogger(__name__)


class DialogIntegrator:
    def __init__(self, llm_client, max_tokens=5000):
        self.llm_client = llm_client
        self.parser = DialogParser()
        self.handler_chain = HandlerChain()
        self.memory_manager = CompactMemoryManager(max_tokens=max_tokens)
        self.structured_adapter = StructuredOutputAdapter(llm_client)

    def process_with_structured_dialog(
        self,
        messages: list[dict],
        response_format: dict | None = None,
        ** llm_kwargs,
    ) -> dict:
        if response_format:
            result = self.structured_adapter.chat_with_structured_output(
                messages=messages,
                response_format=response_format,
                **llm_kwargs,
            )
        else:
            result = self.llm_client.chat(messages=messages, **llm_kwargs)

        content = result.get("content", "")
        tokens = self.parser.parse(content)

        if tokens:
            processed = self.handler_chain.process(tokens)
            return processed
        else:
            return {
                "display_message": content,
                "choices": [],
                "stat_changes": {},
                "cot_text": "",
                "narrative": "",
            }

    def compress_memory(self, messages: list[dict]) -> tuple[list, list]:
        return self.memory_manager.compress_conversation(messages)

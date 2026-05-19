import logging
from abc import ABC, abstractmethod
from .tokens import DialogToken, TokenType

logger = logging.getLogger(__name__)


class MessageHandler(ABC):
    @abstractmethod
    def handle(self, token: DialogToken) -> bool:
        """Handle a dialog token. Return True if handled."""
        pass

    @property
    @abstractmethod
    def supported_types(self) -> list[TokenType]:
        """Return list of supported token types."""
        pass


class HandlerChain:
    def __init__(self):
        self._handlers: list[MessageHandler] = []

    def register(self, handler: MessageHandler):
        self._handlers.append(handler)
        logger.info(f"Registered handler: {handler.__class__.__name__}")

    def process(self, tokens: list[DialogToken]) -> dict:
        result = {
            "display_message": "",
            "choices": [],
            "stat_changes": {},
            "cot_text": "",
            "narration": ""
        }

        for token in tokens:
            for handler in self._handlers:
                if token.type in handler.supported_types:
                    handler.handle(token)
                    break

            if token.type == TokenType.DIALOG:
                result["display_message"] += token.text
            elif token.type == TokenType.CHOICE:
                result["choices"].extend(token.options)
            elif token.type == TokenType.STAT:
                result["stat_changes"].update(token.stat_changes)
            elif token.type == TokenType.COT:
                result["cot_text"] += token.text
            elif token.type == TokenType.NARR:
                result["narration"] += token.text

        return result

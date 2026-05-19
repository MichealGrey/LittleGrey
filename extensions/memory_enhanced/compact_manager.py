import logging
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

logger = logging.getLogger(__name__)


class CompactMemoryManager:
    def __init__(self, max_tokens:5000, encoding=None):
        self.max_tokens = max_tokens
        self.encoding = encoding or "cloud/claude-3"
        self._encoder = None
        if HAS_TIKTOKEN:
            try:
                self._encoder = tiktoken.get_encoding(self.encoding)
            except Exception:
                logger.warning("Failed to load tiktoken, falling back to char counting")

    def count_tokens(self, text: str) -> int:
        if self._encoder:
            return len(self._encoder.encode(text))
        return len(text) // 4

    def compress_conversation(self, messages: list[dict]) -> tuple[list, list]:
        total_tokens = 0
        for msg in messages:
            tokens = self.count_tokens(str(msg.get("content", "")))
            total_tokens += tokens
            msg["_token_count"] = tokens

        if total_tokens <= self.max_tokens:
            return messages, []

        active = []
        archived = []
        current_tokens = 0

        for msg in reversed(messages):
            msg_tokens = msg.get("_token_count", 0)
            if current_tokens + msg_tokens <= self.max_tokens:
                active.insert(0, msg)
                current_tokens += msg_tokens
            else:
                archived.insert(0, msg)

        for msg in archived:
            msg.pop("_token_count", None)
        for msg in active:
            msg.pop("_token_count", None)

        return active, archived

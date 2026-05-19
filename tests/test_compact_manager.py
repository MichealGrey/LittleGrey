import pytest
from extensions.memory_enhanced.compact_manager import CompactMemoryManager


def test_count_tokens_with_char_counting():
    manager = CompactMemoryManager(max_tokens=1000)
    text = "Hello world"
    count = manager.count_tokens(text)
    assert count > 0


def test_compress_within_limit():
    manager = CompactMemoryManager(max_tokens=5000)
    messages = [{"role": "user", "content": "Hello"}]
    active, archived = manager.compress_conversation(messages)
    assert len(active) == 1
    assert len(archived) == 0


def test_compress_exceeds_limit():
    manager = CompactMemoryManager(max_tokens=100)
    messages = [
        {"role": "user", "content": "A"},
        {"role": "assistant", "content": "B"},
        {"role": "user", "content": "C"},
    ]
    active, archived = manager.compress_conversation(messages)
    assert len(active) + len(archived) == 3

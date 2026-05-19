import pytest
from unittest.mock import MagicMock
from extensions.dialog import DialogToken, TokenType, DialogParser, HandlerChain
from extensions.memory_enhanced import CompactMemoryManager
from extensions.dialog.structured_llm import StructuredOutputAdapter
from src.cli.dialog_integrator import DialogIntegrator


def test_integrator_creation():
    mock_llm = MagicMock()
    integrator = DialogIntegrator(mock_llm)
    assert integrator.parser is not None
    assert integrator.handler_chain is not None
    assert integrator.memory_manager is not None


def test_memory_compression_integration():
    integrator = DialogIntegrator(MagicMock())
    messages = [
        {"role": "user", "content": "A" * 100},
        {"role": "assistant", "content": "Bb" * 100},
        {"role": "user", "content": "C" * 100},
    ]
    active, archived = integrator.compress_memory(messages)
    assert len(active) + len(archived) == 3


def test_structured_dialog_processing():
    mock_llm = MagicMock()
    mock_llm.chat.return_value = {"content": '{"dialog": [{"type": "DIALOG", "text": "Hello"}]}'}
    integrator = DialogIntegrator(mock_llm)
    result = integrator.process_with_structured_dialog(
        messages=[{"role": "user", "content": "Hi"}]
    )
    assert result["display_message"] == "Hello"


def test_fallback_to_normal_response():
    mock_llm = MagicMock()
    mock_llm.chat.return_value = {"content": "Plain text response"}
    integrator = DialogIntegrator(mock_llm)
    result = integrator.process_with_structured_dialog(
        messages=[{"role": "user", "content": "Hi"}]
    )
    assert result["display_message"] == "Plain text response"

import pytest
from extensions.dialog.tokens import DialogToken, TokenType
from extensions.dialog.handlers import HandlerChain


def test_handler_chain_process_dialog():
    chain = HandlerChain()
    tokens = [
        DialogToken(type=TokenType.DIALOG, text="Hello!")
    ]
    result = chain.process(tokens)
    assert result["display_message"] == "Hello!"


def test_handler_chain_process_multiple():
    chain = HandlerChain()
    tokens = [
        DialogToken(type=TokenType.COT, text="(thinking)"),
        DialogToken(type=TokenType.DIALOG, text="Hi!"),
        DialogToken(type=TokenType.CHOICE, text="", options=["A","B"])
    ]
    result = chain.process(tokens)
    assert result["display_message"] == "Hi!"
    assert result["choices"] == ["A", "B"]
    assert result["cot_text"] == "(thinking)"


def test_handler_chain_stat_changes():
    chain = HandlerChain()
    tokens = [
        DialogToken(type=TokenType.STAT, text="", stat_changes={"trust": 0.1})
    ]
    result = chain.process(tokens)
    assert result["stat_changes"]["trust"] == 0.1

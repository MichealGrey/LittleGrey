import pytest
from extensions.dialog.tokens import DialogToken, TokenType


def test_dialog_token_creation():
    token = DialogToken(type=TokenType.DIALOG, text="Hello!", character="LittleGrey")
    assert token.type == TokenType.DIALOG
    assert token.text == "Hello!"
    assert token.character == "LittleGrey"


def test_token_type_enum():
    assert TokenType.COT.value == "COT"
    assert TokenType.NARR.value == "NARR"
    assert TokenType.DIALOG.value == "DIALOG"
    assert TokenType.CHOICE.value == "CHOICE"
    assert TokenType.STAT.value == "STAT"


def test_choice_token_with_options():
    token = DialogToken(
        type=TokenType.CHOICE,
        text="",
        options=["Option A", "Option B", "Option C"]
    )
    assert len(token.options) == 3


def test_stat_token_with_changes():
    token = DialogToken(
        type=TokenType.STAT,
        text="",
        stat_changes={"trust": 0.1, "intimacy": 0.05}
    )
    assert token.stat_changes["trust"] == 0.1

from extensions.dialog.parser import DialogParser


def test_parse_valid_json():
    json_str = '{"dialog": [{"type": "DIALOG", "text": "Hello!"}]}'
    result = DialogParser.parse(json_str)
    assert len(result) == 1
    assert result[0].type.value == "DIALOG"
    assert result[0].text == "Hello!"


def test_parse_multiple_tokens():
    json_str = '{"dialog": [{"type": "COT", "text": "(thinking...)"}, {"type": "DIALOG", "text": "Hi!"}]}'
    result = DialogParser.parse(json_str)
    assert len(result) == 2
    assert result[0].type.value == "COT"
    assert result[1].type.value == "DIALOG"


def test_parse_choice_token():
    json_str = '{"dialog": [{"type": "CHOICE", "options": ["A", "B"]}]}'
    result = DialogParser.parse(json_str)
    assert result[0].type.value == "CHOICE"
    assert result[0].options == ["A", "B"]


def test_parse_stat_token():
    json_str = '{"dialog": [{"type": "STAT", "stat_changes": {"trust": 0.1}}]}'
    result = DialogParser.parse(json_str)
    assert result[0].type.value == "STAT"
    assert result[0].stat_changes["trust"] == 0.1


def test_parse_invalid_json_returns_empty():
    result = DialogParser.parse("not json")
    assert result == []


def test_parse_missing_dialog_key():
    json_str = '{"other": "data"}'
    result = DialogParser.parse(json_str)
    assert result == []

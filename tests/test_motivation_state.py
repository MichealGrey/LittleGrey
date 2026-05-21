import pytest
from src.agent.motivation_state import MotivationState


class TestMotivationState:
    def test_default_state(self):
        state = MotivationState()
        assert state.current_need == ""
        assert state.current_desire == ""
        assert state.current_energy == ""
        assert not state.wants_interaction
        assert not state.wants_solitude
        assert not state.feels_purposeless

    def test_has_drive_empty(self):
        state = MotivationState()
        assert not state.has_drive()

    def test_has_drive_with_need(self):
        state = MotivationState(current_need="想被理解")
        assert state.has_drive()

    def test_has_drive_with_desire(self):
        state = MotivationState(current_desire="想聊天")
        assert state.has_drive()

    def test_to_prompt_snippet_empty(self):
        state = MotivationState()
        assert state.to_prompt_snippet() == ""

    def test_to_prompt_snippet_full(self):
        state = MotivationState(
            current_need="被尊重",
            current_desire="安静待会",
            current_energy="疲惫",
        )
        snippet = state.to_prompt_snippet()
        assert "被尊重" in snippet
        assert "安静待会" in snippet
        assert "疲惫" in snippet

    def test_from_dict(self):
        data = {
            "my_need": "想被关心",
            "my_desire": "说说话",
            "my_energy": "充沛",
            "wants_interaction": True,
            "wants_solitude": False,
            "feels_purposeless": False,
        }
        state = MotivationState.from_dict(data)
        assert state.current_need == "想被关心"
        assert state.current_desire == "说说话"
        assert state.current_energy == "充沛"
        assert state.wants_interaction
        assert not state.wants_solitude

    def test_from_dict_missing_fields(self):
        data = {"my_need": "需要安全感"}
        state = MotivationState.from_dict(data)
        assert state.current_need == "需要安全感"
        assert state.current_desire == ""
        assert not state.wants_interaction

    def test_need_truncated(self):
        long_need = "这是一个非常非常非常非常非常非常非常非常长的需求描述"
        state = MotivationState.from_dict({"my_need": long_need})
        assert len(state.current_need) <= 30

    def test_desire_truncated(self):
        long_desire = "这是一个非常非常非常非常非常非常非常非常长的欲望描述"
        state = MotivationState.from_dict({"my_desire": long_desire})
        assert len(state.current_desire) <= 30

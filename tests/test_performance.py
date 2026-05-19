import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.performance.enums import ExpressionType, AnimationType, TransitionType
from src.performance.marks import ExpressionMark, AnimationMark, SceneMark, TTSMARK, EffectMark
from src.performance.parser import PerformanceParser
from src.performance.executor import PerformanceExecutor


class TestPerformanceEnums:
    def test_expression_types(self):
        assert ExpressionType.HAPPY.value == 'happy'
        assert ExpressionType.SAD.value == 'sad'
        assert ExpressionType.ANGRY.value == 'angry'

    def test_animation_types(self):
        assert AnimationType.SHAKE.value == 'shake'
        assert AnimationType.BOUNCE.value == 'bounce'

    def test_transition_types(self):
        assert TransitionType.FADE.value == 'fade'
        assert TransitionType.INSTANT.value == 'instant'


class TestPerformanceMarks:
    def test_expression_mark(self):
        mark = ExpressionMark(expression=ExpressionType.HAPPY, intensity=0.8)
        assert mark.mark_type == 'expression'
        assert mark.parameters['expression'] == 'happy'
        assert mark.parameters['intensity'] == 0.8

    def test_animation_mark(self):
        mark = AnimationMark(animation=AnimationType.SHAKE, target='character', repeat=3)
        assert mark.mark_type == 'animation'
        assert mark.parameters['animation'] == 'shake'
        assert mark.parameters['repeat'] == 3

    def test_scene_mark(self):
        mark = SceneMark(background='room', character='alice', transition=TransitionType.FADE)
        assert mark.mark_type == 'scene'
        assert mark.parameters['background'] == 'room'
        assert mark.parameters['transition'] == 'fade'

    def test_tts_mark(self):
        mark = TTSMARK(voice_id='female', speed=1.2, text='Hello')
        assert mark.mark_type == 'tts'
        assert mark.parameters['text'] == 'Hello'

    def test_effect_mark(self):
        mark = EffectMark(effect_name='sparkle', effect_params={'color': 'gold'})
        assert mark.mark_type == 'effect'
        assert mark.parameters['effect_name'] == 'sparkle'


class TestPerformanceParser:
    def setup_method(self):
        self.parser = PerformanceParser()

    def test_parse_expression(self):
        text = '[expression:HAPPY intensity:0.8]Hello!'
        marks = self.parser.parse_text(text)
        assert len(marks) == 1
        assert marks[0].mark_type == 'expression'
        assert marks[0].parameters['expression'] == 'happy'

    def test_parse_animation(self):
        text = '[animation:SHAKE target:character repeat:2]Shaking!'
        marks = self.parser.parse_text(text)
        assert len(marks) == 1
        assert marks[0].mark_type == 'animation'
        assert marks[0].parameters['repeat'] == 2

    def test_parse_scene(self):
        text = '[scene bg:room char:alice transition:FADE]Scene change'
        marks = self.parser.parse_text(text)
        assert len(marks) == 1
        assert marks[0].mark_type == 'scene'
        assert marks[0].parameters['background'] == 'room'

    def test_parse_tts(self):
        text = '[tts voice:female speed:1.2]Speak this[/tts]'
        marks = self.parser.parse_text(text)
        assert len(marks) == 1
        assert marks[0].mark_type == 'tts'
        assert marks[0].parameters['text'] == 'Speak this'

    def test_parse_multiple_marks(self):
        text = '[expression:HAPPY][animation:NOD]Hello[scene bg:park]'
        marks = self.parser.parse_text(text)
        assert len(marks) == 3

    def test_clean_text(self):
        text = '[expression:HAPPY]Hello[animation:SHAKE]World'
        cleaned = self.parser.clean_text(text)
        assert cleaned == 'HelloWorld'

    def test_parse_unknown_expression(self):
        text = '[expression:UNKNOWN]Test'
        marks = self.parser.parse_text(text)
        assert len(marks) == 0


class TestPerformanceExecutor:
    def setup_method(self):
        self.executor = PerformanceExecutor()

    def test_execute_expression(self):
        mark = ExpressionMark(expression=ExpressionType.HAPPY, intensity=0.8)
        results = self.executor.execute([mark])
        assert len(results) == 1
        assert results[0]['action'] == 'set_expression'
        assert results[0]['expression'] == 'happy'

    def test_execute_animation(self):
        mark = AnimationMark(animation=AnimationType.SHAKE, repeat=2)
        results = self.executor.execute([mark])
        assert len(results) == 1
        assert results[0]['action'] == 'play_animation'
        assert results[0]['animation'] == 'shake'

    def test_execute_scene(self):
        mark = SceneMark(background='room', character='alice', transition=TransitionType.FADE)
        results = self.executor.execute([mark])
        assert len(results) == 1
        assert results[0]['action'] == 'update_scene'
        assert results[0]['background'] == 'room'

    def test_execute_tts(self):
        mark = TTSMARK(voice_id='female', text='Hello')
        results = self.executor.execute([mark])
        assert len(results) == 1
        assert results[0]['action'] == 'speak'
        assert results[0]['text'] == 'Hello'

    def test_state_tracking(self):
        mark1 = ExpressionMark(expression=ExpressionType.HAPPY)
        mark2 = SceneMark(background='park')
        self.executor.execute([mark1, mark2])
        state = self.executor.get_state()
        assert state['current_expression'] == 'happy'
        assert state['current_background'] == 'park'

    def test_reset_state(self):
        mark = ExpressionMark(expression=ExpressionType.ANGRY)
        self.executor.execute([mark])
        self.executor.reset_state()
        state = self.executor.get_state()
        assert state['current_expression'] == 'neutral'
        assert state['current_background'] is None

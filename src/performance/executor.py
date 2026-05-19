import logging
from typing import List, Callable, Dict, Any
from .marks import PerformanceMark, ExpressionMark, AnimationMark, SceneMark, TTSMARK, EffectMark

logger = logging.getLogger(__name__)


class PerformanceExecutor:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {
            'expression': self._handle_expression,
            'animation': self._handle_animation,
            'scene': self._handle_scene,
            'tts': self._handle_tts,
            'effect': self._handle_effect,
        }
        self._state: Dict[str, Any] = {
            'current_expression': 'neutral',
            'current_background': None,
            'current_character': None,
            'current_position': None,
            'is_animating': False,
        }

    def execute(self, marks: List[PerformanceMark]) -> List[Dict[str, Any]]:
        results = []
        for mark in marks:
            handler = self._handlers.get(mark.mark_type)
            if handler:
                try:
                    result = handler(mark)
                    results.append(result)
                except Exception as e:
                    logger.error(f'Failed to execute mark {mark.mark_type}: {e}')
            else:
                logger.warning(f'No handler for mark type: {mark.mark_type}')
        return results

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def reset_state(self):
        self._state = {
            'current_expression': 'neutral',
            'current_background': None,
            'current_character': None,
            'current_position': None,
            'is_animating': False,
        }

    def _handle_expression(self, mark: ExpressionMark) -> Dict[str, Any]:
        self._state['current_expression'] = mark.expression.value
        return {
            'type': 'expression',
            'action': 'set_expression',
            'expression': mark.expression.value,
            'intensity': mark.intensity,
            'duration': mark.duration,
        }

    def _handle_animation(self, mark: AnimationMark) -> Dict[str, Any]:
        self._state['is_animating'] = True
        return {
            'type': 'animation',
            'action': 'play_animation',
            'animation': mark.animation.value,
            'target': mark.target,
            'repeat': mark.repeat,
            'duration': mark.duration,
        }

    def _handle_scene(self, mark: SceneMark) -> Dict[str, Any]:
        if mark.background:
            self._state['current_background'] = mark.background
        if mark.character:
            self._state['current_character'] = mark.character
        if mark.position:
            self._state['current_position'] = mark.position
        return {
            'type': 'scene',
            'action': 'update_scene',
            'background': mark.background,
            'character': mark.character,
            'position': mark.position,
            'transition': mark.transition.value,
        }

    def _handle_tts(self, mark: TTSMARK) -> Dict[str, Any]:
        return {
            'type': 'tts',
            'action': 'speak',
            'voice_id': mark.voice_id,
            'speed': mark.speed,
            'pitch': mark.pitch,
            'volume': mark.volume,
            'text': mark.text,
        }

    def _handle_effect(self, mark: EffectMark) -> Dict[str, Any]:
        return {
            'type': 'effect',
            'action': 'play_effect',
            'effect_name': mark.effect_name,
            'params': mark.effect_params,
        }

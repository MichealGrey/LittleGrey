from dataclasses import dataclass, field
from typing import Optional
from .enums import ExpressionType, AnimationType, TransitionType


@dataclass
class PerformanceMark:
    mark_type: str = field(init=False, default='')
    timestamp: float = 0.0
    duration: float = 0.0
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'type': self.mark_type,
            'timestamp': self.timestamp,
            'duration': self.duration,
            'parameters': self.parameters,
        }


@dataclass
class ExpressionMark(PerformanceMark):
    expression: ExpressionType = ExpressionType.NEUTRAL
    intensity: float = 1.0

    def __post_init__(self):
        self.mark_type = 'expression'
        self.parameters = {
            'expression': self.expression.value,
            'intensity': self.intensity,
        }


@dataclass
class AnimationMark(PerformanceMark):
    animation: AnimationType = AnimationType.NONE
    target: str = 'character'
    repeat: int = 1

    def __post_init__(self):
        self.mark_type = 'animation'
        self.parameters = {
            'animation': self.animation.value,
            'target': self.target,
            'repeat': self.repeat,
        }


@dataclass
class SceneMark(PerformanceMark):
    background: Optional[str] = None
    character: Optional[str] = None
    position: Optional[str] = None
    transition: TransitionType = TransitionType.INSTANT

    def __post_init__(self):
        self.mark_type = 'scene'
        self.parameters = {
            'background': self.background,
            'character': self.character,
            'position': self.position,
            'transition': self.transition.value,
        }


@dataclass
class TTSMARK(PerformanceMark):
    voice_id: str = 'default'
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    text: str = ''

    def __post_init__(self):
        self.mark_type = 'tts'
        self.parameters = {
            'voice_id': self.voice_id,
            'speed': self.speed,
            'pitch': self.pitch,
            'volume': self.volume,
            'text': self.text,
        }


@dataclass
class EffectMark(PerformanceMark):
    effect_name: str = ''
    effect_params: dict = field(default_factory=dict)

    def __post_init__(self):
        self.mark_type = 'effect'
        self.parameters = {
            'effect_name': self.effect_name,
            **self.effect_params,
        }

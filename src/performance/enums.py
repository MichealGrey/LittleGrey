from enum import Enum


class ExpressionType(Enum):
    NEUTRAL = 'neutral'
    HAPPY = 'happy'
    SAD = 'sad'
    ANGRY = 'angry'
    SURPRISED = 'surprised'
    WORRIED = 'worried'
    EMBARRASSED = 'embarrassed'
    PROUD = 'proud'
    CONFUSED = 'confused'
    SCARED = 'scared'
    DISGUSTED = 'disgusted'
    TIRED = 'tired'
    EXCITED = 'excited'
    CALM = 'calm'
    LOVE = 'love'


class AnimationType(Enum):
    NONE = 'none'
    SHAKE = 'shake'
    BOUNCE = 'bounce'
    FADE_IN = 'fade_in'
    FADE_OUT = 'fade_out'
    SLIDE_LEFT = 'slide_left'
    SLIDE_RIGHT = 'slide_right'
    SLIDE_UP = 'slide_up'
    SLIDE_DOWN = 'slide_down'
    ZOOM_IN = 'zoom_in'
    ZOOM_OUT = 'zoom_out'
    PULSE = 'pulse'
    BLINK = 'blink'
    NOD = 'nod'
    HEAD_TILT = 'head_tilt'


class TransitionType(Enum):
    INSTANT = 'instant'
    FADE = 'fade'
    DISSOLVE = 'dissolve'
    WIPE_LEFT = 'wipe_left'
    WIPE_RIGHT = 'wipe_right'
    WIPE_UP = 'wipe_up'
    WIPE_DOWN = 'wipe_down'
    CROSSFADE = 'crossfade'
    SLIDE = 'slide'
    PUSH = 'push'

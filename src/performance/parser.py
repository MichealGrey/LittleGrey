import re
import logging
from typing import List, Optional
from .enums import ExpressionType, AnimationType, TransitionType
from .marks import PerformanceMark, ExpressionMark, AnimationMark, SceneMark, TTSMARK, EffectMark

logger = logging.getLogger(__name__)


class PerformanceParser:
    def parse_text(self, text: str) -> List[PerformanceMark]:
        marks = []
        expression_marks = self._parse_expressions(text)
        animation_marks = self._parse_animations(text)
        scene_marks = self._parse_scenes(text)
        tts_marks = self._parse_tts(text)
        effect_marks = self._parse_effects(text)
        marks.extend(expression_marks)
        marks.extend(animation_marks)
        marks.extend(scene_marks)
        marks.extend(tts_marks)
        marks.extend(effect_marks)
        marks.sort(key=lambda m: m.timestamp)
        return marks

    def _parse_expressions(self, text: str) -> List[ExpressionMark]:
        marks = []
        pattern = r'\[expression:(\w+)(?:\s+intensity:(\d+(?:\.\d+)?))?\]'
        for match in re.finditer(pattern, text):
            expr_name = match.group(1).upper()
            intensity = float(match.group(2)) if match.group(2) else 1.0
            try:
                expression = ExpressionType[expr_name]
                marks.append(ExpressionMark(expression=expression, intensity=intensity))
            except KeyError:
                logger.warning(f'Unknown expression: {expr_name}')
        return marks

    def _parse_animations(self, text: str) -> List[AnimationMark]:
        marks = []
        pattern = r'\[animation:(\w+)(?:\s+target:(\w+))?(?:\s+repeat:(\d+))?\]'
        for match in re.finditer(pattern, text):
            anim_name = match.group(1).upper()
            target = match.group(2) or 'character'
            repeat = int(match.group(3)) if match.group(3) else 1
            try:
                animation = AnimationType[anim_name]
                marks.append(AnimationMark(animation=animation, target=target, repeat=repeat))
            except KeyError:
                logger.warning(f'Unknown animation: {anim_name}')
        return marks

    def _parse_scenes(self, text: str) -> List[SceneMark]:
        marks = []
        pattern = r'\[scene(?:\s+bg:(\S+))?(?:\s+char:(\S+))?(?:\s+pos:(\S+))?(?:\s+transition:(\w+))?\]'
        for match in re.finditer(pattern, text):
            bg = match.group(1)
            char = match.group(2)
            pos = match.group(3)
            trans_name = (match.group(4) or 'instant').upper()
            try:
                transition = TransitionType[trans_name]
                marks.append(SceneMark(background=bg, character=char, position=pos, transition=transition))
            except KeyError:
                logger.warning(f'Unknown transition: {trans_name}')
        return marks

    def _parse_tts(self, text: str) -> List[TTSMARK]:
        marks = []
        pattern = r'\[tts(?:\s+voice:(\w+))?(?:\s+speed:(\d+(?:\.\d+)?))?(?:\s+pitch:(\d+(?:\.\d+)?))?(?:\s+volume:(\d+(?:\.\d+)?))?\](.*?)\[/tts\]'
        for match in re.finditer(pattern, text, re.DOTALL):
            voice = match.group(1) or 'default'
            speed = float(match.group(2)) if match.group(2) else 1.0
            pitch = float(match.group(3)) if match.group(3) else 1.0
            volume = float(match.group(4)) if match.group(4) else 1.0
            tts_text = match.group(5).strip()
            marks.append(TTSMARK(voice_id=voice, speed=speed, pitch=pitch, volume=volume, text=tts_text))
        return marks

    def _parse_effects(self, text: str) -> List[EffectMark]:
        marks = []
        pattern = r'\[effect:(\w+)(?:\s+(\{.*?\}))?\]'
        for match in re.finditer(pattern, text):
            effect_name = match.group(1)
            params_str = match.group(2)
            params = {}
            if params_str:
                try:
                    import json
                    params = json.loads(params_str)
                except json.JSONDecodeError:
                    logger.warning(f'Invalid effect params: {params_str}')
            marks.append(EffectMark(effect_name=effect_name, effect_params=params))
        return marks

    def clean_text(self, text: str) -> str:
        cleaned = re.sub(r'\[expression:\w+(?:\s+intensity:\d+(?:\.\d+)?)?\]', '', text)
        cleaned = re.sub(r'\[animation:\w+(?:\s+target:\w+)?(?:\s+repeat:\d+)?\]', '', cleaned)
        cleaned = re.sub(r'\[scene(?:\s+bg:\S+)?(?:\s+char:\S+)?(?:\s+pos:\S+)?(?:\s+transition:\w+)?\]', '', cleaned)
        cleaned = re.sub(r'\[tts(?:\s+voice:\w+)?(?:\s+speed:\d+(?:\.\d+)?)?(?:\s+pitch:\d+(?:\.\d+)?)?(?:\s+volume:\d+(?:\.\d+)?)?\](.*?)\[/tts\]', r'\1', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\[effect:\w+(?:\s+\{.*?\})?\]', '', cleaned)
        return cleaned.strip()

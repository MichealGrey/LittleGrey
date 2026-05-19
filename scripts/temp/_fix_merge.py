import pathlib
p = pathlib.Path("src/agent/emotion.py")
c = p.read_text(encoding="utf-8")
old = '    def _merge_with_loaded_emotion(self, result: EmotionResult) -> None:\n        if not self._loaded_emotion_levels:\n            return\n        projection = result.core_projection()\n        for emo, loaded_val in self._loaded_emotion_levels.items():\n            if emo in projection:\n                current = projection[emo]\n                projection[emo] = max(current, loaded_val * 0.7)\n        result._core_projection = projection'

new = '    def _merge_with_loaded_emotion(self, result: EmotionResult) -> None:\n        if not self._loaded_emotion_levels:\n            return\n        projection = result.core_projection()\n        for emo, loaded_val in self._loaded_emotion_levels.items():\n            decayed_loaded = loaded_val * 0.7\n            if emo in projection:\n                projection[emo] = max(projection[emo], decayed_loaded)\n            else:\n                projection[emo] = decayed_loaded\n        result._core_projection = projection'

c = c.replace(old, new)
p.write_text(c, encoding='utf-8')
print('Fixed _merge_with_loaded_emotion')

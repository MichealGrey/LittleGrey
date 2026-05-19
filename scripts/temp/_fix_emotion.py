import pathlib
p = pathlib.Path("src/agent/emotion.py")
c = p.read_text(encoding="utf-8")
lines = c.splitlines()
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if '    def understand(self, text: str) -> EmotionResult:' in line:
        # Found understand method, replace it
        new_lines.append('    def understand(self, text: str) -> EmotionResult:')
        new_lines.append('        self._last_interaction_time = time.monotonic()')
        new_lines.append('')
        new_lines.append('        cached = self._emotion_cache.get(text)')
        new_lines.append('        if cached is not None:')
        new_lines.append('            self._last_result = cached')
        new_lines.append('            return cached')
        new_lines.append('')
        new_lines.append('        if self._loaded_emotion_levels is not None:')
        new_lines.append('            self._decay()')
        new_lines.append('            result = self._llm_understand(text)')
        new_lines.append('            self._merge_with_loaded_emotion(result)')
        new_lines.append('            self._loaded_emotion_levels = None')
        new_lines.append('        else:')
        new_lines.append('            self._decay()')
        new_lines.append('            result = self._llm_understand(text)')
        new_lines.append('')
        new_lines.append('        self._emotion_cache.put(text, result)')
        new_lines.append('        self._merge_to_core(result)')
        new_lines.append('        self._last_result = result')
        new_lines.append('        return result')
        # Skip old lines until we find the next method
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('def '):
            i += 1
    elif '                self._loaded_emotion_levels[emo] = val' in line:
        # Skip this line if it already exists
        i += 1
    else:
        new_lines.append(line)
        i += 1

# Add merge method before _llm_understand
final_lines = []
for line in new_lines:
    if '    def _llm_understand' in line:
        # Add merge method before _llm_understand
        final_lines.append('    def _merge_with_loaded_emotion(self, result: EmotionResult) -> None:')
        final_lines.append('        if not self._loaded_emotion_levels:')
        final_lines.append('            return')
        final_lines.append('        projection = result.core_projection()')
        final_lines.append('        for emo, loaded_val in self._loaded_emotion_levels.items():')
        final_lines.append('            if emo in projection:')
        final_lines.append('                current = projection[emo]')
        final_lines.append('                projection[emo] = max(current, loaded_val * 0.7)')
        final_lines.append('        result._core_projection = projection')
        final_lines.append('')
    final_lines.append(line)

p .write_text('\n'.join(final_lines), encoding='utf-8')
print('Modified successfully')

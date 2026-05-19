import pathlib
p = pathlib.Path("src/agent/emotion.py")
c = p.read_text(encoding="utf-8")
lines = c.splitlines()
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if '            saved_levels = data.get("levels")' in line:
        new_lines.append('            saved_levels = data.get("levels")')
        new_lines.append('            if saved_levels:')
        new_lines.append('                self._loaded_emotion_levels = {}')
        new_lines.append('                for emo, val in saved_levels.items():')
        new_lines.append('                    if emo in self._levels:')
        new_lines.append('                        val = max(0.0, min(1.0, float(val)))')
        new_lines.append('                        self._levels[emo] = val')
        new_lines.append('                        self._loaded_emotion_levels[emo] = val')
        i += 6
    else:
        new_lines.append(line)
        i += 1
p.write_text('\n'.join(new_lines), encoding='utf-8')
print('Modified successfully')

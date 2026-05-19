import pathlib
p = pathlib.Path("src/agent/emotion.py")
c = p.read_text(encoding="utf-8")
lines = c.splitlines()
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if '            if saved_baseline:' in line:
        new_lines.append('            saved_baseline = data.get("baseline")')
        new_lines.append('            if saved_baseline:')
        new_lines.append('                for emo, val in saved_baseline.items():')
        new_lines.append('                    if emo in self._baseline:')
        new_lines.append('                        self._baseline[emo] = max(0.0, min(0.15, float(val)))')
        i += 5
    else:
        new_lines.append(line)
        i += 1
p.write_text('\n'.join(new_lines), encoding='utf-8')
print('Modified successfully')

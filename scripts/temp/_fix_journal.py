import pathlib
p = pathlib.Path("src/agent/emotion.py")
c = p.read_text(encoding="utf-8")
lines = c.splitlines()
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if '            for entry in recent_journal:' in line:
        new_lines.append('            recent_journal = data.get("recent_journal", [])')
        new_lines.append(line)
    else:
        new_lines.append(line)
    i += 1
p.write_text('\n'.join(new_lines), encoding='utf-8')
print('Fixed recent_journal definition')

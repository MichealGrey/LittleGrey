import pathlib
p = pathlib.Path("src/agent/emotion.py")
c = p.read_text(encoding="utf-8")
lines = c.splitlines()
print(f'Total lines: {len(lines)}')
for i, line in enumerate(lines):
    if '_loaded = None' in line or '_loaded_emotion_levels' in line:
        print(f'Line {i+1}: {line}')
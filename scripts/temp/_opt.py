import pathlib, re
print('Starting Token optimization...')
print('[A] Compressing System Prompt...')
p1 = pathlib.Path('src/agent/llm.py')
c1 = p1.read_text(encoding='utf-8')
# Find and replace style_guide
start = c1.find('style_guide = (')
depth = 0
for i in range(start, len(c1)):
    if c1[i] == '(': depth += 1
    elif c1[i] == ')':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
old = c1[start:end]

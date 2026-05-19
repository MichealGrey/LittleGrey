import pathlib
p = pathlib.Path('e:/Proj/AgentProj/src/agent/emotion.py')
c = p.read_text('utf-8')
# Fix 1  f-string inside double quotes + Fix 2  $-> {}
c = c.replace('parts.append(f"{emo}(stats["avg_intensity"]:.1f}")', 'parts.append(f"{emo}(stats['avg_intensity']:.1f}")')
c = c.replace('return f"${dominant},${trend}: "+ ", ".join(parts)', 'return f"{dominant},{trend}: "+ ", ".join(parts)')
p.write_text(c, 'utf-8')
print('fixed')

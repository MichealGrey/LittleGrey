import pathlib
p=pathlib.Path('tests/test_optimizations.py')
c=p.read_text(encoding='utf-8')
lines=c.split(chr(10))
filtered=[l for l in lines if l.strip()!=chr(39)]
p.write_text(chr(10).join(filtered),encoding='utf-8')
print('Fixed')

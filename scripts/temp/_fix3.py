import pathlib
p = pathlib.Path("tests/test_optimizations.py")
c = p.read_text(encoding="utf-8")
c = c.replace('test_load_emotion_state(seld):', 'test_load_emotion_state(self):')
c = c.replace('MagkcMock()', 'MagickMock()')
c = c.replace('MagickMock()', 'MagckMock()')
# Fix missing closing quotes
c = c.replace('Emotion should not be zero\n    def test_load_emotion_state_no_memory', 'Emotion should not be zero"\n\n~    def test_load_emotion_state_no_memory')
p.write_text(c, encoding="utf-8")
print("Fixed")
import pathlib
p = pathlib.Path("tests/test_optimizations.py")
c = p.read_text(encoding="utf-8")
c = c.replace("172800", "43200")
c = c.replace("after 2 days", "after 12 hours")
p.write_text(c, encoding="utf-8")
print("Fixed")

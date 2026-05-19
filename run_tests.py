import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_optimizations.py", "-v", "--tb=short"],
    capture_output=True,
    text=True,
    cwd="e:\\Proj\\AIProj\\LittleGrey"
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)

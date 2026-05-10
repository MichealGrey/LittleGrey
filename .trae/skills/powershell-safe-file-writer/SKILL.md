---
name: powershell-safe-file-writer
description: Safely write large files with CJK content on Windows PowerShell. Invoke when writing files with Chinese content or PSReadLine buffer overflow occurs.
---

# PowerShell Safe File Writer

## Problem

On Windows, PowerShell PSReadLine has a limited console buffer. When using python -c with long Chinese/CJK content, PSReadLine crashes with System.ArgumentOutOfRangeException. This makes it impossible to write large files with Chinese content directly through shell commands.

## Solution: Chunked Base64 Encoding

Split file content into chunks, base64-encode each chunk, write encoded chunks to temp files, then assemble and decode into the final file.

## Workflow

### Step 1: Build content using unicode escapes

Use chr(10).join([...]) with unicode escape sequences (backslash-u-XXXX) to build text content. This avoids shell encoding issues.

Key tricks:
- Use chr(10) for newlines (avoids escaping issues)
- Use chr(96)*3 for triple backticks (avoids shell interpretation)
- Use backslash-u-XXXX for all CJK characters
- Avoid raw backticks, quotes, and special chars in the Python string literal

### Step 2: Base64-encode and save each chunk

After building the content string, base64-encode and write to a temp file. Keep each chunk under ~2500 base64 characters. Split into multiple chunks if needed.

### Step 3: Assemble all chunks into the final file

After all chunks are written, decode and concatenate them:

```python
import pathlib, base64
chunks = ["docs/chunk1_b64.txt", "docs/chunk2_b64.txt"]
full_doc = ""
for f in chunks:
    b64 = pathlib.Path(f).read_text("ascii")
    full_doc += base64.b64decode(b64).decode("utf-8")
pathlib.Path("docs/final-file.md").write_text(full_doc, encoding="utf-8")
```

### Step 4: Post-processing fixes

Apply fixes for missing blank lines, backtick formatting, etc using pathlib read_text/write_text.

### Step 5: Clean up temp files

Delete all chunk*b64.txt temp files after assembly.

## Tips

1. Keep each RunCommand under ~2500 chars of base64
2. Use pathlib.Path.write_text() not open() - handles encoding reliably
3. Avoid PowerShell echo/Set-content - they add BOM
4. Use chr(96) instead of backticks in Python strings
5. For small files under 500 chars of CJK, use direct write

## When to Use

- Writing .md, .txt, .py files with Chinese/CJK content on Windows
- When python -c with Chinese causes PSReadLine crash
- When writing docs, config files, or code comments in Chinese
- When file content exceeds ~500 characters of CJK text

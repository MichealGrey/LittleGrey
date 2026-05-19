---
name: "powershell-safe-file-writer"
description: "Safely write large files with CJK content on Windows PowerShell. Invoke when writing files with Chinese content or PSReadLine buffer overflow occurs."
---

# PowerShell Safe File Writer

## Problem

When writing files on Windows PowerShell with long Chinese content, several issues occur:

1. **PSReadLine buffer overflow** - long commands fail with "system.console.setcursorposition" errors
2. **Unicode errors** - Chinese characters get corrupted in command lines
3. **String literal errors** - multiline strings get truncated or malformed
4. **Base64 length limits** - even base64-encoded content can exceed PowerShell command line limits

## 推荐方案：临时脚本写入法（最简单可靠）

对于需要写入中文/长内容的文件，最佳方案是：

1. 用 Write 工具创建一个临时 Python 脚本（脚本内容包含要写入的文件内容）
2. 运行这个脚本
3. 脚本执行后删除自己

### 示例

**目标**：创建 `docs/my_plan.md`，内容包含大量中文

**步骤 1：创建临时脚本**

```python
# 文件名: _write_file.py

content = '''# 我的计划

这是一个包含大量中文内容的文件...

# 完整内容在这里
'''

with open('docs/my_plan.md', 'w', encoding='utf-8') as f:
    f.write(content)

import os
os.remove(__file__)  # 删除自己
```

**步骤 2：运行脚本**

```shell
python _write_file.py
```

### 优点

- ✅ 完全绕过 PowerShell 命令长度限制
- ✅ 中文内容不经过命令行，不会被转义
- ✅ 只需两步操作，简单可靠
- ✅ 脚本执行后自动删除，不残留

---

## 方案二：Base64 编码法（适用于较短内容）

对于较短的文件内容（base64 后 < 2000 字符）：

### Step 1: Encode Content in Base64

```python
import base64
content = """your chinese content here"""
encoded = base64.b64encode(content.encode('utf-8')).decode().strip()
print(encoded)
```

### Step 2: Use Short Command to Decode and Write

```shell
python -c "import base64; open('path/to/file', 'w', encoding='utf-8').write(base64.b64decode('BASE64_CONTENT').decode('utf-8'))"
```

### Step 3: For Very Large Files, Split into Chunks

```shell
python -c "import base64; open('file.py', 'w', encoding='utf-8').write(base64.b64decode('CHUNK_1').decode('utf-8'))"
python -c "import base64; open('file.py', 'a', encoding='utf-8').write(base64.b64decode('CHUNK_2').decode('utf-8'))"
```

Note: Use `'a'` mode (append) for subsequent chunks.

---

## 方案三：PowerShell Here-String（简单文件）

对于简单的、不需要在代码中包含三引号的文件：

```shell
@"
file content here
"@ | Out-File -FilePath "path/to/file" -Encoding utf8
```

**注意**：如果内容包含 `'''` 或 `"""`，此方法不适用，因为会和 PowerShell here-string 冲突。

---

## 决策流程

```
需要写入中文/长内容？
    │
    ├── 是 → 方案一：临时脚本写入法（推荐）
    │
    └── 否 → 检查内容长度
             │
             ├── base64 < 2000 字符 → 方案二：Base64 编码
             │
             └── 内容简单，不含三引号 → 方案三：Here-String
```

---

## When to Use

- Writing files with Chinese/CJK content
- PowerShell buffer overflow errors
- Unicode errors in command lines
- Multiline string issues in PowerShell
- Content contains triple quotes (`'''` or `"""`)

## 最佳实践

1. **首选临时脚本写入法** - 最可靠，无长度限制
2. 总是指定 `encoding='utf-8'`
3. 写入后验证文件内容（Read 工具）
4. 临时脚本执行后自动删除

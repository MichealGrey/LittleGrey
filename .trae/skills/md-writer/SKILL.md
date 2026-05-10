---
name: "md-writer"
description: "Write long Chinese/Unicode markdown documents to disk reliably. Invoke when user asks to write, save, or export content as .md files, especially long documents with CJK characters."
---

# Markdown Writer

Write long markdown documents (especially with CJK/Unicode content) to disk reliably, avoiding PowerShell PSReadLine buffer crashes and encoding issues.

## When to Use

- User asks to write content to a .md file
- User asks to save/export documentation as markdown
- User asks to create a README or design doc
- Any task that involves writing substantial markdown content to disk

## Core Problem

On Windows PowerShell, writing long content to files has multiple failure modes:

1. **PSReadLine buffer crash**: Commands exceeding ~4000 chars cause `System.ArgumentOutOfRangeException` in PSConsoleReadLine
2. **Python -c encoding error**: Emoji/surrogate pairs passed through PowerShell cause `UnicodeEncodeError: surrogates not allowed`
3. **Here-string escaping**: PowerShell double-quoted here-strings `@"..."@` interpret `$` and backticks, corrupting code content
4. **File encoding BOM**: `Out-File -Encoding utf8` adds BOM by default

## Solution: Segmented Add-Content with Literal Here-Strings

### Method: PowerShell `Add-Content` + `@'...'@`

Use PowerShell `Add-Content` with **single-quoted here-string** `@'...'@` to write content in segments of ~2000-3000 characters each.

**Why single-quoted here-string?**
- `@'...'@` is **literal** - no variable expansion, no escape interpretation
- `@"..."@` would interpret `$var`, backticks, and other PowerShell syntax
- Content inside `@'...'@` is written exactly as-is

### Step-by-Step Workflow

#### Step 1: Prepare

- Ensure target directory exists: `New-Item -ItemType Directory -Force -Path "<dir>" | Out-Null`
- Clear/create the file: `python -c "open(r'<path>','w',encoding='utf-8').close()"`

#### Step 2: Write in Segments

Split the markdown content into logical segments (e.g., by major sections). For each segment:

```powershell
Add-Content -Path "<filepath>" -Value @'
<segment content here>
---
name: "md-writer"
description: "Write long Chinese/Unicode markdown documents to disk reliably. Invoke when user asks to write, save, or export content as .md files, especially long documents with CJK characters."
---

# Markdown Writer

Write long markdown documents (especially with CJK/Unicode content) to disk reliably, avoiding PowerShell PSReadLine buffer crashes and encoding issues.

## When to Use

- User asks to write content to a .md file
- User asks to save/export documentation as markdown
- User asks to create a README or design doc
- Any task that involves writing substantial markdown content to disk

## Core Problem

On Windows PowerShell, writing long content to files has multiple failure modes:

1. PSReadLine buffer crash: Commands exceeding ~4000 chars cause System.ArgumentOutOfRangeException
2. Python -c encoding error: Emoji/surrogate pairs cause UnicodeEncodeError surrogates not allowed
3. Here-string escaping: Double-quoted here-strings interpret $ and backticks
4. File encoding BOM: Out-File adds BOM by default

## Solution: Segmented Add-Content with Literal Here-Strings

Use PowerShell Add-Content with single-quoted here-string to write content in segments of ~2000-3000 characters each.

Why single-quoted here-string:
- Single-quoted is literal - no variable expansion, no escape interpretation
- Double-quoted would interpret $var, backticks, and other PowerShell syntax
- Content inside is written exactly as-is

### Step-by-Step Workflow

Step 1 - Prepare:
- Ensure target directory exists: New-Item -ItemType Directory -Force -Path dir | Out-Null
- Clear/create the file: python -c "open(r'path','w',encoding='utf-8').close()"

Step 2 - Write in Segments:
- Split the markdown content into logical segments (e.g., by major sections)
- Keep each segment under 3000 characters
- Split at natural boundaries (section headers, --- dividers)
- Count segments and track progress with TodoWrite
- Use Add-Content -Path filepath -Value @'...'@ -Encoding utf8 for each segment

Step 3 - Verify:
After all segments are written, verify completeness with Python:
  - Check file size and line count
  - Check that first and last lines are correct
  - Check that all expected section headers exist in the content

## Critical Rules

### DO

- Always use single-quoted here-string for content - never double-quoted
- Split long content into segments of 2000-3000 chars each
- Use -Encoding utf8 on Add-Content
- Track progress with TodoWrite (one todo per segment)
- Verify after writing: file size, line count, section presence
- Avoid emoji in here-strings - replace with text markers like [严重] instead of emoji
- Use Add-Content (append mode) for all segments since file is pre-cleared

### DO NOT

- Never use python -c with long strings containing Unicode - PSReadLine will crash
- Never use double-quoted here-string - it interprets PowerShell syntax
- Never pass emoji through PowerShell command line - surrogate pair encoding errors
- Never try to write 10000+ chars in one command - always segment
- Never use Out-File for content with CJK characters - it may add BOM
- Never assume the file was written correctly without verification

## Emoji Handling

Emoji characters cause UnicodeEncodeError surrogates not allowed when passed through PowerShell to Python. Solutions:

1. Replace emoji with text markers in the source content:
   - Red circle -> [严重]
   - Yellow circle -> [中等]
   - Orange circle -> [轻微]
2. If emoji must be preserved, use a two-step approach:
   - Write content without emoji using this method
   - Then use Python to do find-and-replace

## Encoding Notes

- Add-Content -Encoding utf8 on PowerShell 5.x adds BOM
- Add-Content -Encoding utf8 on PowerShell 7+ does NOT add BOM
- If BOM-free UTF-8 is required, use Python for post-processing:
  Read with utf-8-sig encoding, write with utf-8 encoding

## Example Segmentation

For a document with 6 major sections, split into 5 segments:

- Segment 1: Title + Section 1 (overview)
- Segment 2: Section 2 (goals) + Section 3 preamble + Module 1
- Segment 3: Module 2 + Module 3
- Segment 4: Module 4 + Module 5
- Segment 5: Module 6 + Section 4 (data flow) + Section 5 (principles) + Section 6 (acceptance criteria)

Each segment uses: Add-Content -Path "docs/design.md" -Value @'...'@ -Encoding utf8

After all segments, verify with Python that all expected sections are present.

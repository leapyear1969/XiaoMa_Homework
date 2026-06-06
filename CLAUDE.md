# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"小马的每日学习" (XiaoMa Daily Homework) — a Tkinter GUI app that generates A4 PDF homework sheets for Chinese, Math, and English. Primarily for elementary school daily practice. Single Python file: `homework_app.py` (~1500 lines).

## Run & build

```bash
# Install dependencies (Windows)
pip install reportlab pypinyin

# Run the GUI
python homework_app.py
# or double-click start.bat

# Syntax check (no GUI)
python -c "import py_compile; py_compile.compile('homework_app.py', doraise=True)"

# Build to EXE
pip install pyinstaller
pyinstaller homework_app.spec
```

## Architecture

### Three-layer PDF generation

1. **Custom Flowable components** (reportlab `Flowable` subclasses) — the rendering primitives:
   - `HanziPracticeRow` — 田字格 (rice-grid) character practice with pinyin above, optional stroke tracing via MakeMeAHanzi SVG paths
   - `FourLineWordPractice` — four-line English handwriting guide with colored exemplar + trace copies
   - `EnglishWordPracticeBlock` — wraps `FourLineWordPractice` with per-word color from palette

2. **Section builders** — assemble one subject's content into a reportlab story:
   - `_build_chinese_section(story, characters, *, heading_text, enable_stroke_demo)`
   - `_build_math_section(story, problems, *, available_width, heading_text, columns)`
   - `_build_english_section(story, words, level, *, available_width, heading_text, copies, columns, ...)`

3. **PDF generators** — create `SimpleDocTemplate`, call section builders, build:
   - `generate_chinese_pdf(hanzi_level, output_path, count)` → standalone Chinese PDF
   - `generate_math_pdf(math_max, output_path, count, columns)` → standalone Math PDF
   - `generate_english_pdf(level, output_path, count, columns)` → standalone English PDF
   - `generate_homework(subjects, output_mode, ...)` → **unified dispatcher**: builds merged PDF (all subjects in one story) or calls individual generators for separate PDFs

### UI: basic vs advanced mode

`HomeworkGeneratorApp` has two modes sharing the same settings (level, hanzi_level, math_max):

- **Basic mode** (`_handle_basic_mode`): calls `generate_homework(["chinese","math","english"], "merged", ...)` with default counts (5 chars / 10 math / 5 words).
- **Advanced mode** (`_handle_advanced_mode`): checkbox per subject + radio for merged/separate output. Calls `generate_homework(subjects, output_mode, ...)` with expanded counts (10 chars / 60 math in 3 columns / 10 words).

Count parameters flow: `_handle_*_mode` → `generate_homework(chinese_count, math_count, math_columns, english_count, english_columns)` → individual `generate_*_pdf(count, columns)` → `_select_*` / section builders.

### Data files

| File | Purpose |
|------|---------|
| `yuwen.txt` | ~3500 common Chinese characters, one per line |
| `oxford-3000.csv` | Oxford 3000 word list: `word,class,level` (a1/a2/b1/b2) |
| `hanzi_metadata.csv` | Character metadata for beginner filtering: `char,strokes,freq_rank,polyphonic,radical,semantic` |
| `makemeahanzi/graphics.txt` | ~30MB stroke SVG path data; auto-downloaded from GitHub on first use |

### Chinese character levels

- **普通**: random selection from all of `yuwen.txt`, no stroke tracing
- **初级**: filters via `hanzi_metadata.csv` (strokes ≤ 8, freq ≤ 2000, non-polyphonic, common radical, basic semantic category), enables stroke tracing from MakeMeAHanzi

### Font strategy (Windows-only)

Priority chain for each role:
- Chinese: STSong-Light (CID) → KaiTi/SimKai (system TTF) → STSong-Light fallback
- Pinyin: Arial/Segoe UI/etc (Latin fonts with tone-mark glyphs) → STSong-Light
- English: Comic Sans MS → Helvetica

## Key implementation notes

- All PDF generation requires `ensure_reportlab()` / `ensure_pinyin()` guards that raise `DependencyError` with Chinese messages on missing deps.
- `COLOR_PALETTE_HEX` (11 colors) — each character/word gets a random color via `_random_unique_palette(n)`; trace copies use `_lighten_hex()`.
- Math problems are `{a:>2} {op} {b:>2} = ` format strings, 2-3 columns in a `Table`; TOPPADDING/BOTTOMPADDING controls vertical spacing.
- The `_select_chinese_characters_with_level` function supports the original file's mojibake check (`level_s.startswith("初")`) alongside a normal check (`"初" in level_s`) to stay compatible with any encoding-corrupted data.
- Error handling in UI: all exceptions caught → `messagebox.showerror`; no silent crashes.

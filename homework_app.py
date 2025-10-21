# -*- coding: utf-8 -*-
"""Daily homework generator GUI application.

Generates subject-specific PDF documents for Chinese, Math, and English homework.
"""

from __future__ import annotations

import csv
import math
import random
import sys
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List

import tkinter as tk
from tkinter import messagebox, ttk

ROOT_DIR = Path(__file__).resolve().parent
YUWEN_BANK = ROOT_DIR / "yuwen.txt"
OXP_BANK = ROOT_DIR / "oxford-3000.csv"

WINDOWS_FONT_DIR = Path("C:/Windows/Fonts")
PINYIN_FONT_FILES = (
    WINDOWS_FONT_DIR / "simkai.ttf",
    WINDOWS_FONT_DIR / "KaiTi.ttf",
)
COMIC_SANS_FONT_FILES = (
    WINDOWS_FONT_DIR / "comic.ttf",
    WINDOWS_FONT_DIR / "comicz.ttf",
)
CHINESE_FONT_NAME = "STSong-Light"
PINYIN_FONT_NAME = "STSong-Light"
ENGLISH_FONT_NAME = "Helvetica"

# Color palette for random coloring of characters/words
COLOR_PALETTE_HEX = [
    "#333333",  # Graphite Gray
    "#4A586E",  # Gray Blue
    "#B8A89F",  # Warm Gray
    "#9AA57C",  # Olive Gray
    "#A8B97A",  # Bamboo Leaf
    "#6A7BA2",  # Slate Blue
    "#8BA3C7",  # Indigo Light
    "#B56547",  # Brick
    "#C47F5A",  # Clay
    "#B7A9CF",  # Lavender Gray
    "#D7A9E3",  # Lilac Mist
]

def _hex_to_rgb01(hex_str: str) -> tuple[float, float, float]:
    """Convert #RRGGBB hex to RGB floats in [0,1]."""
    hex_clean = hex_str.strip().lstrip('#')
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0
    return r, g, b

def _lighten_hex(hex_str: str, factor: float = 0.55):
    """Return a reportlab color blended toward white by `factor` [0..1]."""
    factor = max(0.0, min(1.0, factor))
    r, g, b = _hex_to_rgb01(hex_str)
    r_l = r + (1.0 - r) * factor
    g_l = g + (1.0 - g) * factor
    b_l = b + (1.0 - b) * factor
    return colors.Color(r_l, g_l, b_l)

def _random_unique_palette(n: int) -> list[str]:
    """Return at least n hex colors by shuffling the palette (repeat after cycle)."""
    base = COLOR_PALETTE_HEX[:]
    random.shuffle(base)
    if n <= len(base):
        return base[:n]
    # Need more than palette size: repeat shuffled cycles
    out: list[str] = []
    while len(out) < n:
        random.shuffle(base)
        out.extend(base)
    return out[:n]

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Flowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
    REPORTLAB_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover
    colors = None  # type: ignore[assignment]
    A4 = None  # type: ignore[assignment]
    ParagraphStyle = None  # type: ignore[assignment]
    getSampleStyleSheet = None  # type: ignore[assignment]
    cm = None  # type: ignore[assignment]
    pdfmetrics = None  # type: ignore[assignment]
    UnicodeCIDFont = None  # type: ignore[assignment]

    class _FlowableStub:  # pragma: no cover - placeholder when reportlab missing
        pass

    Flowable = _FlowableStub  # type: ignore[assignment]
    PageBreak = None  # type: ignore[assignment]
    Paragraph = None  # type: ignore[assignment]
    SimpleDocTemplate = None  # type: ignore[assignment]
    Spacer = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    TableStyle = None  # type: ignore[assignment]
    REPORTLAB_AVAILABLE = False
    REPORTLAB_IMPORT_ERROR = exc

try:
    from pypinyin import Style, lazy_pinyin

    PYPINYIN_AVAILABLE = True
    PYPINYIN_IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover
    Style = None  # type: ignore[assignment]
    lazy_pinyin = None  # type: ignore[assignment]
    PYPINYIN_AVAILABLE = False
    PYPINYIN_IMPORT_ERROR = exc


class DependencyError(RuntimeError):
    """Raised when a third-party dependency is unavailable."""


if REPORTLAB_AVAILABLE and cm is not None:
    PAGE_SETUP = dict(
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
else:  # pragma: no cover - reportlab unavailable
    PAGE_SETUP = {}


def ensure_reportlab() -> None:
    if REPORTLAB_IMPORT_ERROR:
        raise DependencyError(
            "缺少依赖 reportlab，请先运行 pip install reportlab 再生成文档。"
        ) from REPORTLAB_IMPORT_ERROR


def ensure_pinyin() -> None:
    if PYPINYIN_IMPORT_ERROR:
        raise DependencyError(
            "缺少依赖 pypinyin，请先运行 pip install pypinyin 再生成语文作业。"
        ) from PYPINYIN_IMPORT_ERROR


_FONTS_REGISTERED = False


def _register_tt_font(font_name: str, candidates: Iterable[Path]) -> bool:
    """Register a TrueType font if any candidate file exists."""

    for candidate in candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(candidate)))
            except Exception:
                continue
            return True
    return False


def _register_fonts() -> None:
    ensure_reportlab()
    global _FONTS_REGISTERED, CHINESE_FONT_NAME, PINYIN_FONT_NAME, ENGLISH_FONT_NAME
    if _FONTS_REGISTERED:
        return
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception as exc:  # pragma: no cover - unexpected font error
        raise DependencyError("无法注册中文字体（STSong-Light），请确认 reportlab 已安装。") from exc

    CHINESE_FONT_NAME = "STSong-Light"
    PINYIN_FONT_NAME = "STSong-Light"
    ENGLISH_FONT_NAME = "Helvetica"

    if _register_tt_font("KaiTi", PINYIN_FONT_FILES):
        CHINESE_FONT_NAME = "KaiTi"
        PINYIN_FONT_NAME = "KaiTi"

    if _register_tt_font("ComicSansMS", COMIC_SANS_FONT_FILES):
        ENGLISH_FONT_NAME = "ComicSansMS"

    _FONTS_REGISTERED = True


_STYLES: Dict[str, ParagraphStyle] | None = None


def _get_styles() -> Dict[str, ParagraphStyle]:
    ensure_reportlab()
    _register_fonts()
    global _STYLES
    if _STYLES is None:
        base = getSampleStyleSheet()
        styles: Dict[str, ParagraphStyle] = {}
        styles["title"] = ParagraphStyle(
            name="HomeworkTitle",
            parent=base["Title"],
            fontName=CHINESE_FONT_NAME,
            fontSize=28,
            leading=32,
            alignment=1,
            textColor=colors.HexColor("#333333"),
            spaceAfter=12,
        )
        styles["heading"] = ParagraphStyle(
            name="HomeworkHeading",
            parent=base["Heading2"],
            fontName=CHINESE_FONT_NAME,
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#333333"),
            spaceBefore=6,
            spaceAfter=6,
        )
        styles["info"] = ParagraphStyle(
            name="HomeworkInfo",
            parent=base["Normal"],
            fontName=CHINESE_FONT_NAME,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#555555"),
        )
        styles["body"] = ParagraphStyle(
            name="HomeworkBody",
            parent=base["Normal"],
            fontName=CHINESE_FONT_NAME,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#333333"),
        )
        styles["caption"] = ParagraphStyle(
            name="HomeworkCaption",
            parent=base["Normal"],
            fontName=ENGLISH_FONT_NAME,
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#333333"),
            spaceBefore=0,
            spaceAfter=0,
        )
        _STYLES = styles
    return _STYLES


class HanziPracticeRow(Flowable):
    """Flowable rendering a set of character practice squares with pinyin."""

    def __init__(
        self,
        character: str,
        pinyin_text: str,
        *,
        squares: int = 12,
        cell_size: float | None = None,
        pinyin_height: float | None = None,
    ) -> None:
        ensure_reportlab()
        super().__init__()
        self.character = character
        self.pinyin_text = pinyin_text
        self.squares = max(1, squares)
        self.cell_size = cell_size if cell_size is not None else 1.3 * cm
        self.pinyin_height = pinyin_height if pinyin_height is not None else 0.5 * cm
        self.total_width = self.squares * self.cell_size
        self.total_height = self.cell_size + self.pinyin_height
        self.outer_color = colors.HexColor("#2ead6f")
        self.guide_color = colors.HexColor("#9fdcb8")
        self.pinyin_border_color = colors.HexColor("#2ead6f")
        # These colors may be overridden per-row from the palette
        self.primary_text_color = colors.HexColor("#147a4c")
        self.secondary_text_color = colors.HexColor("#8bcf9d")
        self.pinyin_text_color = colors.HexColor("#147a4c")
        self.font_name = CHINESE_FONT_NAME
        self.pinyin_font_name = PINYIN_FONT_NAME
        self.pinyin_font_size = 14
        self.dash_pattern = (2, 2)

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:  # noqa: D401
        return self.total_width, self.total_height

    def draw(self) -> None:  # noqa: D401
        canvas = self.canv
        canvas.saveState()

        canvas.setStrokeColor(self.pinyin_border_color)
        canvas.setLineWidth(1)
        canvas.setDash(self.dash_pattern, 0)
        canvas.rect(0, self.cell_size, self.total_width, self.pinyin_height)
        canvas.setDash()

        if self.pinyin_text:
            canvas.setFillColor(self.pinyin_text_color)
            self._draw_centered_text(
                canvas,
                self.pinyin_text,
                self.pinyin_font_name,
                self.pinyin_font_size,
                self.total_width / 2,
                self.cell_size + self.pinyin_height / 2,
            )

        for idx in range(self.squares):
            x = idx * self.cell_size
            mid_x = x + self.cell_size / 2
            mid_y = self.cell_size / 2

            canvas.setStrokeColor(self.outer_color)
            canvas.setLineWidth(1)
            canvas.setDash(self.dash_pattern, 0)
            canvas.rect(x, 0, self.cell_size, self.cell_size)
            canvas.setDash()

            canvas.setStrokeColor(self.guide_color)
            canvas.setLineWidth(0.7)
            canvas.setDash(self.dash_pattern, 0)
            canvas.line(x, mid_y, x + self.cell_size, mid_y)
            canvas.line(mid_x, 0, mid_x, self.cell_size)
            canvas.line(x, 0, x + self.cell_size, self.cell_size)
            canvas.line(x + self.cell_size, 0, x, self.cell_size)
            canvas.setDash()

            if self.character:
                color = self.primary_text_color if idx == 0 else self.secondary_text_color
                font_size = 24
                canvas.setFillColor(color)
                self._draw_centered_text(
                    canvas,
                    self.character,
                    self.font_name,
                    font_size,
                    mid_x,
                    mid_y,
                )

        canvas.restoreState()

    @staticmethod
    def _draw_centered_text(
        canvas,
        text: str,
        font_name: str,
        font_size: float,
        center_x: float,
        center_y: float,
    ) -> None:
        canvas.setFont(font_name, font_size)
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        x = center_x - text_width / 2
        y = center_y - font_size * 0.35
        canvas.drawString(x, y, text)


class FourLineWordPractice(Flowable):
    """Flowable rendering four-line handwriting guides for a word."""

    def __init__(
        self,
        word: str,
        *,
        width: float,
        copies: int = 1,
        line_height: float | None = None,
    ) -> None:
        ensure_reportlab()
        super().__init__()
        self.word = word
        self.width = width
        self.copies = max(1, copies)
        self.line_height = line_height if line_height is not None else 0.38 * cm
        self.block_height = self.line_height * 3
        self.gap = self.line_height * 0.5
        self.total_height = self.copies * self.block_height + (self.copies - 1) * self.gap
        self.line_color_primary = colors.HexColor("#4b5563")
        self.line_color_secondary = colors.HexColor("#9ca3af")
        # Primary color for the first word and a lighter trace color for copies
        self.word_color_primary = colors.HexColor("#ec6f8e")
        self.word_color_trace = _lighten_hex("#ec6f8e", 0.65)
        self.word_font = ENGLISH_FONT_NAME
        self.word_font_size = self.line_height * 1.15 + 9

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:  # noqa: D401
        return self.width, self.total_height

    def draw(self) -> None:  # noqa: D401
        canvas = self.canv
        canvas.saveState()

        for copy_idx in range(self.copies):
            y_base = copy_idx * (self.block_height + self.gap)

            for line_idx in range(4):
                y = y_base + line_idx * self.line_height
                if line_idx in (0, 3):
                    canvas.setStrokeColor(self.line_color_primary)
                    canvas.setLineWidth(1.1)
                else:
                    canvas.setStrokeColor(self.line_color_secondary)
                    canvas.setLineWidth(0.8)
                canvas.setDash()
                canvas.line(0, y, self.width, y)

            # Draw the word once in strong color and 4 additional trace copies
            # evenly distributed across the width (only on the first copy row).
            if copy_idx == 0 and self.word:
                canvas.setFont(self.word_font, self.word_font_size)
                baseline = y_base + self.line_height

                total = 5  # 1 primary + 4 trace copies
                segment = self.width / total
                for i in range(total):
                    color = self.word_color_primary if i == 0 else self.word_color_trace
                    canvas.setFillColor(color)
                    center_x = (i + 0.5) * segment
                    text_w = pdfmetrics.stringWidth(self.word, self.word_font, self.word_font_size)
                    x = max(2, center_x - text_w / 2)
                    canvas.drawString(x, baseline, self.word)

        canvas.restoreState()



class EnglishWordPracticeBlock(Flowable):
    """Handwriting grid block for a single English word."""

    def __init__(
        self,
        index: int,
        word: str,
        part_of_speech: str,
        *,
        width: float,
        copies: int = 1,
        line_height: float | None = None,
        base_color_hex: str | None = None,
    ) -> None:
        ensure_reportlab()
        super().__init__()
        self.index = index
        self.word = word
        self.part_of_speech = part_of_speech
        self.width = width
        self.copies = copies
        self.line_height = line_height if line_height is not None else 0.5 * cm
        self.grid = FourLineWordPractice(
            word,
            width=width,
            copies=copies,
            line_height=self.line_height,
        )
        # Apply per-word color from palette if provided
        if base_color_hex:
            self.grid.word_color_primary = colors.HexColor(base_color_hex)
            self.grid.word_color_trace = _lighten_hex(base_color_hex, 0.65)
        self._grid_size: tuple[float, float] = (0.0, 0.0)

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:  # noqa: D401
        target_width = min(self.width, available_width)
        grid_w, grid_h = self.grid.wrap(target_width, available_height)
        self._grid_size = (grid_w, grid_h)
        return target_width, grid_h

    def draw(self) -> None:  # noqa: D401
        canvas = self.canv
        canvas.saveState()
        self.grid.drawOn(canvas, 0, 0)
        canvas.restoreState()



def _document_preamble(title: str) -> List:
    styles = _get_styles()
    story = [
        Spacer(1, 0.2 * cm),
        Paragraph(f"日期：{date.today().isoformat()}", styles["info"]),
        Spacer(1, 0.35 * cm),
    ]
    return story


def _load_chinese_chars(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"未找到语文题库文件：{path}")
    content = path.read_text(encoding="utf-8", errors="ignore")
    chars = [line.strip() for line in content.splitlines() if line.strip()]
    return chars


def _pinyin_for_char(character: str) -> str:
    ensure_pinyin()
    result = lazy_pinyin(character, style=Style.TONE, strict=False)
    pinyin_text = " ".join(result).strip()
    return pinyin_text or character


def _add_chinese_practice_row(story: List, character: str, pinyin_text: str) -> None:
    story.append(HanziPracticeRow(character, pinyin_text))


def _build_chinese_section(
    story: List,
    characters: Iterable[str],
    *,
    heading_text: str | None = None,
) -> None:
    ensure_reportlab()
    ensure_pinyin()
    styles = _get_styles()
    char_list = list(characters)
    if not char_list:
        return
    if heading_text:
        story.append(Paragraph(heading_text, styles["heading"]))
        story.append(Spacer(1, 0.3 * cm))
    # Assign a unique random color per character for the glyphs
    base_colors = _random_unique_palette(len(char_list))
    for idx, hanzi in enumerate(char_list, start=1):
        pinyin_text = _pinyin_for_char(hanzi)
        row = HanziPracticeRow(hanzi, pinyin_text)
        base_hex = base_colors[idx - 1]
        row.primary_text_color = colors.HexColor(base_hex)
        row.secondary_text_color = _lighten_hex(base_hex, 0.6)
        row.pinyin_text_color = row.primary_text_color
        story.append(row)
        if idx != len(char_list):
            story.append(Spacer(1, 0.22 * cm))
    story.append(Spacer(1, 0.4 * cm))


def _generate_math_problems(count: int = 10) -> List[str]:
    problems: List[str] = []
    while len(problems) < count:
        op = random.choice(("+", "-"))
        if op == "+":
            a = random.randint(0, 99)
            b = random.randint(0, 99)
            if a + b > 100:
                continue
        else:
            a = random.randint(0, 99)
            b = random.randint(0, a)
        problems.append(f"{a:>2} {op} {b:>2} = ")
    return problems


def _create_math_table(problems: List[str], columns: int, available_width: float) -> Table:
    columns = max(1, columns)
    rows = math.ceil(len(problems) / columns)
    data = [["" for _ in range(columns)] for _ in range(rows)]
    for idx, problem in enumerate(problems):
        row_idx, col_idx = divmod(idx, columns)
        data[row_idx][col_idx] = problem
    col_width = available_width / columns
    table = Table(data, colWidths=[col_width] * columns, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 14),
                ("LEADING", (0, 0), (-1, -1), 18),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _build_math_section(
    story: List,
    problems: Iterable[str],
    *,
    available_width: float,
    heading_text: str | None = None,
    columns: int = 2,
) -> None:
    ensure_reportlab()
    problem_list = [item.strip() for item in problems if item and item.strip()]
    if not problem_list:
        return
    styles = _get_styles()
    if heading_text:
        story.append(Paragraph(heading_text, styles["heading"]))
        story.append(Spacer(1, 0.3 * cm))
    table = _create_math_table(problem_list, columns, available_width)
    story.append(table)
    story.append(Spacer(1, 0.6 * cm))


def _load_words_by_level(path: Path, level: str) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"未找到英语词汇表文件：{path}")
    level_key = level.strip().lower()
    with path.open(encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        words = [row for row in reader if row.get("level", "").strip().lower() == level_key]
    return words


def _select_chinese_characters(count: int = 5) -> List[str]:
    ensure_pinyin()
    characters = _load_chinese_chars(YUWEN_BANK)
    if len(characters) < count:
        raise RuntimeError(f"语文题库不足 {count} 个汉字。")
    return random.sample(characters, count)


def _select_english_words(level: str, count: int = 5) -> List[Dict[str, str]]:
    words = _load_words_by_level(OXP_BANK, level)
    if len(words) < count:
        raise RuntimeError(f"词汇等级 {level.strip().upper()} 的单词不足 {count} 个。")
    return random.sample(words, count)


def _build_english_section(
    story: List,
    words: Iterable[Dict[str, str]],
    level: str,
    *,
    available_width: float,
    heading_text: str | None = None,
    copies: int = 1,
    columns: int = 1,
    grid_width_cm: float | None = None,
    line_height_cm: float = 0.5,
    show_level_info: bool = True,
    force_page_break: bool = False,
) -> None:
    ensure_reportlab()
    word_list = list(words)
    if not word_list:
        return
    if force_page_break and story:
        story.append(PageBreak())
    styles = _get_styles()
    level_clean = level.strip().upper()
    if heading_text:
        story.append(Paragraph(heading_text, styles["heading"]))
        story.append(Spacer(1, 0.12 * cm))
    if show_level_info:
        story.append(Paragraph(f"???????{level_clean}", styles["info"]))
        story.append(Spacer(1, 0.1 * cm))

    columns = max(1, columns)
    grid_width_default = 14.5 if columns == 1 else 7.0
    grid_width_pt = (grid_width_cm if grid_width_cm is not None else grid_width_default) * cm
    max_width_per_column = available_width / columns
    grid_width_pt = min(grid_width_pt, max_width_per_column)
    line_height = max(0.3, line_height_cm) * cm

    # Assign a unique random color per word for coloring + traces
    base_colors = _random_unique_palette(len(word_list))
    blocks: List[EnglishWordPracticeBlock] = []
    for index, item in enumerate(word_list, start=1):
        word = item.get("word", "").strip()
        part_of_speech = item.get("class", "").strip()
        block = EnglishWordPracticeBlock(
            index,
            word,
            part_of_speech,
            width=grid_width_pt,
            copies=copies,
            line_height=line_height,
            base_color_hex=base_colors[index - 1],
        )
        blocks.append(block)

    if columns == 1:
        table = Table([[block] for block in blocks], colWidths=[grid_width_pt], hAlign="CENTER")
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.35 * cm))
        return

    rows = math.ceil(len(blocks) / columns)
    table_data: List[List[object]] = [["" for _ in range(columns)] for _ in range(rows)]
    for idx, block in enumerate(blocks):
        row_idx, col_idx = divmod(idx, columns)
        table_data[row_idx][col_idx] = block

    table = Table(table_data, colWidths=[grid_width_pt] * columns, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.35 * cm))


def generate_chinese_homework() -> Path:
    ensure_reportlab()
    ensure_pinyin()
    selected = _select_chinese_characters()
    output_path = ROOT_DIR / f"{date.today().isoformat()}-语文作业.pdf"
    doc = SimpleDocTemplate(str(output_path), **PAGE_SETUP)
    story = _document_preamble("语文作业")
    _build_chinese_section(story, selected, heading_text=None)
    doc.build(story)
    return output_path


def generate_math_homework() -> Path:
    ensure_reportlab()
    output_path = ROOT_DIR / f"{date.today().isoformat()}-数学作业.pdf"
    doc = SimpleDocTemplate(str(output_path), **PAGE_SETUP)
    story = _document_preamble("数学作业")
    problems = _generate_math_problems(10)
    _build_math_section(story, problems, available_width=doc.width, heading_text=None)
    doc.build(story)
    return output_path


def generate_english_homework(level: str) -> Path:
    ensure_reportlab()
    level_clean = level.strip().upper()
    selected = _select_english_words(level_clean)
    output_path = ROOT_DIR / f"{date.today().isoformat()}-英语作业.pdf"
    doc = SimpleDocTemplate(str(output_path), **PAGE_SETUP)
    story = _document_preamble("英语作业")
    _build_english_section(
        story,
        selected,
        level_clean,
        available_width=doc.width,
        heading_text=None,
        copies=1,
        columns=1,
        grid_width_cm=None,
        line_height_cm=0.5,
        show_level_info=True,
    )
    doc.build(story)
    return output_path


def generate_daily_homework_bundle(level: str) -> Path:
    ensure_reportlab()
    ensure_pinyin()
    level_clean = level.strip().upper()
    chinese_chars = _select_chinese_characters()
    math_problems = _generate_math_problems(10)
    english_words = _select_english_words(level_clean)

    output_path = ROOT_DIR / f"{date.today().isoformat()}-每日作业.pdf"
    doc = SimpleDocTemplate(str(output_path), **PAGE_SETUP)
    story = _document_preamble("每日作业")
    _build_chinese_section(story, chinese_chars, heading_text=None)
    _build_math_section(story, math_problems, available_width=doc.width, heading_text=None)
    _build_english_section(
        story,
        english_words,
        level_clean,
        available_width=doc.width,
        heading_text=None,
        copies=1,
        columns=1,
        grid_width_cm=doc.width / cm,
        line_height_cm=0.38,
        show_level_info=False,
        force_page_break=False,
    )
    doc.build(story)
    return output_path


class HomeworkGeneratorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("每日作业生成器")
        self.root.resizable(False, False)
        self.level_var = tk.StringVar(value="A1")
        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Microsoft YaHei", 12))
        style.configure("TLabel", font=("Microsoft YaHei", 11))

        container = ttk.Frame(self.root, padding=20)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        level_label = ttk.Label(container, text="英语词汇等级：")
        level_label.grid(row=0, column=0, padx=10, pady=(0, 12), sticky="e")

        level_combo = ttk.Combobox(
            container,
            textvariable=self.level_var,
            values=("A1", "A2", "B1", "B2"),
            state="readonly",
            width=6,
        )
        level_combo.grid(row=0, column=1, padx=10, pady=(0, 12), sticky="w")
        level_combo.set(self.level_var.get())

        generate_btn = ttk.Button(container, text="生成全部作业", command=self._handle_bundle)
        generate_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        hint = ttk.Label(container, text="默认生成语文、数学，英语请先选择词汇等级，输出为 PDF。")
        hint.grid(row=2, column=0, columnspan=2, padx=10, pady=(6, 0), sticky="ew")
        hint.configure(anchor="center")

        for col in range(2):
            container.columnconfigure(col, weight=1)

    def _handle_bundle(self) -> None:
        level = self.level_var.get().strip().upper() or "A1"
        self._run_generator(lambda: generate_daily_homework_bundle(level), "每日作业")

    def _run_generator(self, generator: Callable[[], Path], subject_label: str) -> None:
        try:
            output_path = generator()
        except DependencyError as exc:
            messagebox.showerror("缺少依赖", str(exc), parent=self.root)
        except FileNotFoundError as exc:
            messagebox.showerror("文件缺失", str(exc), parent=self.root)
        except Exception as exc:  # pragma: no cover
            messagebox.showerror(
                "生成失败",
                f"生成{subject_label}时出现错误：\n{exc}",
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                "生成成功",
                f"已生成{subject_label}：\n{output_path}",
                parent=self.root,
            )

    def _handle_chinese(self) -> None:
        self._run_generator(generate_chinese_homework, "语文")

    def _handle_math(self) -> None:
        self._run_generator(generate_math_homework, "数学")

    def _handle_english(self) -> None:
        level = self.level_var.get().strip().upper() or "A1"
        self._run_generator(lambda: generate_english_homework(level), "英语")

    def run(self) -> None:
        self.root.mainloop()


def main(argv: Iterable[str] | None = None) -> int:
    app = HomeworkGeneratorApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

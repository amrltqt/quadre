from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

from .engine import Widget
from ..components import DIMENSIONS, KPICard, COLORS, FONTS, ImageBlock, ProgressBar, StatusBadge
from ..components.config import load_cjk_font
from .defaults import parse_color
from ..components.tables import (
    create_auto_table,
    EnhancedTable,
    ColumnDefinition,
    CellType,
    CellAlignment,
    TableStyle,
)


@dataclass
class KPIWidget(Widget):
    title: str
    value: str
    delta: Optional[dict] = None

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        return (avail_w, min(DIMENSIONS.KPI_CARD_HEIGHT, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        card = KPICard(self.title, self.value, self.delta)
        card.render(draw, x, y, w)


@dataclass
class TableWidget(Widget):
    data: Union[List[List[str]], dict]
    header_height: Optional[int] = None
    row_height: Optional[int] = None
    fill_height: bool = False
    min_row_height: int = 28
    max_row_height: int = 90
    fit: str = "truncate"  # "truncate" | "shrink"
    shrink_row_height_floor: int = 14
    style_overrides: Optional[dict] = None

    def _make_columns(self, headers: List[str], total_width: int) -> List[ColumnDefinition]:
        # Make columns whose widths sum to (total_width - 2*padding already accounted by caller)
        num = max(1, len(headers))
        base = total_width // num if num else total_width
        rem = total_width % num if num else 0
        cols: List[ColumnDefinition] = []
        for i, title in enumerate(headers):
            width = base + (1 if i < rem else 0)
            if i == 0:
                width += 30
            elif i >= num - 2:
                width = max(50, width - 15)
            cols.append(ColumnDefinition(
                title=title,
                width=width,
                alignment=CellAlignment.LEFT,
                cell_type=CellType.BOLD_TEXT if i == 0 else CellType.PERCENTAGE,
            ))
        return cols

    def _style(self) -> TableStyle:
        s = self.style_overrides or {}
        def co(value, default):
            if value is None:
                return default
            c = parse_color(value)
            return c if c is not None else value
        return TableStyle(
            background_color=co(s.get("background_color"), COLORS.CARD_BACKGROUND),
            border_color=co(s.get("border_color"), COLORS.BORDER),
            header_background=co(s.get("header_background"), COLORS.MUTED),
            alt_row_background=co(s.get("alt_row_background"), COLORS.MUTED),
            text_color=co(s.get("text_color"), COLORS.FOREGROUND),
            header_text_color=co(s.get("header_text_color"), COLORS.FOREGROUND),
            padding=int(s.get("padding", 20)),
            use_alternating_rows=bool(s.get("use_alternating_rows", True)),
        )

    def _table(self, total_width: int, header_h_override: Optional[int] = None, row_h_override: Optional[int] = None) -> EnhancedTable:
        # We target column sum ~= total_width - 2*padding (padding=20)
        available = max(0, total_width - 40)
        style = self._style()
        if isinstance(self.data, dict) and self.data.get("headers") and self.data.get("rows"):
            headers = list(self.data.get("headers", []))
            rows = list(self.data.get("rows", []))
            columns = self._make_columns(headers, available)
            return EnhancedTable(
                rows, columns,
                style=style,
                header_height=header_h_override or self.header_height,
                row_height=row_h_override or self.row_height,
            )
        else:
            # Assume list-of-lists, use auto sizing with explicit total_width
            rows = self.data if isinstance(self.data, list) else []
            table = create_auto_table(rows, style=style, total_width=available)
            # Apply overrides if provided
            if header_h_override is not None:
                table.header_height = header_h_override
            if row_h_override is not None:
                table.row_height = row_h_override
            table.total_height = table.header_height + len(rows) * table.row_height + 20
            return table

    def _row_count(self) -> int:
        if isinstance(self.data, dict) and self.data.get("rows"):
            return len(self.data.get("rows", []))
        if isinstance(self.data, list):
            # include header row visually as part of data? EnhancedTable already has its own header bar,
            # so list-of-lists are rendered as body rows only.
            return len(self.data)
        return 0

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        header_h = self.header_height or DIMENSIONS.TABLE_HEADER_HEIGHT
        row_h = self.row_height or DIMENSIONS.TABLE_ROW_HEIGHT
        rows_n = self._row_count()
        total_h = header_h + rows_n * row_h + 20
        return (avail_w, min(total_h, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        header_h = self.header_height or DIMENSIONS.TABLE_HEADER_HEIGHT
        default_row_h = self.row_height or DIMENSIONS.TABLE_ROW_HEIGHT

        # Determine rows list for rendering (may be truncated later)
        if isinstance(self.data, dict) and self.data.get("rows"):
            rows_all = list(self.data.get("rows", []))
            headers = list(self.data.get("headers", []))
        elif isinstance(self.data, list):
            rows_all = list(self.data)
            headers = []
        else:
            rows_all = []
            headers = []

        # Compute row height / truncation to fit exactly if fill_height
        content_space = max(0, h - header_h - 20)
        row_h = default_row_h
        rows_to_draw = rows_all

        if self.fill_height and rows_all:
            # Ideal row height to fill all rows exactly in the available space
            n = len(rows_all)
            ideal = content_space / n if n > 0 else default_row_h
            if self.fit == "shrink":
                # Always fit exactly: shrink or expand rows to match content_space
                row_h = max(1, int(ideal))
            else:  # truncate
                if ideal >= self.min_row_height and ideal <= self.max_row_height:
                    row_h = int(ideal)
                elif ideal < self.min_row_height:
                    # Truncate rows to keep at least min_row_height and fill perfectly
                    max_rows_fit = max(1, content_space // self.min_row_height) if content_space > 0 else 0
                    rows_to_draw = rows_all[:max_rows_fit]
                    row_h = max(self.min_row_height, int(content_space / max_rows_fit)) if max_rows_fit > 0 else self.min_row_height
                else:  # ideal > max -> cap row height
                    row_h = self.max_row_height
        else:
            # Not fill-height: truncate overflowing rows to default row height
            if default_row_h > 0:
                max_rows_fit = max(0, content_space // default_row_h)
                if max_rows_fit:
                    rows_to_draw = rows_all[:max_rows_fit]

        # Build table object with overrides
        if headers:
            table_data = {"headers": headers, "rows": rows_to_draw}
        else:
            table_data = rows_to_draw

        tmp = TableWidget(table_data, header_h, row_h)
        table = tmp._table(w, header_h_override=header_h, row_h_override=row_h)
        table.render(draw, x, y, w)


@dataclass
class Spacer(Widget):
    height: int

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        # Width should be whatever is available; height is the spacer's height (clamped)
        return (avail_w, min(self.height, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        # No drawing; space only
        return None


# -------------------------
# Additional reporting widgets
# -------------------------


@dataclass
class ImageWidget(Widget):
    src: str
    fit: str = "contain"  # contain|cover
    radius: int = 0
    opacity: float = 1.0
    align: str = "center"  # left|center|right

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        block = ImageBlock(self.src, self.fit, self.radius, self.opacity, self.align)
        mw, mh = block.measure(avail_w, avail_h)
        return (mw, mh)

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        block = ImageBlock(self.src, self.fit, self.radius, self.opacity, self.align)
        block.render(draw, x, y, w, h)


@dataclass
class ProgressBarWidget(Widget):
    value: float  # 0..1 (accepts >1 treated as percentage by adapter)
    label: Optional[str] = None
    bar_height: int = 18
    bg_fill: Union[str, Tuple[int, int, int]] = COLORS.MUTED
    fill: Union[str, Tuple[int, int, int]] = COLORS.SUCCESS

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        bar = ProgressBar(self.value, self.label, self.bar_height, self.bg_fill, self.fill, FONTS.SMALL)
        _, hh = bar.measure(avail_w, avail_h)
        return (avail_w, min(hh, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        bar = ProgressBar(self.value, self.label, self.bar_height, self.bg_fill, self.fill, FONTS.SMALL)
        bar.render(draw, x, y, w, h)


@dataclass
class StatusBadgeWidget(Widget):
    text: str
    variant: str = "secondary"  # default|secondary|destructive|success|warning|outline

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        sb = StatusBadge(self.text, self.variant)
        w, h = sb.measure()
        return (min(avail_w, w), min(avail_h, h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        # Align within box: left + vertically centered
        sb = StatusBadge(self.text, self.variant)
        _, bh = sb.measure()
        by = y + (h - bh) // 2
        sb.render(draw, x, by)
from dataclasses import dataclass


@dataclass
class TextWidget(Widget):
    text: str
    fill: Tuple[int, int, int] = (20, 20, 20)
    font: Optional[ImageFont.ImageFont] = None
    font_key: Optional[str] = None  # dynamic key resolved against FONTS at render time
    align: str = "left"  # left|center|right

    def _font(self) -> ImageFont.ImageFont:
        # Prefer dynamic lookup if a key is provided (keeps in sync with scaling)
        if self.font_key:
            key = str(self.font_key).lower()
            if key == "title":
                return FONTS.H1
            if key == "heading":
                return FONTS.H2
            if key == "number":
                return FONTS.NUMBER
            if key == "table":
                return FONTS.TABLE
            if key == "small" or key == "caption":
                return FONTS.SMALL
            return FONTS.BODY
        if self.font:
            return self.font
        return ImageFont.load_default()

    def _cjk_font(self) -> ImageFont.ImageFont:
        base = self._font()
        try:
            size = getattr(base, "size", 14) or 14
        except Exception:
            size = 14
        return load_cjk_font(size)

    @staticmethod
    def _is_cjk(ch: str) -> bool:
        o = ord(ch)
        return (
            0x4E00 <= o <= 0x9FFF
            or 0x3400 <= o <= 0x4DBF
            or 0xF900 <= o <= 0xFAFF
        )

    def _segment_runs(self) -> List[Tuple[str, ImageFont.ImageFont]]:
        base = self._font()
        cjk = self._cjk_font()
        segments: List[Tuple[str, ImageFont.ImageFont]] = []
        buf: List[str] = []
        cur_font = base
        for ch in self.text:
            want = cjk if self._is_cjk(ch) else base
            if want is cur_font:
                buf.append(ch)
            else:
                if buf:
                    segments.append(("".join(buf), cur_font))
                    buf = []
                cur_font = want
                buf.append(ch)
        if buf:
            segments.append(("".join(buf), cur_font))
        return segments

    def _line_height(self, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont) -> int:
        try:
            asc, desc = font.getmetrics()
            return int(asc + desc)
        except Exception:
            bb = draw.textbbox((0, 0), "Ag", font=font)
            return int(bb[3] - bb[1])

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        runs = self._segment_runs()
        if runs:
            total_w = sum(int(f.getlength(s)) for s, f in runs)
            # Use font metrics (ascent+descent) to guarantee room for descenders
            heights = [self._line_height(draw, f) for _, f in runs]
            h = max(heights) if heights else 0
            # Add a 1px safety pad to avoid AA clipping in tight boxes
            h_safe = h + 1 if h > 0 else 0
            return (min(total_w, avail_w), min(h_safe, avail_h))
        else:
            font = self._font()
            # Height from metrics with a small safety pad
            h = self._line_height(draw, font)
            w = int(font.getlength(self.text))
            h_safe = h + 1 if h > 0 else 0
            return (min(w, avail_w), min(h_safe, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        runs = self._segment_runs()
        if not runs:
            font = self._font()
            bbox = draw.textbbox((0, 0), self.text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if self.align == "center":
                tx = x + (w - tw) // 2
            elif self.align == "right":
                tx = x + w - tw
            else:
                tx = x
            ty = y + (h - th) // 2
            draw.text((tx, ty), self.text, fill=self.fill, font=font)
            return

        total_w = sum(int(f.getlength(s)) for s, f in runs)
        th = max((self._line_height(draw, f) for _, f in runs), default=0)

        if self.align == "center":
            tx = x + (w - total_w) // 2
        elif self.align == "right":
            tx = x + w - total_w
        else:
            tx = x
        ty = y + (h - th) // 2

        cx = tx
        for seg, fnt in runs:
            draw.text((cx, ty), seg, fill=self.fill, font=fnt)
            cx += int(fnt.getlength(seg))

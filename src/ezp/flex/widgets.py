from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Union

from PIL import ImageDraw

from .engine import Widget
from ..components import DIMENSIONS, KPICard
from ..components.tables import (
    create_auto_table,
    EnhancedTable,
    ColumnDefinition,
    CellType,
    CellAlignment,
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

    def _table(self, total_width: int, header_h_override: Optional[int] = None, row_h_override: Optional[int] = None) -> EnhancedTable:
        # We target column sum ~= total_width - 2*padding (padding=20)
        available = max(0, total_width - 40)
        if isinstance(self.data, dict) and self.data.get("headers") and self.data.get("rows"):
            headers = list(self.data.get("headers", []))
            rows = list(self.data.get("rows", []))
            columns = self._make_columns(headers, available)
            return EnhancedTable(
                rows, columns,
                header_height=header_h_override or self.header_height,
                row_height=row_h_override or self.row_height,
            )
        else:
            # Assume list-of-lists, use auto sizing with explicit total_width
            rows = self.data if isinstance(self.data, list) else []
            table = create_auto_table(rows, total_width=available)
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
        return (min(avail_w, avail_w), min(self.height, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        # No drawing; space only
        return None

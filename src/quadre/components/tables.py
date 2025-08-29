"""
Generic table components for quadre dashboards.

This module contains flexible table-based UI components for displaying tabular data
with customizable styling, cell renderers, and column configurations.
"""

from PIL import ImageDraw, ImageFont
from typing import Any, List, Optional, Callable
from enum import Enum
from .config import COLORS, FONTS, DIMENSIONS
from .primitives import rounded_rectangle, draw_percentage_text


class CellAlignment(Enum):
    """Cell content alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class CellType(Enum):
    """Cell content type for automatic formatting."""

    TEXT = "text"
    NUMBER = "number"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    BOLD_TEXT = "bold_text"


class ColumnDefinition:
    """Definition for a table column with rendering options."""

    def __init__(
        self,
        title: str,
        width: int,
        alignment: CellAlignment = CellAlignment.LEFT,
        cell_type: CellType = CellType.TEXT,
        font: Optional[ImageFont.ImageFont] = None,
        color: Optional[str] = None,
        renderer: Optional[Callable[[Any], str]] = None,
    ):
        """
        Initialize column definition.

        Args:
            title: Column header title
            width: Column width in pixels
            alignment: Text alignment within the cell
            cell_type: Type of content for automatic formatting
            font: Custom font for this column
            color: Custom text color for this column
            renderer: Custom render function for cells in this column
        """
        self.title = title
        self.width = width
        self.alignment = alignment
        self.cell_type = cell_type
        self.font = font or FONTS.TABLE
        # Use live foreground color so themes update correctly (avoid static TEXT_PRIMARY alias)
        self.color = color or COLORS.FOREGROUND
        self.renderer = renderer


class TableStyle:
    """Style configuration for tables."""

    def __init__(
        self,
        background_color: str = COLORS.CARD_BACKGROUND,
        border_color: str = COLORS.BORDER,
        header_background: str = COLORS.MUTED,
        alt_row_background: str = COLORS.MUTED,
        text_color: str = COLORS.FOREGROUND,
        header_text_color: str = COLORS.FOREGROUND,
        padding: int = 20,
        use_alternating_rows: bool = True,
    ):
        """Initialize table style configuration."""
        self.background_color = background_color
        self.border_color = border_color
        self.header_background = header_background
        self.alt_row_background = alt_row_background
        self.text_color = text_color
        self.header_text_color = header_text_color
        self.padding = padding
        self.use_alternating_rows = use_alternating_rows


class EnhancedTable:
    """
    A flexible, enhanced table component with customizable styling and cell rendering.

    Features:
    - Configurable column definitions with custom renderers
    - Flexible cell alignment and formatting
    - Customizable styling and colors
    - Automatic percentage detection and coloring
    - Custom cell type handling
    - Shadow and border effects
    """

    def __init__(
        self,
        rows: List[List[str]],
        columns: List[ColumnDefinition],
        style: Optional[TableStyle] = None,
        header_height: Optional[int] = None,
        row_height: Optional[int] = None,
    ):
        """
        Initialize enhanced table.

        Args:
            rows: List of data rows, each row is a list of cell values
            columns: List of column definitions
            style: Optional custom table style
            header_height: Optional custom header height
            row_height: Optional custom row height
        """
        self.rows = rows
        self.columns = columns
        self.style = style or TableStyle()
        self.header_height = header_height or DIMENSIONS.TABLE_HEADER_HEIGHT
        self.row_height = row_height or DIMENSIONS.TABLE_ROW_HEIGHT
        self.total_height = self.header_height + len(rows) * self.row_height + 20

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> int:
        """
        Render the table at the specified position.

        Args:
            draw: PIL ImageDraw object
            x: X position
            y: Y position
            width: Table width

        Returns:
            Height of the rendered table
        """
        # Draw main table container
        rounded_rectangle(
            draw,
            (x, y, x + width, y + self.total_height),
            DIMENSIONS.CARD_RADIUS,
            fill=self.style.background_color,
            outline=self.style.border_color,
            width=1,
        )

        # Draw header
        self._render_header(draw, x, y, width)

        # Draw data rows
        self._render_data_rows(draw, x, y + self.header_height + 10, width)

        return self.total_height

    def _render_header(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int
    ) -> None:
        """Render table header row."""
        # Header background (rounded at top)
        draw.rounded_rectangle(
            (x, y, x + width, y + self.header_height),
            DIMENSIONS.CARD_RADIUS,
            fill=self.style.header_background,
        )

        # Stroke around the header area (on top and sides)
        draw.rounded_rectangle(
            (x, y, x + width, y + self.header_height),
            DIMENSIONS.CARD_RADIUS,
            outline=self.style.border_color,
            width=1,
        )

        # Fill bottom part of header to make it rectangular at the bottom
        # (also hides the curved bottom outline just drawn)
        draw.rectangle(
            (
                x,
                y + self.header_height - DIMENSIONS.CARD_RADIUS,
                x + width,
                y + self.header_height,
            ),
            fill=self.style.header_background,
        )

        # Bottom border under the header for separation
        draw.line(
            [(x + 1, y + self.header_height), (x + width - 1, y + self.header_height)],
            fill=self.style.border_color,
            width=1,
        )

        # Header text
        current_x = x + self.style.padding
        for column in self.columns:
            self._render_header_cell(draw, current_x, y + 15, column)
            current_x += column.width

    def _render_header_cell(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, column: ColumnDefinition
    ) -> None:
        """Render a single header cell."""
        text_x = self._calculate_text_position(
            x, column.width, column.title, FONTS.BOLD_SMALL, column.alignment
        )
        # Center vertically in header
        text_y = y + (self.header_height - 40) // 2  # 40 is approximate font height
        draw.text(
            (text_x, text_y),
            column.title,
            font=FONTS.BOLD_SMALL,
            fill=self.style.header_text_color,
        )

    def _render_data_rows(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int
    ) -> None:
        """Render table data rows."""
        current_y = y

        for row_index, row in enumerate(self.rows):
            # Draw alternating row background (guard against very small row heights)
            if (
                self.style.use_alternating_rows
                and row_index % 2 == 1
                and self.row_height > 5
            ):
                top = current_y - 5
                bottom = current_y + self.row_height - 10
                if bottom >= top:
                    draw.rectangle(
                        (x + 2, top, x + width - 2, bottom),
                        fill=self.style.alt_row_background,
                    )

            # Render cells in this row
            self._render_row_cells(draw, row, x + self.style.padding, current_y)

            current_y += self.row_height

    def _render_row_cells(
        self, draw: ImageDraw.ImageDraw, row: List[str], start_x: int, y: int
    ) -> None:
        """Render cells in a single row."""
        current_x = start_x
        # Center vertically in row
        cell_y = y + (self.row_height - 30) // 2  # 30 is approximate font height

        for col_index, (cell_value, column) in enumerate(zip(row, self.columns)):
            if column.renderer:
                # Use custom renderer
                column.renderer(
                    draw, current_x, cell_y, column.width, cell_value, column
                )
            else:
                # Use default renderer based on cell type
                self._render_cell_by_type(draw, current_x, cell_y, column, cell_value)

            current_x += column.width

    def _render_cell_by_type(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        column: ColumnDefinition,
        cell_value: str,
    ) -> None:
        """Render cell based on its type configuration."""
        if column.cell_type == CellType.PERCENTAGE and self._has_percentage(cell_value):
            self._render_percentage_cell(draw, cell_value, x, y, column)
        elif column.cell_type == CellType.BOLD_TEXT:
            self._render_bold_cell(draw, cell_value, x, y, column)
        elif column.cell_type == CellType.NUMBER:
            self._render_number_cell(draw, cell_value, x, y, column)
        else:
            # Default text rendering
            self._render_text_cell(draw, cell_value, x, y, column)

    def _render_text_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell_value: str,
        x: int,
        y: int,
        column: ColumnDefinition,
    ) -> None:
        """Render a regular text cell."""
        # Truncate text to fit in column width
        max_width = column.width - 20  # Leave padding
        truncated_text = self._truncate_text(cell_value, column.font, max_width)
        text_x = self._calculate_text_position(
            x, column.width, truncated_text, column.font, column.alignment
        )
        draw.text((text_x, y), truncated_text, font=column.font, fill=column.color)

    def _render_bold_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell_value: str,
        x: int,
        y: int,
        column: ColumnDefinition,
    ) -> None:
        """Render a bold text cell."""
        # Truncate text to fit in column width
        max_width = column.width - 20  # Leave padding
        truncated_text = self._truncate_text(cell_value, FONTS.BOLD_SMALL, max_width)
        text_x = self._calculate_text_position(
            x, column.width, truncated_text, FONTS.BOLD_SMALL, column.alignment
        )
        draw.text((text_x, y), truncated_text, font=FONTS.BOLD_SMALL, fill=column.color)

    def _render_number_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell_value: str,
        x: int,
        y: int,
        column: ColumnDefinition,
    ) -> None:
        """Render a number cell with right alignment."""
        # Truncate text to fit in column width
        max_width = column.width - 20  # Leave padding
        truncated_text = self._truncate_text(cell_value, column.font, max_width)
        text_x = self._calculate_text_position(
            x, column.width, truncated_text, column.font, CellAlignment.RIGHT
        )
        draw.text((text_x, y), truncated_text, font=column.font, fill=column.color)

    def _render_percentage_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell_value: str,
        x: int,
        y: int,
        column: ColumnDefinition,
    ) -> None:
        """Render cell with colored percentage highlighting."""
        try:
            # Split main text and percentage
            parts = cell_value.split("(", 1)
            main_text = parts[0].strip()
            pct_part = parts[1].replace(")", "").strip()

            # Truncate main text to fit in column
            max_width = column.width - 80  # Leave space for percentage
            main_text = self._truncate_text(main_text, column.font, max_width)

            # Determine percentage color with semantic colors
            pct_color = column.color
            if pct_part.startswith("+"):
                pct_color = COLORS.SUCCESS
            elif pct_part.startswith("-"):
                pct_color = COLORS.DESTRUCTIVE

            # Calculate position based on alignment
            if column.alignment == CellAlignment.CENTER:
                full_text = f"{main_text} ({pct_part})"
                text_x = self._calculate_text_position(
                    x, column.width, full_text, column.font, column.alignment
                )
            else:
                text_x = self._calculate_text_position(
                    x, column.width, main_text, column.font, column.alignment
                )

            # Render main text and percentage
            draw_percentage_text(
                draw,
                (text_x, y),
                main_text,
                f"({pct_part})",
                column.font,
                column.font,
                column.color,
                pct_color,
                spacing=5,
            )
        except (IndexError, ValueError):
            # Fallback to regular rendering if parsing fails
            self._render_text_cell(draw, cell_value, x, y, column)

    def _truncate_text(self, text: str, font, max_width: int) -> str:
        """Truncate text with ellipsis if it exceeds max width."""
        if font.getlength(text) <= max_width:
            return text

        # Try to fit text with ellipsis
        ellipsis = "..."
        ellipsis_width = font.getlength(ellipsis)
        available_width = max_width - ellipsis_width

        if available_width <= 0:
            return ellipsis

        # Binary search to find the longest text that fits
        left, right = 0, len(text)
        result = ""

        while left <= right:
            mid = (left + right) // 2
            candidate = text[:mid]

            if font.getlength(candidate) <= available_width:
                result = candidate
                left = mid + 1
            else:
                right = mid - 1

        return result + ellipsis if result else text[:1] + ellipsis

    def _calculate_text_position(
        self,
        x: int,
        width: int,
        text: str,
        font: ImageFont.ImageFont,
        alignment: CellAlignment,
    ) -> int:
        """Calculate text x position based on alignment."""
        if alignment == CellAlignment.CENTER:
            text_width = font.getlength(text)
            return x + (width - text_width) // 2
        elif alignment == CellAlignment.RIGHT:
            text_width = font.getlength(text)
            return x + width - text_width - 10  # Small right padding
        else:  # LEFT alignment
            return x

    def _has_percentage(self, cell_value: str) -> bool:
        """Check if cell contains a percentage in parentheses."""
        return "(" in cell_value and ")" in cell_value and "%" in cell_value


def create_auto_table(
    rows: List[List[str]], style: Optional[TableStyle] = None, total_width: int = 1740
) -> EnhancedTable:
    """
    Factory function to create a table with auto-calculated columns from data.

    Args:
        rows: List of data rows
        style: Optional custom table style
        total_width: Total width to distribute among columns

    Returns:
        EnhancedTable instance with dynamic columns
    """
    if not rows:
        return EnhancedTable([], [], style)

    # Determine number of columns from first row
    num_columns = len(rows[0])
    if num_columns == 0:
        return EnhancedTable([], [], style)

    # Calculate column widths - distribute evenly with slight variation
    base_width = total_width // num_columns
    remainder = total_width % num_columns

    column_widths = []
    for i in range(num_columns):
        width = base_width + (1 if i < remainder else 0)
        # First column slightly wider for names/platforms
        if i == 0:
            width += 20
        # Last columns slightly narrower for compact data
        elif i >= num_columns - 2:
            width -= 10
        column_widths.append(width)

    # Generate generic column headers and definitions
    columns = []
    for i, width in enumerate(column_widths):
        # Determine cell type based on data patterns
        cell_type = CellType.BOLD_TEXT if i == 0 else CellType.PERCENTAGE
        alignment = CellAlignment.LEFT

        # Generic column names
        if i == 0:
            title = "Item"
        else:
            title = f"Col {i + 1}"

        columns.append(ColumnDefinition(title, width, alignment, cell_type))

    return EnhancedTable(rows, columns, style)

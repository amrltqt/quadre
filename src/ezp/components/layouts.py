"""
Layout components for EZ Pillow dashboard.

This module contains layout management components that handle positioning,
spacing, and organization of dashboard elements. It provides high-level
layout abstractions for creating consistent dashboard structures.
"""

from PIL import ImageDraw
from typing import List, Dict, Any, Optional, Tuple
from .config import COLORS, FONTS, DIMENSIONS
from .cards import KPICard, SectionCard
from .tables import EnhancedTable
from .primitives import calculate_layout_positions
from .kpi_layouts import KPILayoutManager, KPILayoutType
from .global_layouts import GlobalLayoutManager, ComponentType, LayoutDirection


class DashboardLayout:
    """
    Main dashboard layout manager.

    Handles the overall structure and positioning of dashboard sections.
    Provides methods for rendering headers, KPI sections, tables, and card grids.
    """

    def __init__(self, width: int = DIMENSIONS.WIDTH, height: int = DIMENSIONS.HEIGHT):
        """
        Initialize dashboard layout.

        Args:
            width: Canvas width
            height: Canvas height
        """
        self.width = width
        self.height = height
        self.padding = DIMENSIONS.PADDING
        self.content_width = width - 2 * self.padding
        self.kpi_layout_manager = KPILayoutManager(width, self.padding)
        self.global_layout_manager = GlobalLayoutManager(width, height, self.padding)

    def render_header(self, draw: ImageDraw.ImageDraw, title: str, date_note: Optional[str] = None) -> int:
        """
        Render dashboard header with title and optional date.

        Args:
            draw: PIL ImageDraw object
            title: Main title text
            date_note: Optional date/period note

        Returns:
            Y position after header (for next element)
        """
        header_y = self.padding

        # Draw main title
        draw.text((self.padding, header_y), title, font=FONTS.H1, fill=COLORS.FOREGROUND)

        # Draw date note if provided (right-aligned)
        if date_note:
            date_width = FONTS.BODY.getlength(date_note)
            date_x = self.width - date_width - self.padding - 20
            draw.text((date_x, header_y + 12), date_note, font=FONTS.BODY, fill=COLORS.MUTED_FOREGROUND)

        return header_y + 90

    def render_kpi_section(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                          y_position: int, layout_type: KPILayoutType = KPILayoutType.HORIZONTAL,
                          layout_config: Optional[Dict[str, Any]] = None) -> int:
        """
        Render KPI cards with flexible layout options.

        Args:
            draw: PIL ImageDraw object
            kpi_cards: List of KPI card components
            y_position: Starting Y position
            layout_type: Type of layout to use for KPIs
            layout_config: Additional configuration for custom layouts

        Returns:
            Y position after KPI section
        """
        return self.kpi_layout_manager.render_kpis(
            draw, kpi_cards, y_position, layout_type, layout_config
        )

    def render_with_global_layout(self, draw: ImageDraw.ImageDraw, data: Dict[str, Any],
                                 layout_config: Optional[Dict[str, Any]] = None) -> int:
        """
        Render entire dashboard using global layout system.

        Args:
            draw: PIL ImageDraw object
            data: Complete dashboard data
            layout_config: Optional global layout configuration

        Returns:
            Final Y position after rendering
        """
        # Create components from data
        components = self.global_layout_manager.create_layout_from_data(data)

        # Use provided layout config or create default vertical layout
        if layout_config is None:
            layout_config = {
                "direction": "vertical",
                "start_y": self.padding,
                "gap": DIMENSIONS.GAP_LARGE
            }

        return self.global_layout_manager.render_component_layout(draw, components, layout_config)

    def render_table_section(self, draw: ImageDraw.ImageDraw, table: EnhancedTable, y_position: int) -> int:
        """
        Render table section.

        Args:
            draw: PIL ImageDraw object
            table: Enhanced table component
            y_position: Starting Y position

        Returns:
            Y position after table section
        """
        table_height = table.render(draw, self.padding, y_position, self.content_width)
        return y_position + table_height + DIMENSIONS.GAP_LARGE

    def render_notes_section(self, draw: ImageDraw.ImageDraw, left_note: Optional[str],
                           right_note: Optional[str], y_position: int) -> int:
        """
        Render notes section with left and right notes.

        Args:
            draw: PIL ImageDraw object
            left_note: Left side note text
            right_note: Right side note text
            y_position: Starting Y position

        Returns:
            Y position after notes section
        """
        if not left_note and not right_note:
            return y_position

        # Left note
        if left_note:
            draw.text((self.padding + 20, y_position), left_note,
                     font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

        # Right note
        if right_note:
            draw.text((self.width // 2 + 40, y_position), right_note,
                     font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

        return y_position + 50

    def render_section_header(self, draw: ImageDraw.ImageDraw, title: str, y_position: int) -> int:
        """
        Render section header.

        Args:
            draw: PIL ImageDraw object
            title: Section title
            y_position: Starting Y position

        Returns:
            Y position after section header
        """
        draw.text((self.padding, y_position), title, font=FONTS.H2, fill=COLORS.FOREGROUND)
        return y_position + 60

    def render_card_grid(self, draw: ImageDraw.ImageDraw, cards: List[SectionCard],
                        y_position: int, columns: int, card_height: int) -> int:
        """
        Render cards in a grid layout.

        Args:
            draw: PIL ImageDraw object
            cards: List of section card components
            y_position: Starting Y position
            columns: Number of columns in the grid
            card_height: Height of each card

        Returns:
            Y position after card grid
        """
        gap = DIMENSIONS.GAP_MEDIUM
        card_width = (self.content_width - (columns - 1) * gap) // columns

        positions = calculate_layout_positions(
            self.content_width, self.padding, columns, card_width, gap
        )

        for i, card in enumerate(cards):
            if i < len(positions):  # Ensure we don't exceed available positions
                card.render(draw, positions[i], y_position, card_width, card_height)

        return y_position + card_height + DIMENSIONS.GAP_LARGE

    def render_table_with_config(self, draw: ImageDraw.ImageDraw, table_config: Dict[str, Any],
                                x: int, y: int, width: int) -> int:
        """
        Render table with configuration options.

        Args:
            draw: PIL ImageDraw object
            table_config: Table configuration dictionary
            x: X position
            y: Y position
            width: Table width

        Returns:
            Height of rendered table
        """
        from .tables import create_platform_table, create_simple_table, TableStyle

        table_type = table_config.get("type", "platform")
        rows = table_config.get("rows", [])

        if table_type == "platform":
            table = create_platform_table(rows)
        else:
            headers = table_config.get("headers", [])
            table = create_simple_table(rows, headers)

        # Apply custom style if provided
        style_config = table_config.get("style", {})
        if style_config:
            table.style = TableStyle(**style_config)

        return table.render(draw, x, y, width)


class CardGrid:
    """
    A flexible card grid layout component.

    Handles positioning and rendering of multiple cards in a grid pattern
    with consistent spacing and alignment.
    """

    def __init__(self, cards: List[SectionCard], columns: int, gap: int = DIMENSIONS.GAP_MEDIUM):
        """
        Initialize card grid.

        Args:
            cards: List of cards to arrange
            columns: Number of columns
            gap: Gap between cards
        """
        self.cards = cards
        self.columns = columns
        self.gap = gap
        self.rows = (len(cards) + columns - 1) // columns  # Ceiling division

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int,
              available_width: int, card_height: int) -> Tuple[int, int]:
        """
        Render the card grid.

        Args:
            draw: PIL ImageDraw object
            x: Starting X position
            y: Starting Y position
            available_width: Available width for the grid
            card_height: Height of each card

        Returns:
            Tuple of (total_width, total_height) used by the grid
        """
        card_width = (available_width - (self.columns - 1) * self.gap) // self.columns

        positions = calculate_layout_positions(
            available_width, x, self.columns, card_width, self.gap
        )

        current_row = 0
        for i, card in enumerate(self.cards):
            col = i % self.columns
            if col == 0 and i > 0:
                current_row += 1

            card_x = positions[col]
            card_y = y + current_row * (card_height + self.gap)

            card.render(draw, card_x, card_y, card_width, card_height)

        total_height = self.rows * card_height + (self.rows - 1) * self.gap
        return available_width, total_height


class FlexibleLayout:
    """
    A flexible layout system for custom dashboard arrangements.

    Provides utility methods for common layout patterns and spacing calculations.
    """

    @staticmethod
    def distribute_horizontal(total_width: int, num_items: int,
                            min_gap: int = DIMENSIONS.GAP_MEDIUM) -> Tuple[int, int]:
        """
        Calculate item width and gap for horizontal distribution.

        Args:
            total_width: Total available width
            num_items: Number of items to distribute
            min_gap: Minimum gap between items

        Returns:
            Tuple of (item_width, actual_gap)
        """
        total_gaps = (num_items - 1) * min_gap
        available_width = total_width - total_gaps
        item_width = available_width // num_items

        # Calculate actual gap (might be larger than min_gap due to integer division)
        remaining_width = total_width - (num_items * item_width)
        actual_gap = remaining_width // (num_items - 1) if num_items > 1 else 0

        return item_width, actual_gap

    @staticmethod
    def calculate_grid_dimensions(num_items: int, preferred_columns: int) -> Tuple[int, int]:
        """
        Calculate optimal grid dimensions for a given number of items.

        Args:
            num_items: Total number of items
            preferred_columns: Preferred number of columns

        Returns:
            Tuple of (columns, rows)
        """
        columns = min(preferred_columns, num_items)
        rows = (num_items + columns - 1) // columns
        return columns, rows

    @staticmethod
    def center_content(container_width: int, content_width: int) -> int:
        """
        Calculate X position to center content in container.

        Args:
            container_width: Width of container
            content_width: Width of content to center

        Returns:
            X position for centered content
        """
        return (container_width - content_width) // 2

    @staticmethod
    def align_right(container_width: int, content_width: int, margin: int = 0) -> int:
        """
        Calculate X position to right-align content in container.

        Args:
            container_width: Width of container
            content_width: Width of content to align
            margin: Right margin

        Returns:
            X position for right-aligned content
        """
        return container_width - content_width - margin

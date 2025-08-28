"""
KPI Layout Systems for EZ Pillow Dashboard Components.

This module provides flexible layout options for displaying KPI cards with
different arrangements: grid, priority-based, responsive, and custom layouts.
"""

from PIL import ImageDraw
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from .config import COLORS, FONTS, DIMENSIONS
from .cards import KPICard
from .primitives import calculate_layout_positions


class KPILayoutType(Enum):
    """Available KPI layout types."""
    HORIZONTAL = "horizontal"        # Standard horizontal row
    GRID_2x3 = "grid_2x3"          # 2 rows, 3 columns
    GRID_3x2 = "grid_3x2"          # 3 rows, 2 columns
    PRIORITY = "priority"           # Larger first card, smaller others
    PYRAMID = "pyramid"             # Pyramid arrangement
    FEATURED = "featured"           # One large featured + others small
    RESPONSIVE = "responsive"       # Auto-adapt based on count
    CUSTOM = "custom"               # Custom positioning


class KPILayoutManager:
    """
    Manager for different KPI card layout arrangements.

    Provides multiple layout strategies to organize KPIs based on importance,
    screen space, and visual hierarchy needs.
    """

    def __init__(self, canvas_width: int = DIMENSIONS.WIDTH, padding: int = DIMENSIONS.PADDING):
        """Initialize layout manager."""
        self.canvas_width = canvas_width
        self.padding = padding
        self.content_width = canvas_width - 2 * padding

    def render_horizontal_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                                y_position: int) -> int:
        """Standard horizontal layout - all cards same size in a row."""
        if not kpi_cards:
            return y_position

        gap = DIMENSIONS.GAP_MEDIUM
        card_width = (self.content_width - (len(kpi_cards) - 1) * gap) // len(kpi_cards)

        positions = calculate_layout_positions(
            self.content_width, self.padding, len(kpi_cards), card_width, gap
        )

        for card, x_pos in zip(kpi_cards, positions):
            card.render(draw, x_pos, y_position, card_width)

        return y_position + DIMENSIONS.KPI_CARD_HEIGHT + DIMENSIONS.GAP_LARGE

    def render_grid_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                          y_position: int, rows: int, cols: int) -> int:
        """Grid layout - arrange cards in specified rows and columns."""
        if not kpi_cards:
            return y_position

        gap = DIMENSIONS.GAP_MEDIUM
        card_width = (self.content_width - (cols - 1) * gap) // cols
        card_height = DIMENSIONS.KPI_CARD_HEIGHT

        current_y = y_position
        cards_per_row = cols

        for row in range(rows):
            if row * cards_per_row >= len(kpi_cards):
                break

            row_cards = kpi_cards[row * cards_per_row:(row + 1) * cards_per_row]

            positions = calculate_layout_positions(
                self.content_width, self.padding, len(row_cards), card_width, gap
            )

            for card, x_pos in zip(row_cards, positions):
                card.render(draw, x_pos, current_y, card_width)

            current_y += card_height + gap

        return current_y + DIMENSIONS.GAP_LARGE - gap

    def render_priority_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                             y_position: int) -> int:
        """Priority layout - first card larger, others smaller."""
        if not kpi_cards:
            return y_position

        if len(kpi_cards) == 1:
            return self.render_horizontal_layout(draw, kpi_cards, y_position)

        gap = DIMENSIONS.GAP_MEDIUM

        # First card gets 40% of width, others share remaining 60%
        featured_width = int(self.content_width * 0.4)
        remaining_width = self.content_width - featured_width - gap
        other_width = (remaining_width - (len(kpi_cards) - 2) * gap) // (len(kpi_cards) - 1)

        # Render featured card (first one)
        kpi_cards[0].render(draw, self.padding, y_position, featured_width)

        # Render other cards
        current_x = self.padding + featured_width + gap
        for card in kpi_cards[1:]:
            card.render(draw, current_x, y_position, other_width)
            current_x += other_width + gap

        return y_position + DIMENSIONS.KPI_CARD_HEIGHT + DIMENSIONS.GAP_LARGE

    def render_pyramid_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                            y_position: int) -> int:
        """Pyramid layout - arrange cards in pyramid shape."""
        if not kpi_cards:
            return y_position

        gap = DIMENSIONS.GAP_MEDIUM
        card_height = DIMENSIONS.KPI_CARD_HEIGHT
        current_y = y_position

        if len(kpi_cards) <= 3:
            # Single row for 3 or fewer cards
            return self.render_horizontal_layout(draw, kpi_cards, y_position)

        elif len(kpi_cards) <= 6:
            # 2 rows: 2 on top, rest on bottom
            top_count = 2
            bottom_count = len(kpi_cards) - top_count

            # Top row (2 cards, centered)
            top_cards = kpi_cards[:top_count]
            top_width = (self.content_width - gap) // 2
            top_start_x = self.padding + (self.content_width - (2 * top_width + gap)) // 2

            for i, card in enumerate(top_cards):
                x_pos = top_start_x + i * (top_width + gap)
                card.render(draw, x_pos, current_y, top_width)

            current_y += card_height + gap

            # Bottom row
            bottom_cards = kpi_cards[top_count:]
            bottom_width = (self.content_width - (bottom_count - 1) * gap) // bottom_count
            bottom_positions = calculate_layout_positions(
                self.content_width, self.padding, bottom_count, bottom_width, gap
            )

            for card, x_pos in zip(bottom_cards, bottom_positions):
                card.render(draw, x_pos, current_y, bottom_width)

            current_y += card_height

        else:
            # 3 rows: 1, 2, rest
            # Top row (1 card, centered)
            top_card = kpi_cards[0]
            top_width = int(self.content_width * 0.3)
            top_x = self.padding + (self.content_width - top_width) // 2
            top_card.render(draw, top_x, current_y, top_width)

            current_y += card_height + gap

            # Middle row (2 cards)
            middle_cards = kpi_cards[1:3]
            middle_width = (self.content_width - gap) // 2
            for i, card in enumerate(middle_cards):
                x_pos = self.padding + i * (middle_width + gap)
                card.render(draw, x_pos, current_y, middle_width)

            current_y += card_height + gap

            # Bottom row (remaining cards)
            bottom_cards = kpi_cards[3:]
            if bottom_cards:
                bottom_width = (self.content_width - (len(bottom_cards) - 1) * gap) // len(bottom_cards)
                bottom_positions = calculate_layout_positions(
                    self.content_width, self.padding, len(bottom_cards), bottom_width, gap
                )

                for card, x_pos in zip(bottom_cards, bottom_positions):
                    card.render(draw, x_pos, current_y, bottom_width)

                current_y += card_height

        return current_y + DIMENSIONS.GAP_LARGE

    def render_featured_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                             y_position: int) -> int:
        """Featured layout - one large card on left, others stacked on right."""
        if not kpi_cards:
            return y_position

        if len(kpi_cards) == 1:
            return self.render_horizontal_layout(draw, kpi_cards, y_position)

        gap = DIMENSIONS.GAP_MEDIUM

        # Featured card gets 50% width, others share the remaining 50%
        featured_width = int(self.content_width * 0.5)
        others_width = self.content_width - featured_width - gap

        # Calculate height for other cards
        other_card_height = DIMENSIONS.KPI_CARD_HEIGHT
        if len(kpi_cards) > 2:
            available_height = DIMENSIONS.KPI_CARD_HEIGHT
            other_card_height = (available_height - (len(kpi_cards) - 2) * gap) // (len(kpi_cards) - 1)
            other_card_height = max(other_card_height, 80)  # Minimum height

        # Render featured card (first one)
        kpi_cards[0].render(draw, self.padding, y_position, featured_width)

        # Render other cards vertically stacked
        others_x = self.padding + featured_width + gap
        current_y = y_position

        for card in kpi_cards[1:]:
            card.render(draw, others_x, current_y, others_width)
            current_y += other_card_height + gap

        return y_position + DIMENSIONS.KPI_CARD_HEIGHT + DIMENSIONS.GAP_LARGE

    def render_responsive_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                               y_position: int) -> int:
        """Responsive layout - automatically choose best layout based on card count."""
        count = len(kpi_cards)

        if count <= 0:
            return y_position
        elif count <= 4:
            return self.render_horizontal_layout(draw, kpi_cards, y_position)
        elif count == 5:
            return self.render_priority_layout(draw, kpi_cards, y_position)
        elif count == 6:
            return self.render_grid_layout(draw, kpi_cards, y_position, 2, 3)
        elif count <= 8:
            return self.render_grid_layout(draw, kpi_cards, y_position, 2, 4)
        else:
            return self.render_pyramid_layout(draw, kpi_cards, y_position)

    def render_custom_layout(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                           y_position: int, layout_config: Dict[str, Any]) -> int:
        """Custom layout based on provided configuration."""
        if not kpi_cards or not layout_config:
            return self.render_horizontal_layout(draw, kpi_cards, y_position)

        positions = layout_config.get('positions', [])
        if len(positions) < len(kpi_cards):
            # Fallback to horizontal if not enough positions defined
            return self.render_horizontal_layout(draw, kpi_cards, y_position)

        max_y = y_position

        for i, card in enumerate(kpi_cards):
            if i < len(positions):
                pos_config = positions[i]
                x = self.padding + pos_config.get('x', 0)
                y = y_position + pos_config.get('y', 0)
                width = pos_config.get('width', 200)

                card.render(draw, x, y, width)
                max_y = max(max_y, y + DIMENSIONS.KPI_CARD_HEIGHT)

        return max_y + DIMENSIONS.GAP_LARGE

    def render_kpis(self, draw: ImageDraw.ImageDraw, kpi_cards: List[KPICard],
                   y_position: int, layout_type: KPILayoutType = KPILayoutType.HORIZONTAL,
                   layout_config: Optional[Dict[str, Any]] = None) -> int:
        """
        Main method to render KPIs with specified layout type.

        Args:
            draw: PIL ImageDraw object
            kpi_cards: List of KPI cards to render
            y_position: Starting Y position
            layout_type: Type of layout to use
            layout_config: Additional configuration for custom layouts

        Returns:
            Y position after rendering all KPIs
        """
        if layout_type == KPILayoutType.HORIZONTAL:
            return self.render_horizontal_layout(draw, kpi_cards, y_position)
        elif layout_type == KPILayoutType.GRID_2x3:
            return self.render_grid_layout(draw, kpi_cards, y_position, 2, 3)
        elif layout_type == KPILayoutType.GRID_3x2:
            return self.render_grid_layout(draw, kpi_cards, y_position, 3, 2)
        elif layout_type == KPILayoutType.PRIORITY:
            return self.render_priority_layout(draw, kpi_cards, y_position)
        elif layout_type == KPILayoutType.PYRAMID:
            return self.render_pyramid_layout(draw, kpi_cards, y_position)
        elif layout_type == KPILayoutType.FEATURED:
            return self.render_featured_layout(draw, kpi_cards, y_position)
        elif layout_type == KPILayoutType.RESPONSIVE:
            return self.render_responsive_layout(draw, kpi_cards, y_position)
        elif layout_type == KPILayoutType.CUSTOM:
            return self.render_custom_layout(draw, kpi_cards, y_position, layout_config or {})
        else:
            return self.render_horizontal_layout(draw, kpi_cards, y_position)


def create_kpi_layout_manager(canvas_width: int = DIMENSIONS.WIDTH,
                            padding: int = DIMENSIONS.PADDING) -> KPILayoutManager:
    """Factory function to create a KPI layout manager."""
    return KPILayoutManager(canvas_width, padding)


def suggest_layout_for_count(kpi_count: int) -> KPILayoutType:
    """Suggest the best layout type based on KPI count."""
    if kpi_count <= 0:
        return KPILayoutType.HORIZONTAL
    elif kpi_count <= 4:
        return KPILayoutType.HORIZONTAL
    elif kpi_count == 5:
        return KPILayoutType.PRIORITY
    elif kpi_count == 6:
        return KPILayoutType.GRID_2x3
    elif kpi_count <= 8:
        return KPILayoutType.GRID_3x2
    else:
        return KPILayoutType.PYRAMID


def create_custom_layout_config(positions: List[Dict[str, int]]) -> Dict[str, Any]:
    """
    Helper to create custom layout configuration.

    Args:
        positions: List of position dictionaries with 'x', 'y', 'width' keys

    Returns:
        Configuration dictionary for custom layout

    Example:
        config = create_custom_layout_config([
            {'x': 0, 'y': 0, 'width': 300},
            {'x': 350, 'y': 0, 'width': 300},
            {'x': 175, 'y': 180, 'width': 300}
        ])
    """
    return {'positions': positions}

"""
Card components for quadre (Not A Dashboard App).

This module contains card-based UI components including KPI cards and section cards.
All cards follow consistent styling patterns and can be easily customized.
"""

from PIL import ImageDraw
from typing import Dict, Optional, Any
from .config import COLORS, FONTS, DIMENSIONS, px
from .primitives import rounded_rectangle, badge, get_delta_display_info


class KPICard:
    """
    A Key Performance Indicator card component.

    Displays a title, value, and optional delta information in a styled card format.
    """

    def __init__(self, title: str, value: str, delta: Optional[Dict[str, Any]] = None):
        """
        Initialize KPI card.

        Args:
            title: Card title/label
            value: Main value to display
            delta: Optional delta information with 'pct' and 'from' keys
        """
        self.title = title
        self.value = value
        self.delta = delta
        self.width = 0
        self.height = DIMENSIONS.KPI_CARD_HEIGHT

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> None:
        """
        Render the KPI card at the specified position.

        Args:
            draw: PIL ImageDraw object
            x: X position
            y: Y position
            width: Card width
        """
        self.width = width

        # Draw card background
        # Inset bottom/right by 1px to avoid clipping the stroke when the
        # widget is rendered inside a tightly clipped layer.
        x2 = x + max(0, width - 1)
        y2 = y + max(0, self.height - 1)
        rounded_rectangle(
            draw,
            (x, y, x2, y2),
            DIMENSIONS.CARD_RADIUS,
            fill=COLORS.CARD_BACKGROUND,
            outline=COLORS.BORDER,
            width=1,
        )

        # Available width for content (minus padding)
        pad = px(20)
        content_width = width - 2 * pad

        # Draw title with text wrapping if needed
        title_x = x + pad
        title_y = y + px(16)
        title_text = self._truncate_text(self.title, FONTS.SMALL, content_width)
        draw.text(
            (title_x, title_y),
            title_text,
            font=FONTS.SMALL,
            fill=COLORS.MUTED_FOREGROUND,
        )

        # Draw value with text wrapping if needed
        value_x = x + pad
        value_y = y + px(50)
        value_text = self._truncate_text(self.value, FONTS.NUMBER, content_width)
        draw.text(
            (value_x, value_y), value_text, font=FONTS.NUMBER, fill=COLORS.FOREGROUND
        )

        # Draw delta badge if present
        if self.delta:
            # Support both percentage delta and optional absolute "vs" value.
            has_pct = "pct" in self.delta and self.delta.get("pct") is not None
            vs_value = self.delta.get("vs")
            from_label = self.delta.get("from")

            text_parts = []
            variant = "secondary"
            if has_pct:
                pct = float(self.delta.get("pct", 0) or 0)
                icon, _, _ = get_delta_display_info(pct)
                text_parts.append(
                    f"{icon} {abs(int(pct) if pct.is_integer() else pct)}%"
                )
                variant = (
                    "success"
                    if pct > 0
                    else ("destructive" if pct < 0 else "secondary")
                )

            # Prefer explicit vs absolute value over from-label if provided
            if vs_value is not None and str(vs_value) != "":
                text_parts.append(f"vs {vs_value}")
            elif from_label:
                text_parts.append(f"vs {from_label}")

            if text_parts:
                delta_text = " ".join(text_parts)
                badge_x = x + pad
                badge_y = y + px(105)
                badge(draw, (badge_x, badge_y), delta_text, variant=variant)

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


class SectionCard:
    """
    A section card component for displaying metrics in dashboard sections.

    Similar to KPI cards but with different proportions and styling for use
    in the middle and bottom sections of the dashboard.
    """

    def __init__(self, title: str, value: str, delta: Optional[Dict[str, Any]] = None):
        """
        Initialize section card.

        Args:
            title: Card title/label
            value: Main value to display
            delta: Optional delta information with 'pct' and 'from' keys
        """
        self.title = title
        self.value = value
        self.delta = delta
        self.width = 0
        self.height = 0

    def render(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int
    ) -> None:
        """
        Render the section card at the specified position.

        Args:
            draw: PIL ImageDraw object
            x: X position
            y: Y position
            width: Card width
            height: Card height
        """
        self.width = width
        self.height = height

        # Draw card background
        x2 = x + max(0, width - 1)
        y2 = y + max(0, height - 1)
        rounded_rectangle(
            draw,
            (x, y, x2, y2),
            DIMENSIONS.CARD_RADIUS,
            fill=COLORS.CARD_BACKGROUND,
            outline=COLORS.BORDER,
            width=1,
        )

        # Draw title
        pad = px(20)
        title_x = x + pad
        title_y = y + px(16)
        draw.text(
            (title_x, title_y),
            self.title,
            font=FONTS.SMALL,
            fill=COLORS.MUTED_FOREGROUND,
        )

        # Draw value
        value_x = x + pad
        value_y = y + px(50)
        draw.text(
            (value_x, value_y), self.value, font=FONTS.NUMBER, fill=COLORS.FOREGROUND
        )

        # Draw delta text if present (not as badge for section cards)
        if self.delta:
            has_pct = "pct" in self.delta and self.delta.get("pct") is not None
            vs_value = self.delta.get("vs")
            from_label = self.delta.get("from")

            text_parts = []
            color = COLORS.MUTED_FOREGROUND
            if has_pct:
                pct = float(self.delta.get("pct", 0) or 0)
                icon, color, _ = get_delta_display_info(pct)
                text_parts.append(
                    f"{icon} {abs(int(pct) if pct.is_integer() else pct)}%"
                )

            if vs_value is not None and str(vs_value) != "":
                text_parts.append(f"vs {vs_value}")
            elif from_label:
                text_parts.append(f"vs {from_label}")

            if text_parts:
                delta_text = " ".join(text_parts)
                delta_x = x + pad
                delta_y = y + height - px(35)
                draw.text((delta_x, delta_y), delta_text, font=FONTS.SMALL, fill=color)

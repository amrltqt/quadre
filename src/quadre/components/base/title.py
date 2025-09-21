import logging
from typing import Literal, Tuple

from quadre.cairo_canvas import CairoCanvas
from quadre.components.registry import Component, component
from quadre.components.text_utils import truncate_text
from quadre.config import COLORS, FONTS, px

logger = logging.getLogger(__name__)

@component("title")
class Title(Component):
    """
    Title component for displaying headings of various sizes.
    """

    type: Literal["title"] = "title"
    text: str = ""
    size: Literal["h1", "h2", "h3", "h4", "body"] = "h1"
    color: str | Tuple[int, int, int] | None = None
    align: Literal["left", "center", "right"] = "left"
    weight: Literal["normal", "bold"] | None = None

    def _get_font_spec(self):
        """Get the appropriate font spec based on size and weight."""
        # Map size to font specs
        size_map = {
            "h1": FONTS.H1,
            "h2": FONTS.H2,
            "h3": FONTS.H3,
            "h4": FONTS.H4,
            "body": FONTS.BODY
        }

        font_spec = size_map.get(self.size, FONTS.H1)

        # Override weight if specified
        if self.weight:
            from quadre.font import FontSpec
            font_spec = FontSpec(font_spec.family, font_spec.size, self.weight)

        return font_spec

    def _get_color(self):
        """Get the color for the title."""
        if self.color:
            if isinstance(self.color, str):
                # Handle hex colors or named colors
                if self.color.startswith("#"):
                    return self.color
                # Try to get from COLORS class
                return getattr(COLORS, self.color.upper(), COLORS.FOREGROUND)
            else:
                # Assume it's a tuple (r, g, b)
                return self.color
        return COLORS.FOREGROUND

    def measure(self, canvas: CairoCanvas, avail_w: int, avail_h: int) -> Tuple[int, int]:
        """Calculate the preferred size of the title."""
        if not self.text.strip():
            return (0, 0)

        font_spec = self._get_font_spec()
        text_w, text_h = canvas.measure_text(self.text.strip(), font_spec)

        # Add some vertical padding for better spacing
        padding_v = px(8)

        width = min(text_w, avail_w) if avail_w > 0 else text_w
        height = min(text_h + 2 * padding_v, avail_h) if avail_h > 0 else text_h + 2 * padding_v

        logger.debug(f"Title measured", extra={
            "text": self.text[:50] + "..." if len(self.text) > 50 else self.text,
            "size": self.size,
            "font_size": font_spec.size,
            "result_size": f"{width}x{height}"
        })

        return (width, height)



    def render(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        """Render the title."""
        if w <= 0 or h <= 0:
            logger.debug(f"Title render skipped due to invalid dimensions: {w}x{h}")
            return

        text = self.text.strip()
        if not text:
            return

        font_spec = self._get_font_spec()
        color = self._get_color()
        padding_v = px(8)

        # Calculate available width for text (accounting for padding)
        available_w = max(0, w)

        # Truncate text if it doesn't fit
        truncated_text = truncate_text(canvas, text, font_spec, available_w)

        # Measure truncated text for positioning
        text_w, text_h = canvas.measure_text(truncated_text, font_spec)

        # Calculate x position based on alignment
        if self.align == "center":
            text_x = x + max(0, (w - text_w) // 2)
        elif self.align == "right":
            text_x = x + max(0, w - text_w)
        else:  # left
            text_x = x

        # Center vertically with padding
        text_y = y + padding_v

        # Ensure positioning is within bounds
        text_x = max(x, min(text_x, x + w - text_w)) if text_w <= w else x
        available_h = h - 2 * padding_v
        if text_h <= available_h:
            text_y = y + padding_v
        else:
            text_y = max(y, y + (h - text_h) // 2)

        canvas.draw_text(truncated_text, text_x, text_y, font_spec, color)

        logger.debug(f"Title rendered", extra={
            "original_text": text[:30] + "..." if len(text) > 30 else text,
            "rendered_text": truncated_text[:30] + "..." if len(truncated_text) > 30 else truncated_text,
            "truncated": len(truncated_text) < len(text),
            "position": f"{text_x},{text_y}",
            "size": self.size,
            "align": self.align
        })

    def resolve(self, data):
        """Resolve dynamic data if needed."""
        pass

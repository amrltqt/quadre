import logging

from typing import Any, Literal, Tuple

from quadre.cairo_canvas import CairoCanvas
from quadre.components.primitives import rounded_rectangle
from quadre.components.registry import Component, component
from quadre.components.text_utils import truncate_text
from quadre.config import COLORS, DIMENSIONS, FONTS, px

logger = logging.getLogger(__name__)

@component("card")
class Card(Component):
    type: Literal["card"] = "card"
    value: str = ""

    def measure(self, canvas: CairoCanvas, avail_w: int, avail_h: int) -> Tuple[int, int]:
        return (avail_w, min(DIMENSIONS.KPI_CARD_HEIGHT, avail_h))



    def render(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        if w <= 0 or h <= 0:
            return
        layer = canvas.new_layer(w, h)
        self._render_contents(layer, 0, 0, w, h)
        canvas.composite_layer(layer, x, y)

    def _render_contents(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        rounded_rectangle(
            canvas,
            (x, y, x + w - 1, y + h - 1),
            DIMENSIONS.CARD_RADIUS,
            fill=COLORS.CARD_BACKGROUND,
            outline=COLORS.BORDER,
            width=1,
        )

        pad = px(20)
        value_x = x + pad
        value_y = y + pad
        value_text = self.value.strip()

        # Calculate available width for text
        available_w = max(0, w - 2 * pad)

        # Truncate text if needed
        truncated_text = truncate_text(canvas, value_text, FONTS.SMALL, available_w)

        text_size = canvas.measure_text(truncated_text, FONTS.SMALL)
        canvas.draw_text(truncated_text, value_x, value_y, FONTS.SMALL, COLORS.PRIMARY)

        logger.debug(
            "Draw text in card",
            extra={
                "original_value": value_text[:50] + "..." if len(value_text) > 50 else value_text,
                "rendered_value": truncated_text[:50] + "..." if len(truncated_text) > 50 else truncated_text,
                "truncated": len(truncated_text) < len(value_text),
                "size": text_size,
                "card_type": self.type,
            },
        )

    def resolve(self, data: Any):
        pass

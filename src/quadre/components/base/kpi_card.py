from __future__ import annotations

import logging
from typing import Any, Literal, Optional, Tuple

from quadre.cairo_canvas import CairoCanvas
from quadre.components.primitives import rounded_rectangle
from quadre.components.registry import Component, component
from quadre.components.text_utils import truncate_text
from quadre.config import COLORS, DIMENSIONS, FONTS, px


logger = logging.getLogger(__name__)


@component("kpi_card")
class KPICard(Component):
    type: Literal["kpi_card"] = "kpi_card"

    label: str = ""
    value: str = ""
    delta: Optional[float] = None
    delta_label: Optional[str] = None
    align: Literal["left", "center", "right"] = "left"
    bg_fill: Optional[str | Tuple[int, int, int]] = None
    bg_outline: Optional[str | Tuple[int, int, int]] = None



    def measure(self, canvas: CairoCanvas, avail_w: int, avail_h: int) -> Tuple[int, int]:
        pad = px(24)
        gap = px(12)

        label_text = self.label.upper().strip()
        label_w, label_h = canvas.measure_text(label_text, FONTS.SMALL) if label_text else (0, 0)

        value_text = self.value.strip()
        value_w, value_h = canvas.measure_text(value_text, FONTS.NUMBER)

        delta_text = self._formatted_delta()
        delta_w, delta_h = canvas.measure_text(delta_text, FONTS.SMALL) if delta_text else (0, 0)

        total_h = pad
        if label_h:
            total_h += label_h + gap
        total_h += value_h
        if delta_h:
            total_h += gap + delta_h
        total_h += pad

        preferred_w = max(label_w, value_w, delta_w) + 2 * pad

        width = max(0, avail_w)
        if avail_w < 0:
            width = preferred_w
        height = min(total_h, avail_h) if avail_h >= 0 else total_h

        return width, height

    def render(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        if w <= 0 or h <= 0:
            return

        layer = canvas.new_layer(w, h)

        fill_color = self.bg_fill or COLORS.SECONDARY
        outline_color = self.bg_outline or COLORS.BORDER_LIGHT

        rounded_rectangle(
            layer,
            (0, 0, w - 1, h - 1),
            DIMENSIONS.CARD_RADIUS,
            fill=fill_color,
            outline=outline_color,
            width=1,
        )

        pad = px(24)
        gap = px(12)
        cursor_y = pad
        content_width = max(0, w - 2 * pad)

        def _x_for(text_width: int) -> float:
            if self.align == "center":
                return pad + max(0, (content_width - text_width) / 2)
            if self.align == "right":
                return pad + max(0, content_width - text_width)
            return pad

        label_text = self.label.upper().strip()
        if label_text:
            label_color = COLORS.MUTED_FOREGROUND
            # Truncate label if needed
            truncated_label = truncate_text(layer, label_text, FONTS.SMALL, content_width)
            label_w, label_h = layer.measure_text(truncated_label, FONTS.SMALL)
            layer.draw_text(truncated_label, _x_for(label_w), cursor_y, FONTS.SMALL, label_color)
            cursor_y += label_h + gap

        value_text = self.value.strip()
        # Truncate value if needed
        truncated_value = truncate_text(layer, value_text, FONTS.NUMBER, content_width)
        value_w, value_h = layer.measure_text(truncated_value, FONTS.NUMBER)
        layer.draw_text(truncated_value, _x_for(value_w), cursor_y, FONTS.NUMBER, COLORS.FOREGROUND)
        cursor_y += value_h

        delta_text = self._formatted_delta()
        if delta_text:
            delta_color = self._delta_color()
            cursor_y += gap
            # Truncate delta text if needed
            truncated_delta = truncate_text(layer, delta_text, FONTS.SMALL, content_width)
            delta_w, delta_h = layer.measure_text(truncated_delta, FONTS.SMALL)
            layer.draw_text(truncated_delta, _x_for(delta_w), cursor_y, FONTS.SMALL, delta_color)

        canvas.composite_layer(layer, x, y)

        logger.debug(
            "Rendered KPI card",
            extra={
                "label": self.label,
                "value": self.value,
                "delta": self.delta,
                "content_width": content_width,
            },
        )

    def _formatted_delta(self) -> str:
        pieces: list[str] = []
        if self.delta is not None:
            symbol = "+" if self.delta > 0 else "-" if self.delta < 0 else "="
            pct = abs(self.delta)
            pieces.append(f"{symbol}{pct:.1f}%")
        if self.delta_label:
            pieces.append(self.delta_label)
        return " ".join(pieces)

    def _delta_color(self) -> Tuple[int, int, int] | str:
        if self.delta is None:
            return COLORS.MUTED_FOREGROUND
        if self.delta > 0:
            return COLORS.SUCCESS
        if self.delta < 0:
            return COLORS.DESTRUCTIVE
        return COLORS.MUTED_FOREGROUND

    def resolve(self, data: Any):
        pass

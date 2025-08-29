from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union

from PIL import ImageDraw, ImageFont

from .config import COLORS, FONTS
from ..flex.defaults import parse_color


def _co(value, default=None):
    c = parse_color(value)
    return c if c is not None else (value if value is not None else default)


@dataclass
class ProgressBar:
    value: float  # 0..1
    label: str | None = None
    bar_height: int = 18
    bg_fill: Union[str, Tuple[int, int, int]] = COLORS.MUTED
    fill: Union[str, Tuple[int, int, int]] = COLORS.SUCCESS
    font: ImageFont.ImageFont = FONTS.SMALL

    def measure(self, w: int, h: int) -> Tuple[int, int]:
        hh = self.bar_height
        if self.label:
            hh += self.font.size + 6
        return (w, min(h, hh))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        # Draw optional label
        top = y
        if self.label:
            draw.text((x, top), self.label, font=self.font, fill=COLORS.MUTED_FOREGROUND)
            top += self.font.size + 4

        # Track
        radius = min(6, self.bar_height // 2)
        track_y2 = top + self.bar_height
        draw.rounded_rectangle((x, top, x + w, track_y2), radius, fill=_co(self.bg_fill, COLORS.MUTED))

        # Value
        v = max(0.0, min(1.0, float(self.value)))
        val_w = int(w * v)
        if val_w > 0:
            draw.rounded_rectangle((x, top, x + val_w, track_y2), radius, fill=_co(self.fill, COLORS.SUCCESS))


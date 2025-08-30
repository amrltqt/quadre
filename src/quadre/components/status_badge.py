from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from PIL import ImageDraw

from .config import FONTS, px
from .primitives import badge


@dataclass
class StatusBadge:
    text: str
    variant: str = "secondary"  # default|secondary|destructive|success|warning|outline

    def measure(self) -> Tuple[int, int]:
        padx, pady = px(12), px(6)
        w = int(FONTS.SMALL.getlength(self.text)) + 2 * padx
        h = FONTS.SMALL.size + 2 * pady
        return (w, h)

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int) -> Tuple[int, int]:
        badge(draw, (x, y), self.text, variant=self.variant, font=FONTS.SMALL)
        return self.measure()

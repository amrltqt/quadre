from __future__ import annotations

from PIL import Image, ImageDraw

from quadre.flex.engine import Widget, FlexContainer
from quadre.components import COLORS


class LeftRed(Widget):
    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int):
        return (80, 40)

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
        # Fill exactly within assigned box
        draw.rectangle((x, y, x + w, y + h), fill=(255, 0, 0))


class RightGreenOverdraw(Widget):
    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int):
        return (80, 40)

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int):
        # Intentional overdraw 30px to the left beyond assigned box
        draw.rectangle((x - 30, y, x + w, y + h), fill=(0, 255, 0))


def test_row_children_are_clipped_to_bounds():
    cont = FlexContainer(direction="row", gap=0, padding=0, align_items="stretch")
    cont.add(LeftRed())
    cont.add(RightGreenOverdraw())

    W, H = 200, 50
    img = Image.new("RGB", (W, H), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)
    # Enable per-child clipping via the backing image handle
    setattr(draw, "_quadre_image", img)

    cont.render(draw, 0, 0, W, H)

    mid_y = H // 2

    # Near the right edge of the first child's box: should remain red (no green bleed)
    px1 = 80 - 5
    r1, g1, b1 = img.getpixel((px1, mid_y))
    assert r1 > 200 and g1 < 50, "expected red near first child's edge without bleed"

    # Inside the second child's box: should be green
    px2 = 80 + 5
    r2, g2, b2 = img.getpixel((px2, mid_y))
    assert g2 > 200 and r2 < 50, "expected green inside second child's area"


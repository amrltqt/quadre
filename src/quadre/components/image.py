from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from .config import COLORS, FONTS


@dataclass
class ImageBlock:
    """
    Basic image component that draws an image into a rectangle.
    """

    src: str
    fit: str = "contain"  # contain|cover
    radius: int = 0
    opacity: float = 1.0
    align: str = "center"  # left|center|right

    def _open(self) -> Optional[Image.Image]:
        try:
            im = Image.open(self.src)
            return im.convert("RGBA")
        except Exception:
            return None

    def _scale(self, iw: int, ih: int, avail_w: int, avail_h: int) -> Tuple[int, int]:
        if iw <= 0 or ih <= 0 or avail_w <= 0 or avail_h <= 0:
            return (0, 0)
        if self.fit == "cover":
            scale = max(avail_w / iw, avail_h / ih)
        else:  # contain
            scale = min(avail_w / iw, avail_h / ih)
        return (max(1, int(iw * scale)), max(1, int(ih * scale)))

    def measure(self, w: int, h: int) -> Tuple[int, int]:
        im = self._open()
        if not im:
            return (w, min(h, 0))
        tw, th = self._scale(im.width, im.height, w, h)
        return (min(w, tw), min(h, th))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        base_img: Optional[Image.Image] = getattr(draw, "_quadre_image", None)
        im = self._open()
        if not im or base_img is None:
            # Fallback placeholder
            r = min(self.radius, min(w, h) // 2)
            draw.rounded_rectangle(
                (x, y, x + w, y + h), r, outline=COLORS.BORDER, width=1
            )
            msg = "[image]"
            tx = x + (w - int(FONTS.SMALL.getlength(msg))) // 2
            ty = y + (h - FONTS.SMALL.size) // 2
            draw.text((tx, ty), msg, font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)
            return

        tw, th = self._scale(im.width, im.height, w, h)
        if tw <= 0 or th <= 0:
            return
        resized = im.resize((tw, th), Image.LANCZOS)

        # Apply opacity if needed
        if self.opacity < 1.0:
            alpha = resized.split()[3]
            alpha = alpha.point(lambda a: int(a * max(0.0, min(1.0, self.opacity))))
            resized.putalpha(alpha)

        # Positioning within box based on align
        if self.align == "left":
            px = x
        elif self.align == "right":
            px = x + (w - tw)
        else:
            px = x + (w - tw) // 2
        py = y + (h - th) // 2

        if self.radius and self.radius > 0:
            # Create a mask with rounded corners
            mask = Image.new("L", (tw, th), 0)
            mdraw = ImageDraw.Draw(mask)
            r = min(self.radius, min(tw, th) // 2)
            mdraw.rounded_rectangle((0, 0, tw, th), r, fill=255)
            if resized.mode != "RGBA":
                resized = resized.convert("RGBA")
            base_img.paste(resized, (px, py), mask)
        else:
            if resized.mode == "RGBA":
                base_img.paste(resized, (px, py), resized)
            else:
                base_img.paste(resized, (px, py))

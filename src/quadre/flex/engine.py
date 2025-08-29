"""
Data binding utilities are provided by quadre.utils.dataref.
resolve_path is re-imported here for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from quadre.components.config import load_emoji_font, load_cjk_font


class Widget:
    """Base widget interface for the flex engine."""

    def measure(
        self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int
    ) -> Tuple[int, int]:
        """Return intrinsic width, height needed (preferred size)."""
        return (0, 0)

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        """Render into the given box (x,y,w,h)."""
        raise NotImplementedError


@dataclass
class FixedBox(Widget):
    width: int
    height: int
    fill: Tuple[int, int, int] = (230, 230, 230)
    outline: Tuple[int, int, int] = (180, 180, 180)
    radius: int = 8

    def measure(
        self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int
    ) -> Tuple[int, int]:
        return (min(self.width, avail_w), min(self.height, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        r = min(self.radius, min(w, h) // 2)
        draw.rounded_rectangle(
            (x, y, x + w, y + h), r, fill=self.fill, outline=self.outline
        )


@dataclass
class TextWidget(Widget):
    text: str
    fill: Tuple[int, int, int] = (20, 20, 20)
    font: Optional[ImageFont.ImageFont] = None
    align: str = "left"  # left|center|right

    def _font(self) -> ImageFont.ImageFont:
        if self.font:
            return self.font
        # fallback default font
        return ImageFont.load_default()

    def _emoji_font(self) -> ImageFont.ImageFont:
        base = self._font()
        try:
            size = getattr(base, "size", 14) or 14
        except Exception:
            size = 14
        return load_emoji_font(size)

    def _cjk_font(self) -> ImageFont.ImageFont:
        base = self._font()
        try:
            size = getattr(base, "size", 14) or 14
        except Exception:
            size = 14
        return load_cjk_font(size)

    @staticmethod
    def _is_emoji(ch: str) -> bool:
        o = ord(ch)
        return (0x1F300 <= o <= 0x1FAFF) or (0x2700 <= o <= 0x27BF) or (o == 0xFE0F)

    @staticmethod
    def _is_cjk(ch: str) -> bool:
        o = ord(ch)
        return (
            0x4E00 <= o <= 0x9FFF  # CJK Unified Ideographs
            or 0x3400 <= o <= 0x4DBF  # CJK Unified Ideographs Extension A
            or 0xF900 <= o <= 0xFAFF  # CJK Compatibility Ideographs
        )

    def _segment_runs(self) -> List[Tuple[str, ImageFont.ImageFont]]:
        base = self._font()
        emoji = self._emoji_font()
        cjk = self._cjk_font()
        segments: List[Tuple[str, ImageFont.ImageFont]] = []
        buf: List[str] = []
        cur_font = base
        for ch in self.text:
            want = cjk if self._is_cjk(ch) else (emoji if self._is_emoji(ch) else base)
            if want is cur_font:
                buf.append(ch)
            else:
                if buf:
                    segments.append(("".join(buf), cur_font))
                    buf = []
                cur_font = want
                buf.append(ch)
        if buf:
            segments.append(("".join(buf), cur_font))
        return segments

    def measure(
        self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int
    ) -> Tuple[int, int]:
        runs = self._segment_runs()
        if runs:
            total_w = sum(int(f.getlength(s)) for s, f in runs)
            # height: approximate max of per-font line heights using textbbox on 'Ay'
            heights = []
            for _, f in runs:
                bb = draw.textbbox((0, 0), "Ay", font=f)
                heights.append(bb[3] - bb[1])
            h = max(heights) if heights else 0
            return (min(total_w, avail_w), min(h, avail_h))
        else:
            font = self._font()
            bbox = draw.textbbox((0, 0), self.text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            return (min(w, avail_w), min(h, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        runs = self._segment_runs()
        if not runs:
            font = self._font()
            bbox = draw.textbbox((0, 0), self.text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            if self.align == "center":
                tx = x + (w - tw) // 2
            elif self.align == "right":
                tx = x + w - tw
            else:
                tx = x
            ty = y + (h - th) // 2
            draw.text((tx, ty), self.text, fill=self.fill, font=font)
            return

        total_w = sum(int(f.getlength(s)) for s, f in runs)
        # Determine vertical placement using max height
        heights = []
        for _, f in runs:
            bb = draw.textbbox((0, 0), "Ay", font=f)
            heights.append(bb[3] - bb[1])
        th = max(heights) if heights else 0

        if self.align == "center":
            tx = x + (w - total_w) // 2
        elif self.align == "right":
            tx = x + w - total_w
        else:
            tx = x
        ty = y + (h - th) // 2

        cx = tx
        for seg, fnt in runs:
            draw.text((cx, ty), seg, fill=self.fill, font=fnt)
            cx += int(fnt.getlength(seg))


@dataclass
class FlexItem:
    widget: Widget
    grow: float = 0.0
    shrink: float = 1.0
    basis: Optional[int] = None  # pixels; if None, use intrinsic measure
    align_self: Optional[str] = None  # start|center|end|stretch


@dataclass
class FlexContainer(Widget):
    children: List[FlexItem] = field(default_factory=list)
    direction: str = "row"  # row|column
    gap: int = 10
    align_items: str = "stretch"  # start|center|end|stretch (cross axis)
    justify_content: str = (
        "start"  # start|center|end|space-between|space-around|space-evenly
    )
    padding: int = 0
    bg_fill: Optional[Tuple[int, int, int]] = None
    bg_outline: Optional[Tuple[int, int, int]] = None
    bg_radius: int = 12
    clip_children: bool = True

    def add(
        self,
        widget: Widget,
        *,
        grow: float = 0.0,
        shrink: float = 1.0,
        basis: Optional[int] = None,
        align_self: Optional[str] = None,
    ) -> "FlexContainer":
        self.children.append(FlexItem(widget, grow, shrink, basis, align_self))
        return self

    # Measure returns preferred size if unconstrained. For simplicity, sum of children along main axis.
    def measure(
        self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int
    ) -> Tuple[int, int]:
        inner_w = max(0, avail_w - 2 * self.padding)
        inner_h = max(0, avail_h - 2 * self.padding)

        main_sum = 0
        cross_max = 0
        is_row = self.direction == "row"

        for i, item in enumerate(self.children):
            mw, mh = item.widget.measure(draw, inner_w, inner_h)
            if is_row:
                base = item.basis if item.basis is not None else mw
                main_sum += base
                cross_max = max(cross_max, mh)
            else:
                base = item.basis if item.basis is not None else mh
                main_sum += base
                cross_max = max(cross_max, mw)

        if len(self.children) > 1:
            main_sum += (len(self.children) - 1) * self.gap

        preferred_w = (main_sum if is_row else cross_max) + 2 * self.padding
        preferred_h = (cross_max if is_row else main_sum) + 2 * self.padding
        return (min(preferred_w, avail_w), min(preferred_h, avail_h))

    def _layout(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int
    ) -> List[Tuple[int, int, int, int]]:
        # Compute layout rects for each child
        is_row = self.direction == "row"
        inner_x = x + self.padding
        inner_y = y + self.padding
        inner_w = max(0, w - 2 * self.padding)
        inner_h = max(0, h - 2 * self.padding)

        # 1) Determine base sizes
        bases: List[int] = []  # along main axis
        cross_sizes: List[int] = []
        for item in self.children:
            mw, mh = item.widget.measure(draw, inner_w, inner_h)
            if is_row:
                bases.append(item.basis if item.basis is not None else mw)
                cross_sizes.append(mh)
            else:
                bases.append(item.basis if item.basis is not None else mh)
                cross_sizes.append(mw)

        main_space = inner_w if is_row else inner_h
        total_gaps = self.gap * max(0, len(self.children) - 1)
        used = sum(bases) + total_gaps
        free = main_space - used

        # 2) Distribute free space (grow) or shrink if negative
        sizes = bases[:]
        if free > 0:
            grow_sum = sum(ci.grow for ci in self.children)
            if grow_sum > 0:
                for i, ci in enumerate(self.children):
                    sizes[i] += int(free * (ci.grow / grow_sum))
        elif free < 0:
            shrink_sum = sum(ci.shrink for ci in self.children)
            if shrink_sum > 0:
                deficit = -free
                for i, ci in enumerate(self.children):
                    sizes[i] -= int(deficit * (ci.shrink / shrink_sum))
                    sizes[i] = max(0, sizes[i])

        # 3) Compute positions along main axis
        rects: List[Tuple[int, int, int, int]] = []
        cur_main_base = inner_x if is_row else inner_y

        # Remaining space after sizes + default gaps
        actual_used = sum(sizes) + total_gaps
        remaining = max(0, main_space - actual_used)

        # Adjust start offset and inter-item gap according to justify_content
        gap_val = self.gap
        offset = 0
        n = len(self.children)
        if self.justify_content in ("center", "end") or (
            self.justify_content.startswith("space") and n > 1
        ):
            if self.justify_content == "center":
                offset = remaining // 2
            elif self.justify_content == "end":
                offset = remaining
            elif self.justify_content == "space-between" and n > 1:
                gap_val = self.gap + (remaining // (n - 1))
            elif self.justify_content == "space-around" and n > 0:
                # equal space around each item: half at ends
                gap_val = self.gap + (remaining // n)
                offset = gap_val // 2
            elif self.justify_content == "space-evenly" and n > 0:
                # equal spaces including ends
                gap_val = self.gap + (remaining // (n + 1))
                offset = gap_val

        cur_main = cur_main_base + offset
        for i, ci in enumerate(self.children):
            main_size = sizes[i]
            cross = cross_sizes[i]

            if is_row:
                cw = main_size
                ch = (
                    inner_h
                    if (ci.align_self or self.align_items) == "stretch"
                    else min(cross, inner_h)
                )
                # Align on cross axis
                align = ci.align_self or self.align_items
                if align == "center":
                    cy = inner_y + (inner_h - ch) // 2
                elif align == "end":
                    cy = inner_y + (inner_h - ch)
                else:  # start or stretch
                    cy = inner_y
                rects.append((cur_main, cy, cw, ch))
                cur_main += cw + gap_val
            else:
                ch = main_size
                cw = (
                    inner_w
                    if (ci.align_self or self.align_items) == "stretch"
                    else min(cross, inner_w)
                )
                align = ci.align_self or self.align_items
                if align == "center":
                    cx = inner_x + (inner_w - cw) // 2
                elif align == "end":
                    cx = inner_x + (inner_w - cw)
                else:
                    cx = inner_x
                rects.append((cx, cur_main, cw, ch))
                cur_main += ch + gap_val

        return rects

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        # optional background
        if self.bg_fill or self.bg_outline:
            r = min(self.bg_radius, min(w, h) // 2)
            draw.rounded_rectangle(
                (x, y, x + w, y + h), r, fill=self.bg_fill, outline=self.bg_outline
            )
        rects = self._layout(draw, x, y, w, h)
        base_img = getattr(draw, "_ezp_image", None)
        for item, rect in zip(self.children, rects):
            ix, iy, iw, ih = rect
            if self.clip_children and base_img is not None and iw > 0 and ih > 0:
                # Render child into an offscreen layer to guarantee no overdraw outside bounds
                layer = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
                ldraw = ImageDraw.Draw(layer)
                setattr(ldraw, "_ezp_image", layer)
                try:
                    item.widget.render(ldraw, 0, 0, iw, ih)
                finally:
                    # Composite with its own alpha as mask
                    base_img.paste(layer, (ix, iy), layer)
            else:
                item.widget.render(draw, ix, iy, iw, ih)


# End of file

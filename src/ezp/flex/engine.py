from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFont


# -----------------------
# Data binding utilities
# -----------------------

def resolve_path(path: str, data: Any) -> Any:
    """
    Resolve a simple JSONPath-like reference (e.g. $.a.b[0].c) in a Python object.

    Supports:
    - Root symbol: $
    - Dot navigation: $.a.b
    - Index access: $.arr[0]
    """
    if not path:
        return None
    if path.startswith("$"):
        path = path[1:]
    if path.startswith("."):
        path = path[1:]
    if not path:
        return data

    cur: Any = data
    token = ""
    i = 0

    def flush_token(tok: str, current: Any) -> Any:
        if tok == "":
            return current
        if isinstance(current, dict):
            return current.get(tok)
        return None

    while i < len(path):
        ch = path[i]
        if ch == ".":
            cur = flush_token(token, cur)
            token = ""
            i += 1
            continue
        if ch == "[":
            cur = flush_token(token, cur)
            token = ""
            # parse index until ']'
            j = path.find("]", i + 1)
            if j == -1:
                return None
            idx_str = path[i + 1 : j]
            try:
                idx = int(idx_str)
            except ValueError:
                return None
            if isinstance(cur, Sequence) and not isinstance(cur, (str, bytes)):
                if 0 <= idx < len(cur):
                    cur = cur[idx]
                else:
                    return None
            else:
                return None
            i = j + 1
            continue
        token += ch
        i += 1

    cur = flush_token(token, cur)
    return cur


# -----------------------
# Layout primitives
# -----------------------


class Widget:
    """Base widget interface for the flex engine."""

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
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

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        return (min(self.width, avail_w), min(self.height, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        r = min(self.radius, min(w, h) // 2)
        draw.rounded_rectangle((x, y, x + w, y + h), r, fill=self.fill, outline=self.outline)


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

    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
        font = self._font()
        bbox = draw.textbbox((0, 0), self.text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return (min(w, avail_w), min(h, avail_h))

    def render(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
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
    justify_content: str = "start"  # start|center|end|space-between|space-around|space-evenly
    padding: int = 0
    bg_fill: Optional[Tuple[int, int, int]] = None
    bg_outline: Optional[Tuple[int, int, int]] = None
    bg_radius: int = 12

    def add(self, widget: Widget, *, grow: float = 0.0, shrink: float = 1.0,
            basis: Optional[int] = None, align_self: Optional[str] = None) -> "FlexContainer":
        self.children.append(FlexItem(widget, grow, shrink, basis, align_self))
        return self

    # Measure returns preferred size if unconstrained. For simplicity, sum of children along main axis.
    def measure(self, draw: ImageDraw.ImageDraw, avail_w: int, avail_h: int) -> Tuple[int, int]:
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

    def _layout(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> List[Tuple[int, int, int, int]]:
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
                offset = (gap_val // 2)
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
                ch = inner_h if (ci.align_self or self.align_items) == "stretch" else min(cross, inner_h)
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
                cw = inner_w if (ci.align_self or self.align_items) == "stretch" else min(cross, inner_w)
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
        for (item, rect) in zip(self.children, rects):
            ix, iy, iw, ih = rect
            item.widget.render(draw, ix, iy, iw, ih)


# -----------------------
# Simple renderer helper
# -----------------------

def render_to_image(root: Widget, width: int, height: int, bg: Tuple[int, int, int] = (250, 250, 250)) -> Image.Image:
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    root.render(draw, 0, 0, width, height)
    return img

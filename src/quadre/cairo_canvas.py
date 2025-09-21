"""Utility helpers around Cairo surfaces/contexts for Quadre."""

from __future__ import annotations

import math
from typing import Iterable, Tuple

import cairo

from quadre.font import FontSpec

try:
    import gi

    gi.require_version("Pango", "1.0")
    gi.require_version("PangoCairo", "1.0")
    from gi.repository import Pango, PangoCairo  # type: ignore

    _HAVE_PANGO = True
except Exception:  # pragma: no cover - optional dependency / missing runtime deps
    _HAVE_PANGO = False


def _color_to_rgba(color: Iterable[float | int | str] | str, alpha: float | None = None) -> Tuple[float, float, float, float]:
    if isinstance(color, str):
        value = color.strip()
        if value.startswith("#"):
            value = value[1:]
        if len(value) in (3, 4):
            value = "".join(ch * 2 for ch in value)
        if len(value) not in (6, 8):
            raise ValueError(f"Unsupported color string: {color}")
        r = int(value[0:2], 16) / 255.0
        g = int(value[2:4], 16) / 255.0
        b = int(value[4:6], 16) / 255.0
        a = int(value[6:8], 16) / 255.0 if len(value) == 8 else 1.0
        return r, g, b, alpha if alpha is not None else a

    components = list(color)  # type: ignore[arg-type]
    if not components:
        raise ValueError("Color tuple cannot be empty")
    if all(isinstance(c, int) for c in components):
        rgba = [min(255, max(0, int(c))) / 255.0 for c in components]
    else:
        rgba = [float(c) for c in components]
    while len(rgba) < 4:
        rgba.append(1.0 if len(rgba) == 3 else 0.0)
    if alpha is not None:
        rgba[3] = alpha
    return tuple(rgba[:4])  # type: ignore[return-value]


class CairoCanvas:
    """Thin wrapper around cairo.Context with helpers for Quadre."""

    def __init__(self, surface: cairo.ImageSurface, context: cairo.Context) -> None:
        self.surface = surface
        self.ctx = context
        self.ctx.set_antialias(cairo.ANTIALIAS_BEST)

    @classmethod
    def create(cls, width: int, height: int, background: str | tuple | None = None) -> "CairoCanvas":
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        context = cairo.Context(surface)
        canvas = cls(surface, context)
        if background is not None:
            canvas.fill_rect(0, 0, width, height, background)
        return canvas

    def copy(self) -> "CairoCanvas":
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)
        ctx.set_source_surface(self.surface, 0, 0)
        ctx.paint()
        return CairoCanvas(surface, ctx)

    @property
    def width(self) -> int:
        return self.surface.get_width()

    @property
    def height(self) -> int:
        return self.surface.get_height()

    # Drawing helpers ----------------------------------------------------
    def fill_rect(self, x: float, y: float, w: float, h: float, color: str | tuple, radius: float | None = None) -> None:
        if radius and radius > 0:
            self._rounded_rectangle_path(x, y, w, h, radius)
        else:
            self.ctx.rectangle(x, y, w, h)
        self._set_source(color)
        self.ctx.fill()

    def stroke_rect(self, x: float, y: float, w: float, h: float, color: str | tuple, width: float = 1.0, radius: float | None = None) -> None:
        if radius and radius > 0:
            self._rounded_rectangle_path(x, y, w, h, radius)
        else:
            self.ctx.rectangle(x, y, w, h)
        self.ctx.set_line_width(width)
        self._set_source(color)
        self.ctx.stroke()

    def rounded_rectangle(self, x: float, y: float, w: float, h: float, radius: float, fill: str | tuple | None = None, outline: str | tuple | None = None, outline_width: float = 1.0) -> None:
        self._rounded_rectangle_path(x, y, w, h, radius)
        if fill is not None:
            self._set_source(fill)
            if outline is None:
                self.ctx.fill()
            else:
                self.ctx.fill_preserve()
        if outline is not None:
            self.ctx.set_line_width(outline_width)
            self._set_source(outline)
            self.ctx.stroke()

    # Text ---------------------------------------------------------------
    def draw_text(self, text: str, x: float, y: float, font: FontSpec, color: str | tuple) -> None:
        if not text:
            return
        self._set_source(color)
        if _HAVE_PANGO:
            layout = self._create_pango_layout(text, font)
            baseline = layout.get_baseline() / Pango.SCALE
            self.ctx.move_to(x, y + baseline)
            PangoCairo.show_layout(self.ctx, layout)
        else:
            self._apply_font(font)
            metrics = self.ctx.font_extents()
            ascent = metrics[0]
            baseline = y + ascent
            self.ctx.move_to(x, baseline)
            self.ctx.show_text(text)

    def measure_text(self, text: str, font: FontSpec) -> Tuple[int, int]:
        if not text:
            return (0, max(1, font.size))
        if _HAVE_PANGO:
            layout = self._create_pango_layout(text, font)
            width, height = layout.get_pixel_size()
            return int(width), int(height)
        self._apply_font(font)
        extents = self.ctx.text_extents(text)
        x_advance = extents[4]
        metrics = self.ctx.font_extents()
        ascent, descent = metrics[0], metrics[1]
        width = int(math.ceil(x_advance))
        height = int(math.ceil(ascent + descent))
        return width, height

    # Layers -------------------------------------------------------------
    def new_layer(self, width: int, height: int) -> "CairoCanvas":
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, width), max(1, height))
        ctx = cairo.Context(surface)
        return CairoCanvas(surface, ctx)

    def composite_layer(self, layer: "CairoCanvas", x: float, y: float, alpha: float = 1.0) -> None:
        self.ctx.save()
        self.ctx.set_source_surface(layer.surface, x, y)
        if alpha < 1.0:
            self.ctx.paint_with_alpha(alpha)
        else:
            self.ctx.paint()
        self.ctx.restore()

    # Internal -----------------------------------------------------------
    def _set_source(self, color: str | tuple, alpha: float | None = None) -> None:
        r, g, b, a = _color_to_rgba(color, alpha)
        self.ctx.set_source_rgba(r, g, b, a)

    def _apply_font(self, font: FontSpec) -> None:
        weight = cairo.FONT_WEIGHT_BOLD if font.weight == "bold" else cairo.FONT_WEIGHT_NORMAL
        self.ctx.select_font_face(font.family, cairo.FONT_SLANT_NORMAL, weight)
        self.ctx.set_font_size(font.size)

    def _rounded_rectangle_path(self, x: float, y: float, w: float, h: float, r: float) -> None:
        radius = max(0.0, min(r, min(w, h) / 2.0))
        if radius == 0:
            self.ctx.rectangle(x, y, w, h)
            return
        self.ctx.new_sub_path()
        self.ctx.arc(x + w - radius, y + radius, radius, -math.pi / 2, 0)
        self.ctx.arc(x + w - radius, y + h - radius, radius, 0, math.pi / 2)
        self.ctx.arc(x + radius, y + h - radius, radius, math.pi / 2, math.pi)
        self.ctx.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        self.ctx.close_path()

    def _create_pango_layout(self, text: str, font: FontSpec):  # type: ignore[return-type]
        if not _HAVE_PANGO:  # pragma: no cover - guard
            raise RuntimeError("Pango is not available")
        layout = PangoCairo.create_layout(self.ctx)
        layout.set_text(text)
        desc = Pango.FontDescription()
        desc.set_family(font.family)
        desc.set_weight(Pango.Weight.BOLD if font.weight == "bold" else Pango.Weight.NORMAL)
        desc.set_absolute_size(font.size * Pango.SCALE)
        layout.set_font_description(desc)
        return layout


__all__ = ["CairoCanvas"]

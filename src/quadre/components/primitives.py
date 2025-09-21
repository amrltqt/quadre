"""Primitives built atop the Cairo canvas abstraction."""

from __future__ import annotations

from quadre.cairo_canvas import CairoCanvas


def rounded_rectangle(
    canvas: CairoCanvas,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str | tuple,
    outline: str | tuple | None = None,
    width: float = 1.0,
) -> None:
    x1, y1, x2, y2 = xy
    canvas.rounded_rectangle(
        x1,
        y1,
        x2 - x1,
        y2 - y1,
        radius,
        fill=fill,
        outline=outline,
        outline_width=width,
    )

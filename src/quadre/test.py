"""Tiny Cairo demo to verify the native stack is installed."""

from __future__ import annotations

import math

import cairo

WIDTH, HEIGHT = 600, 320
BG_COLOR = (0.06, 0.10, 0.16)
CARD_BG = (0.12, 0.20, 0.30)
BORDER = (0.29, 0.58, 0.96)
TEXT_PRIMARY = (0.95, 0.97, 1.0)
TEXT_DARK = (0.04, 0.08, 0.12)
ACCENT = (0.36, 0.70, 0.94)


def rounded_rectangle(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def draw_text(
    ctx: cairo.Context,
    text: str,
    x: float,
    y: float,
    size: float,
    *,
    bold: bool = False,
    color: tuple[float, float, float],
) -> None:
    ctx.select_font_face(
        "Helvetica",
        cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL,
    )
    ctx.set_font_size(size)
    ctx.move_to(x, y)
    ctx.set_source_rgb(*color)
    ctx.show_text(text)
    ctx.stroke()


def main() -> None:
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    ctx.set_source_rgb(*BG_COLOR)
    ctx.paint()

    card_x, card_y, card_w, card_h = 40, 40, WIDTH - 80, HEIGHT - 80
    rounded_rectangle(ctx, card_x, card_y, card_w, card_h, 28)
    ctx.set_source_rgb(*CARD_BG)
    ctx.fill_preserve()
    ctx.set_line_width(3.0)
    ctx.set_source_rgba(*BORDER, 0.35)
    ctx.stroke()

    draw_text(ctx, "Sales Performance", card_x + 32, card_y + 60, 32, bold=True, color=TEXT_PRIMARY)
    draw_text(ctx, "Q1 2025 vs Q1 2024", card_x + 32, card_y + 108, 22, bold=False, color=TEXT_PRIMARY)

    pill_x, pill_y, pill_w, pill_h = card_x + 32, card_y + card_h - 92, 220, 60
    rounded_rectangle(ctx, pill_x, pill_y, pill_w, pill_h, 20)
    ctx.set_source_rgba(*ACCENT, 0.9)
    ctx.fill()

    ctx.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26)
    ext = ctx.text_extents("Conversion rate")
    text_x = pill_x + (pill_w - ext.width) / 2 - ext.x_bearing
    text_y = pill_y + (pill_h + ext.height) / 2 - 6
    ctx.move_to(text_x, text_y)
    ctx.set_source_rgb(*TEXT_DARK)
    ctx.show_text("Conversion rate")

    draw_text(ctx, "7.6% vs last year", text_x + 12, text_y + 30, 20, color=TEXT_DARK)

    surface.write_to_png("cairo_card.png")
    print("Generated cairo_card.png")


if __name__ == "__main__":
    main()


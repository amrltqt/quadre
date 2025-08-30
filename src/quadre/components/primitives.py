"""
Basic drawing primitives for quadre dashboard components.

This module contains low-level drawing functions that are used by higher-level components.
All primitives work with PIL ImageDraw objects and follow consistent styling patterns.
"""

from PIL import ImageDraw, ImageFont
from typing import Tuple, Optional
from .config import COLORS, FONTS, DIMENSIONS, px


def rounded_rectangle(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: Optional[str] = None,
    width: int = 1,
) -> None:
    """
    Draw a rounded rectangle with optional outline.

    Args:
        draw: PIL ImageDraw object
        xy: Bounding box coordinates (x1, y1, x2, y2)
        radius: Corner radius for rounded rectangle
        fill: Fill color
        outline: Outline color (if None, no outline is drawn)
        width: Outline width
    """
    # Draw main rectangle without shadow
    draw.rounded_rectangle(xy, radius, fill=fill, outline=outline, width=width)


def badge(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    variant: str = "default",
    font: Optional[ImageFont.ImageFont] = None,
) -> Tuple[int, int]:
    """
    Draw a compact rounded badge.

    Args:
        draw: PIL ImageDraw object
        xy: Top-left position (x, y)
        text: Badge text
        variant: Badge variant (default, secondary, destructive, success, warning, outline)
        font: Font to use (defaults to FONTS.SMALL)

    Returns:
        Tuple of (width, height) of the drawn badge
    """
    if font is None:
        font = FONTS.SMALL

    # Define badge variants
    variants = {
        "default": (COLORS.PRIMARY, COLORS.PRIMARY_FOREGROUND),
        "secondary": (COLORS.SECONDARY, COLORS.SECONDARY_FOREGROUND),
        "destructive": (COLORS.DESTRUCTIVE, COLORS.DESTRUCTIVE_FOREGROUND),
        "success": (COLORS.SUCCESS, COLORS.SUCCESS_FOREGROUND),
        "warning": (COLORS.WARNING, COLORS.WARNING_FOREGROUND),
        "outline": (COLORS.BACKGROUND, COLORS.FOREGROUND),
    }

    fill_color, text_color = variants.get(variant, variants["default"])

    x, y = xy
    text_width = font.getlength(text)
    padx, pady = px(12), px(6)
    radius = DIMENSIONS.BUTTON_RADIUS
    badge_width = int(text_width) + 2 * padx
    badge_height = font.size + 2 * pady

    # Draw main badge
    badge_xy = (x, y, x + badge_width, y + badge_height)
    outline_color = COLORS.BORDER if variant == "outline" else None
    draw.rounded_rectangle(
        badge_xy, radius, fill=fill_color, outline=outline_color, width=1
    )

    # Draw text centered vertically
    text_y = y + (badge_height - font.size) // 2
    draw.text((x + padx, text_y), text, font=font, fill=text_color)

    return badge_width, badge_height


def draw_percentage_text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    main_text: str,
    percentage: str,
    main_font: ImageFont.ImageFont,
    pct_font: ImageFont.ImageFont,
    main_color: str,
    pct_color: str,
    spacing: int = 5,
) -> int:
    """
    Draw main text followed by colored percentage in parentheses.

    Args:
        draw: PIL ImageDraw object
        xy: Position (x, y)
        main_text: Main text content
        percentage: Percentage text (should include parentheses)
        main_font: Font for main text
        pct_font: Font for percentage
        main_color: Color for main text
        pct_color: Color for percentage
        spacing: Space between main text and percentage

    Returns:
        Total width of rendered text
    """
    x, y = xy

    # Draw main text
    draw.text((x, y), main_text, font=main_font, fill=main_color)
    main_width = int(main_font.getlength(main_text))

    # Draw percentage with spacing
    pct_x = x + main_width + spacing
    draw.text((pct_x, y), percentage, font=pct_font, fill=pct_color)
    pct_width = int(pct_font.getlength(percentage))

    return main_width + spacing + pct_width


def get_delta_display_info(delta_pct: float) -> Tuple[str, str, str]:
    """
    Get display information for a delta percentage with semantic colors.

    Args:
        delta_pct: Percentage change (can be positive, negative, or zero)

    Returns:
        Tuple of (icon, color, formatted_percentage)
    """
    if delta_pct > 0:
        return "+", COLORS.SUCCESS, f"+{delta_pct}%"
    elif delta_pct < 0:
        return "-", COLORS.DESTRUCTIVE, f"{delta_pct}%"  # Already has minus sign
    else:
        return "=", COLORS.MUTED_FOREGROUND, "0%"

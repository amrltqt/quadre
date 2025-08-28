#!/usr/bin/env python3
"""
Style Comparison Utility for EZ Pillow

This utility helps compare the old shadow-based styling with the new shadcn/ui
clean styling. It generates side-by-side comparisons and analyzes the differences.
"""

import os
import sys
import json
from PIL import Image, ImageDraw
from typing import Dict, List, Tuple

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ezp.components import (
    COLORS, FONTS, DIMENSIONS,
    KPICard, SectionCard,
    rounded_rectangle, shadcn_badge
)


class LegacyColors:
    """Legacy color scheme with shadows for comparison."""

    # Background colors
    BACKGROUND = '#f8fafc'
    CARD_BACKGROUND = '#ffffff'
    CARD_SHADOW = '#e2e8f0'

    # Border colors
    BORDER = '#cbd5e1'
    BORDER_LIGHT = '#e2e8f0'

    # Text colors
    TEXT_PRIMARY = '#0f172a'
    TEXT_SECONDARY = '#475569'
    TEXT_MUTED = '#64748b'

    # State colors
    POSITIVE = '#10b981'
    NEGATIVE = '#ef4444'
    NEUTRAL = '#6b7280'

    # Table colors
    TABLE_HEADER = '#f1f5f9'
    TABLE_ALT_ROW = '#f8fafc'


def draw_legacy_card(draw: ImageDraw.ImageDraw, x: int, y: int,
                    width: int, height: int, title: str, value: str) -> None:
    """Draw a card with the old shadow-based styling."""

    # Draw shadow
    shadow_offset = 3
    shadow_xy = (
        x + shadow_offset,
        y + shadow_offset,
        x + width + shadow_offset,
        y + height + shadow_offset
    )
    draw.rounded_rectangle(shadow_xy, 16, fill=LegacyColors.CARD_SHADOW)

    # Draw main card
    draw.rounded_rectangle(
        (x, y, x + width, y + height), 16,
        fill=LegacyColors.CARD_BACKGROUND,
        outline=LegacyColors.BORDER_LIGHT, width=2
    )

    # Draw content
    draw.text((x + 20, y + 16), title, font=FONTS.SMALL, fill=LegacyColors.TEXT_MUTED)
    draw.text((x + 20, y + 50), value, font=FONTS.NUMBER, fill=LegacyColors.TEXT_PRIMARY)


def draw_shadcn_card(draw: ImageDraw.ImageDraw, x: int, y: int,
                    width: int, height: int, title: str, value: str) -> None:
    """Draw a card with the new shadcn/ui styling."""

    # Draw main card (no shadow)
    rounded_rectangle(
        draw, (x, y, x + width, y + height), DIMENSIONS.CARD_RADIUS,
        fill=COLORS.CARD_BACKGROUND, outline=COLORS.BORDER, width=1
    )

    # Draw content
    draw.text((x + 20, y + 16), title, font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)
    draw.text((x + 20, y + 50), value, font=FONTS.NUMBER, fill=COLORS.FOREGROUND)


def create_comparison_image() -> Image.Image:
    """Create a side-by-side comparison of old vs new styling."""

    width = 1600
    height = 1000
    img = Image.new("RGB", (width, height), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((50, 30), "Style Comparison: Legacy vs Shadcn/UI",
              font=FONTS.H1, fill=COLORS.FOREGROUND)

    # Section divider
    middle_x = width // 2
    draw.line((middle_x, 100, middle_x, height - 50), fill=COLORS.BORDER, width=2)

    # Legacy section title
    draw.text((50, 120), "Legacy Style (With Shadows)",
              font=FONTS.H2, fill=LegacyColors.TEXT_PRIMARY)

    # Shadcn section title
    draw.text((middle_x + 50, 120), "Shadcn/UI Style (Clean)",
              font=FONTS.H2, fill=COLORS.FOREGROUND)

    # Card comparisons
    card_width = 300
    card_height = 120
    start_y = 180

    sample_cards = [
        ("Revenue", "1,234.5 k€"),
        ("Orders", "42,567"),
        ("Conversion", "3.42%")
    ]

    for i, (title, value) in enumerate(sample_cards):
        y_pos = start_y + i * (card_height + 30)

        # Legacy card
        draw_legacy_card(draw, 50, y_pos, card_width, card_height, title, value)

        # Shadcn card
        draw_shadcn_card(draw, middle_x + 50, y_pos, card_width, card_height, title, value)

    # Feature comparison
    features_y = start_y + len(sample_cards) * (card_height + 30) + 50

    # Legacy features
    draw.text((50, features_y), "Legacy Features:", font=FONTS.BOLD_SMALL, fill=LegacyColors.TEXT_PRIMARY)
    legacy_features = [
        "• Drop shadows on all elements",
        "• Thicker borders (2px)",
        "• More saturated colors",
        "• 3D appearance",
        "• Higher visual weight"
    ]

    for i, feature in enumerate(legacy_features):
        draw.text((50, features_y + 30 + i * 25), feature,
                  font=FONTS.SMALL, fill=LegacyColors.TEXT_SECONDARY)

    # Shadcn features
    draw.text((middle_x + 50, features_y), "Shadcn/UI Features:",
              font=FONTS.BOLD_SMALL, fill=COLORS.FOREGROUND)
    shadcn_features = [
        "• No shadows - flat design",
        "• Thin borders (1px)",
        "• Subtle, harmonious colors",
        "• Clean, minimal appearance",
        "• Better accessibility"
    ]

    for i, feature in enumerate(shadcn_features):
        draw.text((middle_x + 50, features_y + 30 + i * 25), feature,
                  font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

    return img


def create_color_palette_comparison() -> Image.Image:
    """Create a comparison of color palettes."""

    width = 1400
    height = 800
    img = Image.new("RGB", (width, height), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((50, 30), "Color Palette Comparison",
              font=FONTS.H1, fill=COLORS.FOREGROUND)

    # Legacy palette
    draw.text((50, 100), "Legacy Colors", font=FONTS.H2, fill=COLORS.FOREGROUND)

    legacy_colors = [
        ("Background", LegacyColors.BACKGROUND),
        ("Card Shadow", LegacyColors.CARD_SHADOW),
        ("Border", LegacyColors.BORDER),
        ("Text Primary", LegacyColors.TEXT_PRIMARY),
        ("Text Secondary", LegacyColors.TEXT_SECONDARY),
        ("Positive", LegacyColors.POSITIVE),
        ("Negative", LegacyColors.NEGATIVE)
    ]

    # Shadcn palette
    draw.text((width//2 + 50, 100), "Shadcn/UI Colors", font=FONTS.H2, fill=COLORS.FOREGROUND)

    shadcn_colors = [
        ("Background", COLORS.BACKGROUND),
        ("Muted", COLORS.MUTED),
        ("Border", COLORS.BORDER),
        ("Foreground", COLORS.FOREGROUND),
        ("Muted Foreground", COLORS.MUTED_FOREGROUND),
        ("Success", COLORS.SUCCESS),
        ("Destructive", COLORS.DESTRUCTIVE)
    ]

    swatch_size = 60
    start_y = 150

    # Draw legacy swatches
    for i, (name, color) in enumerate(legacy_colors):
        y_pos = start_y + i * (swatch_size + 20)
        draw.rectangle((50, y_pos, 50 + swatch_size, y_pos + swatch_size),
                      fill=color, outline=COLORS.BORDER, width=1)
        draw.text((50 + swatch_size + 20, y_pos + 20), name,
                  font=FONTS.SMALL, fill=COLORS.FOREGROUND)
        draw.text((50 + swatch_size + 20, y_pos + 40), color,
                  font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

    # Draw shadcn swatches
    for i, (name, color) in enumerate(shadcn_colors):
        y_pos = start_y + i * (swatch_size + 20)
        x_pos = width//2 + 50
        draw.rectangle((x_pos, y_pos, x_pos + swatch_size, y_pos + swatch_size),
                      fill=color, outline=COLORS.BORDER, width=1)
        draw.text((x_pos + swatch_size + 20, y_pos + 20), name,
                  font=FONTS.SMALL, fill=COLORS.FOREGROUND)
        draw.text((x_pos + swatch_size + 20, y_pos + 40), color,
                  font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

    return img


def create_badge_comparison() -> Image.Image:
    """Create a comparison of badge styles."""

    width = 1200
    height = 600
    img = Image.new("RGB", (width, height), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((50, 30), "Badge Style Comparison",
              font=FONTS.H1, fill=COLORS.FOREGROUND)

    # Legacy badges (simulated with rounded rectangles)
    draw.text((50, 100), "Legacy Badges (with shadows)",
              font=FONTS.H2, fill=COLORS.FOREGROUND)

    legacy_y = 150
    badges = ["Success", "Warning", "Error", "Info"]
    colors = [LegacyColors.POSITIVE, "#eab308", LegacyColors.NEGATIVE, "#3b82f6"]

    x_pos = 50
    for badge, color in zip(badges, colors):
        # Shadow
        draw.rounded_rectangle(
            (x_pos + 2, legacy_y + 2, x_pos + 102, legacy_y + 32),
            12, fill=LegacyColors.CARD_SHADOW
        )
        # Badge
        draw.rounded_rectangle(
            (x_pos, legacy_y, x_pos + 100, legacy_y + 30),
            12, fill=color
        )
        draw.text((x_pos + 20, legacy_y + 8), badge, font=FONTS.SMALL, fill="white")
        x_pos += 120

    # Shadcn badges
    draw.text((50, 250), "Shadcn/UI Badges (clean)",
              font=FONTS.H2, fill=COLORS.FOREGROUND)

    shadcn_y = 300
    variants = ["success", "warning", "destructive", "secondary"]

    x_pos = 50
    for badge, variant in zip(badges, variants):
        shadcn_badge(draw, (x_pos, shadcn_y), badge, variant=variant)
        x_pos += 120

    # Comparison notes
    notes_y = 400
    draw.text((50, notes_y), "Key Differences:", font=FONTS.BOLD_SMALL, fill=COLORS.FOREGROUND)

    differences = [
        "• Legacy: Drop shadows create depth but add visual noise",
        "• Shadcn/UI: Clean borders focus attention on content",
        "• Legacy: Fixed color scheme with limited variants",
        "• Shadcn/UI: Semantic color system with multiple variants",
        "• Legacy: Higher visual weight competes with content",
        "• Shadcn/UI: Subtle styling supports content hierarchy"
    ]

    for i, diff in enumerate(differences):
        draw.text((50, notes_y + 30 + i * 25), diff,
                  font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

    return img


def generate_all_comparisons():
    """Generate all comparison images."""

    print("Generating style comparisons...")

    # Ensure output directory exists
    os.makedirs("out", exist_ok=True)

    # Generate comparison images
    comparison = create_comparison_image()
    comparison.save("out/style_comparison.png")
    print("✓ Generated: out/style_comparison.png")

    color_comparison = create_color_palette_comparison()
    color_comparison.save("out/color_comparison.png")
    print("✓ Generated: out/color_comparison.png")

    badge_comparison = create_badge_comparison()
    badge_comparison.save("out/badge_comparison.png")
    print("✓ Generated: out/badge_comparison.png")

    print("\nStyle comparison summary:")
    print("=" * 40)
    print("Legacy Style:")
    print("  • Uses drop shadows for depth")
    print("  • Thicker borders and higher contrast")
    print("  • More saturated color palette")
    print("  • 3D appearance with visual weight")
    print()
    print("Shadcn/UI Style:")
    print("  • Flat design without shadows")
    print("  • Subtle borders and clean lines")
    print("  • Harmonious, accessible colors")
    print("  • Minimal aesthetic focusing on content")
    print()
    print("Benefits of migration:")
    print("  ✓ Modern, professional appearance")
    print("  ✓ Better accessibility and contrast")
    print("  ✓ Cleaner visual hierarchy")
    print("  ✓ Easier maintenance and customization")


def main():
    """Main function to run style comparisons."""

    print("EZ Pillow Style Comparison Utility")
    print("=" * 35)
    print()

    generate_all_comparisons()

    print()
    print("All comparison images have been generated in the 'out' directory.")
    print("You can now visually compare the legacy and shadcn/ui styles.")


if __name__ == "__main__":
    main()

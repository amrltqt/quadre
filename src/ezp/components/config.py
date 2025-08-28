"""
Configuration module for EZ Pillow dashboard components.

Contains all shared configuration including colors, fonts, and dimensions.
"""

import os
from PIL import ImageFont

# ---------- Dimensions ----------
class DIMENSIONS:
    """Canvas and layout dimensions."""
    WIDTH = 1920
    HEIGHT = 1280
    PADDING = 32
    CARD_RADIUS = 8
    BUTTON_RADIUS = 6

    # Component heights
    KPI_CARD_HEIGHT = 150
    SECTION_CARD_HEIGHT_MID = 170
    SECTION_CARD_HEIGHT_BOTTOM = 140
    TABLE_HEADER_HEIGHT = 70
    TABLE_ROW_HEIGHT = 60

    # Gaps and spacing
    GAP_SMALL = 12
    GAP_MEDIUM = 24
    GAP_LARGE = 32

# ---------- Colors ----------
class COLORS:
    """Shadcn/ui inspired color palette for dashboard components."""
    # Background colors
    BACKGROUND = '#ffffff'
    CARD_BACKGROUND = '#ffffff'
    MUTED = '#f1f5f9'

    # Border colors
    BORDER = '#e2e8f0'
    INPUT = '#e2e8f0'
    RING = '#3b82f6'

    # Text colors
    FOREGROUND = '#0f172a'
    MUTED_FOREGROUND = '#64748b'

    # Primary colors
    PRIMARY = '#0f172a'
    PRIMARY_FOREGROUND = '#f8fafc'

    # Secondary colors
    SECONDARY = '#f1f5f9'
    SECONDARY_FOREGROUND = '#0f172a'

    # Accent colors
    ACCENT = '#f1f5f9'
    ACCENT_FOREGROUND = '#0f172a'

    # State colors
    DESTRUCTIVE = '#ef4444'
    DESTRUCTIVE_FOREGROUND = '#f8fafc'
    SUCCESS = '#22c55e'
    SUCCESS_FOREGROUND = '#f8fafc'
    WARNING = '#eab308'
    WARNING_FOREGROUND = '#0f172a'

    # Legacy aliases for backward compatibility
    TEXT_PRIMARY = FOREGROUND
    TEXT_SECONDARY = MUTED_FOREGROUND
    TEXT_MUTED = MUTED_FOREGROUND
    POSITIVE = SUCCESS
    NEGATIVE = DESTRUCTIVE
    NEUTRAL = MUTED_FOREGROUND
    TABLE_HEADER = MUTED
    TABLE_ALT_ROW = MUTED
    BORDER_LIGHT = BORDER

def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load system font with fallback to default."""
    import platform

    # Check for custom font path from environment variable
    custom_font_path = os.environ.get('EZP_FONT_PATH')
    if custom_font_path:
        try:
            return ImageFont.truetype(custom_font_path, size)
        except Exception:
            print(f"Warning: Could not load custom font from {custom_font_path}")

    # Platform-specific font paths
    system = platform.system()

    if system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Geneva.ttf",
            "/Library/Fonts/Verdana.ttf",
            "/System/Library/Fonts/Palatino.ttc",
            # Homebrew fonts (if installed)
            "/usr/local/share/fonts/DejaVuSans-Bold.ttf" if bold else "/usr/local/share/fonts/DejaVuSans.ttf",
            "/opt/homebrew/share/fonts/DejaVuSans-Bold.ttf" if bold else "/opt/homebrew/share/fonts/DejaVuSans.ttf",
        ]
    elif system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/verdana.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    else:  # Linux and others
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        ]

    # Try each font path
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    # Fallback: try to load system default fonts by name
    fallback_names = ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans", "Ubuntu"]
    for font_name in fallback_names:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue

    # Ultimate fallback
    return ImageFont.load_default()

# ---------- Fonts ----------
class FONTS:
    """Typography system with consistent font sizing."""
    H1 = load_font(42, True)
    H2 = load_font(30, True)
    NUMBER = load_font(36, True)
    BODY = load_font(24)
    TABLE = load_font(24)
    SMALL = load_font(20)
    BOLD_SMALL = load_font(24, True)

# ----- Scaling support (supersampling / DPI) -----
_BASE_DIMENSIONS = {
    'WIDTH': DIMENSIONS.WIDTH,
    'HEIGHT': DIMENSIONS.HEIGHT,
    'PADDING': DIMENSIONS.PADDING,
    'CARD_RADIUS': DIMENSIONS.CARD_RADIUS,
    'BUTTON_RADIUS': DIMENSIONS.BUTTON_RADIUS,
    'KPI_CARD_HEIGHT': DIMENSIONS.KPI_CARD_HEIGHT,
    'SECTION_CARD_HEIGHT_MID': DIMENSIONS.SECTION_CARD_HEIGHT_MID,
    'SECTION_CARD_HEIGHT_BOTTOM': DIMENSIONS.SECTION_CARD_HEIGHT_BOTTOM,
    'TABLE_HEADER_HEIGHT': DIMENSIONS.TABLE_HEADER_HEIGHT,
    'TABLE_ROW_HEIGHT': DIMENSIONS.TABLE_ROW_HEIGHT,
    'GAP_SMALL': DIMENSIONS.GAP_SMALL,
    'GAP_MEDIUM': DIMENSIONS.GAP_MEDIUM,
    'GAP_LARGE': DIMENSIONS.GAP_LARGE,
}

_BASE_FONT_SIZES = {
    'H1': 42,
    'H2': 30,
    'NUMBER': 36,
    'BODY': 24,
    'TABLE': 24,
    'SMALL': 20,
    'BOLD_SMALL': 24,
}

_CURRENT_SCALE = 1.0


def set_scale(scale: float) -> None:
    """Apply a global scale factor to dimensions and fonts.

    Useful for supersampling: render at 2x/3x then optionally downscale.
    """
    global _CURRENT_SCALE
    _CURRENT_SCALE = float(scale) if scale and scale > 0 else 1.0

    # Scale dimensions (round to ints)
    for k, v in _BASE_DIMENSIONS.items():
        setattr(DIMENSIONS, k, int(v * _CURRENT_SCALE))

    # Recreate fonts at scaled sizes
    FONTS.H1 = load_font(int(_BASE_FONT_SIZES['H1'] * _CURRENT_SCALE), True)
    FONTS.H2 = load_font(int(_BASE_FONT_SIZES['H2'] * _CURRENT_SCALE), True)
    FONTS.NUMBER = load_font(int(_BASE_FONT_SIZES['NUMBER'] * _CURRENT_SCALE), True)
    FONTS.BODY = load_font(int(_BASE_FONT_SIZES['BODY'] * _CURRENT_SCALE))
    FONTS.TABLE = load_font(int(_BASE_FONT_SIZES['TABLE'] * _CURRENT_SCALE))
    FONTS.SMALL = load_font(int(_BASE_FONT_SIZES['SMALL'] * _CURRENT_SCALE))
    FONTS.BOLD_SMALL = load_font(int(_BASE_FONT_SIZES['BOLD_SMALL'] * _CURRENT_SCALE), True)


def reset_scale() -> None:
    """Reset scale to 1x (base)."""
    set_scale(1.0)


def get_scale() -> float:
    return _CURRENT_SCALE

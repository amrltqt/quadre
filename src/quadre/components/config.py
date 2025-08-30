"""
Configuration module for quadre dashboard components.

Contains all shared configuration including colors, fonts, and dimensions.
"""

import os
from PIL import ImageFont, features


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
    """Application color palette for dashboard components."""

    # Background colors
    BACKGROUND = "#ffffff"
    CARD_BACKGROUND = "#ffffff"
    MUTED = "#f1f5f9"

    # Border colors
    BORDER = "#d1d5db"
    INPUT = "#e2e8f0"
    RING = "#3b82f6"

    # Text colors
    FOREGROUND = "#0f172a"
    MUTED_FOREGROUND = "#64748b"

    # Primary colors
    PRIMARY = "#0f172a"
    PRIMARY_FOREGROUND = "#f8fafc"

    # Secondary colors
    SECONDARY = "#f1f5f9"
    SECONDARY_FOREGROUND = "#0f172a"

    # Accent colors
    ACCENT = "#f1f5f9"
    ACCENT_FOREGROUND = "#0f172a"

    # State colors
    DESTRUCTIVE = "#ef4444"
    DESTRUCTIVE_FOREGROUND = "#f8fafc"
    SUCCESS = "#22c55e"
    SUCCESS_FOREGROUND = "#f8fafc"
    WARNING = "#eab308"
    WARNING_FOREGROUND = "#0f172a"

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


try:
    _PREFERRED_LAYOUT_ENGINE = (
        ImageFont.LAYOUT_RAQM
        if getattr(ImageFont, "LAYOUT_RAQM", None) and features.check("raqm")
        else ImageFont.LAYOUT_BASIC
    )
except Exception:
    _PREFERRED_LAYOUT_ENGINE = getattr(ImageFont, "LAYOUT_BASIC", 0)


_CUSTOM_FONT_WARNED = False


def _candidate_paths(system: str, bold: bool) -> list[str]:
    paths: list[str] = []
    if system == "Darwin":
        # Prefer Noto for wide Unicode coverage, then Inter for Latin aesthetics
        if bold:
            paths += [
                "/Library/Fonts/NotoSans-Bold.ttf",
                "/Library/Fonts/Inter-Bold.ttf",
                "/Library/Fonts/Inter Bold.ttf",
            ]
        else:
            paths += [
                "/Library/Fonts/NotoSans-Regular.ttf",
                "/Library/Fonts/Inter-Regular.ttf",
                "/Library/Fonts/Inter.ttf",
            ]
        # Common system fonts
        paths += [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Geneva.ttf",
            "/Library/Fonts/Verdana.ttf",
            "/System/Library/Fonts/Palatino.ttc",
        ]
    elif system == "Windows":
        # Windows defaults (Inter not guaranteed)
        if bold:
            paths += [
                "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
                "C:/Windows/Fonts/arialbd.ttf",
            ]
        else:
            paths += [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/verdana.ttf",
            ]
    else:
        # Linux: prefer Noto for wide Unicode coverage, then Inter, then DejaVu/Liberation/Ubuntu
        if bold:
            paths += [
                "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
                "/usr/share/fonts/truetype/inter/Inter.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
        else:
            paths += [
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                "/usr/share/fonts/truetype/inter/Inter-Regular.ttf",
                "/usr/share/fonts/truetype/inter/Inter.ttf",
                "/usr/share/fonts/truetype/inter/Inter-VariableFont_slnt,wght.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            ]
    return paths


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load system font with fallback to default."""
    import platform

    # Check for custom font path from environment variable
    # Prefer system fonts first (Inter/Noto/DejaVu), no env management required
    system = platform.system()
    font_paths = _candidate_paths(system, bold)

    # Try each font path
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(
                    font_path, size, layout_engine=_PREFERRED_LAYOUT_ENGINE
                )
            except Exception:
                continue

    # Optional: allow env override as a last resort (silent if missing)
    custom_font_path = os.environ.get("quadre_FONT_PATH")
    if custom_font_path and os.path.exists(custom_font_path):
        try:
            return ImageFont.truetype(
                custom_font_path, size, layout_engine=_PREFERRED_LAYOUT_ENGINE
            )
        except Exception:
            pass

    # Fallback: try to load system default fonts by name
    fallback_names = ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans", "Ubuntu"]
    for font_name in fallback_names:
        try:
            return ImageFont.truetype(
                font_name, size, layout_engine=_PREFERRED_LAYOUT_ENGINE
            )
        except Exception:
            continue

    # Ultimate fallback
    return ImageFont.load_default()


# ---------- Fonts ----------
class FONTS:
    """Typography system with consistent font sizing."""

    H1 = load_font(42, True)
    H2 = load_font(30, True)
    NUMBER = load_font(40, True)
    BODY = load_font(24)
    TABLE = load_font(24)
    SMALL = load_font(20)
    BOLD_SMALL = load_font(24, True)


# ----- Scaling support (supersampling / DPI) -----
_BASE_DIMENSIONS = {
    "WIDTH": DIMENSIONS.WIDTH,
    "HEIGHT": DIMENSIONS.HEIGHT,
    "PADDING": DIMENSIONS.PADDING,
    "CARD_RADIUS": DIMENSIONS.CARD_RADIUS,
    "BUTTON_RADIUS": DIMENSIONS.BUTTON_RADIUS,
    "KPI_CARD_HEIGHT": DIMENSIONS.KPI_CARD_HEIGHT,
    "SECTION_CARD_HEIGHT_MID": DIMENSIONS.SECTION_CARD_HEIGHT_MID,
    "SECTION_CARD_HEIGHT_BOTTOM": DIMENSIONS.SECTION_CARD_HEIGHT_BOTTOM,
    "TABLE_HEADER_HEIGHT": DIMENSIONS.TABLE_HEADER_HEIGHT,
    "TABLE_ROW_HEIGHT": DIMENSIONS.TABLE_ROW_HEIGHT,
    "GAP_SMALL": DIMENSIONS.GAP_SMALL,
    "GAP_MEDIUM": DIMENSIONS.GAP_MEDIUM,
    "GAP_LARGE": DIMENSIONS.GAP_LARGE,
}

_BASE_FONT_SIZES = {
    "H1": 42,
    "H2": 30,
    "NUMBER": 36,
    "BODY": 24,
    "TABLE": 24,
    "SMALL": 20,
    "BOLD_SMALL": 24,
}

_CURRENT_SCALE = 1.0


def px(value: float | int) -> int:
    """Scale a pixel value according to current supersampling scale.

    Keeps integer rounding consistent across the codebase so that component
    paddings and offsets remain proportional when `set_scale()` is active.
    """
    try:
        f = float(value)
    except Exception:
        f = 0.0
    return max(0, int(round(f * _CURRENT_SCALE)))


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
    FONTS.H1 = load_font(int(_BASE_FONT_SIZES["H1"] * _CURRENT_SCALE), True)
    FONTS.H2 = load_font(int(_BASE_FONT_SIZES["H2"] * _CURRENT_SCALE), True)
    FONTS.NUMBER = load_font(int(_BASE_FONT_SIZES["NUMBER"] * _CURRENT_SCALE), True)
    FONTS.BODY = load_font(int(_BASE_FONT_SIZES["BODY"] * _CURRENT_SCALE))
    FONTS.TABLE = load_font(int(_BASE_FONT_SIZES["TABLE"] * _CURRENT_SCALE))
    FONTS.SMALL = load_font(int(_BASE_FONT_SIZES["SMALL"] * _CURRENT_SCALE))
    FONTS.BOLD_SMALL = load_font(
        int(_BASE_FONT_SIZES["BOLD_SMALL"] * _CURRENT_SCALE), True
    )


def reset_scale() -> None:
    """Reset scale to 1x (base)."""
    set_scale(1.0)



def load_cjk_font(size: int) -> ImageFont.ImageFont:
    """Load a CJK-capable font if available (Noto CJK), else default.

    Covers common CJK Unified Ideographs blocks with a TTC font.
    """
    candidates = [
        # Debian/Ubuntu noto-cjk
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        # Alternative naming
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(
                    p, size, layout_engine=_PREFERRED_LAYOUT_ENGINE
                )
            except Exception:
                continue
    return ImageFont.load_default()


def apply_theme(theme: dict) -> None:
    """Apply a theme dict to COLORS and FONTS (case-insensitive keys).

    Theme schema (all fields optional):
    {
      "colors" | "COLORS": { "background": "#ffffff", "FOREGROUND": "#0f172a", ... },
      "fonts" | "FONTS": { "h1": 44, "H2": 32, "number": 42, "body": 24, "small": 18, "table": 24 }
    }
    """
    if not isinstance(theme, dict):
        return

    # Resolve top-level sections case-insensitively
    def _get_section(names: list[str]):
        for name in names:
            if name in theme and isinstance(theme[name], dict):
                return theme[name]
        # fallback: try case-insensitive
        lower_map = {str(k).lower(): v for k, v in theme.items() if isinstance(v, dict)}
        for name in names:
            if name.lower() in lower_map:
                return lower_map[name.lower()]
        return None

    colors = _get_section(["colors", "COLORS"])
    if isinstance(colors, dict):
        for k, v in colors.items():
            key = str(k).upper()
            if isinstance(v, str) and hasattr(COLORS, key):
                setattr(COLORS, key, v)

    fonts = _get_section(["fonts", "FONTS"])
    if isinstance(fonts, dict):
        # Accept both upper/lower and snake variants for BOLD_SMALL
        def _get_font_size(keys: list[str]):
            for name in keys:
                for variant in (name, name.upper(), name.lower()):
                    if (
                        variant in fonts
                        and isinstance(fonts[variant], (int, float))
                        and fonts[variant] > 0
                    ):
                        return int(fonts[variant])
            return None

        def _apply(name: str, bold: bool, current):
            sz = _get_font_size([name])
            if sz:
                return load_font(sz, bold)
            return current

        FONTS.H1 = _apply("H1", True, FONTS.H1)
        FONTS.H2 = _apply("H2", True, FONTS.H2)
        FONTS.NUMBER = _apply("NUMBER", True, FONTS.NUMBER)
        FONTS.BODY = _apply("BODY", False, FONTS.BODY)
        FONTS.TABLE = _apply("TABLE", False, FONTS.TABLE)
        FONTS.SMALL = _apply("SMALL", False, FONTS.SMALL)
        # handle bold_small key variants
        bs = _get_font_size(["BOLD_SMALL", "bold_small", "boldSmall"])
        if bs:
            FONTS.BOLD_SMALL = load_font(int(bs), True)

    # Allow per-style font files (paths). Keys are case-insensitive.
    font_files = (
        _get_section(["font_files", "fontfiles", "font_paths", "fontpaths"]) or {}
    )
    if isinstance(font_files, dict):
        # helper to load a style from path with size fallback
        def _apply_path(style_key: str, bold: bool, current_font):
            # resolve style path case-insensitively
            chosen = None
            for cand in (style_key, style_key.upper(), style_key.lower()):
                if cand in font_files and isinstance(font_files[cand], str):
                    chosen = font_files[cand]
                    break
            if not chosen:
                return current_font
            # choose size from the already-applied sizes
            try:
                size = getattr(current_font, "size", None) or _BASE_FONT_SIZES.get(
                    style_key.upper(), 24
                )
            except Exception:
                size = _BASE_FONT_SIZES.get(style_key.upper(), 24)
            try:
                return ImageFont.truetype(
                    chosen, int(size), layout_engine=_PREFERRED_LAYOUT_ENGINE
                )
            except Exception:
                return current_font

        FONTS.H1 = _apply_path("H1", True, FONTS.H1)
        FONTS.H2 = _apply_path("H2", True, FONTS.H2)
        FONTS.NUMBER = _apply_path("NUMBER", True, FONTS.NUMBER)
        FONTS.BODY = _apply_path("BODY", False, FONTS.BODY)
        FONTS.TABLE = _apply_path("TABLE", False, FONTS.TABLE)
        FONTS.SMALL = _apply_path("SMALL", False, FONTS.SMALL)
        FONTS.BOLD_SMALL = _apply_path("BOLD_SMALL", True, FONTS.BOLD_SMALL)

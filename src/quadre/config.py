"""Shared configuration primitives for Quadre."""

from __future__ import annotations

from typing import Any, Dict, List

from quadre.font import (
    BASE_FONT_SPECS,
    FONTS,
    rebuild_fonts,
    set_custom_font_family as _set_font_family,
    get_custom_font_family as _get_font_family,
)

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
    GAP_SMALL = 4
    GAP_MEDIUM = 8
    GAP_LARGE = 16


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


# ----- Scaling support -----
_BASE_DIMENSIONS: Dict[str, int] = {
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

_CURRENT_SCALE = 1.0


def px(value: float | int) -> int:
    """Scale a pixel value according to the active supersampling scale."""

    try:
        numeric = float(value)
    except Exception:
        numeric = 0.0
    return max(0, int(round(numeric * _CURRENT_SCALE)))


def set_scale(scale: float) -> None:
    """Apply a global supersampling scale to dimensions and fonts."""

    global _CURRENT_SCALE
    _CURRENT_SCALE = float(scale) if scale and scale > 0 else 1.0

    for key, base_value in _BASE_DIMENSIONS.items():
        setattr(DIMENSIONS, key, int(round(base_value * _CURRENT_SCALE)))

    rebuild_fonts(_CURRENT_SCALE)


def reset_scale() -> None:
    """Reset the supersampling scale to 1.0."""

    set_scale(1.0)


def get_current_scale() -> float:
    """Return the currently active supersampling scale."""

    return _CURRENT_SCALE


def set_custom_font_family(family: str | None) -> None:
    """Override the font family used by the shared font registry."""

    _set_font_family(family)
    rebuild_fonts(_CURRENT_SCALE)


def get_custom_font_family() -> str | None:
    """Return the requested custom font family, if any."""

    return _get_font_family()


def apply_theme(theme: Dict[str, Any]) -> None:
    """Apply a theme dictionary to COLORS and FONTS (case-insensitive keys)."""

    if not isinstance(theme, dict):
        return

    def _get_section(names: List[str]) -> Dict[str, Any] | None:
        for name in names:
            value = theme.get(name)
            if isinstance(value, dict):
                return value
        lowered = {str(k).lower(): v for k, v in theme.items() if isinstance(v, dict)}
        for name in names:
            value = lowered.get(name.lower())
            if isinstance(value, dict):
                return value
        return None

    colors = _get_section(["colors", "COLORS"])
    if colors:
        for key, value in colors.items():
            attr = str(key).upper()
            if isinstance(value, str) and hasattr(COLORS, attr):
                setattr(COLORS, attr, value)

    fonts = _get_section(["fonts", "FONTS"])
    if fonts:

        def _extract_size(names: List[str]) -> int | None:
            for candidate in names:
                for variant in (candidate, candidate.upper(), candidate.lower()):
                    value = fonts.get(variant)
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
            return None

        for name in BASE_FONT_SPECS.keys():
            new_size = _extract_size([name])
            if new_size is not None:
                FONTS.set_base_size(name, new_size)


__all__ = [
    "COLORS",
    "DIMENSIONS",
    "FONTS",
    "BASE_FONT_SPECS",
    "px",
    "set_scale",
    "reset_scale",
    "get_current_scale",
    "set_custom_font_family",
    "get_custom_font_family",
    "apply_theme",
]

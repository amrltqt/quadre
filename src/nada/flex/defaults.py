from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from ..components import COLORS


_CACHED_DEFAULTS: Optional[Dict[str, Any]] = None


def _load_defaults() -> Dict[str, Any]:
    global _CACHED_DEFAULTS
    if _CACHED_DEFAULTS is not None:
        return _CACHED_DEFAULTS
    # Source defaults exclusively from the validated Theme; any failure should raise
    from ..theme import load_theme_from_env_or_default, widget_defaults_from_theme  # type: ignore

    t = load_theme_from_env_or_default()
    themed = widget_defaults_from_theme(t)
    _CACHED_DEFAULTS = dict(themed or {})
    return _CACHED_DEFAULTS


def defaults_for(widget: str) -> Dict[str, Any]:
    d = _load_defaults().get(widget, {})
    # make a shallow copy to avoid accidental mutations
    return dict(d)


def set_widget_defaults(defaults: Dict[str, Any] | None) -> None:
    """Override the cached widget defaults (used by the runner after theme load)."""
    global _CACHED_DEFAULTS
    _CACHED_DEFAULTS = dict(defaults or {})


def parse_color(value: Any) -> Optional[Tuple[int, int, int]]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    if isinstance(value, str):
        s = value.strip()
        # Theme token resolution (e.g., "FOREGROUND", "colors.foreground", "theme:muted_foreground")
        token = s.replace(" ", "")
        # Normalize common prefixes
        for pref in ("colors.", "COLORS.", "theme.", "THEME.", "colors:", "COLORS:", "theme:", "THEME:"):
            if token.startswith(pref):
                token = token[len(pref):]
                break
        # Support case-insensitive attribute lookup on COLORS
        attr = token.upper()
        if hasattr(COLORS, attr):
            themed = getattr(COLORS, attr)
            if isinstance(themed, str):
                return parse_color(themed)
        # Hex parsing (with or without leading '#')
        if s.startswith('#'):
            s = s[1:]
        if len(s) == 6:
            try:
                r = int(s[0:2], 16)
                g = int(s[2:4], 16)
                b = int(s[4:6], 16)
                return (r, g, b)
            except Exception:
                return None
    return None

from __future__ import annotations

from typing import Dict, Any

from ..components import COLORS, DIMENSIONS, FONTS
from .defaults import defaults_for, parse_color
from .engine import FlexContainer, TextWidget
from .widgets import TableWidget, Spacer


def _apply_container_defaults(cont: FlexContainer, overrides: Dict[str, Any] | None = None) -> FlexContainer:
    d = defaults_for("FlexContainer")
    ov = overrides or {}
    cont.gap = int(ov.get("gap", d.get("gap", cont.gap)))
    cont.align_items = ov.get("align_items", d.get("align_items", cont.align_items))
    cont.justify_content = ov.get("justify_content", d.get("justify_content", cont.justify_content))
    # For row containers, default padding to 0 unless explicitly overridden
    if "padding" in ov:
        cont.padding = int(ov["padding"])
    else:
        cont.padding = 0 if cont.direction == "row" else int(d.get("padding", cont.padding))
    cont.bg_radius = int(ov.get("bg_radius", d.get("bg_radius", cont.bg_radius)))
    cont.bg_fill = parse_color(ov.get("bg_fill", d.get("bg_fill")))
    cont.bg_outline = parse_color(ov.get("bg_outline", d.get("bg_outline")))
    return cont


def _text_from_props(text: str, props: Dict[str, Any] | None = None) -> TextWidget:
    d = defaults_for("TextWidget")
    p = dict(d)
    if props:
        p.update(_norm_props(props))
    font_map = {
        "title": FONTS.H1,
        "heading": FONTS.H2,
        "body": FONTS.BODY,
        "caption": FONTS.SMALL,
        "table": FONTS.TABLE,
    }
    font = font_map.get(p.get("font", "body"), FONTS.BODY)
    fill = parse_color(p.get("fill")) or parse_color(COLORS.FOREGROUND) or (20, 20, 20)
    align = p.get("align", "left")
    return TextWidget(text, fill=fill, font=font, align=align)


def _table_from_props(tbl_data: Any, props: Dict[str, Any] | None = None) -> TableWidget:
    d = defaults_for("TableWidget")
    p = dict(d)
    if props:
        p.update(_norm_props(props))
    # Merge optional style overrides from theme defaults and props["style"]
    style_theme = d.get("style") if isinstance(d.get("style"), dict) else {}
    style_props = (props or {}).get("style") if isinstance((props or {}).get("style"), dict) else {}
    style_overrides = {**style_theme, **style_props} if (style_theme or style_props) else None

    return TableWidget(
        data=tbl_data,
        header_height=int(p.get("header_height", 0)) or None,
        row_height=int(p.get("row_height", 0)) or None,
        fill_height=bool(p.get("fill_height", False)),
        min_row_height=int(p.get("min_row_height", 28)),
        max_row_height=int(p.get("max_row_height", 90)),
        fit=str(p.get("fit", "truncate")),
        shrink_row_height_floor=int(p.get("shrink_row_height_floor", 14)),
        style_overrides=style_overrides,
    )


def _spacer_from_props(props: Dict[str, Any] | None = None) -> Spacer:
    d = defaults_for("Spacer")
    p = _norm_props(props or {})
    h = int(p.get("height", d.get("height", DIMENSIONS.GAP_MEDIUM)))
    return Spacer(h)


def _norm_props(props: Dict[str, Any] | None) -> Dict[str, Any]:
    """Normalize a properties dict to lower-case keys.

    Values are passed as-is; caller may map aliases (e.g., color->fill).
    """
    if not isinstance(props, dict):
        return {}
    return {str(k).lower(): v for k, v in props.items()}

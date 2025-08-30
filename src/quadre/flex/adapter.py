from __future__ import annotations

from typing import Dict, Any, Callable, Optional

from .engine import FlexContainer
from .widgets import TextWidget
from .helpers import (
    _apply_container_defaults,
    _text_from_props,
    _table_from_props,
    _spacer_from_props,
    _norm_props,
)
from .widgets import (
    KPIWidget,
    Spacer,
    ImageWidget,
    ProgressBarWidget,
    StatusBadgeWidget,
)
from ..components import DIMENSIONS, COLORS
from ..utils.dataref import resolve_field


# -------------------------
# Small, testable builder helpers
# -------------------------

ResolveFn = Callable[[Any], Any]
BuilderFn = Callable[[Dict[str, Any]], "FlexContainer | TextWidget | KPIWidget | Spacer | ImageWidget | ProgressBarWidget | StatusBadgeWidget"]


def _int_from_props(props: Dict[str, Any], name: str, default: int = 0) -> int:
    try:
        return int(props.get(name, default))
    except Exception:
        return default


def _wrap_with_margins(widget, props: Dict[str, Any]) -> FlexContainer | Any:
    mt = _int_from_props(props, "margin_top", 0)
    mb = _int_from_props(props, "margin_bottom", 0)
    if (mt and mt > 0) or (mb and mb > 0):
        wrap = FlexContainer(direction="column", gap=0)
        wrap = _apply_container_defaults(
            wrap, {"gap": 0, "padding": 0, "align_items": "stretch"}
        )
        if mt and mt > 0:
            wrap.add(Spacer(mt))
        wrap.add(widget)
        if mb and mb > 0:
            wrap.add(Spacer(mb))
        return wrap
    return widget


def _table_from_node(node: Dict[str, Any], resolve: ResolveFn) -> Any:
    if "table" in node:
        return resolve(node.get("table"))
    headers = node.get("headers")
    rows = node.get("rows")
    if headers is not None or rows is not None:
        return {
            "headers": resolve(headers) if headers is not None else [],
            "rows": resolve(rows) if rows is not None else [],
        }
    return []


def _build_title(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> FlexContainer:
    title_text = resolve(node.get("title"))
    date_note = resolve(node.get("date_note"))
    col = FlexContainer(direction="column", gap=10, padding=0, align_items="start")
    col = _apply_container_defaults(col, {"gap": 10, "padding": 0, "align_items": "start"})
    if title_text:
        col.add(_text_from_props(str(title_text), {"font": "title"}))
    if date_note:
        col.add(_text_from_props(str(date_note), {"font": "body"}))
    return col


def _build_text(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> TextWidget:
    txt = resolve(node.get("text", ""))
    p = dict(props)
    if "color" in p:
        p["fill"] = p.pop("color")
    return _text_from_props(str(txt), p)


def _build_spacer(props: Dict[str, Any]) -> Spacer:
    return _spacer_from_props(props)


def _build_kpi_card(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> KPIWidget:
    k_title = resolve(node.get("title"))
    k_value = resolve(node.get("value"))
    k_delta = resolve(node.get("delta"))
    return KPIWidget(title=str(k_title or ""), value=str(k_value or ""), delta=k_delta)


def _build_table(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> Any:
    table_data = _table_from_node(node, resolve)
    return _table_from_props(table_data, props)


def _build_image(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> Spacer | ImageWidget:
    src_val = resolve(node.get("src"))
    if isinstance(src_val, str) and src_val:
        fit = str(props.get("fit", "contain")).lower()
        radius = _int_from_props(props, "radius", 0)
        try:
            opacity = float(props.get("opacity", 1.0))
        except Exception:
            opacity = 1.0
        align = str(props.get("align", "center")).lower()
        return ImageWidget(src=src_val, fit=fit, radius=radius, opacity=opacity, align=align)
    return Spacer(10)


def _build_progress(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> ProgressBarWidget:
    raw = resolve(node.get("value"))
    label = resolve(node.get("label"))
    try:
        v = float(raw)
        if v > 1.0:
            v = v / 100.0
    except Exception:
        v = 0.0
    bar_h = _int_from_props(props, "bar_height", 18)
    bg = props.get("bg_fill")
    fill = props.get("fill")
    return ProgressBarWidget(
        value=v,
        label=str(label) if label is not None else None,
        bar_height=bar_h,
        bg_fill=bg if bg is not None else COLORS.MUTED,
        fill=fill if fill is not None else COLORS.SUCCESS,
    )


def _build_status_badge(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn) -> StatusBadgeWidget:
    text = resolve(node.get("text"))
    if text is None:
        text = ""
    variant = str(props.get("variant", "secondary"))
    return StatusBadgeWidget(text=str(text), variant=variant)


def _build_row_or_column(
    node: Dict[str, Any],
    props: Dict[str, Any],
    resolve: ResolveFn,
    builder: BuilderFn,
    *,
    is_row: bool,
) -> FlexContainer:
    gap = _int_from_props(props, "gap", DIMENSIONS.GAP_MEDIUM)
    cont = FlexContainer(
        direction="row" if is_row else "column", gap=gap, align_items="stretch"
    )
    # Apply full properties bag so callers can style containers (padding, bg, shadow, etc.)
    merged = dict(props)
    merged.setdefault("gap", gap)
    cont = _apply_container_defaults(cont, merged)
    for child in node.get("children", []) or []:
        w = builder(child)
        grow: float = 0.0
        shrink: float = 1.0
        basis: Optional[int] = None
        cprops = _norm_props(child.get("properties", {}) if isinstance(child, dict) else {})
        ratio = cprops.get("width_ratio")
        fill_remaining = bool(cprops.get("fill_remaining"))
        height_prop = cprops.get("height")

        if is_row:
            if isinstance(ratio, (int, float)):
                grow = float(ratio)
                # If an item explicitly opts out of growth (width_ratio=0),
                # do not shrink it when space is tight. This keeps intrinsic
                # width for things like short text labels next to KPIs.
                if grow == 0.0:
                    shrink = 0.0
            else:
                grow = 1.0
        else:
            grow = 1.0 if fill_remaining else 0.0
            if height_prop is not None:
                try:
                    basis = int(height_prop)
                except Exception:
                    basis = None
        cont.add(w, grow=grow, shrink=shrink, basis=basis)
    return cont


def _build_grid(node: Dict[str, Any], props: Dict[str, Any], resolve: ResolveFn, builder: BuilderFn) -> FlexContainer:
    cols = _int_from_props(props, "columns", 2)
    gap = _int_from_props(props, "gap", DIMENSIONS.GAP_MEDIUM)
    children = node.get("children", []) or []
    grid_col = FlexContainer(direction="column", gap=gap)
    for i in range(0, len(children), cols):
        row = FlexContainer(direction="row", gap=gap)
        for c in children[i : i + cols]:
            row.add(builder(c), grow=1.0)
        grid_col.add(row)
    return grid_col


def build_layout_from_declarative(data: Dict[str, Any]) -> FlexContainer:
    defs = data.get("layout", [])
    canvas_cfg = data.get("canvas") or {}

    def _resolve_field(v: Any) -> Any:
        return resolve_field(data, v)

    def build_node(node: Dict[str, Any]) -> FlexContainer | TextWidget | KPIWidget | Spacer | ImageWidget | ProgressBarWidget | StatusBadgeWidget:
        t = node.get("type")
        props = _norm_props(node.get("properties", {}) or {})

        # Structural pattern matching on the node type
        match t:
            case "title":
                widget = _build_title(node, props, _resolve_field)
            case "text":
                widget = _build_text(node, props, _resolve_field)
            case "spacer":
                widget = _build_spacer(props)
            case "kpi_card":
                widget = _build_kpi_card(node, props, _resolve_field)
            case "table":
                widget = _build_table(node, props, _resolve_field)
            case "image":
                widget = _build_image(node, props, _resolve_field)
            case "progress":
                widget = _build_progress(node, props, _resolve_field)
            case "status_badge":
                widget = _build_status_badge(node, props, _resolve_field)
            case "row":
                widget = _build_row_or_column(node, props, _resolve_field, build_node, is_row=True)
            case "column":
                widget = _build_row_or_column(node, props, _resolve_field, build_node, is_row=False)
            case "grid":
                widget = _build_grid(node, props, _resolve_field, build_node)
            case _:
                widget = Spacer(DIMENSIONS.GAP_SMALL)

        # Optional margins wrapper
        return _wrap_with_margins(widget, props)

    root = FlexContainer(
        direction="column",
        gap=DIMENSIONS.GAP_MEDIUM,
        padding=DIMENSIONS.PADDING,
        align_items="stretch",
    )
    # Allow document-level canvas options to influence the root container spacing
    try:
        if isinstance(canvas_cfg, dict):
            if canvas_cfg.get("padding") is not None:
                root.padding = int(canvas_cfg.get("padding"))
            if canvas_cfg.get("gap") is not None:
                root.gap = int(canvas_cfg.get("gap"))
    except Exception:
        # ignore bad values; validator ignores extras in canvas
        pass

    # Optional outer margins at the top/bottom of the document
    def _int_or_zero(v: Any) -> int:
        try:
            return int(v)
        except Exception:
            return 0

    top_margin = _int_or_zero(canvas_cfg.get("top_margin") or canvas_cfg.get("margin_top"))
    bottom_margin = _int_or_zero(canvas_cfg.get("bottom_margin") or canvas_cfg.get("margin_bottom"))

    if top_margin > 0:
        root.add(Spacer(top_margin))
    for comp in defs:
        root.add(build_node(comp))
    if bottom_margin > 0:
        root.add(Spacer(bottom_margin))
    return root

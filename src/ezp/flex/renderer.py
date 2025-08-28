from __future__ import annotations

from typing import Dict, Any, List

from PIL import Image, ImageDraw

from .engine import FlexContainer
from .widgets import KPIWidget, TableWidget, Spacer
from ..components import COLORS, DIMENSIONS, FONTS
from ..components.config import set_scale, reset_scale
from .engine import TextWidget, resolve_path


def build_layout_from_data(data: Dict[str, Any]) -> FlexContainer:
    root = FlexContainer(direction="column", gap=16, padding=16, align_items="stretch")

    # Header
    from .engine import TextWidget  # local import to avoid circular
    header = FlexContainer(direction="row", gap=16, align_items="center", justify_content="space-between", padding=24)
    header.add(TextWidget(str(data.get("title", "Dashboard"))), grow=1.0)
    if data.get("date_note"):
        header.add(TextWidget(str(data.get("date_note"))))
    root.add(header, basis=112)

    # Top KPIs
    kpis = data.get("top_kpis") or []
    if kpis:
        kpi_row = FlexContainer(direction="row", gap=16, padding=16)
        for k in kpis:
            kpi_row.add(KPIWidget(
                title=str(k.get("title", "")),
                value=str(k.get("value", "")),
                delta=k.get("delta"),
            ), grow=1.0, basis=220)
        root.add(kpi_row, basis=170)

    # Platform table (supports dict with headers/rows or list-of-lists)
    table_data = data.get("platform_table") or data.get("platform_rows") or []
    if table_data:
        # Heuristic: if list-of-lists and likely includes header in first row, convert
        if isinstance(table_data, list) and table_data and isinstance(table_data[0], list):
            first = table_data[0]
            if all(isinstance(x, str) for x in first):
                # treat first as headers
                table_data = {"headers": first, "rows": table_data[1:]}

        # Fill available vertical space and prefer shrinking rows over truncation
        table = TableWidget(table_data, fill_height=True, fit="shrink", min_row_height=24)
        section = FlexContainer(direction="column", padding=8)
        section.add(table, grow=1.0)
        root.add(section, grow=1.0)

    return root


def render_dashboard_with_flex(data: Dict[str, Any], out_path: str = "dashboard.png") -> str:
    """
    Render with effectively unconstrained height then crop to the final canvas.

    This avoids per-widget truncation/shrink decisions by letting content lay out
    naturally, and clipping at the end. Protects memory with a sane max height.
    """
    # Capture base width/height before scaling
    base_W, base_H = DIMENSIONS.WIDTH, DIMENSIONS.HEIGHT
    W, H_default = base_W, base_H
    canvas_cfg = (data.get("canvas") or {}) if isinstance(data, dict) else {}

    # Default to auto-height unless explicitly disabled
    auto_height: bool = True
    fixed_height_override: int | None = None

    # Interpret explicit canvas.height setting
    if "height" in canvas_cfg:
        hv = canvas_cfg.get("height")
        if isinstance(hv, str):
            if hv.lower() == "auto":
                auto_height = True
            elif hv.lower() == "fixed":
                auto_height = False
        elif isinstance(hv, int):
            auto_height = False
            fixed_height_override = hv

    # Top-level switch can override
    if isinstance(data, dict) and "auto_height" in data:
        auto_height = bool(data.get("auto_height"))

    # Bounds for auto height
    max_auto_h = int(canvas_cfg.get("max_height", H_default * 10)) if auto_height else H_default
    min_auto_h = int(canvas_cfg.get("min_height", H_default)) if auto_height else H_default

    # If a declarative layout is provided, adapt it to Flex; otherwise, build from basic data
    if isinstance(data.get("layout"), list):
        root = build_layout_from_declarative(data)
    else:
        root = build_layout_from_data(data)

    # Apply supersampling scale if requested
    scale = float(canvas_cfg.get("scale", 1.0))
    downscale = bool(canvas_cfg.get("downscale", False))
    if scale and scale != 1.0:
        set_scale(scale)
        # refresh scaled W/H
        W, H_default = DIMENSIONS.WIDTH, DIMENSIONS.HEIGHT

    # Measure preferred height with a huge available height (scaled)
    probe_img = Image.new("RGB", (W, 10), COLORS.BACKGROUND)
    probe_draw = ImageDraw.Draw(probe_img)
    _, preferred_h = root.measure(probe_draw, W, 10_000_000)

    if auto_height:
        # Choose final height based on content within bounds
        final_h = max(min_auto_h, min(preferred_h, max_auto_h))
        img = Image.new("RGB", (W, final_h), COLORS.BACKGROUND)
        draw = ImageDraw.Draw(img)
        root.render(draw, 0, 0, W, final_h)
        if scale != 1.0 and downscale:
            # Downsample to base size with high-quality filter
            target_h = max(int(final_h / scale), 1)
            img = img.resize((base_W, target_h), Image.LANCZOS)
        img.save(out_path)
    else:
        # Cap offscreen height to avoid excessive memory usage
        H_page = fixed_height_override or H_default
        MAX_OFFSCREEN = H_page * 5
        off_h = max(H_page, min(preferred_h, MAX_OFFSCREEN))

        # Render to offscreen then crop to fixed page height
        off = Image.new("RGB", (W, off_h), COLORS.BACKGROUND)
        off_draw = ImageDraw.Draw(off)
        root.render(off_draw, 0, 0, W, off_h)

        final = off.crop((0, 0, W, H_page)) if off_h != H_page else off
        if scale != 1.0 and downscale:
            final = final.resize((base_W, int(H_page / scale)), Image.LANCZOS)
        final.save(out_path)
    # Always restore scale back to 1x for subsequent runs
    if scale and scale != 1.0:
        reset_scale()
    return out_path


# -----------------------
# Declarative -> Flex adapter
# -----------------------

def _resolve_ref(data: Dict[str, Any], ref: Any) -> Any:
    if ref is None:
        return None
    ctx = data.get("data", data)
    if isinstance(ref, str):
        s = ref.strip()
        if s.startswith("$"):
            return resolve_path(s, ctx)
        # legacy dot/index
        cur = ctx
        for tok in s.split('.'):
            if isinstance(cur, dict):
                if '[' in tok and tok.endswith(']'):
                    key, idxs = tok[:-1].split('[', 1)
                    cur = cur.get(key)
                    try:
                        cur = cur[int(idxs)] if isinstance(cur, list) else None
                    except Exception:
                        return None
                else:
                    cur = cur.get(tok)
            elif isinstance(cur, list):
                try:
                    cur = cur[int(tok)]
                except Exception:
                    return None
            else:
                return None
        return cur
    if isinstance(ref, int):
        kpis = ctx.get('top_kpis', []) if isinstance(ctx, dict) else []
        return kpis[ref] if 0 <= ref < len(kpis) else None
    if isinstance(ref, list):
        return [_resolve_ref(data, r) for r in ref]
    return None


def _font_from_name(name: str):
    mapping = {
        "title": FONTS.H1,
        "heading": FONTS.H2,
        "body": FONTS.BODY,
        "caption": FONTS.SMALL,
        "table": FONTS.TABLE,
    }
    return mapping.get(name, FONTS.BODY)


def build_layout_from_declarative(data: Dict[str, Any]) -> FlexContainer:
    defs = data.get("layout", [])

    def build_node(node: Dict[str, Any]) -> FlexContainer | TextWidget | KPIWidget | TableWidget | Spacer:
        t = node.get("type")
        props = node.get("properties", {}) or {}
        ref = node.get("data_ref")

        if t == "title":
            title_text = ""
            date_note = ""
            val = _resolve_ref(data, ref)
            if isinstance(val, dict):
                title_text = str(val.get("title", ""))
                date_note = str(val.get("date_note", ""))
            elif isinstance(val, str):
                title_text = val
            col = FlexContainer(direction="column", gap=10, padding=0, align_items="start")
            if title_text:
                col.add(TextWidget(title_text, font=_font_from_name("title")))
            if date_note:
                col.add(TextWidget(date_note, font=_font_from_name("body")))
            return col

            
        if t == "text":
            txt = props.get("text", "")
            val = _resolve_ref(data, ref)
            if isinstance(val, str):
                txt = val
            font = _font_from_name(props.get("font", "body"))
            align = props.get("align", "left")
            color = props.get("color")
            w = TextWidget(txt, font=font, align=align)
            if color:
                # TextWidget supports fill color via constructor
                w.fill = color  # type: ignore
            return w

        if t == "spacer":
            return Spacer(int(props.get("height", DIMENSIONS.GAP_MEDIUM)))

        if t == "kpi_card":
            k = _resolve_ref(data, ref) or {}
            return KPIWidget(
                title=str(k.get("title", "")),
                value=str(k.get("value", "")),
                delta=k.get("delta"),
            )

        if t == "table":
            table_data = _resolve_ref(data, ref) or []
            fill_height = bool(props.get("fill_height")) or bool(props.get("fill_remaining")) or bool(props.get("height"))
            fit = props.get("fit", "truncate")
            min_row_h = int(props.get("min_row_height", 28))
            max_row_h = int(props.get("max_row_height", 90))
            shrink_floor = int(props.get("shrink_row_height_floor", 14))
            return TableWidget(
                table_data,
                fill_height=fill_height,
                row_height=None,
                header_height=None,
                min_row_height=min_row_h,
                max_row_height=max_row_h,
                fit=fit,
                shrink_row_height_floor=shrink_floor,
            )

        if t in ("row", "column"):
            gap = int(props.get("gap", DIMENSIONS.GAP_MEDIUM))
            is_row = t == "row"
            cont = FlexContainer(direction="row" if is_row else "column", gap=gap, align_items="stretch")
            for child in node.get("children", []) or []:
                w = build_node(child)
                grow = 0.0
                basis = None
                cprops = child.get("properties", {}) if isinstance(child, dict) else {}
                # width_ratio approximated via grow weights for rows
                ratio = cprops.get("width_ratio")
                # fill_remaining for columns -> grow
                fill_remaining = bool(cprops.get("fill_remaining"))
                height_prop = cprops.get("height")
                if is_row:
                    if isinstance(ratio, (int, float)):
                        grow = float(ratio)
                    else:
                        grow = 1.0
                else:
                    # column: default no grow unless fill_remaining
                    grow = 1.0 if fill_remaining else 0.0
                    if height_prop is not None:
                        try:
                            basis = int(height_prop)
                        except Exception:
                            basis = None
                cont.add(w, grow=grow, basis=basis)
            return cont

        if t == "grid":
            cols = int(props.get("columns", 2))
            gap = int(props.get("gap", DIMENSIONS.GAP_MEDIUM))
            children = node.get("children", []) or []
            grid_col = FlexContainer(direction="column", gap=gap)
            for i in range(0, len(children), cols):
                row = FlexContainer(direction="row", gap=gap)
                for c in children[i:i+cols]:
                    row.add(build_node(c), grow=1.0)
                grid_col.add(row)
            return grid_col

        # Fallback: empty spacer
        return Spacer(DIMENSIONS.GAP_SMALL)

    root = FlexContainer(direction="column", gap=DIMENSIONS.GAP_MEDIUM, padding=DIMENSIONS.PADDING, align_items="stretch")
    for comp in defs:
        root.add(build_node(comp))
    return root

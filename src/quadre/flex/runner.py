from __future__ import annotations

from typing import Dict, Any

from PIL import Image, ImageDraw, ImageFilter

from ..components import COLORS, DIMENSIONS
from ..components.config import apply_theme, set_scale, reset_scale
from ..theme import (
    load_theme_from_env_or_default,
    as_apply_theme_dict,
    widget_defaults_from_theme,
)
from .defaults import set_widget_defaults
from .adapter import build_layout_from_declarative
from ..plugins import dispatch_outputs


def build_dashboard_image(data: Dict[str, Any]) -> Image.Image:
    """
    Build and return the final rendered dashboard image (Pillow Image).

    Notes:
    - Applies theme and scaling and restores global scale after rendering
    - Does NOT save to disk; callers decide how to persist the image
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
    max_auto_h = (
        int(canvas_cfg.get("max_height", H_default * 10)) if auto_height else H_default
    )
    # Default to 0 in auto-height so the image can shrink below the base page
    # height when no explicit min_height is provided.
    min_auto_h = (
        int(canvas_cfg.get("min_height", 0)) if auto_height else H_default
    )

    # Load validated theme (env var quadre_THEME or bundled default), then allow doc-level overrides
    base_theme = load_theme_from_env_or_default()
    apply_theme(as_apply_theme_dict(base_theme))
    # Expose per-widget defaults from theme to the flex defaults provider
    set_widget_defaults(widget_defaults_from_theme(base_theme))

    # Optional theme application from document (top-level 'theme' can be dict or path to JSON file)
    theme_obj = None
    if isinstance(data, dict) and data.get("theme") is not None:
        theme_val = data.get("theme")
        if isinstance(theme_val, str):
            try:
                import json as _json
                from pathlib import Path as _Path

                theme_obj = _json.loads(_Path(theme_val).read_text(encoding="utf-8"))
            except Exception:
                theme_obj = None
        elif isinstance(theme_val, dict):
            theme_obj = theme_val
    if theme_obj:
        apply_theme(theme_obj)

    root = build_layout_from_declarative(data)

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
    setattr(probe_draw, "_quadre_image", probe_img)
    _, preferred_h = root.measure(probe_draw, W, 10_000_000)

    # Optional default outer margin for auto-height if none specified at canvas level.
    # This avoids content visually touching the bottom edge while keeping
    # backward compatibility (explicit canvas margins take precedence).
    has_canvas_margins = any(
        k in canvas_cfg for k in ("top_margin", "bottom_margin", "margin_top", "margin_bottom")
    )
    default_auto_bottom_margin = 0 if not auto_height else (0 if has_canvas_margins else DIMENSIONS.GAP_MEDIUM)

    # Render to a final image object
    if auto_height:
        # Choose final height based on content within bounds
        final_h = max(min_auto_h, min(preferred_h + default_auto_bottom_margin, max_auto_h))
        img = Image.new("RGB", (W, final_h), COLORS.BACKGROUND)
        draw = ImageDraw.Draw(img)
        setattr(draw, "_quadre_image", img)
        root.render(draw, 0, 0, W, final_h)
        if scale != 1.0 and downscale:
            # Downsample to base size with high-quality filter. Use rounding to
            # avoid systematic 1px cropping when final_h is not an exact
            # multiple of the scale factor.
            target_h = max(int(round(final_h / scale)), 1)
            img = img.resize((base_W, target_h), Image.LANCZOS)
        final_img = img
    else:
        # Cap offscreen height to avoid excessive memory usage
        H_page = fixed_height_override or H_default
        MAX_OFFSCREEN = H_page * 5
        off_h = max(H_page, min(preferred_h, MAX_OFFSCREEN))

        # Render to offscreen then crop to fixed page height
        off = Image.new("RGB", (W, off_h), COLORS.BACKGROUND)
        off_draw = ImageDraw.Draw(off)
        setattr(off_draw, "_quadre_image", off)
        root.render(off_draw, 0, 0, W, off_h)

        final = off.crop((0, 0, W, H_page)) if off_h != H_page else off
        if scale != 1.0 and downscale:
            final = final.resize((base_W, int(round(H_page / scale))), Image.LANCZOS)
        final_img = final

    # Optional unsharp mask to improve perceived text crispness after downscale.
    # Accepts canvas.sharpen as:
    #  - bool: True -> mild default
    #  - float: 0..1 amount
    #  - dict: { amount?:0..1, radius?:float, percent?:int, threshold?:int }
    sharpen_val = canvas_cfg.get("sharpen")
    amount: float = 0.0
    radius: float | None = None
    percent: int | None = None
    threshold: int | None = None
    try:
        if isinstance(sharpen_val, dict):
            raw_amount = sharpen_val.get("amount")
            amount = float(raw_amount) if raw_amount is not None else 0.3
            radius = float(sharpen_val.get("radius")) if sharpen_val.get("radius") is not None else None
            percent = int(sharpen_val.get("percent")) if sharpen_val.get("percent") is not None else None
            threshold = int(sharpen_val.get("threshold")) if sharpen_val.get("threshold") is not None else None
        elif isinstance(sharpen_val, bool):
            amount = 0.3 if sharpen_val else 0.0
        elif sharpen_val is None:
            amount = 0.0
        else:
            amount = float(sharpen_val)
        amount = max(0.0, min(1.0, amount))
    except Exception:
        amount = 0.0
    if amount > 0.0 and isinstance(final_img, Image.Image):
        use_radius = radius if radius is not None else 1.0
        # If percent not explicitly provided, adapt sharpening strength to scale
        # so that higher supersampling factors don't over-thin text.
        if percent is None:
            # Base curve around 150% at amount=1 and scale=1, reduce with sqrt(scale)
            use_percent = max(1, int(150 * amount / (max(1.0, scale) ** 0.5)))
        else:
            use_percent = int(percent)
        use_percent = max(1, min(use_percent, 500))
        # For large scale factors, add a tiny threshold to avoid thinning
        if threshold is None and scale >= 2.5:
            use_threshold = 1
        else:
            use_threshold = max(0, threshold) if threshold is not None else 0
        final_img = final_img.filter(
            ImageFilter.UnsharpMask(radius=use_radius, percent=use_percent, threshold=use_threshold)
        )

    # Always restore scale back to 1x for subsequent runs
    if scale and scale != 1.0:
        reset_scale()
    return final_img


def render_dashboard_with_flex(
    data: Dict[str, Any], out_path: str = "dashboard.png"
) -> str:
    """
    Render with effectively unconstrained height then crop to the final canvas.

    This avoids per-widget truncation/shrink decisions by letting content lay out
    naturally, and clipping at the end. Protects memory with a sane max height.

    Output dispatch is handled via the plugin system. By default, a built-in
    'file' plugin writes the image to `out_path` to preserve existing behavior.
    Users may specify `output` or `outputs` in the document to send the image to
    other destinations in addition to (or instead of) the file.
    """
    final_img = build_dashboard_image(data)
    outputs_spec = (data.get("outputs") if isinstance(data, dict) else None) or (
        data.get("output") if isinstance(data, dict) else None
    )
    dispatch_outputs(final_img, outputs_spec, default_path=out_path, doc=data)
    return out_path

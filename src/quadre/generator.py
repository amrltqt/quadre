from __future__ import annotations

import cairo

from quadre.models import DocumentDef

from quadre.config import (
    COLORS,
    DIMENSIONS,
    apply_theme,
    set_custom_font_family,
    set_scale,
    get_current_scale,
    get_custom_font_family,
)
from quadre.theme import (
    load_theme_from_env_or_default,
    as_apply_theme_dict,
    widget_defaults_from_theme,
)
from quadre.defaults import set_widget_defaults
from quadre.flex import render_tree
from quadre.cairo_canvas import CairoCanvas


def generate_image(document: DocumentDef) -> cairo.ImageSurface:
    """Build and return the final rendered dashboard image (Cairo surface)."""
    previous_scale = get_current_scale()
    previous_font_family = get_custom_font_family()

    canvas_cfg = document.canvas

    try:
        # Normalise to base scale before applying document overrides
        set_scale(1.0)

        # Determine target output width (pre-supersampling)
        base_w = max(1, int(DIMENSIONS.WIDTH))
        target_width = (
            canvas_cfg.width
            if canvas_cfg is not None and canvas_cfg.width is not None
            else base_w
        )
        target_width = max(1, int(target_width))

        render_scale = (
            float(canvas_cfg.scale)
            if canvas_cfg is not None and canvas_cfg.scale is not None
            else 1.0
        )
        if render_scale <= 0:
            render_scale = 1.0

        # Apply canvas-level font override before theme loads fonts
        canvas_font = canvas_cfg.font_family if canvas_cfg is not None else None
        set_custom_font_family(canvas_font)

        set_scale(render_scale)

        # Load validated theme (env var quadre_THEME or bundled default), then allow doc-level overrides
        base_theme = load_theme_from_env_or_default()
        apply_theme(as_apply_theme_dict(base_theme))
        # Expose per-widget defaults from theme to the flex defaults provider
        set_widget_defaults(widget_defaults_from_theme(base_theme))

        # Optional theme application from document (top-level 'theme' can be dict or path to JSON file)
        theme_obj = None
        if isinstance(document, dict) and document.get("theme") is not None:
            theme_val = document.get("theme")
            if isinstance(theme_val, str):
                try:
                    import json as _json
                    from pathlib import Path as _Path

                    theme_obj = _json.loads(
                        _Path(theme_val).read_text(encoding="utf-8")
                    )
                except Exception:
                    theme_obj = None
            elif isinstance(theme_val, dict):
                theme_obj = theme_val
        if theme_obj:
            apply_theme(theme_obj)

        root = render_tree(document)

        render_width = max(1, int(round(target_width * render_scale)))

        # Measure preferred height with a huge available height (scaled)
        probe_canvas = CairoCanvas.create(render_width, 10)
        _, preferred_h = root.measure(probe_canvas, render_width, 10_000_000)

        preferred_h = max(0, int(preferred_h))

        # Optional default outer margin for auto-height if none specified at canvas level.
        # This avoids content visually touching the bottom edge while keeping
        # backward compatibility (explicit canvas margins take precedence).
        default_auto_bottom_margin = (
            0 if canvas_cfg and canvas_cfg.margin else DIMENSIONS.GAP_MEDIUM
        )
        default_auto_bottom_margin = max(0, int(default_auto_bottom_margin))

        render_height = preferred_h + default_auto_bottom_margin
        render_height = max(1, render_height)

        canvas = CairoCanvas.create(render_width, render_height, COLORS.BACKGROUND)
        root.render(canvas, 0, 0, render_width, render_height)

        surface: cairo.ImageSurface = canvas.surface

        if render_scale != 1.0:
            output_height = max(1, int(round(render_height / render_scale)))
            downsampled = cairo.ImageSurface(cairo.FORMAT_ARGB32, target_width, output_height)
            ctx = cairo.Context(downsampled)
            ctx.scale(target_width / render_width, output_height / render_height)
            ctx.set_source_surface(surface, 0, 0)
            ctx.paint()
            surface = downsampled

        return surface
    finally:
        set_custom_font_family(previous_font_family)
        set_scale(previous_scale)


__all__ = ["generate_image"]

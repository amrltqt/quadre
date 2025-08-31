# Architecture

This document explains how Quadre is structured and how a JSON document becomes a rendered PNG. The goal is a small, readable core that is easy to extend with new widgets and layouts.

## High‑Level Overview

Quadre is organized around three layers:

1) Flex layout engine (how things are measured and positioned)
2) Widgets (what is drawn inside boxes)
3) Adapters and runners (how JSON is turned into a tree and rendered)

The “Flex” layer is intentionally simple and focused on layout. Visuals live in the “components” layer and are wrapped by lightweight Flex widgets.

## Data Flow

Document (JSON) → validation → adapter builds a Flex tree → runner applies theme/scale → engine measures preferred height → engine renders into an image → optional downscale/sharpen → plugins write outputs.

## Key Modules

Flex Engine (src/quadre/flex/engine.py)
- Widget: the base interface with two methods: `measure(draw, avail_w, avail_h)` and `render(draw, x, y, w, h)`.
- FlexContainer: flexbox‑like container supporting `direction=row|column`, `gap`, `padding`, cross‑axis `align_items`, main‑axis `justify_content`, per‑child `grow/shrink/basis`, optional rounded background and (opt‑in) soft shadow, and clipping of children to their boxes.

Flex Widgets (src/quadre/flex/widgets.py)
- TextWidget: single‑line text with CJK‑aware segmentation. Font size is resolved at render time from `FONTS` so supersampling/scaling remains consistent. Height uses font metrics (ascent+descent) with a small safety pad to avoid descender clipping.
- KPIWidget: draws a KPI card by delegating to the components layer.
- TableWidget: bridges document table payloads to the `EnhancedTable` component.
- Spacer and utility widgets.

Adapters & Runner (src/quadre/flex)
- adapter.build_layout_from_declarative: interprets the declarative `layout` array. Supports node types such as `title`, `text`, `spacer`, `kpi_card`, `table`, `row`, `column`, `grid`. Container properties (gap, padding, bg_fill/outline/radius, shadow, etc.) are applied on FlexContainer.
- helpers: shared builders for text/table/spacer and theme‑driven defaults.
- runner.build_dashboard_image / render_dashboard_with_flex: load theme, apply supersampling, measure preferred height, render, then optionally downscale and apply an unsharp mask. Canvas options include `height` (auto/fixed/px), `min_height`, `max_height`, `scale`, `downscale`, `sharpen`, `padding`, `gap`, and `top/bottom_margin`.

Components (src/quadre/components)
- config: global `COLORS`, `DIMENSIONS`, `FONTS` + `set_scale/reset_scale/apply_theme`. This is the only place where font sizes and scaling are managed.
- primitives: low‑level drawing helpers (rounded rectangles, badges, text helpers).
- cards: visual KPI/section cards used by KPIWidget.
- tables: table engine (`EnhancedTable`, `ColumnDefinition`, `TableStyle`).

Validation (src/quadre/validator.py)
- Pydantic models describe the declarative JSON. The validator provides helpful errors (e.g., missing required fields) and warnings (unknown properties, invalid colors). It also verifies that DataRef paths resolve when a `data` context exists.

CLI & Library Entrypoints
- src/quadre/cli.py: `quadre` (render) and `quadre-validate` (validate) commands.
- src/quadre/main.py: library functions such as `render_dashboard` and in‑memory bytes rendering.
- src/quadre/api.py: high‑level Python API (render/build_image/to_bytes) and output plugin registry.

Theme System (src/quadre/theme.py)
- Validated theme with colors, font sizes, and per‑widget defaults. The runner loads a theme (bundled default or file from `quadre_THEME`) and exposes widget defaults to the flex layer.
- `apply_theme` updates colors and font sizes dynamically. Theme tokens are resolved case‑insensitively via `parse_color`.

Typed Builder (src/quadre/flex/api.py)
- Optional fluent API to create documents in Python: `Row`, `Column`, `Grid`, `Text`, `Title`, `KPI`, `Table`, `Spacer`, `Progress`, `StatusBadge`, plus `doc()` and `dref()`.
- Builders return JSON compatible with the validator/adapter so the same pipeline is used for rendering.

Plugins (src/quadre/plugins)
- The rendering result is dispatched to one or more outputs. The default “file” plugin writes to disk; a “bytes” plugin returns encoded bytes. Third‑party plugins can be registered and discovered via entry points.
- Registry (plugins/registry.py): defines `PluginFn`, `OutputContext`, a global registry, and `dispatch_outputs(image, outputs_spec, default_path, doc)`.
- Built‑ins (plugins/builtin.py): registers `file` and `bytes` on import.
- Loader (plugins/__init__.py): imports built‑ins and discovers external plugins in the `quadre.output_plugins` entry point group (either a callable or a module exposing `register(register_plugin)`).
- Programmatic helper (plugins/utils.py): `image_to_bytes(img, format)`.

Outputs Spec
- At the document level, you can specify either `output` (single) or `outputs` (list). Each item is a dict with at least `plugin` (name), plus optional `path` and other plugin‑specific keys. If unspecified, the runner uses the built‑in `file` plugin with the path/format implied by the CLI or API.
- Example:
  - `{"outputs": [ {"plugin": "file", "path": "out.webp", "format": "WEBP"}, {"plugin": "bytes"} ] }`

Writing a plugin
- Signature: `def my_plugin(image: PIL.Image, ctx: OutputContext, cfg: Mapping[str, Any]) -> Any`
- Register in code: `from quadre import register_output_plugin; register_output_plugin("my", my_plugin)`
- Or expose via entry points in your package metadata under group `quadre.output_plugins`.

## Rendering Pipeline Details

1) Validation (optional but recommended): run `quadre validate` to catch schema issues early.
2) Build flex tree: the adapter maps JSON nodes to FlexContainer/Widgets, applying theme defaults and per‑node properties.
3) Supersampling: if `canvas.scale > 1`, `set_scale()` updates dimensions and fonts to render at higher DPI.
4) Measure height: the flex root is measured with a very tall available height to determine the preferred content height.
5) Render: the tree renders into a canvas. Children are clipped to their boxes to prevent visual overlap.
6) Post‑processing: optional downscale back to base size (`downscale=true`) and optional sharpen (`sharpen: true|0..1|{amount,radius,percent,threshold}`).
7) Output: plugins receive the final PIL image and write it to the requested destinations.

## Fonts & Determinism

- Font sizes are always taken from `FONTS` at render time, so supersampling does not change perceived text size.
- Tests replace fonts with `ImageFont.load_default()` to keep rendering deterministic across platforms. Optional pixel tests are gated behind environment flags.
- Emoji rendering is not supported by design in the current version. CJK segmentation is handled so ideographs use an appropriate font when available.

## Extending Quadre

Add a declarative node type
- Extend `build_layout_from_declarative` with a new `type`.
- Map properties via `helpers` and create or reuse a widget.
- Update the validator whitelist for new properties and write targeted tests.

Add a new widget
- Implement a Widget in `src/quadre/flex/widgets.py` that draws using the components layer.
- Expose a helper in `helpers` if it’s reusable.
- Wire it in the adapter and (optionally) the typed builder.

Tuning visuals
- Prefer theme defaults for consistent style (colors, paddings, table styles).
- Container visuals (rounded background, outline, shadow) are opt‑in via container properties; they do not affect layout semantics.

## Non‑Goals / Notes

- No global mutable state besides scale/theme; the runner restores scale after each render.
- No implicit page backgrounds for containers; backgrounds are explicit or theme‑driven.
- Supersampling aims at crispness, not photorealistic effects. Paper‑like touches (light background, soft panels, optional shadows) are available but remain subtle.

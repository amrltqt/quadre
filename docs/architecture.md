# Architecture

The system has three main layers: the layout engine, the built-in components components, and the renderers/adapters.

Core modules
- Flex engine (src/quadre/flex/engine.py)
  - Widget: measure(draw, avail_w, avail_h) and render(draw, x, y, w, h)
  - FlexContainer: row/column layout, gap, padding, align/justify, grow/shrink/basis
  - TextWidget: segmented text drawing, consistent measurement via textbbox
  - resolve_path: simple JSONPath‑like resolver (e.g., $.a.b[0])
- Renderer (src/quadre/flex)
  - runner.render_dashboard_with_flex: theme/scale, measure preferred height, render & crop
  - adapter.build_layout_from_declarative: maps declarative JSON to a Flex layout
  - builder_basic.build_layout_from_data: basic non‑declarative path
  - helpers: defaults, Text/Table/Spacer constructors
- Components (src/quadre/components)
  - config: COLORS, DIMENSIONS, FONTS + set_scale/reset_scale/apply_theme
  - primitives: rounded rectangle, badges, text helpers
  - cards: KPI/section cards
  - tables: EnhancedTable + ColumnDefinition + TableStyle

CLI & validation
- src/quadre/__main__.py: `quadre` CLI (render/validate)
- src/quadre/main.py: library entry (`render_dashboard`)
- src/quadre/validator.py: Pydantic models and friendly validation for declarative JSON

Defaults & theming
- src/quadre/theme.py validates a Theme (colors, fonts, per-widget defaults)
- src/quadre/theme/theme.json bundles the default theme (override via quadre_THEME)
- parse_color in flex/defaults.py resolves theme tokens and hex colors
- apply_theme can change colors and font sizes/paths at runtime

Determinism
- Tests patch fonts to default for cross‑platform stability
- Optional pixel baselines can be recorded/checked behind env flags

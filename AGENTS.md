## Overview

This repository generates dashboard images from JSON using Pillow (PIL). It exposes a CLI to validate JSON and render PNGs. The core is a lightweight Flex layout engine with reusable components (text, KPI cards, tables), and a declarative JSON adapter.

- Language: Python 3.12+
- Core libs: Pillow, Pydantic
- Deterministic tests with font patching and optional pixel baselines

## Repo Map

- `src/quadre/main.py`: high‑level render entry (`render_dashboard`), CLI wiring via `ez-pillow`
- `src/quadre/__main__.py`: `quadre` CLI (render/validate subcommands)
- `src/quadre/validator.py`: JSON schema + validation (Pydantic 2)
- Flex engine and renderer:
  - `src/quadre/flex/engine.py`: primitives (`Widget`, `TextWidget`, `FlexContainer`, `resolve_path`)
  - `src/quadre/flex/widgets.py`: higher‑level widgets (`KPIWidget`, `TableWidget`, `Spacer`)
  - `src/quadre/flex/runner.py`: render pipeline (`render_dashboard_with_flex`)
  - `src/quadre/flex/adapter.py`: declarative JSON → flex layout
  - `src/quadre/flex/builder_basic.py`: simple data‑driven layout
  - `src/quadre/flex/helpers.py`: shared helpers (defaults, text/table/spacer construction)
  - `src/quadre/flex/defaults.py`: theme-driven widget defaults and color parsing
- `src/quadre/theme.py`, `src/quadre/theme/theme.json`: Pydantic theme and bundled defaults
  - Dark theme available at `src/quadre/theme/dark.json` (use with `quadre_THEME=src/quadre/theme/dark.json`)
- Components (UI building blocks):
  - `src/quadre/components/config.py`: colors, fonts, dimensions, DPI/scale, theme application
  - `src/quadre/components/primitives.py`: low‑level drawing helpers
  - `src/quadre/components/cards.py`: KPI/section cards
  - `src/quadre/components/tables.py`: table engine (columns, cell types, styles)
- Tests: `tests/` (validation, rendering, pixels, adapter margins, resolve_path)
- Examples: `examples/*.json`

## Entrypoints & Commands

- Render via Python module:
  - `uv run -m quadre.cli render data.json out/dashboard.png`
- CLI wrappers (installed):
  - `quadre render examples/declarative_featured.json out.png`
  - `quadre validate examples/declarative_featured.json`
- Make targets (Dockerized flow):
  - `make run examples/declarative_featured.json`
  - `make validate examples/declarative_featured.json`
  - `make run-dev DATA=examples/declarative_featured.json`

## Run Locally

- Python 3.12+ recommended (see `pyproject.toml`)
- With uv (preferred): `uv run -m quadre.cli render data.json out.png`
- Or install package then run `quadre`

## Tests

- Unit tests: `pytest -q` or `uv run pytest -q`
- Pixel tests (opt‑in): set `quadre_PIXELS=1` to enable; `quadre_RECORD=1` to record baselines
- Determinism: tests patch fonts to `ImageFont.load_default()` via `tests/conftest.py`
- New tests should follow existing patterns and avoid platform‑dependent assumptions

## Architecture

- Flex Engine (`engine.py`)
  - `Widget` (measure/render contract)
  - `FlexContainer` (row/column, gap, padding, align/justify, grow/shrink)
  - `TextWidget` (CJK segmentation, measures via `textbbox`)
  - `resolve_path` (simple JSONPath‑like resolver: `$.a.b[0]`)
- Renderer modules
  - `runner.render_dashboard_with_flex`: theme/scale, measure preferred height, render/crop
  - `adapter.build_layout_from_declarative`: interprets `layout` (types: title, text, spacer, kpi_card, table, row, column, grid). Supports `margin_top`/`margin_bottom` via `Spacer` wrappers. Data refs accept `{ "$": "$.path" }` or string paths; legacy `data_ref` is rejected by the validator.
  - `builder_basic.build_layout_from_data`: classic path without a declarative layout
  - `helpers`: constructs Text/Table/Spacer with centralized defaults
- Components
  - `config.py`: palette, dimensions, fonts (H1/H2/NUMBER/BODY/TABLE/SMALL), `set_scale`/`reset_scale`, `apply_theme`
  - `tables.py`: `EnhancedTable`, `ColumnDefinition`, `TableStyle`, cell renderers (bold/number/%), auto table builders
- Validator (`validator.py`)
  - Pydantic models per component type, `Content` union (str or DataRef)
  - Friendly errors (e.g., missing fields) and warnings (invalid colors, unknown properties)

## Data Model (JSON)

- Common top‑level keys: `canvas`, `data`, `layout`
- DataRef: `{ "ref" | "$ref" | "$": "$.path" }`
- `canvas`: `{ height: "auto" | "fixed" | number, min_height?, max_height?, scale?, downscale? }`
- `layout`: array of objects with `type` among: `title`, `text`, `spacer`, `kpi_card`, `table`, `row`, `column`, `grid`
- Each type supports a `properties` bag with a subset of keys (see validator)

## Styling / Theme / Fonts

- Colors and dimensions live in `components.config.COLORS` / `DIMENSIONS`
- Themes apply via `apply_theme(theme_dict)` or `canvas.theme` (dict or JSON file path)
- DPI/supersampling via `canvas.scale` + `canvas.downscale`
- Note: system fonts vary; tests swap to default fonts for stability

## Determinism & Gotchas

- Always restore scale via `reset_scale()` after `set_scale()` (handled in `runner`)
- Renders depend on fonts; use `FONTS.*` abstractions and avoid hardcoded paths
- The validator forbids legacy `data_ref`; prefer explicit fields (`text`, `title`, `value`, `table`, …)

## Playbooks (How‑to)

- Add a declarative type
  1) Extend `build_layout_from_declarative` (`src/quadre/flex/adapter.py`) in `build_node`
  2) Map `properties` via `_norm_props` and build the widget (or a `FlexContainer`)
  3) Add the prop to the validator whitelist if needed (`_post_validate_content_vs_props`)
  4) Test: unit tests + (optional) pixel tests

- Add a Flex widget
  1) Implement the class in `src/quadre/flex/widgets.py` (inherits from `Widget`)
  2) Expose construction via `helpers` if reusable
  3) Integrate in the adapter if used by `layout`

- Modify the table
  1) Adjust `EnhancedTable` (`components/tables.py`) or `TableWidget` (`flex/widgets.py`)
  2) Keep `measure()` consistent with `render()` (header/rows height + padding)

- Add a property (e.g., `margin_top`)
  1) Support in the adapter (insert `Spacer` when needed)
  2) Add the key to the props whitelist (validator) and warn for unknowns
  3) Targeted tests

## Conventions & Quality Bar

- Python 3.12+, type annotations required, concise docstrings
- Prefer pure functions and reusable helpers; avoid duplication
- Do not introduce persistent global state (always `reset_scale`)
- Tests: start small (unit), broaden as needed; pixels off by default
- Lint: ruff configured (see `pyproject.toml`); keep a simple, consistent style

## Troubleshooting

- Non‑deterministic render: check fonts; use the test fixture; pick a common font via `apply_theme(fonts={...})`
- Rejected JSON: run `quadre validate` for explicit errors (DataRef, types, props)
- Clipped content: check `canvas.max_height/min_height` and `TableWidget.fill_height/fit`

## Roadmap (suggestions)

- Refine validation of `properties` per component type (more contextual warnings)
- Extend the widget library (images, simple charts)
- Further factor styles (starter themes)

## Contacts / Ownership

- Maintainers: TODO
- Code owners: TODO

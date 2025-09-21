## Overview

This repository generates dashboard images from JSON using a Cairo-based renderer. It exposes a CLI to validate JSON and render PNGs. The core is a lightweight Flex layout engine with reusable components (text, KPI cards, tables), and a declarative JSON adapter.

- Language: Python 3.12+
- Core libs: Pycairo, Pydantic
- Deterministic tests with theme/font patching and optional pixel baselines

## Architecture

Data flows through `DocumentRef` → Layout Engine → Cairo Renderer → Image Buffer.
- **Layout**: Flexible containers (`Root`, `Row`, `Column`) with measure/render pipeline
- **Components**: Text-aware widgets with automatic truncation
- **Scale System**: Logical pixels auto-scaled for high-DPI rendering

## Critical Development Patterns

### Component Registry
```python
@component("my_component")  # Required decorator
class MyComponent(Component):
    # For containers with children:
    @field_validator("children", mode="before")
    @classmethod
    def parse_children(cls, v): ...  # Essential for nested components
```

### Text Handling
- All text **must** use `truncate_text()` utility to prevent overflow
- Components: `Title`, `Card`, `KPICard` auto-truncate with ellipsis

### Layout Pipeline
1. **Measure**: Return preferred size within constraints
2. **Render**: Draw exactly within provided bounds
3. Scale handled automatically via `px()` and `get_current_scale()`

## Key Modules

### Core Pipeline
- `generator.py`: Main render pipeline, handles scaling, theme loading, canvas creation
- `models.py`: Pydantic schemas for JSON validation (`DocumentDef`, `CanvasDef`)
- `cairo_canvas.py`: Wrapper around Cairo with text measurement and drawing utilities
- `main.py`: High-level API (`render_dashboard_bytes`)

### Component System
- `components/registry.py`: Component registration with `@component` decorator and `COMPONENTS` dict
- `components/text_utils.py`: Shared text truncation utilities (binary search algorithm)
- `components/base/title.py`: Text component with h1-h4 sizes, alignment, color support
- `components/base/card.py`: Simple text cards with auto-truncation
- `components/base/kpi_card.py`: KPI widgets with label/value/delta, multi-text truncation

### Layout Engine
- `flex/layout.py`: Entry point, creates Root from DocumentDef with canvas properties
- `flex/components/root.py`: Top-level container, vertical stacking, margin/width support
- `flex/components/row.py`: Horizontal flex container with justify_content/align_items
- `flex/components/column.py`: Vertical flex container with gap/alignment properties

### Configuration
- `config.py`: Global constants (`COLORS`, `DIMENSIONS`, `FONTS`) with scale support
- `font.py`: Font registry, handles family/size/weight with scaling
- `theme.py`: Theme loading and application system

## JSON Schema

```json
{
  "canvas": {"width": 800, "scale": 2, "margin": {"top": 40, "left": 60}},
  "components": [
    {"type": "title", "text": "Hello", "size": "h1", "align": "center"},
    {"type": "row", "gap": 20, "children": [
      {"type": "kpi_card", "label": "Sales", "value": "€1,234", "delta": 12.5}
    ]}
  ]
}
```

## Common Issues & Solutions

- **Missing child parsing**: Add `@field_validator("children")` to containers
- **Text overflow**: Always use `truncate_text()` utility
- **Scale confusion**: `avail_w/h` in render are already scaled
- **Component not found**: Import component file to register it

## Commands

```bash
quadre render examples/demo.json output.png
LOG_LEVEL=debug quadre render file.json out.png  # Debug layout
```

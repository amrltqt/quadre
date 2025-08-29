# Declarative Layout (JSON)

Top‑level structure
```json
{
  "canvas": { "height": "auto", "min_height": 600, "max_height": 1600, "scale": 1.0, "downscale": false },
  "data": { /* your values */ },
  "layout": [ /* list of components */ ]
}
```

Canvas
- height: "auto" (default), "fixed", or a number
- min_height, max_height: bounds for auto height
- scale (float) + downscale (bool): supersampling for high‑quality

Data references
- Use DataRef objects or strings pointing into `data`:
  - `{ "$": "$.path.to.value" }`, `{ "ref": "$.path" }`, `{ "$ref": "$.path" }`
  - "$.path" as a plain string also resolves via resolve_path

Components (layout array)
- Supported types: `title`, `text`, `spacer`, `kpi_card`, `table`, `row`, `column`, `grid`
- Common `properties`: `gap`, `align_items`, `justify_content`, `padding`, `bg_fill`, `bg_outline`, `bg_radius`, `margin_top`, `margin_bottom`
- Text `properties`: `font` (title|heading|body|caption|table), `fill`/`color`, `align`
- Table `properties`: `fill_height`, `min_row_height`, `max_row_height`, `fit` (truncate|shrink), `shrink_row_height_floor`
- Flow hints for children: `width_ratio`, `fill_remaining`, `height` (columns)

Examples
```json
{
  "type": "title",
  "title": { "$": "$.header.title" },
  "date_note": { "$": "$.header.date_note" }
}
```

```json
{
  "type": "row",
  "properties": { "gap": 16 },
  "children": [
    { "type": "kpi_card", "title": {"$": "$.kpis[0].title"}, "value": {"$": "$.kpis[0].value"} },
    { "type": "kpi_card", "title": {"$": "$.kpis[1].title"}, "value": {"$": "$.kpis[1].value"} }
  ]
}
```

Margins
- `margin_top` and `margin_bottom` add vertical space via automatic `Spacer` wrappers.

Validation
- Run `nada validate file.json` to get errors and helpful warnings
- The validator forbids legacy `data_ref`; use explicit fields (e.g., `title`, `text`, `table`)

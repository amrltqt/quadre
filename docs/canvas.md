# Canvas & Rendering

This page documents the `canvas` options that control page size, scaling, and outer spacing when rendering with the Flex engine.

## Height Modes

- `height: "auto"` (default): measures content and uses the preferred height, clamped between `min_height` and `max_height` if provided.
- `height: "fixed"` or a number: renders into an off‑screen surface and crops to the fixed height (protects against partial draws while keeping layout natural).

Recommended bounds in auto mode:

```json
{
  "canvas": { "height": "auto", "min_height": 600, "max_height": 1600 }
}
```

Fixed height examples:

```json
{ "canvas": { "height": 1080 } }
{ "canvas": { "height": "fixed" } }
```

## Supersampling

Render at higher DPI and (optionally) downscale for crisper text and edges:

- `scale: number` – e.g. `2.0` renders at 2× resolution
- `downscale: true|false` – when true, the final image is resized back to the base size using a high‑quality filter

```json
{
  "canvas": { "height": "auto", "scale": 2.0, "downscale": true }
}
```

## Sharpen (optional)

After downscaling, you can add a mild unsharp mask to improve perceived text crispness:

- `sharpen: true` – enable with a default mild amount
- `sharpen: 0.0..1.0` – control strength (0 disables; 0.25–0.4 recommended)
- `sharpen: { amount, radius, percent, threshold }` – advanced tuning

```json
{ "canvas": { "height": "auto", "scale": 2.0, "downscale": true, "sharpen": 0.3 } }

{ "canvas": { "height": "auto", "scale": 3.0, "downscale": true,
  "sharpen": { "amount": 0.35, "radius": 1.0, "percent": 180, "threshold": 0 } } }
```

Notes:
- Sharpen runs on the final image (post-resize). It is disabled by default and does not affect tests unless explicitly set.
- If you see halos, reduce `percent` or increase `threshold` slightly (e.g., 1–2).

## Root Spacing (padding, gap)

The root Flex container (column) can be tuned via canvas keys:

- `padding: number` – inner padding applied inside the page edges.
- `gap: number` – vertical spacing between top‑level blocks.

```json
{
  "canvas": { "height": "auto", "padding": 24, "gap": 12 }
}
```

Notes:
- These keys are handled by the declarative adapter. They are safe to include; the validator ignores unknown canvas fields.

## Outer Margins (top/bottom)

Add explicit space before/after the whole layout to avoid content touching the image edges in auto height:

- `top_margin` (alias `margin_top`)
- `bottom_margin` (alias `margin_bottom`)

```json
{
  "canvas": { "height": "auto", "top_margin": 16, "bottom_margin": 24 }
}
```

Under the hood, these are injected as `Spacer` widgets at the beginning/end of the root column.

Default: when using `height: "auto"` and no canvas margins are provided, the renderer adds a small bottom margin (equal to `GAP_MEDIUM`) to keep content away from the lower edge.

## Builder Examples

Using the typed builder (`quadre.api`):

```python
from quadre.api import doc, Title, Row, Text, KPI, dref, render

d = doc(
    Title("Demo"),
    Row().gap(12).add(
        Text("Headline").font("heading").no_grow(),
        KPI(title=dref("$.perf.title"), value=dref("$.perf.value")).grow(1),
    ),
    data={"perf": {"title": "Revenue", "value": "4,567k€"}},
    canvas={
        "height": "auto",
        "padding": 24,
        "gap": 12,
        "bottom_margin": 24,
    },
).to_dict()

render(d, path="out.png")
```

## Tips

- For a short text label next to flexible KPI cards, set the text to not grow: `properties.width_ratio: 0` (or `Text(...).no_grow()` with the builder). This preserves its intrinsic width and prevents overlap.
- Prefer `min_height`/`max_height` bounds in auto mode to keep images consistent across content changes.

# Troubleshooting

Non‑deterministic output
- Fonts differ across platforms. Use the test fixture or `apply_theme(fonts={...})` to select a common font.
- Ensure `reset_scale()` is called after `set_scale()` (handled by the runner).

Validation errors
- Run `nada validate file.json` to get structured errors and warnings (e.g., invalid colors, unknown properties).
- Legacy `data_ref` fields are not supported; use explicit content fields and DataRefs.

Clipped or overflowing content
- For auto height, set reasonable bounds in `canvas.min_height` / `max_height`.
- For tables, adjust `fill_height`, `fit`, and row height bounds in `properties`.

Docker font issues
- The image includes DejaVu fonts. To use a custom font, mount it and set `nada_FONT_PATH`.

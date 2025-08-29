# Output Plugins

Quadre supports a lightweight plugin system to send rendered images to different destinations.
File saving remains the default behavior, but you can add optional outputs like S3 without adding heavy deps to the core package.

## Concepts

- Plugin: a callable that receives the rendered `PIL.Image.Image`, an `OutputContext`, and a config dict.
- Dispatch: the renderer builds the image and dispatches to one or more plugins defined in the document under `output` or `outputs`.
- Builtins: `file` (write to disk) and `bytes` (return encoded bytes) are included.

Relevant code:
- `src/quadre/flex/runner.py:19` — `build_dashboard_image(data)` creates an image but does not save it.
- `src/quadre/flex/runner.py:135` — `render_dashboard_with_flex(data, out_path)` renders then dispatches outputs (default: file to `out_path`).
- `src/quadre/plugins/registry.py:13` — `OutputContext` (path, format, doc, size).
- `src/quadre/plugins/registry.py:33` — `register_plugin(name, fn)`.
- `src/quadre/plugins/registry.py:84` — `dispatch_outputs(image, outputs_spec, default_path, doc)`.
- `src/quadre/plugins/builtin.py:18` — built-in `file` plugin.
- `src/quadre/plugins/builtin.py:35` — built-in `bytes` plugin.

## Using outputs in JSON (optional)

You can opt-in to additional outputs by adding `output` or `outputs` at the top level of your document.

Accepted shapes:

1) String path — equivalent to the default file output
```
"output": "out.png"
```

2) Single object — explicit plugin and options
```
"output": { "plugin": "file", "path": "out.webp", "format": "WEBP" }
```

3) List — multiple outputs
```
"outputs": [
  { "plugin": "file", "path": "out.png" },
  { "plugin": "s3", "bucket": "my-bucket", "key": "dashboards/out.png" }
]
```

Notes:
- If no `output(s)` is provided, the renderer defaults to `file` at the `out_path` parameter.
- If `format` is not set, it is inferred from the path extension (`.png`→PNG, `.jpg`→JPEG, `.webp`→WEBP, default PNG).
- The CLI prints only the file path; plugin return values are not displayed. Programmatic callers can invoke `dispatch_outputs` directly to capture results.

## Built-in plugins

- `file`: writes the image to disk.
  - Options: `path` (override), `format` (e.g., `PNG`, `JPEG`, `WEBP`), `save_kwargs` (extra Pillow `save()` kwargs).
  - Code: `src/quadre/plugins/builtin.py:18`.

- `bytes`: returns encoded image bytes (useful programmatically, not via CLI).
  - Options: `format` (default from context).
  - Code: `src/quadre/plugins/builtin.py:35`.

## Programmatic usage (Python)

Get a Pillow image:
```
from quadre.flex.runner import build_dashboard_image

img = build_dashboard_image(doc)
```

Encode to bytes without touching disk:
```
from quadre.plugins import image_to_bytes

png_bytes = image_to_bytes(img, format="PNG")
```

Or one-shot helper that renders and returns bytes:
```
from quadre.main import render_dashboard_bytes

png_bytes = render_dashboard_bytes(doc)  # PNG by default
```

Let the renderer handle outputs (default file + extras):
```
from quadre.flex.runner import render_dashboard_with_flex

render_dashboard_with_flex(doc, "out.png")
```

## Writing a plugin (example: S3)

You can publish a separate package that registers a plugin so the core doesn’t depend on heavy SDKs.

Direct registration on import:
```
# quadre_plugin_s3/__init__.py
import io
import boto3
from quadre.plugins import register_plugin

def s3_plugin(image, ctx, cfg):
    # cfg expects: {"bucket": "...", "key": "...", "format"?: "PNG"|"JPEG"|...}
    buf = io.BytesIO()
    fmt = (cfg.get("format") or ctx.format)
    image.save(buf, format=fmt)
    buf.seek(0)
    boto3.client("s3").put_object(
        Bucket=cfg["bucket"], Key=cfg["key"], Body=buf.getvalue(),
        ContentType=f"image/{fmt.lower()}"
    )
    return f"s3://{cfg['bucket']}/{cfg['key']}"

register_plugin("s3", s3_plugin)
```

Or via entry points (auto-loaded by `quadre.plugins`):
```
# pyproject.toml of your plugin package
[project.entry-points."quadre.output_plugins"]
s3 = "quadre_plugin_s3:s3_plugin"
```

Then in your document:
```
"outputs": [
  { "plugin": "file", "path": "out.png" },
  { "plugin": "s3", "bucket": "my-bucket", "key": "dashboards/out.png" }
]
```

## Tips

- For large images and uploads, consider `tempfile.SpooledTemporaryFile` in your plugin to avoid holding the entire buffer in memory.
- Keep plugins pure and stateless; use only the `cfg` dict and `ctx` fields you need.
- If you need custom format options, pass `save_kwargs` to the `file` plugin or handle encoding inside your plugin.

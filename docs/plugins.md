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

- `email`: sends the image as an email attachment or inline via SMTP (stdlib-only).
  - Options (cfg): `to` (required), `from`, `subject`, `host` (required unless via env), `port` (default 587), `user`, `password`, `use_tls` (default true), `use_ssl` (default false), `timeout`, `format`, `body`, `inline` (bool), `html_body` (string; may contain `{cid}`).
  - Env vars (secrets/connection only): `QUADRE_EMAIL_HOST`, `QUADRE_EMAIL_PORT`, `QUADRE_EMAIL_USER`, `QUADRE_EMAIL_PASSWORD`, `QUADRE_EMAIL_TLS`, `QUADRE_EMAIL_SSL`, `QUADRE_EMAIL_TIMEOUT`, `QUADRE_EMAIL_FORMAT`.
  - Code: `src/quadre/plugins/email.py`.

## Programmatic usage (Python)

Prefer the high-level API for most use cases:

```
from quadre import render, build_image, to_bytes

# File output (default plugin)
render(doc, path="out.png")

# Multiple outputs
render(doc, outputs=[
  {"plugin": "file", "path": "out.webp", "format": "WEBP"},
  {"plugin": "bytes"},  # returns encoded bytes
])

# Get a Pillow image or encoded bytes
img = build_image(doc)
buf = to_bytes(doc, "PNG")
```

Advanced: you can still use lower-level functions if you need tighter control:

```
from quadre.flex.runner import build_dashboard_image
from quadre.plugins import dispatch_outputs, image_to_bytes

img = build_dashboard_image(doc)
dispatch_outputs(img, doc.get("outputs") or doc.get("output"), default_path="out.png", doc=doc)
png_bytes = image_to_bytes(img, format="PNG")
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

## Using the built-in Email plugin

A minimal email output is included and auto‑registered as `email` (stdlib‑only, no extra deps). It encodes the image and sends it as an attachment via SMTP.

- Configure secrets/connexion in env: `QUADRE_EMAIL_HOST` (+ optionally `QUADRE_EMAIL_USER`, `QUADRE_EMAIL_PASSWORD`, `QUADRE_EMAIL_TLS`/`QUADRE_EMAIL_SSL`).
- Pass routing/metadata in the document or programmatically: `to` (required), `from`, `subject`, `body`.

Document example:

```
{
  "outputs": [
    { "plugin": "file", "path": "out.png" },
    {
      "plugin": "email",
      "to": "team@example.com",
      "from": "no-reply@example.com",
      "subject": "Daily Dashboard"
    }
  ]
}
```

CLI:

```
export QUADRE_EMAIL_HOST="smtp.example.com"
export QUADRE_EMAIL_USER="smtp-user"
export QUADRE_EMAIL_PASSWORD="smtp-pass"
quadre render examples/declarative_featured.json out.png
```

Programmatic:

```
from quadre import render
render(doc, outputs={
  "plugin": "email",
  "to": "team@example.com",
  "from": "no-reply@example.com",
  "subject": "Daily Dashboard"
})
```

Inline (CID) example:

```
{
  "outputs": [
    {
      "plugin": "email",
      "to": "team@example.com",
      "from": "no-reply@example.com",
      "subject": "Dashboard inline",
      "inline": true
    }
  ]
}
```

Custom HTML body with CID placeholder:

```
{
  "outputs": [
    {
      "plugin": "email",
      "to": "team@example.com",
      "from": "no-reply@example.com",
      "subject": "Dashboard inline",
      "inline": true,
      "html_body": "<h1>Report</h1><p>See inline:</p><img src=\"cid:{cid}\" alt=\"dashboard\">"
    }
  ]
}
```

Notes:
- STARTTLS est activé par défaut (`use_tls: true`). Pour SMTPS, ajoutez `use_ssl: true` (port 465 typique).
- Changez le format joint avec `format: "WEBP"` (ou via `QUADRE_EMAIL_FORMAT`).
- Gardez les identifiants hors JSON (utilisez `QUADRE_EMAIL_*`).

### Email plugin configuration

Best practice: pass routing/metadata via plugin cfg, and keep secrets in env.

- Required cfg: `to`
- Recommended cfg: `from`, `subject`, `body`
- Env (optional):
  - `QUADRE_EMAIL_HOST`: SMTP hostname (required if not in cfg)
  - `QUADRE_EMAIL_PORT`: SMTP port (default 587)
  - `QUADRE_EMAIL_USER`: SMTP username (optional)
  - `QUADRE_EMAIL_PASSWORD`: SMTP password (optional)
  - `QUADRE_EMAIL_TLS`: `1/true/yes` to enable STARTTLS (default true)
  - `QUADRE_EMAIL_SSL`: `1/true/yes` to use SMTP over SSL (port 465 typically; default false)
  - `QUADRE_EMAIL_FORMAT`: image format override (default from context)
  - `QUADRE_EMAIL_TIMEOUT`: socket timeout in seconds

Example:

```
export QUADRE_EMAIL_HOST="smtp.example.com"
export QUADRE_EMAIL_USER="smtp-user"
export QUADRE_EMAIL_PASSWORD="smtp-pass"

# In document (recommended):
# {
#   ...,
#   "outputs": [ {
#     "plugin": "email",
#     "to": "team@example.com",
#     "from": "no-reply@example.com",
#     "subject": "Daily Dashboard"
#   } ]
# }
quadre render examples/declarative_featured.json out.png

# Programmatic use
python -c 'import json,quadre;doc=json.load(open("examples/declarative_featured.json"));quadre.render(doc, outputs={"plugin":"email","to":"team@example.com","from":"no-reply@example.com","subject":"Daily Dashboard"})'
```

## Tips

- For large images and uploads, consider `tempfile.SpooledTemporaryFile` in your plugin to avoid holding the entire buffer in memory.
- Keep plugins pure and stateless; use only the `cfg` dict and `ctx` fields you need.
- If you need custom format options, pass `save_kwargs` to the `file` plugin or handle encoding inside your plugin.

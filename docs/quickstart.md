# Quickstart

Fastest way to render an example (no install, using uv):

```bash
uv run -m quadre.main examples/declarative_featured.json out/featured.png
```

Validate a JSON document with the built‑in schema:

```bash
uv run -m quadre.validator examples/declarative_featured.json
```

Using the installed CLI:

```bash
quadre render examples/declarative_featured.json out.png
quadre validate examples/declarative_featured.json
```

Docker (reproducible environment):

```bash
make run examples/declarative_featured.json
```

See also:
- Architecture: docs/architecture.md
- Declarative layout schema: docs/declarative-layout.md

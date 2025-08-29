# Quickstart

Fastest way to render an example (no install, using uv):

```bash
uv run -m nada.main examples/declarative_featured.json out/featured.png
```

Validate a JSON document with the built‑in schema:

```bash
uv run -m nada.validator examples/declarative_featured.json
```

Using the installed CLI:

```bash
nada render examples/declarative_featured.json out.png
nada validate examples/declarative_featured.json
```

Docker (reproducible environment):

```bash
make run examples/declarative_featured.json
```

See also:
- Architecture: docs/architecture.md
- Declarative layout schema: docs/declarative-layout.md

# Testing & Determinism

Run all tests:

```bash
pytest -q
# or
uv run pytest -q
```

Pixel tests (opt‑in):

```bash
nada_PIXELS=1 uv run pytest -q tests/pixels

# Record/update baselines
nada_PIXELS=1 nada_RECORD=1 uv run pytest -q tests/pixels
```

Determinism
- Tests patch fonts to Pillow's default via `tests/conftest.py` to minimize platform differences.
- Hash checks ensure renders are byte‑stable for given inputs.

Targets
- `tests/test_rendering.py`: functional/deterministic rendering
- `tests/test_validator*.py`: schema validation & friendly errors
- `tests/test_flex_adapter_margins.py`: margin wrappers behavior
- `tests/test_resolve_path_utils.py`: data path resolver


# Publishing to PyPI

This is the single, canonical procedure to build and publish `quadre` using uv.

- Distribution name: `quadre`
- Package layout: `src/quadre/...`
- CLI entry points: `quadre`, `quadre-validate`
- Themes: bundled JSON files under `src/quadre/theme/` are included in the wheel/sdist.

## Prerequisites

- Python 3.12+
- `uv` installed
- PyPI accounts/tokens
  - Create a token in your PyPI/TestPyPI account
  - Username: `__token__`; Password: the API token value

## 1) Bump Version

- Edit `pyproject.toml` → `[project] version = "x.y.z"`
- Commit the change and tag if you maintain tags: `git tag vX.Y.Z`

## 2) Build Artifacts (wheel + sdist)

Build with uv, injecting the `build` tool ephemerally (no local install needed):

```bash
rm -rf dist/
uv run --with build python -m build
```

Artifacts are written to `dist/`.

## 3) Verify Contents

- Ensure theme JSONs are present in the wheel:
  - `unzip -l dist/*.whl | rg quadre/theme`
- Quick import/CLI smoke test in a clean env:
  - `python -m venv .venv-test && . .venv-test/bin/activate`
  - `pip install dist/quadre-*.whl`
  - `quadre --help`
  - `quadre validate examples/declarative_featured.json`
  - `quadre render examples/declarative_featured.json out.png`

## 4) Upload to TestPyPI (dry run)

Use uv to run Twine with ephemeral install. Either configure `~/.pypirc` or export env vars:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=YOUR_TESTPYPI_TOKEN
uv run --with twine python -m twine upload -r testpypi dist/*
```

Install from TestPyPI to verify:

```bash
python -m venv .venv-verify && . .venv-verify/bin/activate
pip install -i https://test.pypi.org/simple/ quadre -U --extra-index-url https://pypi.org/simple
quadre --version || quadre --help
```

## 5) Upload to PyPI

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=YOUR_PYPI_TOKEN
uv run --with twine python -m twine upload dist/*
```

Optionally push your tag: `git push --tags`.

## Notes & Tips

- Entry point group for external plugins is `quadre.output_plugins`.
- Environment override for themes: `quadre_THEME=/path/to/theme.json`.
- Keep the wheel small: only `src/quadre` is packaged; JSON themes are included via Hatch build config in `pyproject.toml`.
- Consider adding a `LICENSE` file before first release.

## Troubleshooting

- Missing themes at runtime: confirm the wheel lists `quadre/theme/theme.json`.
- CLI not found after install: check `[project.scripts]` in `pyproject.toml` and reinstall.
- Version reuse errors: bump the version; PyPI is immutable.

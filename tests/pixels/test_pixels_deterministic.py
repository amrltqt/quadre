from __future__ import annotations

import json
import os
from pathlib import Path
import hashlib

import pytest

from nada.flex.runner import render_dashboard_with_flex


pytestmark = pytest.mark.pixels


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_baselines(file: Path) -> dict:
    if not file.exists():
        return {}
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_baselines(file: Path, data: dict) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


@pytest.mark.skipif(
    os.environ.get("nada_PIXELS") != "1",
    reason="set nada_PIXELS=1 to enable pixel tests",
)
def test_pixels_kpi_row_deterministic(tmp_path: Path):
    # Minimal deterministic scenario (fonts forced by conftest fixture)
    doc = {
        "canvas": {"height": "auto", "min_height": 320, "max_height": 320},
        "data": {},
        "layout": [
            {
                "type": "text",
                "text": "Deterministic KPI Test",
                "properties": {"font": "heading"},
            },
            {
                "type": "row",
                "properties": {"gap": 16},
                "children": [
                    {"type": "kpi_card", "title": "Users", "value": "123k"},
                    {
                        "type": "kpi_card",
                        "title": "Revenue",
                        "value": "2.4M€",
                        "delta": {"pct": 5},
                    },
                ],
            },
        ],
    }

    out = tmp_path / "pixels_kpi.png"
    render_dashboard_with_flex(doc, str(out))
    digest = sha256_file(out)

    # Baseline store
    baseline_file = Path("tests/baselines/deterministic.json")
    baselines = load_baselines(baseline_file)
    key = "kpi_row_v1"

    if os.environ.get("nada_RECORD") == "1":
        baselines[key] = digest
        save_baselines(baseline_file, baselines)
        pytest.skip("Recorded baseline; skipping assertion")

    assert key in baselines, "Baseline missing — set nada_RECORD=1 to record"
    assert baselines[key] == digest, f"Pixel diff detected for {key}"

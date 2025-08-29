from __future__ import annotations

from pathlib import Path
import hashlib

from PIL import Image

from nada.flex.runner import render_dashboard_with_flex
from nada.components.config import DIMENSIONS


def _hash_png(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_flex_basic_render_is_deterministic(tmp_path):
    data = {
        "title": "Test Dashboard",
        "date_note": "Unit",
        "top_kpis": [
            {"title": "A", "value": "1", "delta": {"pct": 1}},
            {"title": "B", "value": "2"},
        ],
        "platform_rows": [
            ["Platform", "Value"],
            ["Web", "1"],
            ["iOS", "2"],
            ["Android", "3"],
        ],
        "canvas": {"height": "auto", "min_height": 600, "max_height": 1600},
    }

    out1 = tmp_path / "render1.png"
    out2 = tmp_path / "render2.png"

    render_dashboard_with_flex(data, str(out1))
    render_dashboard_with_flex(data, str(out2))

    # Both files exist and are identical
    assert out1.exists() and out2.exists()
    assert _hash_png(out1) == _hash_png(out2)

    # Dimensions sane
    im = Image.open(out1)
    w, h = im.size
    assert w == DIMENSIONS.WIDTH
    assert h >= 600 and h <= 1600


def test_declarative_adapter_render(tmp_path):
    data = {
        "data": {
            "header": {"title": "Decl Title", "date_note": "Q1"},
            "kpis": [
                {"title": "Users", "value": "123k"},
                {"title": "Revenue", "value": "2.4M€"},
            ],
        },
        "layout": [
            {"type": "title", "data_ref": "$.header"},
            {
                "type": "row",
                "children": [
                    {"type": "kpi_card", "data_ref": "$.kpis[0]"},
                    {"type": "kpi_card", "data_ref": "$.kpis[1]"},
                ],
            },
        ],
        "canvas": {"height": "auto", "min_height": 600, "max_height": 1600},
    }

    out = tmp_path / "decl.png"
    render_dashboard_with_flex(data, str(out))
    assert out.exists()
    im = Image.open(out)
    w, h = im.size
    assert w == DIMENSIONS.WIDTH
    assert 600 <= h <= 1600


def test_auto_height_bounds(tmp_path):
    # Make a content tall enough to exceed max_height
    rows = [["Platform", "Value"]] + [[f"Row{i}", str(i)] for i in range(200)]
    data = {
        "title": "Tall",
        "platform_rows": rows,
        "canvas": {"height": "auto", "min_height": 800, "max_height": 1200},
    }

    out = tmp_path / "tall.png"
    render_dashboard_with_flex(data, str(out))
    im = Image.open(out)
    w, h = im.size
    assert w == DIMENSIONS.WIDTH
    # h should be clamped between min and max
    assert 800 <= h <= 1200


def test_fixed_height_mode(tmp_path):
    data = {
        "title": "Fixed",
        "canvas": {"height": 900},
    }
    out = tmp_path / "fixed.png"
    render_dashboard_with_flex(data, str(out))
    im = Image.open(out)
    w, h = im.size
    assert w == DIMENSIONS.WIDTH
    assert h == 900

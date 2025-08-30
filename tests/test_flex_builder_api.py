from __future__ import annotations

from quadre.flex import Text, KPI, Row, Title, dref, make_doc
from quadre.validator import validate_layout
from quadre.flex.runner import build_dashboard_image
from quadre.components.config import DIMENSIONS


def test_typed_builder_validates_and_renders():
    doc = make_doc(
        Title("Typed Builder"),
        Row().gap(12).add(
            Text("Awesome KPIs").font("heading").no_grow(),
            KPI(title=dref("$.perf.title"), value=dref("$.perf.value")).grow(1),
            KPI(title="Orders", value="12,345").grow(1),
        ),
        data={"perf": {"title": "Revenue", "value": "4,567k€"}},
        canvas={"height": "auto", "min_height": 300, "max_height": 1600},
    ).to_dict()

    errors, _warns = validate_layout(doc)
    assert errors == []

    img = build_dashboard_image(doc)
    w, h = img.size
    assert w == DIMENSIONS.WIDTH
    assert 300 <= h <= 1600


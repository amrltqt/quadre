from __future__ import annotations

from nada.validator import validate_layout


def test_unknown_property_warns_and_color_hint():
    doc = {
        "data": {},
        "layout": [
            {
                "type": "text",
                "text": "A",
                "properties": {
                    "unknown_prop": 1,
                    "fill": "not-a-color",
                },
            }
        ],
    }

    errors, warns = validate_layout(doc)
    assert errors == []
    assert any("unknown property 'unknown_prop'" in w for w in warns)
    assert any("property 'fill' is not a valid color" in w for w in warns)

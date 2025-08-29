from __future__ import annotations

from quadre.validator import validate_layout


def test_validate_ok_dynamic_tables_example(tmp_path):
    doc = {
        "canvas": {"height": "auto"},
        "data": {
            "header": {"title": "T", "date_note": "D"},
            "sales_table": {"headers": ["A"], "rows": [["x"]]},
        },
        "layout": [
            {
                "type": "title",
                "title": {"$": "$.header.title"},
                "date_note": {"$": "$.header.date_note"},
            },
            {"type": "text", "text": "Quarterly Sales"},
            {"type": "table", "table": {"$": "$.sales_table"}},
        ],
    }
    errors, warnings = validate_layout(doc)
    assert errors == []


def test_validate_errors_for_text_missing_content():
    doc = {"layout": [{"type": "text"}]}
    errors, warnings = validate_layout(doc)
    assert any("text requires a 'text' field" in e for e in errors)

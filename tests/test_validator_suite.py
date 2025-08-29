from __future__ import annotations

from quadre.validator import validate_layout


def _has_error(errors: list[str], snippet: str) -> bool:
    return any(snippet in e for e in errors)


def _has_warn(warns: list[str], snippet: str) -> bool:
    return any(snippet in w for w in warns)


def test_valid_minimal_text():
    doc = {
        "data": {},
        "layout": [{"type": "text", "text": "Hello"}],
    }
    errors, warns = validate_layout(doc)
    assert errors == []


def test_title_requires_title():
    doc = {"layout": [{"type": "title"}]}
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "title widget requires 'title'")


def test_text_requires_text():
    doc = {"layout": [{"type": "text"}]}
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "text requires a 'text' field")


def test_kpi_requires_title_value_or_data_ref():
    doc = {"layout": [{"type": "kpi_card", "title": "A"}]}
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "kpi_card requires 'title' and 'value'")

    # Legacy data_ref is no longer supported (expect error)
    bad_doc = {"layout": [{"type": "kpi_card", "data_ref": "$.kpi0"}]}
    errors, _ = validate_layout(bad_doc)
    assert _has_error(errors, "'data_ref' is no longer supported")


def test_table_requires_payload_or_data_ref():
    doc = {"layout": [{"type": "table"}]}
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "table requires 'table' or ('headers' and 'rows')")

    # Valid with dict payload
    doc2 = {"layout": [{"type": "table", "table": {"headers": ["A"], "rows": [["1"]]}}]}
    errors, _ = validate_layout(doc2)
    assert errors == []

    # Valid with DataRef
    doc3 = {"layout": [{"type": "table", "table": {"$": "$.tbl"}}]}
    errors, _ = validate_layout(doc3)
    assert errors == []


def test_table_payload_type_errors():
    # headers/rows wrong types
    doc = {"layout": [{"type": "table", "table": {"headers": "A", "rows": {}}}]}
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "table.headers must be a list")

    # list-of-lists with non-list row
    doc2 = {"layout": [{"type": "table", "table": ["not_a_row"]}]}
    errors, _ = validate_layout(doc2)
    assert _has_error(errors, "table rows must be lists")


def test_dataref_aliases_and_path():
    for key in ("ref", "$", "$ref"):
        doc = {"layout": [{"type": "text", "text": {key: "$.x"}}]}
        errors, _ = validate_layout(doc)
        assert errors == []
    # invalid path
    doc_bad = {"layout": [{"type": "text", "text": {"$": "x"}}]}
    errors, _ = validate_layout(doc_bad)
    assert any("DataRef path" in e for e in errors)


def test_grid_requires_columns_and_children():
    doc = {
        "layout": [
            {
                "type": "grid",
                "children": [{"type": "text", "text": "A"}],
                "properties": {"columns": 0},
            }
        ]
    }
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "grid.properties.columns must be a positive integer")

    doc2 = {"layout": [{"type": "grid", "properties": {"columns": 2}, "children": []}]}
    errors, _ = validate_layout(doc2)
    assert _has_error(errors, "grid requires non-empty 'children' list")


def test_row_column_children_required():
    for t in ("row", "column"):
        doc = {"layout": [{"type": t, "children": []}]}
        errors, _ = validate_layout(doc)
        assert _has_error(errors, f"{t} requires non-empty 'children' list")


def test_properties_must_not_contain_content():
    doc = {"layout": [{"type": "text", "properties": {"text": "bad"}, "text": "ok"}]}
    errors, _ = validate_layout(doc)
    assert _has_error(errors, "Do not put content 'text' inside properties")


def test_color_warning_format():
    doc = {
        "layout": [{"type": "text", "text": "A", "properties": {"fill": "badcolor"}}]
    }
    errors, warns = validate_layout(doc)
    assert errors == []
    assert _has_warn(warns, "property 'fill' is not a valid color")


def test_top_level_data_warning():
    doc = {"layout": [{"type": "text", "text": "A"}]}
    errors, warns = validate_layout(doc)
    assert errors == []
    assert _has_warn(warns, "Top-level 'data' object is missing")

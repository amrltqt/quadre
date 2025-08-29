from __future__ import annotations

from quadre.utils.dataref import resolve_field


def test_plain_string_is_literal():
    doc = {"data": {"x": {"y": 1}}}
    assert resolve_field(doc, "Hello") == "Hello"


def test_jsonpath_string_resolves():
    doc = {"data": {"x": {"y": 123}}}
    assert resolve_field(doc, "$.x.y") == 123
    # dot-prefix also supported
    assert resolve_field(doc, ".x.y") == 123


def test_dataref_object_resolves():
    doc = {"data": {"a": {"b": 7}}}
    ref = {"$": "$.a.b"}
    assert resolve_field(doc, ref) == 7


def test_list_of_mixed_values_resolves_elementwise():
    doc = {"data": {"k": ["A", "B"], "n": 10}}
    arr = ["literal", {"ref": "$.k[1]"}, "$.n"]
    out = resolve_field(doc, arr)
    assert out == ["literal", "B", 10]


def test_nested_dict_resolves_deep_values():
    doc = {"data": {"u": {"name": "Jane"}}}
    payload = {
        "title": {"$": "$.u.name"},
        "caption": "User profile",
        "extra": {"label": ".u.name"},
    }
    out = resolve_field(doc, payload)
    assert out == {
        "title": "Jane",
        "caption": "User profile",
        "extra": {"label": "Jane"},
    }

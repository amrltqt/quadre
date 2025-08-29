from __future__ import annotations

from nada.utils.dataref import resolve_path


def test_resolve_path_basic_and_indexing():
    data = {
        "a": {"b": [{"c": 1}, {"c": 2}]},
        "arr": [10, 20, 30],
    }

    assert resolve_path("$.a.b[0].c", data) == 1
    assert resolve_path("$.a.b[1].c", data) == 2
    assert resolve_path("$.arr[2]", data) == 30


def test_resolve_path_root_and_dot_prefix():
    data = {"x": 42}

    # '$' alone returns the whole data
    assert resolve_path("$", data) == data

    # dot prefix works like absolute from root after stripping
    assert resolve_path(".x", data) == 42

from __future__ import annotations

from typing import Any, Sequence


def resolve_path(path: str, data: Any) -> Any:
    """
    Resolve a simple JSONPath-like reference (e.g. $.a.b[0].c) in a Python object.

    Supports:
    - Root symbol: $
    - Dot navigation: $.a.b
    - Index access: $.arr[0]
    """
    if not path:
        return None
    s = path
    if s.startswith("$"):
        s = s[1:]
    if s.startswith("."):
        s = s[1:]
    if not s:
        return data

    cur: Any = data
    token = ""
    i = 0

    def flush_token(tok: str, current: Any) -> Any:
        if tok == "":
            return current
        if isinstance(current, dict):
            return current.get(tok)
        return None

    while i < len(s):
        ch = s[i]
        if ch == ".":
            cur = flush_token(token, cur)
            token = ""
            i += 1
            continue
        if ch == "[":
            cur = flush_token(token, cur)
            token = ""
            j = s.find("]", i + 1)
            if j == -1:
                return None
            idx_str = s[i + 1 : j]
            try:
                idx = int(idx_str)
            except ValueError:
                return None
            if isinstance(cur, Sequence) and not isinstance(cur, (str, bytes)):
                if 0 <= idx < len(cur):
                    cur = cur[idx]
                else:
                    return None
            else:
                return None
            i = j + 1
            continue
        token += ch
        i += 1

    cur = flush_token(token, cur)
    return cur


def is_dataref(v: Any) -> bool:
    """Return True if v looks like a DataRef object {ref|$ref|$}."""
    return isinstance(v, dict) and any(k in v for k in ("ref", "$ref", "$"))


def _ctx(data: Any) -> Any:
    return data.get("data", data) if isinstance(data, dict) else data


def resolve_ref(data: Any, ref: Any) -> Any:
    if ref is None:
        return None
    ctx = _ctx(data)
    if isinstance(ref, dict):
        path = ref.get("ref") or ref.get("$ref") or ref.get("$")
        return resolve_path(path, ctx) if isinstance(path, str) else None
    if isinstance(ref, str):
        s = ref.strip()
        # Only treat strings that look like JSONPath as refs; otherwise return literal
        if s.startswith("$") or s.startswith("."):
            return resolve_path(s, ctx)
        return ref
    if isinstance(ref, int):
        kpis = ctx.get("top_kpis", []) if isinstance(ctx, dict) else []
        return kpis[ref] if 0 <= ref < len(kpis) else None
    if isinstance(ref, list):
        return [resolve_ref(data, r) for r in ref]
    return ref


def resolve_field(data: Any, value: Any) -> Any:
    if is_dataref(value) or isinstance(value, (str, list)):
        return resolve_ref(data, value)
    if isinstance(value, dict):
        return {k: resolve_field(data, v) for k, v in value.items()}
    return value

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Sequence, Union, Self

# Public, typed builder API that compiles to the declarative JSON
# accepted by the validator + adapter pipeline.

Json = Dict[str, Any]
Content = Union[str, Dict[str, Any]]  # string or DataRef-like {"$": "$.path"}


def dref(path: str) -> Dict[str, str]:
    """Create a DataRef object for JSON content fields.

    Example: Text(dref("$.title"))
    """
    if not isinstance(path, str) or not path.startswith("$"):
        raise ValueError("DataRef must start with '$'")
    return {"$": path}


@dataclass(frozen=True)
class Component:
    """Base builder component.

    Holds a properties bag and provides fluent helpers that map to the
    adapter/validator properties. Subclasses must implement to_json().
    """

    # Internal properties bag. Keep it keyword-only so positional args of
    # subclasses (e.g., Text("...")) are not affected, but still allow
    # dataclasses.replace(..., _props=...) for fluent APIs.
    _props: Dict[str, Any] = field(
        default_factory=dict, kw_only=True, repr=False, compare=False
    )

    # ----- Common fluent helpers (return new copies) -----
    def prop(self, name: str, value: Any) -> Self:
        p = dict(self._props)
        p[name] = value
        return replace(self, _props=p)

    def props(self, **kwargs: Any) -> Self:
        p = dict(self._props)
        p.update(kwargs)
        return replace(self, _props=p)

    # Spacing
    def gap(self, px: int) -> Self:
        return self.prop("gap", int(px))

    def padding(self, px: int) -> Self:
        return self.prop("padding", int(px))

    def margin_top(self, px: int) -> Self:
        return self.prop("margin_top", int(px))

    def margin_bottom(self, px: int) -> Self:
        return self.prop("margin_bottom", int(px))

    # Background (containers)
    def bg_radius(self, r: int) -> Self:
        return self.prop("bg_radius", int(r))

    def bg_fill(self, color: Any) -> Self:
        return self.prop("bg_fill", color)

    def bg_outline(self, color: Any) -> Self:
        return self.prop("bg_outline", color)

    def bg_outline_width(self, px: int) -> Self:
        return self.prop("bg_outline_width", int(px))

    def shadow(self, on: bool = True) -> Self:
        return self.prop("shadow", bool(on))

    # Flex cross/main alignment (containers)
    def align_items(self, v: str) -> Self:
        return self.prop("align_items", str(v))

    def justify_content(self, v: str) -> Self:
        return self.prop("justify_content", str(v))

    # Size hints when used as a child of a container
    def grow(self, ratio: float) -> Self:
        """For children in a Row: set width_ratio (0 disables growth)."""
        return self.prop("width_ratio", float(ratio))

    def no_grow(self) -> Self:
        return self.grow(0)

    def fill_remaining(self, on: bool = True) -> Self:
        """For children in a Column: ask to stretch along the column."""
        return self.prop("fill_remaining", bool(on))

    def height(self, px: int) -> Self:
        """For children in a Column: suggest a fixed height (basis)."""
        return self.prop("height", int(px))

    # ----- Serialization -----
    def _props_or_none(self) -> Optional[Dict[str, Any]]:
        return self._props or None

    def to_json(self) -> Json:
        raise NotImplementedError


# --------- Leaf widgets ---------


@dataclass(frozen=True)
class Text(Component):
    text: Content = ""

    # styling
    def font(self, key: str) -> "Text":
        return replace(self, _props={**self._props, "font": str(key)})

    def fill(self, color: Any) -> "Text":
        return replace(self, _props={**self._props, "fill": color})

    def align(self, v: str) -> "Text":
        return replace(self, _props={**self._props, "align": str(v)})

    def to_json(self) -> Json:
        out: Json = {"type": "text", "text": self.text}
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class Title(Component):
    title: Content = ""
    date_note: Optional[Content] = None

    def to_json(self) -> Json:
        out: Json = {"type": "title", "title": self.title}
        if self.date_note is not None:
            out["date_note"] = self.date_note
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class KPI(Component):
    title: Content = ""
    value: Content = ""
    delta: Any = None

    def to_json(self) -> Json:
        out: Json = {
            "type": "kpi_card",
            "title": self.title,
            "value": self.value,
        }
        if self.delta is not None:
            out["delta"] = self.delta
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class Table(Component):
    # Provide either table payload (headers+rows) or rows-only L.o.L
    table: Any = None
    headers: Optional[List[Any]] = None
    rows: Optional[List[List[Any]]] = None

    @staticmethod
    def from_payload(payload: Any) -> "Table":
        return Table(table=payload)

    def to_json(self) -> Json:
        out: Json = {"type": "table"}
        if self.table is not None:
            out["table"] = self.table
        elif self.headers is not None or self.rows is not None:
            out["headers"] = self.headers or []
            out["rows"] = self.rows or []
        else:
            out["table"] = []
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class Spacer(Component):
    size: int = 10

    def to_json(self) -> Json:
        out: Json = {"type": "spacer", "properties": {"height": int(self.size)}}
        # Also allow additional props like margins if set
        extra = {k: v for k, v in self._props.items() if k not in ("height",)}
        if extra:
            out.setdefault("properties", {}).update(extra)
        return out


@dataclass(frozen=True)
class Image(Component):
    src: Content = ""

    def fit(self, v: str) -> "Image":
        return replace(self, _props={**self._props, "fit": str(v)})

    def radius(self, r: int) -> "Image":
        return replace(self, _props={**self._props, "radius": int(r)})

    def opacity(self, a: float) -> "Image":
        return replace(self, _props={**self._props, "opacity": float(a)})

    def align(self, v: str) -> "Image":
        return replace(self, _props={**self._props, "align": str(v)})

    def to_json(self) -> Json:
        out: Json = {"type": "image", "src": self.src}
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class Progress(Component):
    value: Union[int, float] = 0.0  # 0..1 or percentage (>1)
    label: Optional[Content] = None

    def bar_height(self, px: int) -> "Progress":
        return replace(self, _props={**self._props, "bar_height": int(px)})

    def colors(self, *, bg_fill: Any = None, fill: Any = None) -> "Progress":
        p = dict(self._props)
        if bg_fill is not None:
            p["bg_fill"] = bg_fill
        if fill is not None:
            p["fill"] = fill
        return replace(self, _props=p)

    def to_json(self) -> Json:
        out: Json = {"type": "progress", "value": self.value}
        if self.label is not None:
            out["label"] = self.label
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class StatusBadge(Component):
    text: Content = ""
    variant_value: str = "secondary"

    def variant(self, v: str) -> "StatusBadge":
        return replace(self, variant_value=str(v))

    def to_json(self) -> Json:
        out: Json = {"type": "status_badge", "text": self.text}
        # variant is a property in validator
        p = dict(self._props)
        p.setdefault("variant", self.variant_value)
        out["properties"] = p
        return out


# --------- Containers ---------


@dataclass(frozen=True)
class Row(Component):
    children: Sequence[Component] = field(default_factory=list)

    def add(self, *kids: Component) -> "Row":
        return replace(self, children=[*self.children, *kids])

    def extend(self, kids: Sequence[Component]) -> "Row":
        return replace(self, children=[*self.children, *kids])

    def to_json(self) -> Json:
        out: Json = {"type": "row", "children": [c.to_json() for c in self.children]}
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class Column(Component):
    children: Sequence[Component] = field(default_factory=list)

    def add(self, *kids: Component) -> "Column":
        return replace(self, children=[*self.children, *kids])

    def extend(self, kids: Sequence[Component]) -> "Column":
        return replace(self, children=[*self.children, *kids])

    def to_json(self) -> Json:
        out: Json = {"type": "column", "children": [c.to_json() for c in self.children]}
        if self._props:
            out["properties"] = dict(self._props)
        return out


@dataclass(frozen=True)
class Grid(Component):
    children: Sequence[Component] = field(default_factory=list)
    columns_value: int = 2

    def columns(self, n: int) -> "Grid":
        return replace(self, columns_value=int(n))

    def add(self, *kids: Component) -> "Grid":
        return replace(self, children=[*self.children, *kids])

    def extend(self, kids: Sequence[Component]) -> "Grid":
        return replace(self, children=[*self.children, *kids])

    def to_json(self) -> Json:
        out: Json = {
            "type": "grid",
            "children": [c.to_json() for c in self.children],
            "properties": {"columns": int(self.columns_value)},
        }
        if self._props:
            out["properties"].update(dict(self._props))
        return out


# --------- Document helpers ---------


@dataclass(frozen=True)
class Doc:
    layout: Sequence[Component]
    data: Optional[Dict[str, Any]] = None
    canvas: Optional[Dict[str, Any]] = None
    theme: Optional[Union[str, Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        doc: Dict[str, Any] = {
            "layout": [c.to_json() for c in self.layout],
        }
        if self.data is not None:
            doc["data"] = self.data
        if self.canvas is not None:
            doc["canvas"] = self.canvas
        if self.theme is not None:
            doc["theme"] = self.theme
        return doc

    # Convenience: render via runner
    def render(self, out_path: str = "dashboard.png") -> str:
        from .runner import render_dashboard_with_flex

        return render_dashboard_with_flex(self.to_dict(), out_path=out_path)


def make_doc(
    *layout: Component,
    data: Optional[Dict[str, Any]] = None,
    canvas: Optional[Dict[str, Any]] = None,
    theme: Optional[Union[str, Dict[str, Any]]] = None,
) -> Doc:
    """Create a document from components.

    Example:
        doc = make_doc(
            Title("My KPIs"),
            Row().gap(12).add(
                Text("Left").no_grow(),
                KPI("Revenue", "4,567k€").grow(1),
                KPI("Orders", "12,345").grow(1),
            ),
            canvas={"height": "auto"},
        )
    """
    return Doc(layout=list(layout), data=data, canvas=canvas, theme=theme)


def doc(
    *layout: Component,
    data: Optional[Dict[str, Any]] = None,
    canvas: Optional[Dict[str, Any]] = None,
    theme: Optional[Union[str, Dict[str, Any]]] = None,
) -> Doc:
    """Alias plus court et idiomatique de make_doc()."""
    return Doc(layout=list(layout), data=data, canvas=canvas, theme=theme)

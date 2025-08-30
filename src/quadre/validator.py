import argparse
import json

from pydantic import BaseModel, Field, ValidationError, ConfigDict, model_validator
from typing_extensions import Literal, Annotated
from typing import Any, Dict, List, Tuple
from .flex.defaults import parse_color
from .utils.dataref import resolve_path


class DataRef(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ref: str | None = None
    dollar: str | None = Field(default=None, alias="$")
    dollar_ref: str | None = Field(default=None, alias="$ref")

    @property
    def path(self) -> str | None:
        return self.ref or self.dollar_ref or self.dollar

    @model_validator(mode="after")
    def _check(self):
        p = self.path
        if not p or not isinstance(p, str) or not p.startswith("$"):
            raise ValueError("DataRef path must be a string starting with '$'")
        return self


Content = Annotated[str | DataRef, Field(union_mode="left_to_right")]


class BaseComponent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str
    properties: Dict[str, Any] | None = None
    # No legacy data_ref allowed anymore


class TitleComponent(BaseComponent):
    type: Literal["title"]
    title: Content | None = None
    date_note: Content | None = None

    @model_validator(mode="after")
    def _require_title(self):
        if self.title is None:
            raise ValueError("title widget requires 'title'")
        return self


class TextComponent(BaseComponent):
    type: Literal["text"]
    text: Content


class KPIComponent(BaseComponent):
    type: Literal["kpi_card"]
    title: Content | None = None
    value: Content | None = None
    delta: Any | None = None

    @model_validator(mode="after")
    def _require_title_value(self):
        if self.title is None or self.value is None:
            raise ValueError("kpi_card requires 'title' and 'value'")
        return self


class TableComponent(BaseComponent):
    type: Literal["table"]
    table: Any | None = None
    headers: Any | None = None
    rows: Any | None = None

    @model_validator(mode="after")
    def _require_payload(self):
        if self.table is None and self.headers is None and self.rows is None:
            raise ValueError("table requires 'table' or ('headers' and 'rows')")
        return self


class SpacerComponent(BaseComponent):
    type: Literal["spacer"]


class RowComponent(BaseComponent):
    type: Literal["row"]
    children: List["Component"]

    @model_validator(mode="after")
    def _non_empty_children(self):
        if not self.children:
            raise ValueError("row requires non-empty 'children' list")
        return self


class ColumnComponent(BaseComponent):
    type: Literal["column"]
    children: List["Component"]

    @model_validator(mode="after")
    def _non_empty_children(self):
        if not self.children:
            raise ValueError("column requires non-empty 'children' list")
        return self


class GridComponent(BaseComponent):
    type: Literal["grid"]
    children: List["Component"]
    properties: Dict[str, Any] | None = None

    @model_validator(mode="after")
    def _require_cols(self):
        cols = (self.properties or {}).get("columns")
        if not isinstance(cols, int) or cols <= 0:
            raise ValueError("grid.properties.columns must be a positive integer")
        if not self.children:
            raise ValueError("grid requires non-empty 'children' list")
        return self


class ImageComponent(BaseComponent):
    type: Literal["image"]
    src: Content | None = None

    @model_validator(mode="after")
    def _require_src(self):
        if self.src is None:
            raise ValueError("image widget requires 'src'")
        return self


class ProgressComponent(BaseComponent):
    type: Literal["progress"]
    value: Any | None = None
    label: Content | None = None

    @model_validator(mode="after")
    def _require_value(self):
        if self.value is None:
            raise ValueError("progress requires 'value'")
        return self


class StatusBadgeComponent(BaseComponent):
    type: Literal["status_badge"]
    text: Content | None = None

    @model_validator(mode="after")
    def _require_text(self):
        if self.text is None:
            raise ValueError("status_badge requires 'text'")
        return self


Component = Annotated[
    TitleComponent
    | TextComponent
    | KPIComponent
    | TableComponent
    | SpacerComponent
    | RowComponent
    | ColumnComponent
    | GridComponent
    | ImageComponent
    | ProgressComponent
    | StatusBadgeComponent,
    Field(discriminator="type"),
]


class CanvasModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    height: str | int | None = None
    min_height: int | None = None
    max_height: int | None = None
    scale: float | None = None
    downscale: bool | None = None


class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    canvas: CanvasModel | None = None
    data: Dict[str, Any] | None = None
    layout: List[Component]


def _post_validate_content_vs_props(
    comp: BaseComponent, errors: List[str], path: str, warnings: List[str]
) -> None:
    props = comp.properties or {}
    for bad in (
        "text",
        "title",
        "date_note",
        "value",
        "delta",
        "headers",
        "rows",
        "table",
    ):
        if bad in props:
            errors.append(
                f"{path}: Do not put content '{bad}' inside properties; use top-level field"
            )
    # color format hints
    for color_key in ("fill", "color", "bg_fill", "bg_outline"):
        if color_key in props and parse_color(props[color_key]) is None:
            warnings.append(
                f"{path}: property '{color_key}' is not a valid color; expected #rrggbb or [r,g,b]"
            )

    # warn on unknown properties (renderer may ignore them)
    allowed = {
        # container/layout styling
        "gap",
        "align_items",
        "justify_content",
        "padding",
        "bg_radius",
        "bg_fill",
        "bg_outline",
        "bg_outline_width",
        # container visuals
        "shadow",
        "shadow_offset_x",
        "shadow_offset_y",
        "shadow_radius",
        "shadow_alpha",
        # text styling
        "font",
        "fill",
        "color",
        "align",
        # image
        "fit",
        "radius",
        "opacity",
        # progress
        "bar_height",
        # status badge
        "variant",
        # table options
        "fill_height",
        "min_row_height",
        "max_row_height",
        "fit",
        "shrink_row_height_floor",
        "style",
        # spacer
        "height",
        # grid
        "columns",
        # flow/layout hints for children
        "width_ratio",
        "fill_remaining",
        # sizing for column children
        "margin_top",
        "margin_bottom",
    }
    for k in props.keys():
        lk = str(k).lower()
        if (
            lk not in allowed
            and lk
            not in {
                # tolerances / legacy aliases possibly added in the future
            }
        ):
            warnings.append(
                f"{path}: unknown property '{k}' may be ignored by renderer"
            )


def validate_layout(doc: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    # Legacy key scanner (defined once, reused pre/post parse)
    def scan_legacy(node: Any, path: str) -> None:
        if isinstance(node, dict):
            if "data_ref" in node:
                errors.append(
                    f"{path}: 'data_ref' is no longer supported; use explicit content fields"
                )
            for k, v in node.items():
                scan_legacy(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                scan_legacy(v, f"{path}[{i}]")

    # Pre-scan for legacy keys regardless of parse success
    scan_legacy(doc.get("layout", []), "layout")

    try:
        parsed = Document.model_validate(doc)
    except ValidationError as ve:
        for err in ve.errors():
            loc_list = list(err.get("loc", []))
            loc = ".".join(str(x) for x in loc_list)
            msg = err.get("msg", "invalid")
            # Friendly remap for common cases
            if loc_list and loc_list[-1] == "text" and "Field required" in msg:
                errors.append(
                    f"{loc}: text requires a 'text' field (string or DataRef)"
                )
            else:
                errors.append(f"{loc}: {msg}")
        return errors, warnings

    if parsed.data is None:
        warnings.append(
            "Top-level 'data' object is missing; prefer placing all values under 'data'"
        )

    # Scan raw layout again post-parse for consistent reporting locations
    scan_legacy(doc.get("layout", []), "layout")

    ctx = parsed.data

    # Walk to enforce formatting/content separation and deeper type checks
    def walk(comp: BaseComponent, path: str) -> None:
        _post_validate_content_vs_props(comp, errors, path, warnings)
        # Deep checks for table payload structure
        if isinstance(comp, TableComponent):
            payload = comp.table
            headers = comp.headers
            rows = comp.rows

            def _is_dataref_like(v: Any) -> bool:
                return isinstance(v, dict) and any(k in v for k in ("ref", "$ref", "$"))

            def _validate_dref(v: Any, field_path: str) -> None:
                # v can be DataRef model or dict-like
                ref_path = None
                if isinstance(v, DataRef):
                    ref_path = v.path
                elif _is_dataref_like(v):
                    ref_path = v.get("ref") or v.get("$ref") or v.get("$")
                if ref_path is None:
                    return
                if ctx is None:
                    warnings.append(
                        f"{field_path}: cannot validate DataRef target (missing top-level data)"
                    )
                    return
                try:
                    resolved = resolve_path(ref_path, ctx)
                except Exception:
                    resolved = None
                if resolved is None:
                    errors.append(
                        f"{field_path}: DataRef '{ref_path}' does not resolve in 'data'"
                    )

            if payload is not None:
                if isinstance(payload, dict):
                    h = payload.get("headers", [])
                    r = payload.get("rows", [])
                    _validate_dref(h, f"{path}.table.headers")
                    _validate_dref(r, f"{path}.table.rows")
                    if not isinstance(h, list) or not isinstance(r, list):
                        errors.append(
                            f"{path}: table.headers must be a list, table.rows must be a list"
                        )
                    else:
                        for i, row in enumerate(r):
                            if not isinstance(row, list):
                                errors.append(
                                    f"{path}: table rows must be lists (row {i})"
                                )
                elif isinstance(payload, list):
                    for i, row in enumerate(payload):
                        if not isinstance(row, list):
                            errors.append(f"{path}: table rows must be lists (row {i})")
                elif _is_dataref_like(payload):
                    _validate_dref(payload, f"{path}.table")
                else:
                    errors.append(
                        f"{path}: table payload must be dict with headers/rows, list-of-lists, or DataRef"
                    )
            elif headers is not None or rows is not None:
                h = headers or []
                r = rows or []
                _validate_dref(h, f"{path}.headers")
                _validate_dref(r, f"{path}.rows")
                if not isinstance(h, list) or not isinstance(r, list):
                    errors.append(
                        f"{path}: table.headers must be a list, table.rows must be a list"
                    )
                else:
                    for i, row in enumerate(r):
                        if not isinstance(row, list):
                            errors.append(f"{path}: table rows must be lists (row {i})")

        # DataRef existence checks for other components
        def _validate_content(val: Any, field_path: str) -> None:
            if isinstance(val, DataRef):
                if ctx is None:
                    warnings.append(
                        f"{field_path}: cannot validate DataRef target (missing top-level data)"
                    )
                    return
                resolved = resolve_path(val.path, ctx)
                if resolved is None:
                    errors.append(
                        f"{field_path}: DataRef '{val.path}' does not resolve in 'data'"
                    )

        if isinstance(comp, TitleComponent):
            _validate_content(comp.title, f"{path}.title")
            if comp.date_note is not None:
                _validate_content(comp.date_note, f"{path}.date_note")
        elif isinstance(comp, TextComponent):
            _validate_content(comp.text, f"{path}.text")
        elif isinstance(comp, KPIComponent):
            _validate_content(comp.title, f"{path}.title")
            _validate_content(comp.value, f"{path}.value")
            # delta can be DataRef-like dict; best-effort check
            # (skip strict validation here if not DataRef model)
        # Forbid legacy data_ref entirely
        if hasattr(comp, "data_ref") and getattr(comp, "data_ref") is not None:
            errors.append(
                f"{path}: 'data_ref' is no longer supported; use explicit content fields"
            )
        if isinstance(comp, (RowComponent, ColumnComponent, GridComponent)):
            children = getattr(comp, "children", [])
            for i, ch in enumerate(children):
                walk(ch, f"{path}.children[{i}]")

    for i, comp in enumerate(parsed.layout):
        walk(comp, f"layout[{i}]")

    return errors, warnings


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Validate quadre declarative JSON document"
    )
    ap.add_argument("json_file", help="Path to JSON document to validate")
    args = ap.parse_args()

    with open(args.json_file, "r", encoding="utf-8") as f:
        doc = json.load(f)

    errors, warnings = validate_layout(doc)
    for w in warnings:
        print(f"[WARN] {w}")
    if errors:
        for e in errors:
            print(f"[ERROR] {e}")
        raise SystemExit(1)
    print("OK: document is valid")


if __name__ == "__main__":
    main()

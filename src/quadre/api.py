"""
High-level Python API for Quadre.

This module provides a clean import surface for library users:
- render(doc, path="dashboard.png", outputs=None, validate=False) -> list
- build_image(doc) -> PIL.Image.Image
- to_bytes(doc, format="PNG") -> bytes
- register_output_plugin(name, fn) -> None
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Union, List, Optional

from PIL import Image as PILImage

from .flex.runner import build_dashboard_image
from .plugins import (
    dispatch_outputs,
    register_plugin as register_output_plugin,
    image_to_bytes,
)
from .validator import validate_layout
from .flex.api import (
    dref,
    Doc,
    doc,
    make_doc,
    Text,
    Title,
    KPI,
    Table,
    Spacer,
    Image as FlexImage,
    Progress,
    StatusBadge,
    Row,
    Column,
    Grid,
)

# Public type for outputs specs accepted by the renderer and CLI
OutputsSpec = Union[
    str,
    Mapping[str, Any],
    Iterable[Mapping[str, Any]],
    None,
]


def build_image(doc: Mapping[str, Any]) -> PILImage.Image:
    """Build and return the final Pillow image for the given document."""
    return build_dashboard_image(dict(doc))


def to_bytes(doc: Mapping[str, Any], format: str = "PNG") -> bytes:
    """Render and return encoded image bytes (PNG by default)."""
    img = build_image(doc)
    return image_to_bytes(img, format=format)


def render(
    doc: Mapping[str, Any],
    *,
    path: Optional[str] = "dashboard.png",
    outputs: OutputsSpec = None,
    validate: bool = False,
) -> List[Any]:
    """
    Render the dashboard and dispatch outputs.

    - doc: JSON-like document (dict) containing `canvas`, `data`, and `layout`.
    - path: default output path for the built-in file plugin (optional).
    - outputs: optional output spec overriding any `output(s)` in the doc.
    - validate: if True, run schema validation and raise on errors.

    Returns a list of plugin results (file path string for the built-in file plugin).
    """
    doc_dict = dict(doc)
    if validate:
        errors, _warnings = validate_layout(doc_dict)
        if errors:
            raise ValueError(
                "Invalid document: "
                + "; ".join(errors[:3])
                + (" …" if len(errors) > 3 else "")
            )

    img = build_dashboard_image(doc_dict)
    # Prefer explicit outputs param; else use document-level output(s)
    spec = (
        outputs
        if outputs is not None
        else (doc_dict.get("outputs") or doc_dict.get("output"))
    )
    return dispatch_outputs(img, spec, default_path=path, doc=doc_dict)


__all__ = [
    "render",
    "build_image",
    "to_bytes",
    "register_output_plugin",
    "validate_layout",
    # Types and helpers
    "OutputsSpec",
    # Typed builder re-exports
    "dref",
    "Doc",
    "doc",
    "make_doc",
    "Text",
    "Title",
    "KPI",
    "Table",
    "Spacer",
    "FlexImage",
    "Progress",
    "StatusBadge",
    "Row",
    "Column",
    "Grid",
]

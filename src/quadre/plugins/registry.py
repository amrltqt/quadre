from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Union

from PIL import Image


# A plugin is a callable taking the image, an OutputContext and a free-form config dict.
PluginFn = Callable[[Image.Image, "OutputContext", Mapping[str, Any]], Any]


@dataclass
class OutputContext:
    """
    Context passed to output plugins.

    - path: preferred path for file-like destinations (may be None)
    - format: desired image format (e.g., "PNG")
    - doc: original dashboard document (for metadata or routing logic)
    - size: (width, height) of the rendered image
    """

    path: Optional[str]
    format: str
    doc: Mapping[str, Any]
    size: Tuple[int, int]


_REGISTRY: MutableMapping[str, PluginFn] = {}


def register_plugin(name: str, fn: PluginFn) -> None:
    key = name.strip().lower()
    if not key:
        raise ValueError("Plugin name must be non-empty")
    _REGISTRY[key] = fn


def get_plugin(name: str) -> PluginFn:
    key = name.strip().lower()
    if key not in _REGISTRY:
        raise KeyError(f"Unknown plugin: {name}")
    return _REGISTRY[key]


def _normalize_outputs_spec(
    spec: Union[str, Mapping[str, Any], Iterable[Mapping[str, Any]], None],
    default_path: Optional[str],
) -> List[Mapping[str, Any]]:
    """
    Normalize various spec shapes into a list of { plugin, ... } dicts.

    Accepted forms:
      - None -> default to file plugin with default_path (if provided)
      - "path/to/file.png" -> file plugin with that path
      - { "plugin": "file", "path": ... }
      - [ { "plugin": "file", ... }, { "plugin": "s3", ... } ]
    """
    if spec is None:
        if default_path:
            return [{"plugin": "file", "path": default_path}]
        return []
    if isinstance(spec, str):
        # Treat as a path
        return [{"plugin": "file", "path": spec}]
    if isinstance(spec, Mapping):
        # If no explicit plugin, assume file
        if "plugin" not in spec:
            merged = {"plugin": "file", **spec}
            return [merged]
        return [spec]
    # Assume iterable of mapping
    out: List[Mapping[str, Any]] = []
    for item in spec:
        if isinstance(item, Mapping):
            if "plugin" not in item:
                out.append({"plugin": "file", **item})
            else:
                out.append(item)
    return out


def dispatch_outputs(
    image: Image.Image,
    outputs_spec: Union[str, Mapping[str, Any], Iterable[Mapping[str, Any]], None],
    *,
    default_path: Optional[str],
    doc: Mapping[str, Any],
) -> List[Any]:
    """
    Dispatch the given image to one or more plugins.

    Returns a list of plugin results (types depend on the plugin). The default
    file plugin returns the path string it wrote to.
    """
    w, h = image.size
    # Determine output format: prefer explicit spec; fall back to path extension; default to PNG
    def _fmt_from_path(p: Optional[str]) -> str:
        if not p:
            return "PNG"
        p = p.lower()
        if p.endswith(".jpg") or p.endswith(".jpeg"):
            return "JPEG"
        if p.endswith(".webp"):
            return "WEBP"
        if p.endswith(".bmp"):
            return "BMP"
        return "PNG"

    normalized = _normalize_outputs_spec(outputs_spec, default_path)
    results: List[Any] = []
    for item in normalized:
        name = str(item.get("plugin", "file")).strip().lower()
        fmt = str(item.get("format") or _fmt_from_path(str(item.get("path") or default_path))).upper()
        ctx = OutputContext(path=str(item.get("path") or default_path) if (item.get("path") or default_path) else None,
                            format=fmt,
                            doc=doc,
                            size=(w, h))
        fn = get_plugin(name)
        # Pass the remaining keys (excluding 'plugin') as plugin config
        cfg = {k: v for k, v in item.items() if k != "plugin"}
        results.append(fn(image, ctx, cfg))
    return results


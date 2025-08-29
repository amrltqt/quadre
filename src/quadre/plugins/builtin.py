from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from PIL import Image

from .registry import OutputContext, register_plugin


def _ensure_parent_dir(path: str) -> None:
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)


def file_plugin(image: Image.Image, ctx: OutputContext, cfg: Mapping[str, Any]):
    """
    Built-in plugin that writes the image to disk.

    Config:
      - path: explicit output path (overrides ctx.path if provided)
      - format: explicit format (PNG, JPEG, WEBP, ...); defaults to ctx.format
      - save_kwargs: dict of extra Pillow save() kwargs (optional)
    """
    path = str(cfg.get("path") or ctx.path or "dashboard.png")
    fmt = str(cfg.get("format") or ctx.format)
    save_kwargs = dict(cfg.get("save_kwargs") or {})
    _ensure_parent_dir(path)
    image.save(path, format=fmt, **save_kwargs)
    return path


def bytes_plugin(image: Image.Image, ctx: OutputContext, cfg: Mapping[str, Any]):
    """
    Built-in plugin that returns the encoded image bytes (PNG by default).

    Config:
      - format: output format (default: ctx.format)
    """
    fmt = str(cfg.get("format") or ctx.format)
    buf = BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()


# Register built-ins when module is imported via `quadre.plugins`
register_plugin("file", file_plugin)
register_plugin("bytes", bytes_plugin)

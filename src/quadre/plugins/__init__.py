from __future__ import annotations

"""
Lightweight output plugin system for quadre.

Goals:
- Make file saving a plugin like any other (default behavior unchanged)
- Allow optional third-party plugins (e.g., S3) without hard deps
- Provide a simple buffer/bytes pathway for programmatic use

Usage patterns:
- Internal: runner dispatches to plugins based on document-level `output`/`outputs` spec,
  defaulting to the built-in `file` plugin using the provided path argument.
- Programmatic: use `image_to_bytes(img, format="PNG")` to get in-memory bytes.
"""

from .registry import (
    OutputContext,
    PluginFn,
    register_plugin,
    dispatch_outputs,
)
from .utils import image_to_bytes

# Ensure builtins are registered on import
from . import builtin  # noqa: F401

# Optional: load external plugins via entry points
try:
    from importlib.metadata import entry_points

    eps = entry_points()
    group = None
    # New API returns a dict-like object with .select
    if hasattr(eps, "select"):
        group = eps.select(group="quadre.output_plugins")
    else:  # pragma: no cover - legacy fallback
        group = eps.get("quadre.output_plugins", [])  # type: ignore[attr-defined]
    for ep in group or []:
        try:
            obj = ep.load()
            if callable(obj):
                # Treat as direct plugin function; use entry point name
                register_plugin(ep.name, obj)  # type: ignore[arg-type]
            elif hasattr(obj, "register") and callable(getattr(obj, "register")):
                obj.register(register_plugin)
            elif isinstance(obj, dict) and "name" in obj and "fn" in obj:
                register_plugin(str(obj["name"]), obj["fn"])
        except Exception:
            # Silently skip faulty plugin entries
            continue
except Exception:
    # No entry points available or importlib.metadata missing
    pass

__all__ = [
    "OutputContext",
    "PluginFn",
    "register_plugin",
    "dispatch_outputs",
    "image_to_bytes",
]

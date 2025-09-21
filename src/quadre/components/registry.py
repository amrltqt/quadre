from __future__ import annotations

import logging

from typing import Any, Tuple, Type, Dict
import importlib
import pkgutil

from pydantic import BaseModel

logger = logging.getLogger(__name__)

COMPONENTS: Dict[str, Type["Component"]] = {}
_loaded = False

def component(type: str):
    def deco(cls: Type["Component"]):
        logger.debug(f"Registering component {type} from {cls.__module__}")
        COMPONENTS[type] = cls
        return cls
    return deco

class Component(BaseModel):
    type: str

    def measure(
        self, canvas, avail_w: int, avail_h: int
    ) -> Tuple[int, int]:
        """Return intrinsic width & height needed (preferred size)."""
        return (0, 0)

    def render(self, canvas, x: int, y: int, w: int, h: int) -> None:
        """Render into the given box (x,y,w,h)."""
        raise NotImplementedError

    def resolve(self, data: Any):
        raise NotImplementedError

def component_discovery():
    global _loaded
    if _loaded:
        return

    # importe tout sous quadre.components.* (dont base.card)
    import quadre.components.base as base_pkg

    for m in pkgutil.walk_packages(base_pkg.__path__, base_pkg.__name__ + "."):
        importlib.import_module(m.name)

    import quadre.flex.components as flex_pkg
    for m in pkgutil.walk_packages(flex_pkg.__path__, flex_pkg.__name__ + "."):
        importlib.import_module(m.name)

    _loaded = True

"""
quadre Components Package

This package contains reusable components for dashboard generation.
Components are organized by complexity and responsibility:

- config: Configuration, colors, fonts
- primitives: Basic drawing functions
- cards: Card-based components (KPI, section cards)
- tables: Table components
- layouts: Layout management components
"""

from quadre.config import COLORS, FONTS, DIMENSIONS
from quadre.components.primitives import rounded_rectangle
from quadre.components.registry import Component, COMPONENTS, component_discovery


__all__ = [
    "COMPONENTS",
    "Component",
    "component_discovery",
    "COLORS",
    "FONTS",
    "DIMENSIONS",
    "rounded_rectangle",
]

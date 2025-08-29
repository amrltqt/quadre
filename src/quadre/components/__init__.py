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

from .config import COLORS, FONTS, DIMENSIONS
from .primitives import rounded_rectangle, badge
from .cards import KPICard, SectionCard
from .tables import (
    EnhancedTable,
    ColumnDefinition,
    TableStyle,
    CellAlignment,
    CellType,
)
from .image import ImageBlock
from .progress import ProgressBar
from .status_badge import StatusBadge

__all__ = [
    "COLORS",
    "FONTS",
    "DIMENSIONS",
    "rounded_rectangle",
    "badge",
    "KPICard",
    "SectionCard",
    "EnhancedTable",
    "ColumnDefinition",
    "TableStyle",
    "CellAlignment",
    "CellType",
    "ImageBlock",
    "ProgressBar",
    "StatusBadge",
]

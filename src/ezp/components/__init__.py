"""
EZ Pillow Components Package

This package contains reusable components for dashboard generation.
Components are organized by complexity and responsibility:

- config: Configuration, colors, fonts
- primitives: Basic drawing functions
- cards: Card-based components (KPI, section cards)
- tables: Table components
- layouts: Layout management components
"""

from .config import COLORS, FONTS, DIMENSIONS
from .primitives import rounded_rectangle, shadcn_badge
from .cards import KPICard, SectionCard
from .tables import (
    EnhancedTable, ColumnDefinition, TableStyle, CellAlignment, CellType,
    create_platform_table, create_simple_table, create_financial_table, create_custom_table
)
from .layouts import DashboardLayout
from .kpi_layouts import (
    KPILayoutManager, KPILayoutType, create_kpi_layout_manager,
    suggest_layout_for_count, create_custom_layout_config
)
from .layout_intelligence import (
    LayoutIntelligenceEngine, LayoutAnalysis, DataImportance, ContentType,
    create_layout_intelligence, suggest_smart_layout
)
from .global_layouts import (
    GlobalLayoutManager, ComponentType, LayoutDirection,
    create_global_layout_manager, create_custom_dashboard_layout
)
from .variants import (
    ButtonVariant, BadgeVariant, CardVariant, TableVariant, StatusVariant, MetricVariant,
    get_variant, list_variants
)

__all__ = [
    'COLORS',
    'FONTS',
    'DIMENSIONS',
    'rounded_rectangle',
    'shadcn_badge',
    'KPICard',
    'SectionCard',
    'EnhancedTable',
    'ColumnDefinition',
    'TableStyle',
    'CellAlignment',
    'CellType',
    'create_platform_table',
    'create_simple_table',
    'create_financial_table',
    'create_custom_table',
    'DashboardLayout',
    'KPILayoutManager',
    'KPILayoutType',
    'create_kpi_layout_manager',
    'suggest_layout_for_count',
    'create_custom_layout_config',
    'LayoutIntelligenceEngine',
    'LayoutAnalysis',
    'DataImportance',
    'ContentType',
    'create_layout_intelligence',
    'suggest_smart_layout',
    'GlobalLayoutManager',
    'ComponentType',
    'LayoutDirection',
    'create_global_layout_manager',
    'create_custom_dashboard_layout',
    'ButtonVariant',
    'BadgeVariant',
    'CardVariant',
    'TableVariant',
    'StatusVariant',
    'MetricVariant',
    'get_variant',
    'list_variants'
]

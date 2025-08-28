"""
Shadcn/ui style variants for EZ Pillow components.

This module defines different visual variants for components following shadcn/ui design patterns.
Each variant specifies colors, spacing, and styling properties for consistent theming.
"""

from typing import Dict, Tuple
from .config import COLORS


class ButtonVariant:
    """Button-like component variants following shadcn/ui patterns."""

    @staticmethod
    def default() -> Dict[str, str]:
        """Default button variant - dark background with light text."""
        return {
            "background": COLORS.PRIMARY,
            "foreground": COLORS.PRIMARY_FOREGROUND,
            "border": COLORS.PRIMARY,
            "hover_background": "#1e293b",  # Darker shade
            "hover_foreground": COLORS.PRIMARY_FOREGROUND,
        }

    @staticmethod
    def destructive() -> Dict[str, str]:
        """Destructive button variant - red background for dangerous actions."""
        return {
            "background": COLORS.DESTRUCTIVE,
            "foreground": COLORS.DESTRUCTIVE_FOREGROUND,
            "border": COLORS.DESTRUCTIVE,
            "hover_background": "#dc2626",  # Darker red
            "hover_foreground": COLORS.DESTRUCTIVE_FOREGROUND,
        }

    @staticmethod
    def outline() -> Dict[str, str]:
        """Outline button variant - transparent background with border."""
        return {
            "background": COLORS.BACKGROUND,
            "foreground": COLORS.FOREGROUND,
            "border": COLORS.BORDER,
            "hover_background": COLORS.ACCENT,
            "hover_foreground": COLORS.ACCENT_FOREGROUND,
        }

    @staticmethod
    def secondary() -> Dict[str, str]:
        """Secondary button variant - muted background."""
        return {
            "background": COLORS.SECONDARY,
            "foreground": COLORS.SECONDARY_FOREGROUND,
            "border": COLORS.SECONDARY,
            "hover_background": "#e2e8f0",  # Slightly darker
            "hover_foreground": COLORS.SECONDARY_FOREGROUND,
        }

    @staticmethod
    def ghost() -> Dict[str, str]:
        """Ghost button variant - transparent with hover effect."""
        return {
            "background": "transparent",
            "foreground": COLORS.FOREGROUND,
            "border": "transparent",
            "hover_background": COLORS.ACCENT,
            "hover_foreground": COLORS.ACCENT_FOREGROUND,
        }

    @staticmethod
    def link() -> Dict[str, str]:
        """Link button variant - styled like a hyperlink."""
        return {
            "background": "transparent",
            "foreground": COLORS.PRIMARY,
            "border": "transparent",
            "hover_background": "transparent",
            "hover_foreground": "#1e293b",  # Darker shade
        }


class BadgeVariant:
    """Badge component variants following shadcn/ui patterns."""

    @staticmethod
    def default() -> Tuple[str, str]:
        """Default badge variant."""
        return COLORS.PRIMARY, COLORS.PRIMARY_FOREGROUND

    @staticmethod
    def secondary() -> Tuple[str, str]:
        """Secondary badge variant."""
        return COLORS.SECONDARY, COLORS.SECONDARY_FOREGROUND

    @staticmethod
    def destructive() -> Tuple[str, str]:
        """Destructive badge variant."""
        return COLORS.DESTRUCTIVE, COLORS.DESTRUCTIVE_FOREGROUND

    @staticmethod
    def success() -> Tuple[str, str]:
        """Success badge variant."""
        return COLORS.SUCCESS, COLORS.SUCCESS_FOREGROUND

    @staticmethod
    def warning() -> Tuple[str, str]:
        """Warning badge variant."""
        return COLORS.WARNING, COLORS.WARNING_FOREGROUND

    @staticmethod
    def outline() -> Tuple[str, str]:
        """Outline badge variant."""
        return COLORS.BACKGROUND, COLORS.FOREGROUND


class CardVariant:
    """Card component variants following shadcn/ui patterns."""

    @staticmethod
    def default() -> Dict[str, str]:
        """Default card variant - clean white background with subtle border."""
        return {
            "background": COLORS.CARD_BACKGROUND,
            "border": COLORS.BORDER,
            "border_width": "1",
            "title_color": COLORS.MUTED_FOREGROUND,
            "content_color": COLORS.FOREGROUND,
            "radius": "8",
        }

    @staticmethod
    def elevated() -> Dict[str, str]:
        """Elevated card variant - slightly different background for hierarchy."""
        return {
            "background": COLORS.CARD_BACKGROUND,
            "border": COLORS.BORDER,
            "border_width": "1",
            "title_color": COLORS.MUTED_FOREGROUND,
            "content_color": COLORS.FOREGROUND,
            "radius": "12",
        }

    @staticmethod
    def muted() -> Dict[str, str]:
        """Muted card variant - subdued appearance."""
        return {
            "background": COLORS.MUTED,
            "border": COLORS.BORDER,
            "border_width": "1",
            "title_color": COLORS.MUTED_FOREGROUND,
            "content_color": COLORS.FOREGROUND,
            "radius": "8",
        }


class TableVariant:
    """Table component variants following shadcn/ui patterns."""

    @staticmethod
    def default() -> Dict[str, str]:
        """Default table variant - clean and minimal."""
        return {
            "background": COLORS.CARD_BACKGROUND,
            "border": COLORS.BORDER,
            "header_background": COLORS.MUTED,
            "header_text": COLORS.FOREGROUND,
            "row_text": COLORS.FOREGROUND,
            "alt_row_background": COLORS.MUTED,
            "border_width": "1",
        }

    @staticmethod
    def striped() -> Dict[str, str]:
        """Striped table variant - with alternating row colors."""
        return {
            "background": COLORS.CARD_BACKGROUND,
            "border": COLORS.BORDER,
            "header_background": COLORS.MUTED,
            "header_text": COLORS.FOREGROUND,
            "row_text": COLORS.FOREGROUND,
            "alt_row_background": "#f8fafc",  # Very light gray
            "border_width": "1",
        }

    @staticmethod
    def minimal() -> Dict[str, str]:
        """Minimal table variant - no background, only borders."""
        return {
            "background": "transparent",
            "border": COLORS.BORDER,
            "header_background": "transparent",
            "header_text": COLORS.FOREGROUND,
            "row_text": COLORS.FOREGROUND,
            "alt_row_background": "transparent",
            "border_width": "1",
        }


class StatusVariant:
    """Status indicator variants for different states."""

    @staticmethod
    def success() -> Dict[str, str]:
        """Success status variant - green color scheme."""
        return {
            "color": COLORS.SUCCESS,
            "background": "#dcfce7",  # Light green background
            "foreground": "#166534",  # Dark green text
            "icon": "✓",
        }

    @staticmethod
    def warning() -> Dict[str, str]:
        """Warning status variant - yellow color scheme."""
        return {
            "color": COLORS.WARNING,
            "background": "#fef3c7",  # Light yellow background
            "foreground": "#92400e",  # Dark yellow text
            "icon": "⚠",
        }

    @staticmethod
    def error() -> Dict[str, str]:
        """Error status variant - red color scheme."""
        return {
            "color": COLORS.DESTRUCTIVE,
            "background": "#fee2e2",  # Light red background
            "foreground": "#991b1b",  # Dark red text
            "icon": "✗",
        }

    @staticmethod
    def info() -> Dict[str, str]:
        """Info status variant - blue color scheme."""
        return {
            "color": "#3b82f6",
            "background": "#dbeafe",  # Light blue background
            "foreground": "#1e40af",  # Dark blue text
            "icon": "ℹ",
        }

    @staticmethod
    def neutral() -> Dict[str, str]:
        """Neutral status variant - gray color scheme."""
        return {
            "color": COLORS.MUTED_FOREGROUND,
            "background": COLORS.MUTED,
            "foreground": COLORS.FOREGROUND,
            "icon": "○",
        }


class MetricVariant:
    """Variants for metric display components."""

    @staticmethod
    def positive() -> Dict[str, str]:
        """Positive metric variant - for good/increasing values."""
        return {
            "color": COLORS.SUCCESS,
            "icon": "↗",
            "background": "#dcfce7",
        }

    @staticmethod
    def negative() -> Dict[str, str]:
        """Negative metric variant - for bad/decreasing values."""
        return {
            "color": COLORS.DESTRUCTIVE,
            "icon": "↘",
            "background": "#fee2e2",
        }

    @staticmethod
    def neutral() -> Dict[str, str]:
        """Neutral metric variant - for unchanged values."""
        return {
            "color": COLORS.MUTED_FOREGROUND,
            "icon": "→",
            "background": COLORS.MUTED,
        }


def get_variant(component: str, variant: str) -> Dict:
    """
    Get variant configuration for a component.

    Args:
        component: Component type (button, badge, card, table, status, metric)
        variant: Variant name (default, secondary, destructive, etc.)

    Returns:
        Dictionary with variant configuration

    Raises:
        ValueError: If component or variant is not found
    """
    component_variants = {
        "button": ButtonVariant,
        "badge": BadgeVariant,
        "card": CardVariant,
        "table": TableVariant,
        "status": StatusVariant,
        "metric": MetricVariant,
    }

    if component not in component_variants:
        raise ValueError(f"Unknown component: {component}")

    variant_class = component_variants[component]

    if not hasattr(variant_class, variant):
        raise ValueError(f"Unknown variant '{variant}' for component '{component}'")

    return getattr(variant_class, variant)()


def list_variants(component: str) -> list[str]:
    """
    List all available variants for a component.

    Args:
        component: Component type

    Returns:
        List of variant names
    """
    component_variants = {
        "button": ButtonVariant,
        "badge": BadgeVariant,
        "card": CardVariant,
        "table": TableVariant,
        "status": StatusVariant,
        "metric": MetricVariant,
    }

    if component not in component_variants:
        return []

    variant_class = component_variants[component]
    return [method for method in dir(variant_class)
            if not method.startswith('_') and callable(getattr(variant_class, method))]

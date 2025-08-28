"""
Global Layout System for EZ Pillow Dashboard Components.

This module provides a comprehensive layout system that can handle all dashboard
components including KPIs, tables, cards sections, and custom content areas.
It allows flexible positioning and sizing of all dashboard elements.
"""

from PIL import ImageDraw
from typing import List, Dict, Any
from enum import Enum
from ezp.components.config import COLORS, FONTS, DIMENSIONS
from ezp.components.cards import KPICard, SectionCard
from ezp.components.kpi_layouts import KPILayoutManager


class ComponentType(Enum):
    """Types of components that can be laid out."""
    HEADER = "header"
    KPI_SECTION = "kpi_section"
    TABLE = "table"
    CARD_SECTION = "card_section"
    TEXT = "text"
    SPACER = "spacer"
    CUSTOM = "custom"


class LayoutDirection(Enum):
    """Layout flow directions."""
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    ABSOLUTE = "absolute"


class GlobalLayoutManager:
    """
    Manager for comprehensive dashboard layouts supporting all component types.

    Provides flexible positioning, sizing, and arrangement of KPIs, tables,
    card sections, and other dashboard elements.
    """

    def __init__(self, canvas_width: int = DIMENSIONS.WIDTH,
                 canvas_height: int = DIMENSIONS.HEIGHT,
                 padding: int = DIMENSIONS.PADDING):
        """Initialize global layout manager."""
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = padding
        self.content_width = canvas_width - 2 * padding
        self.content_height = canvas_height - 2 * padding
        self.kpi_manager = KPILayoutManager(canvas_width, padding)

    def render_component_layout(self, draw: ImageDraw.ImageDraw,
                               components: List[Dict[str, Any]],
                               layout_config: Dict[str, Any]) -> int:
        """
        Render components according to layout configuration.

        Args:
            draw: PIL ImageDraw object
            components: List of component definitions
            layout_config: Global layout configuration

        Returns:
            Final Y position after all components
        """
        direction = LayoutDirection(layout_config.get("direction", "vertical"))

        if direction == LayoutDirection.ABSOLUTE:
            return self._render_absolute_layout(draw, components, layout_config)
        elif direction == LayoutDirection.HORIZONTAL:
            return self._render_horizontal_layout(draw, components, layout_config)
        else:  # VERTICAL
            return self._render_vertical_layout(draw, components, layout_config)

    def _render_vertical_layout(self, draw: ImageDraw.ImageDraw,
                               components: List[Dict[str, Any]],
                               layout_config: Dict[str, Any]) -> int:
        """Render components in vertical flow."""
        current_y = layout_config.get("start_y", self.padding)
        gap = layout_config.get("gap", DIMENSIONS.GAP_LARGE)

        for component in components:
            height = self._render_single_component(draw, component,
                                                 self.padding, current_y,
                                                 self.content_width)
            current_y += height + gap

        return current_y - gap  # Remove last gap

    def _render_horizontal_layout(self, draw: ImageDraw.ImageDraw,
                                 components: List[Dict[str, Any]],
                                 layout_config: Dict[str, Any]) -> int:
        """Render components in horizontal flow."""
        current_x = self.padding
        start_y = layout_config.get("start_y", self.padding)
        gap = layout_config.get("gap", DIMENSIONS.GAP_LARGE)

        max_height = 0

        for component in components:
            width = component.get("width", self.content_width // len(components))
            height = self._render_single_component(draw, component,
                                                 current_x, start_y, width)
            current_x += width + gap
            max_height = max(max_height, height)

        return start_y + max_height

    def _render_absolute_layout(self, draw: ImageDraw.ImageDraw,
                               components: List[Dict[str, Any]],
                               layout_config: Dict[str, Any]) -> int:
        """Render components with absolute positioning."""
        max_y = self.padding

        for component in components:
            x = self.padding + component.get("x", 0)
            y = self.padding + component.get("y", 0)
            width = component.get("width", self.content_width)

            height = self._render_single_component(draw, component, x, y, width)
            max_y = max(max_y, y + height)

        return max_y

    def _render_single_component(self, draw: ImageDraw.ImageDraw,
                                component: Dict[str, Any],
                                x: int, y: int, width: int) -> int:
        """
        Render a single component and return its height.

        Args:
            draw: PIL ImageDraw object
            component: Component configuration
            x: X position
            y: Y position
            width: Component width

        Returns:
            Height of the rendered component
        """
        component_type = ComponentType(component.get("type", "text"))

        if component_type == ComponentType.HEADER:
            return self._render_header_component(draw, component, x, y, width)
        elif component_type == ComponentType.KPI_SECTION:
            return self._render_kpi_component(draw, component, x, y, width)
        elif component_type == ComponentType.TABLE:
            return self._render_table_component(draw, component, x, y, width)
        elif component_type == ComponentType.CARD_SECTION:
            return self._render_card_section_component(draw, component, x, y, width)
        elif component_type == ComponentType.TEXT:
            return self._render_text_component(draw, component, x, y, width)
        elif component_type == ComponentType.SPACER:
            return component.get("height", DIMENSIONS.GAP_LARGE)
        elif component_type == ComponentType.CUSTOM:
            return self._render_custom_component(draw, component, x, y, width)
        else:
            return 0

    def _render_header_component(self, draw: ImageDraw.ImageDraw,
                                component: Dict[str, Any],
                                x: int, y: int, width: int) -> int:
        """Render header component."""
        title = component.get("title", "")
        date_note = component.get("date_note", "")

        # Main title
        if title:
            draw.text((x, y), title, font=FONTS.H1, fill=COLORS.FOREGROUND)

        # Date note (right-aligned)
        if date_note:
            date_width = FONTS.BODY.getlength(date_note)
            date_x = x + width - date_width
            draw.text((date_x, y + 12), date_note, font=FONTS.BODY, fill=COLORS.MUTED_FOREGROUND)

        return component.get("height", 90)

    def _render_kpi_component(self, draw: ImageDraw.ImageDraw,
                             component: Dict[str, Any],
                             x: int, y: int, width: int) -> int:
        """Render KPI section component."""
        kpi_data = component.get("kpis", [])
        kpi_cards = [
            KPICard(
                title=kpi.get("title", ""),
                value=kpi.get("value", ""),
                delta=kpi.get("delta")
            )
            for kpi in kpi_data
        ]

        layout_type_str = component.get("layout", "horizontal")
        gap = DIMENSIONS.GAP_MEDIUM

        # Simple horizontal layout for absolute positioning
        if layout_type_str == "horizontal":
            card_width = (width - (len(kpi_cards) - 1) * gap) // len(kpi_cards)
            current_x = x
            for card in kpi_cards:
                card.render(draw, current_x, y, card_width)
                current_x += card_width + gap
            return DIMENSIONS.KPI_CARD_HEIGHT

        elif layout_type_str == "priority":
            if len(kpi_cards) == 0:
                return 0

            # First card gets 40% of width, others share remaining 60%
            featured_width = int(width * 0.4)
            remaining_width = width - featured_width - gap
            other_width = (remaining_width - (len(kpi_cards) - 2) * gap) // max(1, len(kpi_cards) - 1)

            # Render featured card
            kpi_cards[0].render(draw, x, y, featured_width)

            # Render other cards
            current_x = x + featured_width + gap
            for card in kpi_cards[1:]:
                card.render(draw, current_x, y, other_width)
                current_x += other_width + gap

            return DIMENSIONS.KPI_CARD_HEIGHT

        else:
            # Fallback to horizontal for other layouts
            card_width = (width - (len(kpi_cards) - 1) * gap) // len(kpi_cards)
            current_x = x
            for card in kpi_cards:
                card.render(draw, current_x, y, card_width)
                current_x += card_width + gap
            return DIMENSIONS.KPI_CARD_HEIGHT

    def _render_table_component(self, draw: ImageDraw.ImageDraw,
                               component: Dict[str, Any],
                               x: int, y: int, width: int) -> int:
        """Render table component."""
        from .tables import create_platform_table, create_simple_table, TableStyle

        table_type = component.get("table_type", "platform")
        rows = component.get("rows", [])

        if table_type == "platform":
            table = create_platform_table(rows)
        else:
            headers = component.get("headers", [])
            table = create_simple_table(rows, headers)

        # Apply custom table style if provided
        style_config = component.get("style", {})
        if style_config:
            table.style = TableStyle(**style_config)

        height = table.render(draw, x, y, width)
        return height

    def _render_card_section_component(self, draw: ImageDraw.ImageDraw,
                                      component: Dict[str, Any],
                                      x: int, y: int, width: int) -> int:
        """Render card section component."""
        title = component.get("title", "")
        cards_data = component.get("cards", [])
        columns = component.get("columns", 3)
        card_height = component.get("card_height", DIMENSIONS.SECTION_CARD_HEIGHT_MID)

        current_y = y

        # Section title
        if title:
            draw.text((x, current_y), title, font=FONTS.H2, fill=COLORS.FOREGROUND)
            current_y += 60

        # Create cards
        cards = [
            SectionCard(
                title=card.get("title", ""),
                value=card.get("value", ""),
                delta=card.get("delta")
            )
            for card in cards_data
        ]

        # Render cards in grid
        gap = DIMENSIONS.GAP_MEDIUM
        card_width = (width - (columns - 1) * gap) // columns

        for i, card in enumerate(cards):
            if i >= columns * ((len(cards) + columns - 1) // columns):
                break

            col = i % columns
            row = i // columns

            card_x = x + col * (card_width + gap)
            card_y = current_y + row * (card_height + gap)

            card.render(draw, card_x, card_y, card_width, card_height)

        rows = (len(cards) + columns - 1) // columns
        total_height = 60 + rows * card_height + (rows - 1) * gap
        if title:
            total_height += 60

        return total_height

    def _render_text_component(self, draw: ImageDraw.ImageDraw,
                              component: Dict[str, Any],
                              x: int, y: int, width: int) -> int:
        """Render text component."""
        text = component.get("text", "")
        font_name = component.get("font", "body")
        color = component.get("color", COLORS.FOREGROUND)
        align = component.get("align", "left")

        # Map font names to actual fonts
        font_mapping = {
            "h1": FONTS.H1,
            "h2": FONTS.H2,
            "body": FONTS.BODY,
            "small": FONTS.SMALL,
            "bold": FONTS.BOLD_SMALL,
            "number": FONTS.NUMBER
        }
        font = font_mapping.get(font_name, FONTS.BODY)

        # Handle alignment
        text_x = x
        if align == "center":
            text_width = font.getlength(text)
            text_x = x + (width - text_width) // 2
        elif align == "right":
            text_width = font.getlength(text)
            text_x = x + width - text_width

        draw.text((text_x, y), text, font=font, fill=color)

        return component.get("height", font.size + 10)

    def _render_custom_component(self, draw: ImageDraw.ImageDraw,
                                component: Dict[str, Any],
                                x: int, y: int, width: int) -> int:
        """Render custom component - placeholder for user extensions."""
        # This method can be overridden by users for custom components
        custom_type = component.get("custom_type", "")
        height = component.get("height", 100)

        # Draw a placeholder rectangle for custom components
        draw.rectangle((x, y, x + width, y + height),
                      outline=COLORS.BORDER, width=1)
        draw.text((x + 20, y + 20), f"Custom: {custom_type}",
                 font=FONTS.SMALL, fill=COLORS.MUTED_FOREGROUND)

        return height

    def create_layout_from_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create component layout from dashboard data.

        Args:
            data: Dashboard data dictionary

        Returns:
            List of component configurations
        """
        components = []

        # Add header if present
        if "title" in data:
            components.append({
                "type": "header",
                "title": data.get("title", ""),
                "date_note": data.get("date_note", "")
            })

        # Add KPIs if present
        if "top_kpis" in data:
            kpi_component = {
                "type": "kpi_section",
                "kpis": data["top_kpis"]
            }

            # Include layout configuration
            layout_config = data.get("layout", {})
            if layout_config:
                kpi_component["layout"] = layout_config.get("type", "horizontal")
                if "positions" in layout_config:
                    kpi_component["positions"] = layout_config["positions"]

            components.append(kpi_component)

        # Add table if present
        if "platform_rows" in data:
            components.append({
                "type": "table",
                "table_type": "platform",
                "rows": data["platform_rows"]
            })

        # Add notes as text components
        if "notes_left" in data or "notes_right" in data:
            components.append({"type": "spacer", "height": 30})

            if "notes_left" in data:
                components.append({
                    "type": "text",
                    "text": data["notes_left"],
                    "font": "small",
                    "color": COLORS.MUTED_FOREGROUND,
                    "align": "left"
                })

        # Add middle section
        if "mid_section" in data:
            components.append({
                "type": "card_section",
                "title": data["mid_section"].get("title", ""),
                "cards": data["mid_section"].get("cards", []),
                "columns": 3,
                "card_height": DIMENSIONS.SECTION_CARD_HEIGHT_MID
            })

        # Add bottom section
        if "bottom_section" in data:
            components.append({
                "type": "card_section",
                "title": data["bottom_section"].get("title", ""),
                "cards": data["bottom_section"].get("cards", []),
                "columns": 5,
                "card_height": DIMENSIONS.SECTION_CARD_HEIGHT_BOTTOM
            })

        return components


def create_global_layout_manager(canvas_width: int = DIMENSIONS.WIDTH,
                                canvas_height: int = DIMENSIONS.HEIGHT,
                                padding: int = DIMENSIONS.PADDING) -> GlobalLayoutManager:
    """Factory function to create a global layout manager."""
    return GlobalLayoutManager(canvas_width, canvas_height, padding)


def create_custom_dashboard_layout(components: List[Dict[str, Any]],
                                  layout_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to create a custom dashboard layout configuration.

    Args:
        components: List of component definitions
        layout_config: Global layout configuration

    Returns:
        Complete layout configuration

    Example:
        layout = create_custom_dashboard_layout([
            {"type": "header", "title": "My Dashboard"},
            {"type": "kpi_section", "kpis": [...], "layout": "priority"},
            {"type": "table", "rows": [...], "width": 800, "x": 100, "y": 300}
        ], {
            "direction": "absolute",
            "gap": 20
        })
    """
    return {
        "components": components,
        "layout": layout_config
    }

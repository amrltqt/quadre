"""
Declarative Layout System for EZ Pillow Dashboard Components.

This module provides a declarative approach to dashboard layouts where
the layout structure directly references data elements, eliminating the
need for automatic detection or word analysis.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from PIL import ImageDraw
from .config import COLORS, FONTS, DIMENSIONS
from .cards import KPICard, SectionCard
from .tables import EnhancedTable, create_platform_table


class ComponentType(Enum):
    """Available component types for declarative layouts."""
    TITLE = "title"
    KPI_CARD = "kpi_card"
    SECTION_CARD = "section_card"
    TABLE = "table"
    TEXT = "text"
    SPACER = "spacer"
    GRID = "grid"
    ROW = "row"
    COLUMN = "column"


@dataclass
class LayoutComponent:
    """Individual component in a declarative layout."""
    type: ComponentType
    data_ref: Optional[Union[str, int, List[Union[str, int]]]] = None
    properties: Dict[str, Any] = None
    children: List['LayoutComponent'] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.children is None:
            self.children = []


class DeclarativeLayoutManager:
    """
    Manager for declarative dashboard layouts.

    Instead of analyzing data to guess the layout, this system uses
    explicit layout definitions that reference data by index or key.
    """

    def __init__(self, canvas_width: int = DIMENSIONS.WIDTH, padding: int = DIMENSIONS.PADDING):
        """Initialize the declarative layout manager."""
        self.canvas_width = canvas_width
        self.padding = padding
        self.content_width = canvas_width - 2 * padding
        self.data_context = {}

    def set_data_context(self, data: Dict[str, Any]):
        """Set the data context for component references."""
        self.data_context = data.get("data", data)

    def resolve_data_reference(self, ref: Union[str, int, List[Union[str, int]]]) -> Any:
        """
        Resolve a data reference to actual data.

        Args:
            ref: Data reference (key string, index, or list of refs)

        Returns:
            The referenced data
        """
        if ref is None:
            return None

        # Handle list of references
        if isinstance(ref, list):
            return [self.resolve_data_reference(r) for r in ref]

        # Handle string key reference
        if isinstance(ref, str):
            # Support dot notation like "top_kpis.0" or "sections.performance"
            keys = ref.split('.')
            current = self.data_context

            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    try:
                        current = current[int(key)]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None

            return current

        # Handle integer index reference
        if isinstance(ref, int):
            # Default to top_kpis if available
            kpis = self.data_context.get('top_kpis', [])
            if 0 <= ref < len(kpis):
                return kpis[ref]

        return None

    def render_kpi_card(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                       x: int, y: int, width: int, height: int = None) -> int:
        """Render a KPI card component."""
        if height is None:
            height = DIMENSIONS.KPI_CARD_HEIGHT

        kpi_data = self.resolve_data_reference(component.data_ref)
        if not kpi_data:
            return y + height

        card = KPICard(
            title=kpi_data.get("title", ""),
            value=kpi_data.get("value", ""),
            delta=kpi_data.get("delta")
        )

        card.render(draw, x, y, width)
        return y + height

    def render_title(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                    x: int, y: int, width: int, height: int = None) -> int:
        """Render a title component."""
        title_text = component.properties.get("text", "")
        date_note = component.properties.get("date_note", "")

        if component.data_ref:
            title_data = self.resolve_data_reference(component.data_ref)
            if isinstance(title_data, dict):
                title_text = title_data.get("title", title_text)
                date_note = title_data.get("date_note", date_note)
            elif isinstance(title_data, str):
                title_text = title_data

        if not title_text:
            return y

        # Render title similar to DashboardLayout.render_header
        title_font = FONTS.H1
        subtitle_font = FONTS.BODY

        # Title
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_height = title_bbox[3] - title_bbox[1]

        draw.text((x, y), title_text, fill=COLORS.FOREGROUND, font=title_font)
        current_y = y + title_height + 10

        # Date note if provided
        if date_note:
            draw.text((x, current_y), date_note, fill=COLORS.MUTED_FOREGROUND, font=subtitle_font)
            subtitle_bbox = draw.textbbox((0, 0), date_note, font=subtitle_font)
            subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
            current_y += subtitle_height + 15

        return current_y

    def render_section_card(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                          x: int, y: int, width: int, height: int = None) -> int:
        """Render a section card component."""
        if height is None:
            height = DIMENSIONS.SECTION_CARD_HEIGHT_MID

        card_data = self.resolve_data_reference(component.data_ref)
        if not card_data:
            return y + height

        card = SectionCard(
            title=card_data.get("title", ""),
            value=card_data.get("value", ""),
            delta=card_data.get("delta")
        )

        card.render(draw, x, y, width)
        return y + height

    def render_table(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                    x: int, y: int, width: int, height: int = None) -> int:
        """Render a table component."""
        table_data = self.resolve_data_reference(component.data_ref)
        if not table_data:
            return y + (height or 200)

        # Handle new structure with headers + rows
        if isinstance(table_data, dict):
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])
            if headers and rows:
                table = self._create_dynamic_table(headers, rows, width)
                return table.render(draw, x, y, width)

        # Fallback: old structure (list of lists)
        elif isinstance(table_data, list) and table_data:
            table = create_platform_table(table_data)
            return table.render(draw, x, y, width)

        return y + (height or 200)

    def render_text(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                   x: int, y: int, width: int, height: int = None) -> int:
        """Render a text component."""
        text_content = component.properties.get("text", "")
        if component.data_ref:
            referenced_data = self.resolve_data_reference(component.data_ref)
            if isinstance(referenced_data, str):
                text_content = referenced_data

        if not text_content:
            return y

        font_name = component.properties.get("font", "body")
        font_mapping = {
            "title": FONTS.H1,
            "heading": FONTS.H2,
            "body": FONTS.BODY,
            "caption": FONTS.SMALL,
            "table": FONTS.TABLE
        }
        font = font_mapping.get(font_name, FONTS.BODY)
        color = component.properties.get("color", COLORS.FOREGROUND)
        align = component.properties.get("align", "left")

        # Handle text wrapping for long content
        max_width = width - 20  # Leave some padding
        wrapped_text = self._wrap_text(text_content, font, max_width)

        lines = wrapped_text.split('\n')
        current_y = y
        line_height = int(font.getlength('Ay') * 1.2)  # Approximate line height

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)

            if align == "center":
                text_x = x + (width - (bbox[2] - bbox[0])) // 2
            elif align == "right":
                text_x = x + width - (bbox[2] - bbox[0])
            else:
                text_x = x + 10  # Small left padding

            draw.text((text_x, current_y), line, fill=color, font=font)
            current_y += line_height

        return current_y + component.properties.get("margin_bottom", 10)

    def render_spacer(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                     x: int, y: int, width: int, height: int = None) -> int:
        """Render a spacer component."""
        spacer_height = component.properties.get("height", DIMENSIONS.GAP_MEDIUM)
        return y + spacer_height

    def render_row(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                  x: int, y: int, width: int, height: int = None) -> int:
        """Render components in a horizontal row."""
        if not component.children:
            return y

        gap = component.properties.get("gap", DIMENSIONS.GAP_MEDIUM)

        # Calculate widths based on custom ratios or equal distribution
        child_widths = self._calculate_row_widths(component.children, width, gap)

        max_y = y
        current_x = x

        for child, child_width in zip(component.children, child_widths):
            child_end_y = self.render_component(draw, child, current_x, y, child_width, height)
            max_y = max(max_y, child_end_y)
            current_x += child_width + gap

        return max_y

    def _calculate_row_widths(self, children: List[LayoutComponent],
                             total_width: int, gap: int) -> List[int]:
        """Calculate widths for row children based on their properties."""
        total_gap = (len(children) - 1) * gap
        available_width = total_width - total_gap

        # Check if any child has a custom width_ratio
        ratios = []
        for child in children:
            ratio = child.properties.get("width_ratio", None)
            ratios.append(ratio)

        # If no custom ratios, distribute equally
        if all(ratio is None for ratio in ratios):
            child_width = available_width // len(children)
            return [child_width] * len(children)

        # Calculate widths based on ratios
        widths = []
        remaining_width = available_width
        remaining_children = len(children)

        for i, (child, ratio) in enumerate(zip(children, ratios)):
            if ratio is not None:
                # Use specified ratio
                width = int(available_width * ratio)
                widths.append(width)
                remaining_width -= width
                remaining_children -= 1
            else:
                # Will be calculated later for remaining children
                widths.append(None)

        # Distribute remaining width equally among children without ratios
        if remaining_children > 0:
            default_width = remaining_width // remaining_children
            for i, width in enumerate(widths):
                if width is None:
                    widths[i] = default_width

        return widths

    def render_column(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                     x: int, y: int, width: int, height: int = None) -> int:
        """Render components in a vertical column."""
        if not component.children:
            return y

        gap = component.properties.get("gap", DIMENSIONS.GAP_MEDIUM)
        current_y = y

        for child in component.children:
            current_y = self.render_component(draw, child, x, current_y, width, height)
            current_y += gap

        return current_y - gap  # Remove last gap

    def render_grid(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                   x: int, y: int, width: int, height: int = None) -> int:
        """Render components in a grid layout."""
        if not component.children:
            return y

        cols = component.properties.get("columns", 2)
        gap = component.properties.get("gap", DIMENSIONS.GAP_MEDIUM)

        child_width = (width - (cols - 1) * gap) // cols

        current_y = y
        row_height = 0

        for i, child in enumerate(component.children):
            col = i % cols
            row = i // cols

            child_x = x + col * (child_width + gap)
            child_y = current_y if col == 0 else current_y

            if col == 0 and i > 0:
                current_y += row_height + gap
                child_y = current_y
                row_height = 0

            child_end_y = self.render_component(draw, child, child_x, child_y, child_width, height)
            row_height = max(row_height, child_end_y - child_y)

        return current_y + row_height

    def render_component(self, draw: ImageDraw.ImageDraw, component: LayoutComponent,
                        x: int, y: int, width: int, height: int = None) -> int:
        """Render a single component based on its type."""
        component_type = component.type

        if component_type == ComponentType.TITLE:
            return self.render_title(draw, component, x, y, width, height)
        elif component_type == ComponentType.KPI_CARD:
            return self.render_kpi_card(draw, component, x, y, width, height)
        elif component_type == ComponentType.SECTION_CARD:
            return self.render_section_card(draw, component, x, y, width, height)
        elif component_type == ComponentType.TABLE:
            return self.render_table(draw, component, x, y, width, height)
        elif component_type == ComponentType.TEXT:
            return self.render_text(draw, component, x, y, width, height)
        elif component_type == ComponentType.SPACER:
            return self.render_spacer(draw, component, x, y, width, height)
        elif component_type == ComponentType.ROW:
            return self.render_row(draw, component, x, y, width, height)
        elif component_type == ComponentType.COLUMN:
            return self.render_column(draw, component, x, y, width, height)
        elif component_type == ComponentType.GRID:
            return self.render_grid(draw, component, x, y, width, height)
        else:
            return y

    def render_layout(self, draw: ImageDraw.ImageDraw, layout_components: List[Dict[str, Any]],
                     start_y: int = None) -> int:
        """
        Render a complete declarative layout.

        Args:
            draw: PIL ImageDraw object
            layout_components: List of component definitions
            start_y: Starting Y position

        Returns:
            Final Y position after rendering
        """
        if start_y is None:
            start_y = self.padding

        current_y = start_y

        for i, comp_def in enumerate(layout_components):
            component = self.create_component_from_definition(comp_def)
            current_y = self.render_component(
                draw, component, self.padding, current_y, self.content_width
            )

            # Add different spacing based on component type
            comp_type = comp_def.get("type", "")
            if comp_type == "title":
                current_y += DIMENSIONS.GAP_LARGE
            elif comp_type == "spacer":
                # Spacer already adds its own height
                pass
            elif comp_type in ["text"] and comp_def.get("properties", {}).get("font") == "heading":
                current_y += DIMENSIONS.GAP_MEDIUM
            else:
                current_y += DIMENSIONS.GAP_MEDIUM

        return current_y

    def create_component_from_definition(self, definition: Dict[str, Any]) -> LayoutComponent:
        """Create a LayoutComponent from a dictionary definition."""
        comp_type_str = definition.get("type", "text")

        # Map string types to enum
        type_mapping = {
            "title": ComponentType.TITLE,
            "kpi_card": ComponentType.KPI_CARD,
            "section_card": ComponentType.SECTION_CARD,
            "table": ComponentType.TABLE,
            "text": ComponentType.TEXT,
            "spacer": ComponentType.SPACER,
            "row": ComponentType.ROW,
            "column": ComponentType.COLUMN,
            "grid": ComponentType.GRID
        }

        comp_type = type_mapping.get(comp_type_str, ComponentType.TEXT)

        # Handle children
        children = []
        if "children" in definition:
            children = [
                self.create_component_from_definition(child_def)
                for child_def in definition["children"]
            ]

        return LayoutComponent(
            type=comp_type,
            data_ref=definition.get("data_ref"),
            properties=definition.get("properties", {}),
            children=children
        )

    def _wrap_text(self, text: str, font, max_width: int) -> str:
        """Wrap text to fit within max_width."""
        if font.getlength(text) <= max_width:
            return text

        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.getlength(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, truncate it
                    truncated = self._truncate_word(word, font, max_width)
                    lines.append(truncated)
                    current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    def _truncate_word(self, word: str, font, max_width: int) -> str:
        """Truncate a single word if it's too long."""
        if font.getlength(word) <= max_width:
            return word

        ellipsis = "..."
        ellipsis_width = font.getlength(ellipsis)
        available_width = max_width - ellipsis_width

        if available_width <= 0:
            return ellipsis[:max(1, max_width // font.getlength('.'))]

        for i in range(len(word) - 1, 0, -1):
            if font.getlength(word[:i]) <= available_width:
                return word[:i] + ellipsis

        return word[:i] + ellipsis if len(word) > 0 else ellipsis

    def _create_dynamic_table(self, headers: list, rows: list, total_width: int):
        """Create a table with dynamic column widths from headers and rows."""
        from .tables import EnhancedTable, ColumnDefinition, CellType, CellAlignment

        if not headers or not rows:
            return None

        num_columns = len(headers)
        available_width = total_width - 60  # Account for padding and borders

        # Calculate column widths - distribute proportionally
        base_width = available_width // num_columns
        remainder = available_width % num_columns

        columns = []
        for i, header in enumerate(headers):
            width = base_width + (1 if i < remainder else 0)

            # First column (usually names) gets extra space
            if i == 0:
                width += 30
            # Last columns (usually short data) get less space
            elif i >= num_columns - 2:
                width -= 15

            # Determine cell type based on column content patterns
            cell_type = CellType.BOLD_TEXT if i == 0 else CellType.PERCENTAGE
            alignment = CellAlignment.LEFT

            columns.append(ColumnDefinition(
                title=header,
                width=width,
                alignment=alignment,
                cell_type=cell_type
            ))

        return EnhancedTable(rows, columns)


def create_declarative_layout_manager(canvas_width: int = DIMENSIONS.WIDTH,
                                    padding: int = DIMENSIONS.PADDING) -> DeclarativeLayoutManager:
    """Factory function to create a declarative layout manager."""
    return DeclarativeLayoutManager(canvas_width, padding)


# Helper functions for common layout patterns
def create_kpi_row_layout(kpi_indices: List[int], gap: int = DIMENSIONS.GAP_MEDIUM) -> Dict[str, Any]:
    """Create a row layout for KPI cards."""
    return {
        "type": "row",
        "properties": {"gap": gap},
        "children": [
            {"type": "kpi_card", "data_ref": i}
            for i in kpi_indices
        ]
    }


def create_kpi_grid_layout(kpi_indices: List[int], columns: int = 2,
                          gap: int = DIMENSIONS.GAP_MEDIUM) -> Dict[str, Any]:
    """Create a grid layout for KPI cards."""
    return {
        "type": "grid",
        "properties": {"columns": columns, "gap": gap},
        "children": [
            {"type": "kpi_card", "data_ref": i}
            for i in kpi_indices
        ]
    }


def create_featured_layout(primary_kpi_index: int, secondary_kpi_indices: List[int]) -> Dict[str, Any]:
    """Create a featured layout with one large KPI and smaller ones."""
    return {
        "type": "row",
        "properties": {"gap": DIMENSIONS.GAP_MEDIUM},
        "children": [
            {
                "type": "kpi_card",
                "data_ref": primary_kpi_index,
                "properties": {"featured": True}
            },
            {
                "type": "column",
                "properties": {"gap": DIMENSIONS.GAP_SMALL},
                "children": [
                    {"type": "kpi_card", "data_ref": i}
                    for i in secondary_kpi_indices
                ]
            }
        ]
    }


def create_dashboard_with_table_layout(kpi_indices: List[int], table_ref: str) -> List[Dict[str, Any]]:
    """Create a complete dashboard layout with KPIs and table."""
    return [
        create_kpi_row_layout(kpi_indices),
        {"type": "spacer", "properties": {"height": DIMENSIONS.GAP_LARGE}},
        {"type": "table", "data_ref": table_ref}
    ]

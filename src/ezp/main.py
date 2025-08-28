#!/usr/bin/env python3
"""
EZ Pillow Dashboard Generator - Main Entry Point

A Python CLI tool that generates beautiful dashboard images from JSON data using PIL/Pillow.
This modular version uses reusable components for maintainable and flexible dashboard creation.
"""

import argparse
import json
import sys
from PIL import Image, ImageDraw

from .components import (
    COLORS, DIMENSIONS,
    KPICard, SectionCard, DashboardLayout,
    create_platform_table
)
from .components.kpi_layouts import KPILayoutType
from .components.global_layouts import GlobalLayoutManager
from .components.layout_intelligence import (
    suggest_smart_layout,
    create_layout_intelligence
)
from .components.declarative_layout import DeclarativeLayoutManager


def create_kpi_cards_from_data(kpi_data: list) -> list[KPICard]:
    """
    Create KPI card components from JSON data.

    Args:
        kpi_data: List of KPI dictionaries with title, value, and delta

    Returns:
        List of KPICard components
    """
    cards = []
    for kpi in kpi_data:
        card = KPICard(
            title=kpi.get("title", ""),
            value=kpi.get("value", ""),
            delta=kpi.get("delta")
        )
        cards.append(card)
    return cards


def create_section_cards_from_data(section_data: dict) -> list[SectionCard]:
    """
    Create section card components from JSON section data.

    Args:
        section_data: Section dictionary with cards array

    Returns:
        List of SectionCard components
    """
    cards = []
    for card_data in section_data.get("cards", []):
        card = SectionCard(
            title=card_data.get("title", ""),
            value=card_data.get("value", ""),
            delta=card_data.get("delta")
        )
        cards.append(card)
    return cards


def parse_layout_type(layout_config: dict, kpi_data: list = None) -> KPILayoutType:
    """Parse layout type from configuration with intelligent fallback."""
    layout_type_str = layout_config.get("type", "auto")

    # Manual layout mapping for explicit user choices
    layout_mapping = {
        "horizontal": KPILayoutType.HORIZONTAL,
        "grid_2x3": KPILayoutType.GRID_2x3,
        "grid_3x2": KPILayoutType.GRID_3x2,
        "priority": KPILayoutType.PRIORITY,
        "pyramid": KPILayoutType.PYRAMID,
        "featured": KPILayoutType.FEATURED,
        "responsive": KPILayoutType.RESPONSIVE,
        "custom": KPILayoutType.CUSTOM
    }

    # If explicitly specified and valid, use it
    if layout_type_str in layout_mapping:
        return layout_mapping[layout_type_str]

    # Otherwise, use intelligent auto-detection
    if kpi_data:
        return suggest_smart_layout(kpi_data, layout_type_str if layout_type_str != "auto" else None)

    # Final fallback
    return KPILayoutType.HORIZONTAL


def parse_global_layout_config(data: dict) -> dict:
    """Parse global layout configuration from data."""
    layout_config = data.get("global_layout", {})

    # Default to vertical layout if not specified
    direction = layout_config.get("direction", "vertical")

    return {
        "direction": direction,
        "start_y": layout_config.get("start_y", DIMENSIONS.PADDING),
        "gap": layout_config.get("gap", DIMENSIONS.GAP_LARGE)
    }


def should_use_declarative_layout(data: dict) -> bool:
    """Check if data contains declarative layout configuration."""
    return "layout" in data and isinstance(data.get("layout"), list)


def should_use_global_layout(data: dict) -> bool:
    """Check if data contains global layout configuration."""
    return "global_layout" in data or "components" in data


def render_dashboard_with_declarative_layout(data: dict, out_path: str = "dashboard.png") -> str:
    """
    Render dashboard using declarative layout system.

    Args:
        data: Dashboard data dictionary with declarative layout config
        out_path: Output file path

    Returns:
        Path to generated dashboard file
    """
    # Create canvas
    img = Image.new("RGB", (DIMENSIONS.WIDTH, DIMENSIONS.HEIGHT), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Initialize declarative layout manager
    layout_manager = DeclarativeLayoutManager()
    layout_manager.set_data_context(data)

    # Render declarative layout components
    layout_components = data.get("layout", [])
    current_y = layout_manager.render_layout(draw, layout_components, DIMENSIONS.PADDING)

    # Save image
    img.save(out_path)
    return out_path


def render_dashboard_with_global_layout(data: dict, out_path: str = "dashboard.png") -> str:
    """
    Render dashboard using global layout system.

    Args:
        data: Dashboard data dictionary with global layout config
        out_path: Output file path

    Returns:
        Path to generated dashboard file
    """
    # Create canvas
    img = Image.new("RGB", (DIMENSIONS.WIDTH, DIMENSIONS.HEIGHT), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Initialize global layout manager
    global_manager = GlobalLayoutManager()

    # Parse global layout configuration
    global_layout_config = parse_global_layout_config(data)

    # Check if components are explicitly defined
    if "components" in data:
        components = data["components"]
    else:
        # Create components from traditional data structure
        components = global_manager.create_layout_from_data(data)

    # Render with global layout system
    global_manager.render_component_layout(draw, components, global_layout_config)

    # Save image
    img.save(out_path)
    return out_path


def render_dashboard(data: dict, out_path: str = "dashboard.png") -> str:
    """
    Render complete dashboard from data using modular components.

    Args:
        data: Dashboard data dictionary
        out_path: Output file path

    Returns:
        Path to generated dashboard file
    """
    # Check layout system to use
    if should_use_declarative_layout(data):
        return render_dashboard_with_declarative_layout(data, out_path)
    elif should_use_global_layout(data):
        return render_dashboard_with_global_layout(data, out_path)

    # Create canvas
    img = Image.new("RGB", (DIMENSIONS.WIDTH, DIMENSIONS.HEIGHT), COLORS.BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Initialize layout manager
    layout = DashboardLayout()

    # Track current Y position
    current_y = layout.padding

    # 1. Render header
    current_y = layout.render_header(
        draw,
        title=data.get("title", "Dashboard"),
        date_note=data.get("date_note")
    )

    # 2. Render top KPIs with intelligent layout
    if "top_kpis" in data:
        kpi_cards = create_kpi_cards_from_data(data["top_kpis"])

        # Parse layout configuration with intelligent auto-detection
        layout_config = data.get("layout", {})
        layout_type = parse_layout_type(layout_config, data["top_kpis"])

        # Extract custom layout config if needed
        custom_config = None
        if layout_type == KPILayoutType.CUSTOM:
            custom_config = {"positions": layout_config.get("positions", [])}

        # Add debug info if requested
        if data.get("debug_layout", False):
            intelligence = create_layout_intelligence()
            explanation = intelligence.get_layout_explanation(data["top_kpis"])
            print(f"🧠 Layout Intelligence Analysis:")
            print(f"   Recommended: {explanation['recommended_layout']}")
            print(f"   Confidence: {explanation['confidence']:.1%}")
            print(f"   Reasoning: {explanation['reasoning']}")
            print(f"   Content Type: {explanation['content_type']}")

        current_y = layout.render_kpi_section(
            draw, kpi_cards, current_y, layout_type, custom_config
        )

    # 3. Render platform table
    if "platform_rows" in data:
        table = create_platform_table(data["platform_rows"])
        current_y = layout.render_table_section(draw, table, current_y)

    # 4. Render notes
    current_y = layout.render_notes_section(
        draw,
        left_note=data.get("notes_left"),
        right_note=data.get("notes_right"),
        y_position=current_y
    )

    # 5. Render middle section
    if "mid_section" in data:
        current_y = layout.render_section_header(
            draw, data["mid_section"].get("title", ""), current_y
        )

        mid_cards = create_section_cards_from_data(data["mid_section"])
        current_y = layout.render_card_grid(
            draw, mid_cards, current_y,
            columns=3, card_height=DIMENSIONS.SECTION_CARD_HEIGHT_MID
        )

    # 6. Render bottom section
    if "bottom_section" in data:
        current_y = layout.render_section_header(
            draw, data["bottom_section"].get("title", ""), current_y
        )

        bottom_cards = create_section_cards_from_data(data["bottom_section"])
        current_y = layout.render_card_grid(
            draw, bottom_cards, current_y,
            columns=5, card_height=DIMENSIONS.SECTION_CARD_HEIGHT_BOTTOM
        )

    # Save image
    img.save(out_path)
    return out_path


def load_data_from_json(json_path: str) -> dict:
    """
    Load dashboard data from a JSON file.

    Args:
        json_path: Path to JSON file

    Returns:
        Parsed JSON data dictionary

    Raises:
        SystemExit: If file not found, invalid JSON, or other error
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{json_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{json_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{json_path}': {e}")
        sys.exit(1)


def main():
    """Main entry point for dashboard generation."""
    parser = argparse.ArgumentParser(
        description="Generate a dashboard PNG from JSON data using modular components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Named arguments
  python main.py -i data.json
  python main.py -i data.json -o my_dashboard.png
  python main.py --input data.json --output result.png

  # Positional arguments (Docker-compatible)
  python main.py data.json output.png
        """
    )

    parser.add_argument(
        'input_file',
        nargs='?',
        type=str,
        help='Input JSON file (positional argument for Docker compatibility)'
    )

    parser.add_argument(
        'output_file',
        nargs='?',
        type=str,
        help='Output PNG file (positional argument for Docker compatibility)'
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        help='Input JSON file containing dashboard data'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='dashboard.png',
        help='Output PNG file (default: dashboard.png)'
    )

    args = parser.parse_args()

    # Determine input and output files (prioritize named args, fallback to positional)
    input_file = args.input or args.input_file
    output_file = args.output if args.output != 'dashboard.png' else (args.output_file or args.output)

    # Validate input file is provided
    if not input_file:
        print("Error: Input file must be provided either as -i/--input or as first positional argument")
        parser.print_help()
        sys.exit(1)

    # Load data from JSON
    print(f"Loading data from {input_file}...")
    data = load_data_from_json(input_file)

    # Generate dashboard
    print(f"Generating dashboard...")
    try:
        output_path = render_dashboard(data, output_file)
        print(f"Dashboard successfully generated: {output_path}")
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

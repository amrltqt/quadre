#!/usr/bin/env python3
"""
NADA — Not A Dashboard App (Main Entry Point)

A Python CLI that generates static dashboard PNGs from JSON using Pillow.
Built on a lightweight Flex layout engine with reusable components.
"""

import argparse
import json
import sys

from nada.flex.runner import render_dashboard_with_flex


def render_dashboard(data: dict, out_path: str = "dashboard.png") -> str:
    """
    Render complete dashboard from data using modular components.

    Args:
        data: Dashboard data dictionary
        out_path: Output file path

    Returns:
        Path to generated dashboard file
    """
    # Single rendering path: Flex engine
    return render_dashboard_with_flex(data, out_path)

    # Legacy procedural renderer removed in favor of Flex for the default path.


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
        with open(json_path, "r", encoding="utf-8") as f:
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
  uv run -m nada.main -i data.json
  uv run -m nada.main -i data.json -o my_dashboard.png
  uv run -m nada.main --input data.json --output result.png

  # Positional arguments
  uv run -m nada.main data.json output.png
        """,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=str,
        help="Input JSON file (positional argument for Docker compatibility)",
    )

    parser.add_argument(
        "output_file",
        nargs="?",
        type=str,
        help="Output PNG file (positional argument for Docker compatibility)",
    )

    parser.add_argument(
        "-i", "--input", type=str, help="Input JSON file containing dashboard data"
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="dashboard.png",
        help="Output PNG file (default: dashboard.png)",
    )

    args = parser.parse_args()

    # Determine input and output files (prioritize named args, fallback to positional)
    input_file = args.input or args.input_file
    output_file = (
        args.output
        if args.output != "dashboard.png"
        else (args.output_file or args.output)
    )

    # Validate input file is provided
    if not input_file:
        print(
            "Error: Input file must be provided either as -i/--input or as first positional argument"
        )
        parser.print_help()
        sys.exit(1)

    # Load data from JSON
    print(f"Loading data from {input_file}...")
    data = load_data_from_json(input_file)

    # Generate dashboard
    print("Generating dashboard...")
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

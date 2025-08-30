#!/usr/bin/env python3
"""
quadre — Library entry points (no CLI)

High-level functions for rendering dashboards from Python.
"""

import json
import sys

from quadre.flex.runner import render_dashboard_with_flex
from quadre.flex.runner import build_dashboard_image
from quadre.plugins import image_to_bytes


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


def render_dashboard_bytes(data: dict, format: str = "PNG") -> bytes:
    """
    Render the dashboard and return encoded image bytes (PNG by default).

    This is a programmatic API that avoids writing to disk and is suitable for
    piping the result to third-party systems. To change format, pass e.g.
    format="WEBP" or "JPEG".

    Args:
        data: Dashboard data dictionary
        format: Output encoding format (default: "PNG")

    Returns:
        Encoded image bytes
    """
    img = build_dashboard_image(data)
    return image_to_bytes(img, format=format)


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


__all__ = [
    "render_dashboard",
    "render_dashboard_bytes",
    "load_data_from_json",
]

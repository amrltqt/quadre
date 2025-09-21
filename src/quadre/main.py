#!/usr/bin/env python3
"""
quadre — Library entry points (no CLI)

High-level functions for rendering dashboards from Python.
"""

import json
import sys

from quadre.generator import generate_image
from quadre.plugins import image_to_bytes
from quadre.models import DocumentDef


def render_dashboard_bytes(data: dict, format: str = "PNG") -> bytes:
    """
    Render the dashboard and return encoded image bytes (PNG by default).

    This is a programmatic API that avoids writing to disk and is suitable for
    piping the result to third-party systems. The Cairo backend currently
    supports PNG output only; other formats will raise `ValueError`.

    Args:
        data: Dashboard data dictionary
        format: Output encoding format (default: "PNG")

    Returns:
        Encoded image bytes
    """
    doc = data if isinstance(data, DocumentDef) else DocumentDef.model_validate(data)
    surface = generate_image(doc)
    return image_to_bytes(surface, format=format)


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

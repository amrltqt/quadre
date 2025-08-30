"""Quadre — top-level package exports (no function definitions)."""

from .api import render, build_image, to_bytes, register_output_plugin, validate_layout

__all__ = ["render", "build_image", "to_bytes", "register_output_plugin", "validate_layout"]

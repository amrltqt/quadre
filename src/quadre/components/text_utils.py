"""Text utilities for component rendering."""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def truncate_text(canvas, text: str, font_spec, max_width: int) -> str:
    """
    Truncate text to fit within max_width, adding ellipsis if needed.

    Uses binary search to find the longest possible text that fits with "..." suffix.

    Args:
        canvas: CairoCanvas instance for text measurement
        text: Original text to truncate
        font_spec: Font specification for measuring
        max_width: Maximum width in pixels

    Returns:
        Truncated text with ellipsis if needed, or original text if it fits
    """
    if max_width <= 0:
        return ""

    text = text.strip()
    if not text:
        return ""

    # Check if full text fits
    full_w, _ = canvas.measure_text(text, font_spec)
    if full_w <= max_width:
        return text

    # Binary search for the longest text that fits with ellipsis
    ellipsis = "..."
    ellipsis_w, _ = canvas.measure_text(ellipsis, font_spec)
    available_w = max_width - ellipsis_w

    if available_w <= 0:
        return ellipsis

    # Start with reasonable bounds
    left, right = 0, len(text)
    best_text = ""

    while left <= right:
        mid = (left + right) // 2
        candidate = text[:mid]
        candidate_w, _ = canvas.measure_text(candidate, font_spec)

        if candidate_w <= available_w:
            best_text = candidate
            left = mid + 1
        else:
            right = mid - 1

    result = best_text + ellipsis if best_text else ellipsis

    logger.debug(f"Text truncated", extra={
        "original_length": len(text),
        "truncated_length": len(best_text),
        "max_width": max_width,
        "ellipsis_added": len(result) > len(text)
    })

    return result


def fit_text_multiline(canvas, text: str, font_spec, max_width: int, max_height: int) -> Tuple[str, int]:
    """
    Fit text into multiple lines within given dimensions.

    Args:
        canvas: CairoCanvas instance for text measurement
        text: Original text to fit
        font_spec: Font specification for measuring
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels

    Returns:
        Tuple of (fitted_text, actual_height)
    """
    if max_width <= 0 or max_height <= 0:
        return "", 0

    text = text.strip()
    if not text:
        return "", 0

    # Get line height
    _, line_height = canvas.measure_text("Ag", font_spec)
    max_lines = max(1, max_height // line_height)

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_w, _ = canvas.measure_text(test_line, font_spec)

        if test_w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word too long, truncate it
                current_line = truncate_text(canvas, word, font_spec, max_width)
                lines.append(current_line)
                current_line = ""

            if len(lines) >= max_lines:
                break

    # Add remaining text
    if current_line and len(lines) < max_lines:
        lines.append(current_line)

    # If we have too many lines, truncate the last one with ellipsis
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = truncate_text(canvas, lines[-1], font_spec, max_width)

    fitted_text = "\n".join(lines)
    actual_height = len(lines) * line_height

    logger.debug(f"Text fitted to multiline", extra={
        "original_words": len(words),
        "fitted_lines": len(lines),
        "max_lines": max_lines,
        "actual_height": actual_height
    })

    return fitted_text, actual_height


def measure_text_bounds(canvas, text: str, font_spec) -> Tuple[int, int]:
    """
    Get the precise bounds of text.

    Args:
        canvas: CairoCanvas instance for text measurement
        text: Text to measure
        font_spec: Font specification

    Returns:
        Tuple of (width, height) in pixels
    """
    if not text.strip():
        return 0, 0

    return canvas.measure_text(text, font_spec)

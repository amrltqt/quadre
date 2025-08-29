from __future__ import annotations

"""
Theme system for quadre.

Provides a Pydantic-validated theme that controls:
- Global colors and font sizes
- Per-widget default properties (FlexContainer, TextWidget, TableWidget, Spacer)

Load order:
- If env var quadre_THEME points to a JSON file, load and validate it
- Otherwise, load bundled default at src/quadre/theme/theme.json

Renderer integration:
- The runner applies colors/fonts via components.config.apply_theme
- Widget defaults are exposed to flex.defaults via a mapping

Widgets can still override properties explicitly in layout nodes.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class ColorsModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    background: str = Field("#ffffff", description="Canvas background color")
    card_background: str = Field("#ffffff", description="Card background color")
    muted: str = Field(
        "#f1f5f9", description="Muted background surfaces (e.g., header)"
    )

    border: str = Field("#d1d5db", description="Neutral border color")
    input: str = Field("#e2e8f0", description="Input border/fill color")
    ring: str = Field("#3b82f6", description="Focus ring color")

    foreground: str = Field("#0f172a", description="Primary foreground text color")
    muted_foreground: str = Field("#64748b", description="Muted text color")

    primary: str = Field("#0f172a", description="Primary brand color")
    primary_foreground: str = Field("#f8fafc", description="On-primary text color")

    secondary: str = Field("#f1f5f9", description="Secondary surface color")
    secondary_foreground: str = Field("#0f172a", description="On-secondary text color")

    accent: str = Field("#f1f5f9", description="Accent surface color")
    accent_foreground: str = Field("#0f172a", description="On-accent text color")

    destructive: str = Field("#ef4444", description="Negative / error color")
    destructive_foreground: str = Field(
        "#f8fafc", description="On-destructive text color"
    )
    success: str = Field("#22c55e", description="Positive / success color")
    success_foreground: str = Field("#f8fafc", description="On-success text color")
    warning: str = Field("#eab308", description="Warning color")
    warning_foreground: str = Field("#0f172a", description="On-warning text color")


class FontsModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    h1: int = Field(42, description="Heading 1 font size (px)")
    h2: int = Field(30, description="Heading 2 font size (px)")
    number: int = Field(40, description="Numeric large font size (px)")
    body: int = Field(24, description="Body text font size (px)")
    table: int = Field(24, description="Table text font size (px)")
    small: int = Field(20, description="Small text font size (px)")
    bold_small: int = Field(24, description="Small bold text font size (px)")


class FlexContainerDefaults(BaseModel):
    model_config = ConfigDict(extra="ignore")

    gap: int = Field(16, description="Gap between items (px)")
    align_items: str = Field(
        "stretch", description="Cross-axis alignment: start|center|end|stretch"
    )
    justify_content: str = Field(
        "start",
        description="Main-axis distribution: start|center|end|space-between|space-around|space-evenly",
    )
    padding: int = Field(0, description="Padding inside container (px)")
    bg_fill: Optional[str] = Field(
        None, description="Background fill color token or hex"
    )
    bg_outline: Optional[str] = Field(
        None, description="Background outline color token or hex"
    )
    bg_radius: int = Field(12, description="Background corner radius (px)")


class TextWidgetDefaults(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fill: str = Field("FOREGROUND", description="Text color token or hex")
    align: str = Field("left", description="left|center|right")
    font: str = Field(
        "body", description="Font style: title|heading|body|caption|table"
    )


class TableWidgetDefaults(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fill_height: bool = Field(
        False, description="Stretch rows to fill available height"
    )
    fit: str = Field("truncate", description="Row fit strategy: truncate|shrink")
    min_row_height: int = Field(
        28, description="Minimum row height when truncating (px)"
    )
    max_row_height: int = Field(90, description="Maximum row height when filling (px)")
    shrink_row_height_floor: int = Field(
        14, description="Lower bound for shrink strategy (px)"
    )


class SpacerDefaults(BaseModel):
    model_config = ConfigDict(extra="ignore")

    height: int = Field(24, description="Spacer height (px)")


class WidgetsModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    FlexContainer: FlexContainerDefaults = Field(default_factory=FlexContainerDefaults)
    TextWidget: TextWidgetDefaults = Field(default_factory=TextWidgetDefaults)
    TableWidget: TableWidgetDefaults = Field(default_factory=TableWidgetDefaults)
    Spacer: SpacerDefaults = Field(default_factory=SpacerDefaults)


class ThemeModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    colors: ColorsModel = Field(
        default_factory=ColorsModel, description="Global color palette"
    )
    fonts: FontsModel = Field(
        default_factory=FontsModel, description="Global font sizes"
    )
    widgets: WidgetsModel = Field(
        default_factory=WidgetsModel, description="Per-widget default properties"
    )


def _default_theme_path() -> Path:
    here = Path(__file__).parent
    return here / "theme" / "theme.json"


def builtin_theme_path(name: str) -> Path:
    """Return the path to a bundled theme by name (e.g., 'dark' or 'theme')."""
    here = Path(__file__).parent / "theme"
    if name.lower() in ("light", "default", "theme"):
        return here / "theme.json"
    return here / f"{name}.json"


def load_theme_from_env_or_default() -> ThemeModel:
    """Load theme from quadre_THEME path or the bundled default; fail hard on error.

    - If quadre_THEME is set, it must point to a readable JSON file matching ThemeModel.
    - Otherwise, the bundled default theme must exist and be valid.
    """
    env_path = os.environ.get("quadre_THEME")
    if env_path:
        candidate = Path(env_path)
        if not candidate.exists():
            raise FileNotFoundError(
                f"quadre_THEME points to a missing file: {candidate}"
            )
    else:
        candidate = _default_theme_path()
        if not candidate.exists():
            raise FileNotFoundError(f"Default theme file not found: {candidate}")

    try:
        raw = candidate.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to read theme file: {candidate}: {e}") from e

    try:
        data = json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Invalid JSON in theme file: {candidate}: {e}") from e
    # Normalize color/font keys to lowercase to accept either case in input
    if isinstance(data, dict):
        if isinstance(data.get("colors"), dict):
            data["colors"] = {str(k).lower(): v for k, v in data["colors"].items()}
        if isinstance(data.get("fonts"), dict):
            data["fonts"] = {str(k).lower(): v for k, v in data["fonts"].items()}
    # Will raise pydantic.ValidationError on schema issues
    return ThemeModel.model_validate(data)


def as_apply_theme_dict(theme: ThemeModel) -> Dict[str, Any]:
    """Convert ThemeModel to dict schema accepted by components.config.apply_theme."""
    colors = theme.colors.model_dump()
    fonts = theme.fonts.model_dump()
    return {"colors": colors, "fonts": fonts}


def widget_defaults_from_theme(theme: ThemeModel) -> Dict[str, Any]:
    """Expose per-widget defaults as a simple mapping used by flex.defaults."""
    w = theme.widgets
    return {
        "FlexContainer": w.FlexContainer.model_dump(),
        "TextWidget": w.TextWidget.model_dump(),
        "TableWidget": w.TableWidget.model_dump(),
        "Spacer": w.Spacer.model_dump(),
    }

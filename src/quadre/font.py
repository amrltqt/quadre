"""Font specifications and registry for Cairo rendering."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Iterator


@dataclass(frozen=True)
class FontSpec:
    """Simple font specification understood by the Cairo canvas."""

    family: str
    size: int
    weight: str = "normal"  # "normal" or "bold"

    def scaled(self, scale: float) -> "FontSpec":
        size = max(1, int(round(self.size * scale)))
        return replace(self, size=size)


DEFAULT_FONT_FAMILY = "Inter"

BASE_FONT_SPECS: Dict[str, FontSpec] = {
    "H1": FontSpec(DEFAULT_FONT_FAMILY, 84, "bold"),
    "H2": FontSpec(DEFAULT_FONT_FAMILY, 60, "bold"),
    "H3": FontSpec(DEFAULT_FONT_FAMILY, 52, "bold"),
    "H4": FontSpec(DEFAULT_FONT_FAMILY, 44, "bold"),
    "NUMBER": FontSpec(DEFAULT_FONT_FAMILY, 80, "bold"),
    "BODY": FontSpec(DEFAULT_FONT_FAMILY, 48, "normal"),
    "TABLE": FontSpec(DEFAULT_FONT_FAMILY, 48, "normal"),
    "SMALL": FontSpec(DEFAULT_FONT_FAMILY, 40, "normal"),
    "BOLD_SMALL": FontSpec(DEFAULT_FONT_FAMILY, 48, "bold"),
}


class FontRegistry:
    """Tracks active font specs with optional scale/family overrides."""

    def __init__(self, base_specs: Dict[str, FontSpec]) -> None:
        self._base_specs = dict(base_specs)
        self._scale: float = 1.0
        self._family_override: str | None = None
        self._active: Dict[str, FontSpec] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        self._active.clear()
        for name, spec in self._base_specs.items():
            family = self._family_override or spec.family
            scaled = FontSpec(family, spec.size, spec.weight).scaled(self._scale)
            self._active[name] = scaled

    # Public API ---------------------------------------------------------
    def set_scale(self, scale: float) -> None:
        self._scale = float(scale) if scale and scale > 0 else 1.0
        self._rebuild()

    def set_family(self, family: str | None) -> None:
        if family is None:
            self._family_override = None
        else:
            cleaned = family.strip()
            self._family_override = cleaned or None
        self._rebuild()

    def set_base_size(self, name: str, size: int) -> None:
        if name not in self._base_specs:
            raise KeyError(name)
        spec = self._base_specs[name]
        self._base_specs[name] = replace(spec, size=max(1, int(size)))
        self._rebuild()

    def get(self, name: str) -> FontSpec:
        return self._active[name]

    def __getattr__(self, item: str) -> FontSpec:
        try:
            return self._active[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def items(self) -> Iterator[tuple[str, FontSpec]]:
        return iter(self._active.items())

    @property
    def family_override(self) -> str | None:
        return self._family_override


FONTS = FontRegistry(BASE_FONT_SPECS)


def rebuild_fonts(scale: float) -> None:
    FONTS.set_scale(scale)


def set_custom_font_family(family: str | None) -> None:
    FONTS.set_family(family)


def get_custom_font_family() -> str | None:
    return FONTS.family_override


__all__ = [
    "FontSpec",
    "FONTS",
    "BASE_FONT_SPECS",
    "rebuild_fonts",
    "set_custom_font_family",
    "get_custom_font_family",
]

import logging
from typing import Any, List, Literal, Optional, Tuple, Type
from pydantic import Field, PrivateAttr, field_validator
from quadre.components import Component, COMPONENTS
from quadre.components.registry import component
from quadre.flex.models import FlexLayout
from quadre.cairo_canvas import CairoCanvas
from quadre.config import get_current_scale

logger = logging.getLogger(__name__)


@component("root")
class Root(Component, FlexLayout):
    """
    Root component that serves as the top-level container for the entire canvas.
    Simply stacks children vertically without restricting their preferred size.
    """

    type: Literal["root"] = "root"

    # Canvas-level properties
    children: List[Component] = Field(default_factory=list)
    padding: int = 0
    gap: int = 10  # Space between children
    width: Optional[int] = None  # Optional width constraint
    margin_top: int = 32
    margin_bottom: int = 32
    margin_left: int = 32
    margin_right: int = 32

    _cached_inner_width: Optional[int] = PrivateAttr(default=None)
    _cached_child_sizes: List[Tuple[int, int]] = PrivateAttr(default_factory=list)

    def add(self, component: Component) -> 'Root':
        """Add a component to the root content."""
        self.children.append(component)
        return self

    @field_validator("children", mode="before")
    @classmethod
    def parse_children(cls, v: Any):
        if v is None:
            return []
        out = []
        for i, item in enumerate(v):
            if isinstance(item, Component):
                out.append(item)
                continue
            if not isinstance(item, dict):
                raise TypeError(f"Invalid child component: {type(item)!r}")
            t = item.get("type")
            if not t:
                raise ValueError("Field type is missing from the child component")
            model: Type[Component] | None = COMPONENTS.get(t)
            if not model:
                logger.error(f"Unknown child component type: {t!r}", extra={
                    "available_components": sorted(COMPONENTS.keys()),
                    "component_data": item
                })
                raise ValueError(
                    f"Unknown child component: {t!r}. Registered: {sorted(COMPONENTS)}"
                )
            instance = model.model_validate(item)
            out.append(instance)
        return out

    def measure(self, canvas: CairoCanvas, avail_w: int, avail_h: int) -> Tuple[int, int]:
        """
        Measure root by giving children generous space and stacking vertically.
        This ensures children are not constrained by artificial limits.
        """
        if not self.children:
            return (2 * self.padding, 2 * self.padding)

        # Apply margins and width constraint
        scale = get_current_scale()
        scaled_margin_left = int(round(self.margin_left * scale))
        scaled_margin_right = int(round(self.margin_right * scale))

        # Apply width constraint if specified (scale it to match render units)
        effective_w = avail_w - scaled_margin_left - scaled_margin_right
        if self.width is not None:
            scaled_width = int(round(self.width * scale))
            effective_w = min(scaled_width, effective_w) if effective_w > 0 else scaled_width

        inner_w = max(effective_w - 2 * self.padding, 0)
        # Use a large height allowance so children can reveal their preferred height
        # while still respecting the provided width constraint.
        height_hint = max(avail_h, 10_000_000)

        child_sizes, max_width, total_height = self._measure_children(canvas, inner_w, height_hint)

        self._cached_inner_width = inner_w
        self._cached_child_sizes = child_sizes

        final_w = max_width + 2 * self.padding + scaled_margin_left + scaled_margin_right

        scaled_margin_top = int(round(self.margin_top * scale))
        scaled_margin_bottom = int(round(self.margin_bottom * scale))
        final_h = total_height + 2 * self.padding + scaled_margin_top + scaled_margin_bottom

        # Apply width constraint (scale it to match render units)
        if self.width is not None:
            scaled_width = int(round(self.width * scale)) + scaled_margin_left + scaled_margin_right
            final_w = min(final_w, scaled_width)

        result = (
            min(final_w, avail_w) if avail_w >= 0 else final_w,
            min(final_h, avail_h) if avail_h >= 0 else final_h,
        )
        logger.debug(f"Root measured", extra={
            "available_space": f"{avail_w}x{avail_h}",
            "width_constraint": self.width,
            "margins": f"{self.margin_top},{self.margin_right},{self.margin_bottom},{self.margin_left}",
            "children_count": len(self.children),
            "result_size": f"{result[0]}x{result[1]}",
            "total_content_height": total_height
        })
        return result

    def render(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        """
        Render the root: stack children vertically.
        Each child gets its preferred width and height.
        """
        if not self.children:
            logger.debug("Root render: no children to render")
            return

        # Calculate content area with margins
        scale = get_current_scale()
        scaled_margin_left = int(round(self.margin_left * scale))
        scaled_margin_right = int(round(self.margin_right * scale))
        scaled_margin_top = int(round(self.margin_top * scale))
        scaled_margin_bottom = int(round(self.margin_bottom * scale))

        content_x = x + scaled_margin_left + self.padding
        content_y = y + scaled_margin_top + self.padding
        content_w = max(0, w - scaled_margin_left - scaled_margin_right - 2 * self.padding)
        content_h = max(0, h - scaled_margin_top - scaled_margin_bottom - 2 * self.padding)

        if content_w <= 0 or content_h <= 0:
            logger.debug(f"Root render skipped due to invalid content area: {content_w}x{content_h}")
            return

        child_sizes = self._ensure_layout_cache(canvas, content_w, content_h)

        if not child_sizes:
            logger.debug("Root render: no valid child sizes calculated")
            return

        current_y = content_y
        content_bottom = content_y + content_h

        logger.debug(f"Root rendering {len(self.children)} children", extra={
            "content_area": f"{content_x},{content_y} {content_w}x{content_h}",
            "margins": f"t:{scaled_margin_top} r:{scaled_margin_right} b:{scaled_margin_bottom} l:{scaled_margin_left}"
        })

        for index, (child, (measured_w, measured_h)) in enumerate(zip(self.children, child_sizes)):
            remaining_h = content_bottom - current_y
            if remaining_h <= 0:
                logger.debug(f"Root: stopping at child {index}, no remaining height")
                break

            actual_w = min(measured_w, content_w)
            actual_h = min(measured_h, remaining_h)

            child_x = content_x
            if actual_w < content_w:
                child_x = content_x + (content_w - actual_w) // 2

            child.render(canvas, child_x, current_y, actual_w, actual_h)

            current_y += actual_h
            if index < len(self.children) - 1:
                current_y += self.gap

    def _measure_children(
        self,
        canvas: CairoCanvas,
        inner_w: int,
        height_hint: int,
    ) -> Tuple[List[Tuple[int, int]], int, int]:
        if not self.children:
            return [], 0, 0

        child_sizes: List[Tuple[int, int]] = []
        max_width = 0
        total_height = 0

        for index, child in enumerate(self.children):
            child_w, child_h = child.measure(canvas, inner_w, height_hint)
            child_sizes.append((child_w, child_h))
            max_width = max(max_width, child_w)
            total_height += child_h
            if index < len(self.children) - 1:
                total_height += self.gap

        return child_sizes, max_width, total_height

    def _ensure_layout_cache(
        self, canvas: CairoCanvas, content_w: int, content_h: int
    ) -> List[Tuple[int, int]]:
        if not self.children or content_w <= 0:
            return []

        if (
            self._cached_inner_width == content_w
            and len(self._cached_child_sizes) == len(self.children)
        ):
            return self._cached_child_sizes

        height_hint = max(content_h, 10_000_000)
        child_sizes, _, _ = self._measure_children(
            canvas, content_w, height_hint
        )
        self._cached_inner_width = content_w
        self._cached_child_sizes = child_sizes
        return child_sizes

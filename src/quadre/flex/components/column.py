import logging
from typing import Any, List, Literal, Tuple, Type
from pydantic import Field, field_validator
from quadre.components import Component, COMPONENTS
from quadre.components.registry import component
from quadre.flex.models import FlexLayout
from quadre.cairo_canvas import CairoCanvas

logger = logging.getLogger(__name__)

@component("column")
class Column(Component, FlexLayout):
    """
    Represents a container that arranges its children in a flexible column.
    """

    type: Literal["column"] = "column"

    children: List[Component] = Field(default_factory=list)
    gap: int = 10
    align_items: str = "stretch"  # start|center|end|stretch (cross axis)
    justify_content: str = (
        "start"  # start|center|end|space-between|space-around|space-evenly
    )
    padding: int = 0
    clip_children: bool = True

    def add(
        self,
        component: Component
    ) -> FlexLayout:
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

    # Measure returns preferred size if unconstrained. For simplicity, sum of children along main axis.
    def measure(
        self, canvas: CairoCanvas, avail_w: int, avail_h: int
    ) -> Tuple[int, int]:

        inner_w = max(0, avail_w - 2 * self.padding)
        inner_h = max(0, avail_h - 2 * self.padding)

        main_sum = 0
        cross_max = 0

        for i, item in enumerate(self.children):
            mw, mh = item.measure(canvas, inner_w, inner_h)

            base = mh
            main_sum += base
            cross_max = max(cross_max, mw)

        if len(self.children) > 1:
            main_sum += (len(self.children) - 1) * self.gap

        preferred_w = (cross_max) + 2 * self.padding
        preferred_h = (main_sum) + 2 * self.padding
        result = (min(preferred_w, avail_w), min(preferred_h, avail_h))
        logger.debug("Column measured", extra={
            "available_space": f"{avail_w}x{avail_h}",
            "children_count": len(self.children),
            "result_size": f"{result[0]}x{result[1]}",
            "total_content_height": main_sum
        })
        return result

    def _layout(
        self, canvas: CairoCanvas, x: int, y: int, w: int, h: int
    ) -> List[Tuple[int, int, int, int]]:
        # Compute layout rects for each child
        inner_x = x + self.padding
        inner_y = y + self.padding
        inner_w = max(0, w - 2 * self.padding)
        inner_h = max(0, h - 2 * self.padding)

        if not self.children:
            return []

        # For columns: main axis = vertical (height), cross axis = horizontal (width)
        child_heights: List[int] = []  # main axis sizes
        child_widths: List[int] = []   # cross axis sizes

        for item in self.children:
            mw, mh = item.measure(canvas, inner_w, inner_h)
            child_heights.append(mh)  # main axis size
            child_widths.append(mw)   # cross axis size

        # Calculate total height needed
        total_gaps = self.gap * max(0, len(self.children) - 1)
        total_height_needed = sum(child_heights) + total_gaps
        remaining_height = max(0, inner_h - total_height_needed)

        # Adjust start offset and gaps based on justify_content
        gap_val = self.gap
        start_y_offset = 0
        n = len(self.children)

        if self.justify_content == "center":
            start_y_offset = remaining_height // 2
        elif self.justify_content == "end":
            start_y_offset = remaining_height
        elif self.justify_content == "space-between" and n > 1:
            gap_val = self.gap + (remaining_height // (n - 1))
        elif self.justify_content == "space-around" and n > 0:
            extra_gap = remaining_height // n
            gap_val = self.gap + extra_gap
            start_y_offset = extra_gap // 2
        elif self.justify_content == "space-evenly" and n > 0:
            extra_gap = remaining_height // (n + 1)
            gap_val = self.gap + extra_gap
            start_y_offset = extra_gap

        # Position children
        rects: List[Tuple[int, int, int, int]] = []
        current_y = inner_y + start_y_offset

        for i, (child_w, child_h) in enumerate(zip(child_widths, child_heights)):
            # Height is determined by child preference
            ch = child_h

            # Width depends on align_items
            if self.align_items == "stretch":
                cw = inner_w
                cx = inner_x
            else:
                cw = min(child_w, inner_w)
                if self.align_items == "center":
                    cx = inner_x + (inner_w - cw) // 2
                elif self.align_items == "end":
                    cx = inner_x + (inner_w - cw)
                else:  # start
                    cx = inner_x

            rects.append((cx, current_y, cw, ch))
            current_y += ch + gap_val

        return rects

    def render(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        if w <= 0 or h <= 0:
            logger.debug(f"Column render skipped due to invalid dimensions: {w}x{h}")
            return

        rects = self._layout(canvas, x, y, w, h)
        logger.debug(f"Column rendering {len(self.children)} children", extra={
            "position": f"{x},{y}",
            "size": f"{w}x{h}",
            "child_rects": rects
        })

        for item, rect in zip(self.children, rects):
            ix, iy, iw, ih = rect
            if iw <= 0 or ih <= 0:
                logger.debug(f"Skipping child with invalid dimensions: {iw}x{ih}")
                continue
            if self.clip_children:
                layer = canvas.new_layer(iw, ih)
                item.render(layer, 0, 0, iw, ih)
                canvas.composite_layer(layer, ix, iy)
            else:
                item.render(canvas, ix, iy, iw, ih)

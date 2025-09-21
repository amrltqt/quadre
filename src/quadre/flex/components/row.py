import logging
from typing import Any, List, Literal, Tuple, Type
from pydantic import Field, field_validator
from quadre.components import Component, COMPONENTS
from quadre.components.registry import component
from quadre.flex.models import FlexLayout
from quadre.cairo_canvas import CairoCanvas

logger = logging.getLogger(__name__)


@component("row")
class Row(Component, FlexLayout):
    """
    Horizontal flex container mirroring Column semantics across the x-axis.
    """

    type: Literal["row"] = "row"

    children: List[Component] = Field(default_factory=list)
    gap: int = 10
    align_items: str = "stretch"  # start|center|end|stretch (cross axis)
    justify_content: str = "start"  # start|center|end|space-between|space-around|space-evenly
    padding: int = 0
    clip_children: bool = True

    def add(self, component: Component) -> FlexLayout:
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
        inner_w = max(0, avail_w - 2 * self.padding)
        inner_h = max(0, avail_h - 2 * self.padding)
        n = len(self.children)

        if n == 0 or inner_w <= 0:
            base_width = 2 * self.padding
            width = min(base_width, avail_w) if avail_w >= 0 else base_width
            return max(0, width), 0

        usable = max(0, inner_w - self.gap * max(0, n - 1))
        slot = usable / n if n else 0.0

        cross_max = 0
        for i, child in enumerate(self.children):
            target = max(1, int(round(slot))) if slot > 0 else inner_w
            mw, mh = child.measure(canvas, target, inner_h)
            cross_max = max(cross_max, mh)

        preferred_w = inner_w + 2 * self.padding
        preferred_h = cross_max + 2 * self.padding
        width = min(preferred_w, avail_w) if avail_w >= 0 else preferred_w
        height = min(preferred_h, avail_h) if avail_h >= 0 else preferred_h
        logger.debug("Row measured", extra={
            "available_space": f"{avail_w}x{avail_h}",
            "children_count": len(self.children),
            "result_size": f"{width}x{height}",
            "max_child_height": cross_max
        })
        return width, height

    def _layout(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> List[Tuple[int, int, int, int]]:
        inner_x = x + self.padding
        inner_y = y + self.padding
        inner_w = max(0, w - 2 * self.padding)
        inner_h = max(0, h - 2 * self.padding)

        cross_sizes: List[int] = []
        for item in self.children:
            _, mh = item.measure(canvas, inner_w, inner_h)
            cross_sizes.append(mh)

        total_gaps = self.gap * max(0, len(self.children) - 1)
        remaining = max(0, inner_w - total_gaps)

        gap_val = self.gap
        offset = 0
        n = len(self.children)
        if self.justify_content in ("center", "end") or (self.justify_content.startswith("space") and n > 1):
            if self.justify_content == "center":
                offset = remaining // 2
            elif self.justify_content == "end":
                offset = remaining
            elif self.justify_content == "space-between" and n > 1:
                gap_val = self.gap + (remaining // (n - 1))
            elif self.justify_content == "space-around" and n > 0:
                gap_val = self.gap + (remaining // n)
                offset = gap_val // 2
            elif self.justify_content == "space-evenly" and n > 0:
                gap_val = self.gap + (remaining // (n + 1))
                offset = gap_val

        cur_x = inner_x + offset
        rects: List[Tuple[int, int, int, int]] = []

        slot = remaining / n if n > 0 else 0.0

        for idx, (cross_h, item) in enumerate(zip(cross_sizes, self.children)):
            remaining_w = max(0, inner_x + inner_w - cur_x)
            if remaining_w <= 0:
                break
            target_w = slot if n > 0 else remaining_w
            if idx == n - 1:
                target_w = remaining_w
            cw = max(1, min(int(round(target_w)), remaining_w))
            _, measured_h = item.measure(canvas, cw, inner_h)
            ch = min(measured_h if measured_h else cross_h, inner_h)
            align = self.align_items
            if align == "center":
                cy = inner_y + (inner_h - ch) // 2
            elif align == "end":
                cy = inner_y + (inner_h - ch)
            else:
                cy = inner_y
            rects.append((cur_x, cy, cw, ch))
            cur_x += cw + gap_val
        return rects

    def render(self, canvas: CairoCanvas, x: int, y: int, w: int, h: int) -> None:
        if w <= 0 or h <= 0:
            logger.debug(f"Row render skipped due to invalid dimensions: {w}x{h}")
            return

        rects = self._layout(canvas, x, y, w, h)
        logger.debug(f"Row rendering {len(self.children)} children", extra={
            "position": f"{x},{y}",
            "size": f"{w}x{h}",
            "child_rects": rects
        })

        for item, (ix, iy, iw, ih) in zip(self.children, rects):
            if iw <= 0 or ih <= 0:
                logger.debug(f"Skipping child with invalid dimensions: {iw}x{ih}")
                continue
            if self.clip_children:
                layer = canvas.new_layer(iw, ih)
                item.render(layer, 0, 0, iw, ih)
                canvas.composite_layer(layer, ix, iy)
            else:
                item.render(canvas, ix, iy, iw, ih)

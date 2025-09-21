import logging
from typing import Any, List, Optional, Type
from pydantic import BaseModel, field_validator, ConfigDict
from quadre.components import Component, COMPONENTS

logger = logging.getLogger(__name__)


class MarginDef(BaseModel):
    top: int | None = None
    bottom: int | None = None
    left: int | None = None
    right: int | None = None


class CanvasDef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    margin: Optional[MarginDef] = None
    width: Optional[int] = None
    font_family: Optional[str] = None
    scale: Optional[float] = None

    @field_validator("width")
    @classmethod
    def validate_width(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("canvas.width must be a positive integer")
        return value

    @field_validator("font_family")
    @classmethod
    def validate_font_family(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("canvas.font_family must be a non-empty string")
        return cleaned

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        try:
            scale = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("canvas.scale must be a positive number") from exc
        if scale <= 0:
            raise ValueError("canvas.scale must be a positive number")
        if scale > 8:
            raise ValueError("canvas.scale must be less than or equal to 8")
        return scale


class DocumentDef(BaseModel):
    components: List[Component]
    canvas: Optional[CanvasDef] = None

    @field_validator("components", mode="before")
    @classmethod
    def parse_components(cls, v: Any):
        if v is None:
            return []
        out = []
        for item in v:
            if isinstance(item, Component):
                out.append(item)
                continue
            if not isinstance(item, dict):
                raise TypeError(f"Invalid component: {type(item)!r}")
            t = item.get("type")
            if not t:
                logger.error("Component missing type field", extra={"component_data": item})
                raise ValueError("Field type is missing from the component")
            model: Type[Component] | None = COMPONENTS.get(t)
            if not model:
                logger.error(f"Unknown component type: {t!r}", extra={
                    "available_components": sorted(COMPONENTS.keys()),
                    "component_data": item
                })
                raise ValueError(
                    f"Unknown component: {t!r}. Registered: {sorted(COMPONENTS)}"
                )
            logger.debug(f"Creating component: {t}")
            out.append(model.model_validate(item))
        return out

from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from quadre.components import Component

class FlexLayout:
    """
    Mixin class for components that can contain children.
    Designed to work with Pydantic models that define their own children field.
    """

    def add(self, component: 'Component') -> 'FlexLayout':
        """Add a component to the children list."""
        if not hasattr(self, 'children'):
            self.children: List['Component'] = []
        self.children.append(component)
        return self

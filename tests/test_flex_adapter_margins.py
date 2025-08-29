from __future__ import annotations

from nada.flex.runner import build_layout_from_declarative
from nada.flex.engine import FlexContainer, TextWidget
from nada.flex.widgets import Spacer


def _unwrap_first_container(root: FlexContainer) -> FlexContainer:
    assert isinstance(root, FlexContainer)
    assert root.children, "root should have at least one child"
    child = root.children[0].widget
    assert isinstance(child, FlexContainer)
    return child


def test_text_margins_wrap_with_spacers():
    doc = {
        "data": {},
        "layout": [
            {
                "type": "text",
                "text": "Hello",
                "properties": {"margin_top": 10, "margin_bottom": 20},
            }
        ],
    }

    root = build_layout_from_declarative(doc)
    wrapper = _unwrap_first_container(root)

    # Expect: Spacer(mt=10), TextWidget, Spacer(mb=20)
    assert len(wrapper.children) == 3
    w0 = wrapper.children[0].widget
    w1 = wrapper.children[1].widget
    w2 = wrapper.children[2].widget

    assert isinstance(w0, Spacer)
    assert isinstance(w1, TextWidget)
    assert isinstance(w2, Spacer)

    assert getattr(w0, "height", None) == 10
    assert getattr(w2, "height", None) == 20

from __future__ import annotations

from quadre.flex.adapter import build_layout_from_declarative
from quadre.flex.engine import FlexContainer
from quadre.flex.widgets import Spacer


def test_canvas_top_bottom_margins_injected():
    doc = {
        "canvas": {"top_margin": 7, "bottom_margin": 9},
        "layout": [
            {"type": "text", "text": "Hello"},
        ],
    }

    root = build_layout_from_declarative(doc)
    assert isinstance(root, FlexContainer)
    # Expect: Spacer(top) + Text + Spacer(bottom)
    assert len(root.children) == 3
    assert isinstance(root.children[0].widget, Spacer)
    assert isinstance(root.children[-1].widget, Spacer)
    assert getattr(root.children[0].widget, "height", None) == 7
    assert getattr(root.children[-1].widget, "height", None) == 9


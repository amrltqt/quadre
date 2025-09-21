from quadre.config import DIMENSIONS
from quadre.flex.components.root import Root
from quadre.models import DocumentDef

def render_tree(document: DocumentDef) -> Root:

    components = document.components
    canvas = document.canvas or None # Canvas could be None

    # Use canvas width if specified, otherwise fall back to default
    canvas_width = None
    if canvas and canvas.width:
        canvas_width = canvas.width
    else:
        canvas_width = DIMENSIONS.WIDTH

    # Use canvas margins if specified, otherwise use defaults
    margin_top = DIMENSIONS.PADDING
    margin_bottom = DIMENSIONS.PADDING
    margin_left = DIMENSIONS.PADDING
    margin_right = DIMENSIONS.PADDING

    if canvas and canvas.margin:
        if canvas.margin.top is not None:
            margin_top = canvas.margin.top
        if canvas.margin.bottom is not None:
            margin_bottom = canvas.margin.bottom
        if canvas.margin.left is not None:
            margin_left = canvas.margin.left
        if canvas.margin.right is not None:
            margin_right = canvas.margin.right

    root = Root(  # type: ignore[call-arg]
        type="root",
        width=canvas_width, # type: ignore[reportCallIssue]
        margin_top=margin_top, # type: ignore[reportCallIssue]
        margin_bottom=margin_bottom, # type: ignore[reportCallIssue]
        margin_left=margin_left, # type: ignore[reportCallIssue]
        margin_right=margin_right, # type: ignore[reportCallIssue]
    )

    for component in components:
        root.add(component)  # type: ignore[attr-defined]

    return root

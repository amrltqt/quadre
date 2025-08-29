from __future__ import annotations

from io import BytesIO
from PIL import Image


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """
    Encode a Pillow image into bytes (PNG by default).

    Example:
        data = image_to_bytes(img, "PNG")
    """
    buf = BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()


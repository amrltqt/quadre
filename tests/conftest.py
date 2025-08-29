import hashlib
import pytest
from PIL import ImageFont


@pytest.fixture(autouse=True)
def force_default_fonts(monkeypatch):
    """Force deterministic default fonts across tests.

    This avoids cross-platform font differences impacting rendering output.
    """
    from nada.components.config import FONTS

    default = ImageFont.load_default()
    monkeypatch.setattr(FONTS, "H1", default, raising=False)
    monkeypatch.setattr(FONTS, "H2", default, raising=False)
    monkeypatch.setattr(FONTS, "NUMBER", default, raising=False)
    monkeypatch.setattr(FONTS, "BODY", default, raising=False)
    monkeypatch.setattr(FONTS, "TABLE", default, raising=False)
    monkeypatch.setattr(FONTS, "SMALL", default, raising=False)
    monkeypatch.setattr(FONTS, "BOLD_SMALL", default, raising=False)
    yield


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

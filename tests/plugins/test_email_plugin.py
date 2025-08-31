from __future__ import annotations

import os
from typing import Any, Optional

import pytest
from PIL import Image as PILImage

from quadre.plugins.email import email_plugin
from quadre.plugins.registry import OutputContext


class _DummySMTP:
    def __init__(self, host: str, port: int, timeout: Optional[float] = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in: Optional[tuple[str, str]] = None
        self.sent = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self, context=None):  # noqa: D401
        self.started_tls = True

    def login(self, user: str, password: str):
        self.logged_in = (user, password)

    def send_message(self, msg):
        self.sent = msg


class _DummySMTP_SSL(_DummySMTP):
    def __init__(self, host: str, port: int, context=None, timeout: Optional[float] = None):
        super().__init__(host, port, timeout=timeout)
        self.ssl_context = context


def _make_ctx(fmt: str = "PNG", path: Optional[str] = "out.png") -> OutputContext:
    return OutputContext(path=path, format=fmt, doc={}, size=(4, 4))


def _make_img() -> PILImage.Image:
    return PILImage.new("RGB", (2, 2), (240, 240, 240))


def test_email_plugin_sends_with_starttls_by_default(monkeypatch):
    dummy = _DummySMTP("", 0)

    def _smtp(host, port, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP(host, port, timeout)
        return dummy

    import smtplib

    monkeypatch.setattr(smtplib, "SMTP", _smtp)

    img = _make_img()
    ctx = _make_ctx(fmt="PNG")
    cfg = {"host": "smtp.example.com", "to": "a@example.com, b@example.com", "from": "sender@example.com", "subject": "Sub", "body": "Hello"}

    ret = email_plugin(img, ctx, cfg)

    assert ret == "email://a@example.com,b@example.com"
    assert dummy.host == "smtp.example.com"
    assert dummy.port == 587  # default
    assert dummy.started_tls is True  # default to STARTTLS
    assert dummy.logged_in is None  # no creds
    assert dummy.sent is not None
    msg = dummy.sent
    assert msg["Subject"] == "Sub"
    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "a@example.com, b@example.com"
    # attachment subtype should match ctx/format (PNG)
    atts = list(msg.iter_attachments())
    assert atts and atts[0].get_content_type() == "image/png"


def test_email_plugin_uses_smtps_when_use_ssl(monkeypatch):
    dummy = _DummySMTP_SSL("", 0)

    def _smtp_ssl(host, port, context=None, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP_SSL(host, port, context=context, timeout=timeout)
        return dummy

    import smtplib

    monkeypatch.setattr(smtplib, "SMTP_SSL", _smtp_ssl)

    img = _make_img()
    ctx = _make_ctx(fmt="PNG")
    cfg = {
        "host": "smtp.example.com",
        "to": "x@example.com",
        "user": "u",
        "password": "p",
        "use_ssl": True,
        "port": 465,
    }

    ret = email_plugin(img, ctx, cfg)
    assert ret == "email://x@example.com"
    assert dummy.host == "smtp.example.com"
    assert dummy.port == 465
    # SSL path should not call starttls
    assert dummy.started_tls is False
    assert dummy.logged_in == ("u", "p")
    assert dummy.sent is not None


def test_email_plugin_missing_to_raises():
    img = _make_img()
    ctx = _make_ctx()
    with pytest.raises(ValueError):
        email_plugin(img, ctx, {"host": "smtp.example.com"})


def test_email_plugin_env_host_is_used(monkeypatch):
    import smtplib

    dummy = _DummySMTP("", 0)

    def _smtp(host, port, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP(host, port, timeout)
        return dummy

    monkeypatch.setenv("QUADRE_EMAIL_HOST", "smtp.from.env")
    monkeypatch.setattr(smtplib, "SMTP", _smtp)

    img = _make_img()
    ctx = _make_ctx()
    cfg = {"to": "env@example.com"}

    ret = email_plugin(img, ctx, cfg)
    assert ret == "email://env@example.com"
    assert dummy.host == "smtp.from.env"
    assert dummy.started_tls is True


def test_email_plugin_env_format_overrides_ctx(monkeypatch):
    import smtplib

    dummy = _DummySMTP("", 0)

    def _smtp(host, port, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP(host, port, timeout)
        return dummy

    monkeypatch.setenv("QUADRE_EMAIL_HOST", "smtp.example.com")
    monkeypatch.setenv("QUADRE_EMAIL_FORMAT", "WEBP")
    monkeypatch.setattr(smtplib, "SMTP", _smtp)

    img = _make_img()
    ctx = _make_ctx(fmt="PNG")  # will be overridden by env
    cfg = {"to": "f@example.com"}

    email_plugin(img, ctx, cfg)
    msg = dummy.sent
    assert msg is not None
    atts = list(msg.iter_attachments())
    assert atts and atts[0].get_content_type() == "image/webp"


def test_email_plugin_recipient_parsing_semicolons_and_commas(monkeypatch):
    import smtplib

    dummy = _DummySMTP("", 0)

    def _smtp(host, port, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP(host, port, timeout)
        return dummy

    monkeypatch.setenv("QUADRE_EMAIL_HOST", "smtp.example.com")
    monkeypatch.setattr(smtplib, "SMTP", _smtp)

    img = _make_img()
    ctx = _make_ctx()
    cfg = {"to": "a@x;b@x, c@x ;"}

    ret = email_plugin(img, ctx, cfg)
    assert ret == "email://a@x,b@x,c@x"
    assert dummy.sent["To"] == "a@x, b@x, c@x"


def test_email_plugin_inline_cid_inserts_html_and_related_image(monkeypatch):
    import smtplib

    dummy = _DummySMTP("", 0)

    def _smtp(host, port, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP(host, port, timeout)
        return dummy

    monkeypatch.setenv("QUADRE_EMAIL_HOST", "smtp.example.com")
    monkeypatch.setattr(smtplib, "SMTP", _smtp)

    img = _make_img()
    ctx = _make_ctx(path="report.png", fmt="PNG")
    cfg = {"to": "inline@example.com", "inline": True, "subject": "Inline"}

    email_plugin(img, ctx, cfg)
    msg = dummy.sent
    assert msg is not None
    # Has HTML alternative with cid reference
    html_part = msg.get_body("html")
    assert html_part is not None
    html_payload = html_part.get_content()
    assert "cid:" in html_payload
    # Ensure a related image part exists with Content-ID
    related_found = False
    for part in msg.walk():
        if part.get_content_maintype() == "image" and part.get("Content-ID"):
            related_found = True
            assert part.get_content_subtype() == "png"
            break
    assert related_found


def test_email_plugin_inline_custom_html_with_placeholder(monkeypatch):
    import smtplib, re

    dummy = _DummySMTP("", 0)

    def _smtp(host, port, timeout=None):
        nonlocal dummy
        dummy = _DummySMTP(host, port, timeout)
        return dummy

    monkeypatch.setenv("QUADRE_EMAIL_HOST", "smtp.example.com")
    monkeypatch.setattr(smtplib, "SMTP", _smtp)

    img = _make_img()
    ctx = _make_ctx(path="dash.webp", fmt="WEBP")
    cfg = {
        "to": "inline2@example.com",
        "inline": True,
        "html_body": "<p>Inline here:</p><img src=\"cid:{cid}\">",
    }

    email_plugin(img, ctx, cfg)
    msg = dummy.sent
    html = msg.get_body("html").get_content()
    m = re.search(r'cid:([^"]+)', html)
    assert m, "CID not found in HTML"
    cid_val = m.group(1)
    # Ensure there's an image with matching Content-ID (with angle brackets)
    match_found = False
    for part in msg.walk():
        cid_header = part.get("Content-ID")
        if cid_header and cid_val in cid_header:
            match_found = True
            break
    assert match_found

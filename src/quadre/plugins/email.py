from __future__ import annotations

"""
Minimal email output plugin (stdlib-only).

Reads configuration primarily from the plugin cfg dict. Environment variables
are only used for connection/credentials under the convention: QUADRE_EMAIL_<KEY>.

Supported cfg keys:
- to: recipients (comma-separated string or list) [required]
- from: sender address (default: no-reply@example.com)
- subject: email subject (default: Dashboard)
- host: SMTP hostname [required unless via env]
- port: SMTP port (default 587; can be set via env)
- user: SMTP username (optional; can be set via env)
- password: SMTP password (optional; can be set via env)
- use_tls: enable STARTTLS (default true; can be set via env)
- use_ssl: use SMTPS/SMTP_SSL on connect (default false; can be set via env)
- timeout: socket timeout in seconds (optional; can be set via env)
- format: image format to encode (defaults to ctx.format; can be set via env)
- body: plain text body (default "See attached dashboard")

Environment variable names (connection/format only):
  QUADRE_EMAIL_HOST, QUADRE_EMAIL_PORT, QUADRE_EMAIL_USER,
  QUADRE_EMAIL_PASSWORD, QUADRE_EMAIL_TLS, QUADRE_EMAIL_SSL,
  QUADRE_EMAIL_TIMEOUT, QUADRE_EMAIL_FORMAT

Usage (programmatic):
  from quadre.plugins.email import email_plugin
  from quadre import register_output_plugin
  register_output_plugin("email", email_plugin)

Then pass outputs=[{"plugin": "email", ...}]. Use env only for secrets and
connection parameters.
"""

import io
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Mapping, Optional, Sequence

from PIL import Image

from .registry import OutputContext, register_plugin


def _bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _get(cfg: Mapping[str, Any], key: str, env_key: str, default: Any = None) -> Any:
    if key in cfg and cfg[key] not in (None, ""):
        return cfg[key]
    env_val = os.getenv(env_key)
    if env_val is not None and env_val != "":
        return env_val
    return default


def _split_recipients(value: Any) -> Sequence[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value).replace(";", ",").split(",") if x.strip()]


def email_plugin(image: Image.Image, ctx: OutputContext, cfg: Mapping[str, Any]):
    """
    Encode the image and send it as an email attachment via SMTP.

    Required: to (in cfg), host (cfg or env)
    Optional: from, subject, port, user, password, use_tls/use_ssl, timeout, format, body
    """
    # Resolve config with env fallbacks
    host = _get(cfg, "host", "QUADRE_EMAIL_HOST")
    if not host:
        raise ValueError("email plugin requires 'host' (cfg.host or QUADRE_EMAIL_HOST)")

    port = int(_get(cfg, "port", "QUADRE_EMAIL_PORT", 587))
    user = _get(cfg, "user", "QUADRE_EMAIL_USER")
    password = _get(cfg, "password", "QUADRE_EMAIL_PASSWORD")
    use_ssl = _bool(_get(cfg, "use_ssl", "QUADRE_EMAIL_SSL", False), False)
    use_tls = _bool(_get(cfg, "use_tls", "QUADRE_EMAIL_TLS", True), True)
    timeout_raw = _get(cfg, "timeout", "QUADRE_EMAIL_TIMEOUT")
    timeout: Optional[float] = float(timeout_raw) if timeout_raw is not None else None

    # Require recipients via cfg (do not read from env to avoid leaking routing in env)
    to_val = cfg.get("to")
    recipients = _split_recipients(to_val)
    if not recipients:
        raise ValueError("email plugin requires 'to' (outputs cfg)")

    # Prefer routing/metadata from cfg (not env)
    sender = str(cfg.get("from") or "no-reply@example.com")
    subject = str(cfg.get("subject") or "Dashboard")
    body = str(cfg.get("body") or "See attached dashboard")

    # Encode image
    buf = io.BytesIO()
    fmt = str(_get(cfg, "format", "QUADRE_EMAIL_FORMAT", ctx.format)).upper()
    image.save(buf, format=fmt)
    payload = buf.getvalue()

    # Build message
    msg = EmailMessage()
    msg["Subject"] = str(subject)
    msg["From"] = str(sender)
    msg["To"] = ", ".join(recipients)
    filename = (ctx.path or f"dashboard.{fmt.lower()}").split("/")[-1]
    msg.set_content(str(body))
    msg.add_attachment(
        payload,
        maintype="image",
        subtype=fmt.lower(),
        filename=filename,
    )

    # Send via SMTP
    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=timeout) as s:
            if user and password:
                s.login(str(user), str(password))
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=timeout) as s:
            if use_tls:
                s.starttls(context=context)
            if user and password:
                s.login(str(user), str(password))
            s.send_message(msg)

    return f"email://{','.join(recipients)}"


# Register on import so it's available as a built-in optional plugin name "email"
register_plugin("email", email_plugin)

__all__ = ["email_plugin"]

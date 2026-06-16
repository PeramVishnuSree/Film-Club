"""Transactional email delivery.

Sending is intentionally simple and dependency-free: it uses the standard
library's ``smtplib`` run in a worker thread so it doesn't block the event loop.
When no SMTP host is configured (the default in development) emails are logged to
the console instead of being sent, so the flows are fully exercisable locally.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("filmclub.email")


def _build_message(to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def _send_smtp(msg: EmailMessage) -> None:
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_email(to: str, subject: str, body: str) -> None:
    """Send (or, in dev, log) a plain-text email. Never raises to the caller —
    delivery failures are logged so a flaky mail server can't 500 a request."""
    msg = _build_message(to, subject, body)

    if not settings.email_enabled:
        logger.info(
            "[email:console] To: %s | Subject: %s\n%s", to, subject, body
        )
        return

    try:
        await asyncio.to_thread(_send_smtp, msg)
    except Exception:  # noqa: BLE001 - we never want email to break the request
        logger.exception("Failed to send email to %s", to)


# --------------------------------------------------------------- templates


async def send_password_reset_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    body = (
        "Someone (hopefully you) asked to reset your Film Club password.\n\n"
        f"Use this link to choose a new one:\n{link}\n\n"
        "If you didn't request this, you can safely ignore this email — your "
        "password won't change."
    )
    await send_email(to, "Reset your Film Club password", body)


async def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    body = (
        "Welcome to Film Club! Please confirm your email address to finish "
        "setting up your account:\n\n"
        f"{link}\n\n"
        "If you didn't sign up, you can ignore this email."
    )
    await send_email(to, "Confirm your Film Club email", body)

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import settings

# bcrypt operates on at most 72 bytes.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pw, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # "ver" pins the token to the user's current token_version; bumping that
    # column server-side invalidates every token issued before the bump.
    payload = {"sub": str(subject), "ver": token_version, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


# --------------------------------------------------------------- email tokens
#
# Password-reset and email-verification links carry short-lived signed tokens.
# They are stateless (no DB table): the user id is the subject and a "purpose"
# claim prevents using one flow's token for another.
#
# Reset tokens are additionally bound to the user's current password hash, so a
# token stops working the moment the password changes — making it single-use.

PURPOSE_PASSWORD_RESET = "pwreset"
PURPOSE_EMAIL_VERIFY = "verify"


def _email_token_key(purpose: str, salt: str = "") -> str:
    return f"{settings.secret_key}:{purpose}:{salt}"


def _encode_email_token(
    subject: int, purpose: str, expire_minutes: int, salt: str = ""
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": str(subject), "purpose": purpose, "exp": expire}
    return jwt.encode(
        payload, _email_token_key(purpose, salt), algorithm=settings.jwt_algorithm
    )


def read_token_subject(token: str) -> int | None:
    """Extract the user id from a token *without* verifying its signature.

    Used only to locate the user so the right (user-bound) verification key can
    be assembled; the signature is always checked afterwards.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def create_password_reset_token(user_id: int, hashed_password: str) -> str:
    return _encode_email_token(
        user_id,
        PURPOSE_PASSWORD_RESET,
        settings.password_reset_expire_minutes,
        salt=hashed_password,
    )


def verify_password_reset_token(token: str, hashed_password: str) -> bool:
    try:
        payload = jwt.decode(
            token,
            _email_token_key(PURPOSE_PASSWORD_RESET, hashed_password),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        return False
    return payload.get("purpose") == PURPOSE_PASSWORD_RESET


def create_email_verify_token(user_id: int) -> str:
    return _encode_email_token(
        user_id, PURPOSE_EMAIL_VERIFY, settings.email_verify_expire_minutes
    )


def verify_email_verify_token(token: str) -> bool:
    try:
        payload = jwt.decode(
            token,
            _email_token_key(PURPOSE_EMAIL_VERIFY),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        return False
    return payload.get("purpose") == PURPOSE_EMAIL_VERIFY

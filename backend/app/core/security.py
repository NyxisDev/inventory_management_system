"""Password hashing, password policy, access tokens (JWT) and refresh tokens."""

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

BCRYPT_ROUNDS = 12
PASSWORD_MIN_LENGTH = 10
# bcrypt only uses the first 72 bytes; longer passwords are rejected instead of silently truncated.
PASSWORD_MAX_BYTES = 72

JWT_ALGORITHM = "HS256"

_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_DIGIT_RE = re.compile(r"\d")


# ---------- passwords ----------


def validate_password_strength(password: str) -> str:
    """Return the password if it meets the policy, otherwise raise ValueError (English message)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_BYTES} bytes long")
    if not _LETTER_RE.search(password) or not _DIGIT_RE.search(password):
        raise ValueError("Password must contain at least one letter and one digit")
    return password


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        # Malformed hash or password longer than 72 bytes
        return False


# Verified against when the username does not exist, so the response time is the same.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


# ---------- access tokens ----------


@dataclass(frozen=True, slots=True)
class AccessTokenData:
    employee_id: int
    role: str
    issued_at: int  # unix seconds


class InvalidTokenError(Exception):
    """The access token is missing, malformed, forged or expired."""


def create_access_token(employee_id: int, role: str) -> tuple[str, int]:
    """Return (token, lifetime in seconds). Only the id and the role go into the token."""
    now = datetime.now(UTC)
    lifetime = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(employee_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> AccessTokenData:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[JWT_ALGORITHM],  # fixed list: "none" and other algorithms are rejected
            options={"require": ["sub", "role", "iat", "exp"]},
        )
        return AccessTokenData(
            employee_id=int(payload["sub"]),
            role=str(payload["role"]),
            issued_at=int(payload["iat"]),
        )
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise InvalidTokenError from exc


# ---------- refresh tokens ----------


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 hex digest. Only this value is stored in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

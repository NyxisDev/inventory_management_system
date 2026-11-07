"""Password hashing and password policy.

JWT helpers are added in Part 2.
"""

import re

import bcrypt

BCRYPT_ROUNDS = 12
PASSWORD_MIN_LENGTH = 10
# bcrypt only uses the first 72 bytes; longer passwords are rejected instead of silently truncated.
PASSWORD_MAX_BYTES = 72

_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_DIGIT_RE = re.compile(r"\d")


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
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode(
        "ascii"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        # Malformed hash or password longer than 72 bytes
        return False


# Verified against when the username does not exist, so the response time is the same.
DUMMY_PASSWORD_HASH = hash_password("timing-equalizer-0")

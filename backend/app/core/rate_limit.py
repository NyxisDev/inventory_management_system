"""Rate limits per client IP (slowapi).

Counters live in process memory, so each uvicorn worker counts separately. The account lockout
(failed_login_attempts / locked_until in the database) is the main protection against guessing.
"""

from fastapi import Request
from slowapi import Limiter

from app.core.net import get_client_ip

LOGIN_LIMIT = "5/minute;20/hour"
REFRESH_LIMIT = "30/minute"
PUBLIC_LIMIT = "120/minute"


def _client_key(request: Request) -> str:
    return get_client_ip(request) or "unknown"


limiter = Limiter(key_func=_client_key)

"""Client address and user agent of a request."""

from fastapi import Request

from app.core.config import settings

USER_AGENT_MAX_LENGTH = 500


def get_client_ip(request: Request) -> str | None:
    """Client IP address.

    Behind our nginx (TRUST_PROXY=true) the right-most X-Forwarded-For entry is the address nginx
    saw, so it cannot be spoofed by the client (anything the client sends is further to the left).
    """
    if settings.TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for", "")
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if parts:
            return parts[-1]
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> str | None:
    user_agent = request.headers.get("user-agent")
    return user_agent[:USER_AGENT_MAX_LENGTH] if user_agent else None

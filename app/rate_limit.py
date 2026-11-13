"""
Shared rate limiter instance (slowapi, backed by the `limits` library).

Kept in its own module so both app/main.py (which registers the
exception handler + middleware) and app/routes/analyze.py (which
applies the actual limit) can import the same Limiter instance
without a circular import between them.

Limits by client IP address, since /analyze has no authentication
requirement (it's meant to be usable before signup). This is an
in-memory limiter - counts reset on every backend restart/redeploy.
That's an acceptable tradeoff here: the goal is blunting abuse and
runaway Gemini API costs from a single source hammering the endpoint,
not perfect long-term quota tracking.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def client_ip(request: Request) -> str:
    """
    Real client IP behind a reverse proxy. Behind Render/Cloud Run,
    request.client.host is the PROXY's address, so the old
    get_remote_address key put every user in one shared bucket (one
    heavy user could rate-limit everybody). We read X-Forwarded-For,
    counting from the right by TRUSTED_PROXY_HOPS, because the left-most
    entries can be forged by the client.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    hops = settings.TRUSTED_PROXY_HOPS
    if parts and hops > 0 and len(parts) >= hops:
        return parts[-hops]
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip)

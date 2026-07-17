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

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

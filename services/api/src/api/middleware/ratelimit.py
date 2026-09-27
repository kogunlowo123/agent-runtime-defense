"""Rate limiting configuration via slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Default limiter: 100 requests/minute per IP
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Strict limiter for T2 isolation actions: 10 requests/minute per IP
isolation_limiter = Limiter(
    key_func=get_remote_address, default_limits=["10/minute"]
)

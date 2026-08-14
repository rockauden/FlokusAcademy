"""Shared rate limiter instance.

Lives in its own module rather than in main.py because the routers need to
import it for their @limiter.limit decorators, and main.py imports the
routers — defining it in main.py would be a circular import.

Note on deployment: get_remote_address reads the socket peer address. Behind
Railway's proxy that is the proxy, not the client, so every user would share a
single bucket. Run uvicorn with --proxy-headers --forwarded-allow-ips='*' so
X-Forwarded-For is honoured.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

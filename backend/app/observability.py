"""Request IDs and structured logging.

The problem this solves: every failure this project has hit was silent. A
request was blocked, or rejected, or returned nothing, and the only signal was
a person eventually noticing the app "felt broken". Logs existed but could not
be tied to a particular request, and a 500 gave the caller nothing to quote.

So: every request gets an id, that id appears on every log line the request
produces and in the response headers, and unhandled errors are logged with it
rather than escaping as a bare stack trace.

Logs are JSON when LOG_FORMAT=json (set it in production, where the platform
indexes structured logs) and plain text otherwise, because JSON in a local
terminal is miserable to read.
"""
import json
import logging
import sys
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

REQUEST_ID_HEADER = "X-Request-ID"

# A ContextVar rather than a thread local: this application is async, so many
# requests share a thread and only the context is per-task.
_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach an id to every request and echo it back on the response.

    An inbound X-Request-ID is honoured so a caller (or a proxy) can correlate
    across services, but it is length-capped and stripped of anything exotic --
    it lands in log output, and an unbounded client-controlled string in the
    logs is how log injection happens.
    """

    def __init__(self, app: ASGIApp, max_length: int = 64) -> None:
        super().__init__(app)
        self.max_length = max_length

    def _clean(self, value: str | None) -> str:
        if not value:
            return uuid.uuid4().hex
        cleaned = "".join(c for c in value if c.isalnum() or c in "-_")[: self.max_length]
        return cleaned or uuid.uuid4().hex

    async def dispatch(self, request, call_next):
        request_id = self._clean(request.headers.get(REQUEST_ID_HEADER))
        token = _request_id.set(request_id)
        # Also on request.state so a handler can include it in a response body.
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            _request_id.reset(token)


class _RequestIdFilter(logging.Filter):
    """Make the current request id available to every formatter."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", log_format: str = "text") -> None:
    """Install one handler on the root logger, replacing whatever was there.

    uvicorn installs its own handlers; leaving them would double every line.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())

    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # uvicorn's access log duplicates information the middleware already
    # records, and its own handlers would bypass the filter above.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True

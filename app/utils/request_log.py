import time
from typing import List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

MAX_LOG_BODY_SIZE = 1000  # characters
SENSITIVE_PATHS: List[str] = []


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method
        query = request.url.query
        headers = dict(request.headers)

        # Handle body
        try:
            body_bytes = await request.body()
            body = body_bytes.decode("utf-8")
            if len(body) > MAX_LOG_BODY_SIZE:
                body = body[:MAX_LOG_BODY_SIZE] + "… [truncated]"
        except UnicodeDecodeError:
            body = "<binary data>"

        # Mask body if path is sensitive
        if any(path.startswith(sensitive) for sensitive in SENSITIVE_PATHS):
            body = "<hidden>"

        logger.info(
            f"➡️ {method} {path}"
            f"{f'?{query}' if query else ''} | Headers: {headers} | Body: {body}"
        )

        response = await call_next(request)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"⬅️ {response.status_code} {method} {path} in {elapsed_ms:.2f}ms")

        return response

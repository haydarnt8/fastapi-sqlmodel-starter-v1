"""
Request/Response Logging Middleware

Logs all HTTP requests and responses for debugging and auditing.

Features:
- Logs request method, path, query params
- Logs response status code and processing time
- Skips health check endpoints to reduce noise
- Includes client IP and user agent
- Adds X-Process-Time header to responses

Why logging requests?
- Debug production issues
- Monitor API usage patterns
- Track performance issues
- Audit trail for compliance
- Detect anomalous behavior
"""

import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    Logs:
    - Request method, path, query params
    - Request headers (excluding sensitive ones)
    - Response status code
    - Response time in seconds
    - User agent and IP address

    Usage:
        from app.middleware.request_logging import RequestLoggingMiddleware

        app.add_middleware(RequestLoggingMiddleware)
    """

    # Paths to skip logging (to reduce noise)
    SKIP_PATHS = {"/health", "/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""

        # Skip logging for specified paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        request_id = request.headers.get("X-Request-ID", "unknown")

        # Log request
        logger.info(
            f"Request: {method} {path}",
            extra={
                "event": "request_start",
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "request_id": request_id,
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {method} {path} - {str(e)}",
                extra={
                    "event": "request_error",
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time": f"{process_time:.3f}s",
                    "client_ip": client_ip,
                    "request_id": request_id,
                },
                exc_info=True,
            )
            raise

        # Calculate response time
        process_time = time.time() - start_time

        # Log response
        log_level = "info"
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"

        log_message = (
            f"Response: {method} {path} - {response.status_code} ({process_time:.3f}s)"
        )

        getattr(logger, log_level)(
            log_message,
            extra={
                "event": "request_complete",
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
                "client_ip": client_ip,
                "request_id": request_id,
            },
        )

        # Add response time header
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

"""
Request ID Middleware

Adds unique request IDs to all incoming requests for:
- Distributed tracing
- Log correlation
- Debugging across microservices
- Request tracking in production

How it works:
1. Checks if client sent X-Request-ID header
2. If yes, uses that ID (allows client-side tracing)
3. If no, generates a new UUID
4. Adds request_id to all logs
5. Returns X-Request-ID header in response

Why request tracing?
- Track a single request across multiple services
- Correlate logs from different parts of the system
- Debug production issues faster
- Essential for distributed systems
"""

import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to all requests.

    Usage:
        from app.middleware.request_id import RequestIDMiddleware
        app.add_middleware(RequestIDMiddleware)

    The request ID is:
    - Available via request.state.request_id
    - Included in all logs automatically
    - Returned in X-Request-ID response header
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request to add request ID and timing.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response with X-Request-ID header added
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id

        # Track request timing
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error with request ID
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )
            raise

        # Calculate request duration
        duration = time.time() - start_time

        # Log completed request
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Add timing header for debugging
        response.headers["X-Process-Time"] = f"{duration:.4f}s"

        return response


def get_request_id(request: Request) -> str:
    """
    Helper function to get request ID from request state.

    Args:
        request: The FastAPI request object

    Returns:
        str: The request ID (UUID string)

    Usage:
        from app.middleware.request_id import get_request_id

        @router.get("/example")
        async def example(request: Request):
            request_id = get_request_id(request)
            logger.info(f"Processing request {request_id}")
    """
    return getattr(request.state, "request_id", "unknown")

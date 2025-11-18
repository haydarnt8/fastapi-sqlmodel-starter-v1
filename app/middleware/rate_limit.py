"""
Rate Limiting Middleware

Protects against:
- Brute force attacks on authentication endpoints
- API abuse
- DDoS attempts

Uses SlowAPI with configurable limits per endpoint.

Limits are defined per IP address and time window:
- Login: 5 attempts per minute
- Register: 3 attempts per minute
- Other auth endpoints: 10 per minute
- General API: 100 per minute

Why rate limiting?
- Prevents password guessing attacks
- Protects server resources
- Improves service stability
- Required for production APIs
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Determine storage backend based on Redis availability
# Redis is recommended for production (especially multi-server deployments)
# Memory storage is fine for single-server development
if settings.REDIS_ENABLED:
    storage_uri = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    if settings.REDIS_PASSWORD:
        # Format: redis://:password@host:port/db
        storage_uri = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    logger.info(f"Rate limiting using Redis storage: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
else:
    storage_uri = "memory://"
    logger.warning("Rate limiting using in-memory storage (not suitable for production clusters)")

# Initialize limiter with IP-based rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default for all endpoints
    storage_uri=storage_uri,
    headers_enabled=True,  # Send rate limit info in response headers
)


def get_limiter() -> Limiter:
    """
    Get the limiter instance.

    Returns:
        Limiter: The SlowAPI limiter instance

    Usage:
        from app.middleware.rate_limit import get_limiter
        limiter = get_limiter()

        @router.post("/login")
        @limiter.limit("5/minute")
        async def login(...):
            ...
    """
    return limiter


async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom error handler for rate limit exceeded.

    Args:
        request: The FastAPI request
        exc: The RateLimitExceeded exception

    Returns:
        JSONResponse with 429 status code and helpful message
    """
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)}",
        extra={
            "ip": get_remote_address(request),
            "path": request.url.path,
            "method": request.method,
        }
    )

    return _rate_limit_exceeded_handler(request, exc)


# Rate limit configurations for different endpoint types
class RateLimits:
    """
    Predefined rate limit configurations.

    Usage:
        from app.middleware.rate_limit import RateLimits, get_limiter
        limiter = get_limiter()

        @router.post("/login")
        @limiter.limit(RateLimits.AUTH_LOGIN)
        async def login(...):
            ...
    """

    # Authentication endpoints (strict)
    AUTH_LOGIN = "5/minute"          # Login attempts
    AUTH_REGISTER = "3/minute"       # Registration attempts
    AUTH_REFRESH = "10/minute"       # Token refresh
    AUTH_FORGOT_PASSWORD = "3/minute"  # Password reset requests

    # CRUD endpoints (moderate)
    CREATE = "20/minute"             # Create operations
    UPDATE = "30/minute"             # Update operations
    DELETE = "10/minute"             # Delete operations
    READ = "100/minute"              # Read operations

    # General endpoints (lenient)
    GENERAL = "100/minute"           # General API endpoints
    HEALTH_CHECK = "1000/minute"     # Health check endpoints

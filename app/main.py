"""
FastAPI Starter - Main Application

Production-grade FastAPI application with:
- Dynamic RBAC (Role-Based Access Control)
- JWT Authentication
- Async database operations
- Comprehensive logging
- CORS configuration
- Auto-generated API documentation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import AppException
from app.core.cache import get_redis_cache, close_redis_cache
from app.db.session import init_db, close_db, get_session
from app.db.init_db import init_db_data
from app.api.v1 import api_router
from app.schemas.common import HealthResponse
from app.i18n import load_translations
from app.middleware.rate_limit import get_limiter, rate_limit_error_handler
from app.middleware.request_id import RequestIDMiddleware
from datetime import datetime, timezone

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.

    Startup:
    - Initialize database
    - Create tables
    - Seed roles/permissions
    - Create superuser

    Shutdown:
    - Close database connections
    - Cleanup resources
    """
    # Startup
    logger.info("=" * 70)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("=" * 70)

    try:
        # Production environment validation
        if settings.ENVIRONMENT == "production":
            validation_errors = []

            # Check SECRET_KEY
            if "CHANGE-ME" in settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
                validation_errors.append(
                    "SECRET_KEY must be changed from default and be at least 32 characters"
                )

            # Check default admin password
            if settings.FIRST_SUPERUSER_PASSWORD in ["changeme123", "admin", "password"]:
                validation_errors.append(
                    "FIRST_SUPERUSER_PASSWORD must be changed from default"
                )

            # Check database is not SQLite
            if "sqlite" in settings.DATABASE_URL.lower():
                validation_errors.append(
                    "SQLite is not supported in production. Use PostgreSQL or MySQL."
                )

            # Check Redis is enabled
            if not settings.REDIS_ENABLED:
                logger.warning(
                    "⚠️  Redis is disabled in production. Token revocation will not work!"
                )

            # Check DEBUG is disabled
            if settings.DEBUG:
                validation_errors.append("DEBUG must be False in production")

            # Check CORS origins are specific
            if "*" in str(settings.BACKEND_CORS_ORIGINS):
                validation_errors.append(
                    "CORS origins must be specific in production (not wildcard '*')"
                )

            if validation_errors:
                logger.error("=" * 70)
                logger.error("❌ PRODUCTION ENVIRONMENT VALIDATION FAILED:")
                for error in validation_errors:
                    logger.error(f"  ❌ {error}")
                logger.error("=" * 70)
                raise RuntimeError(
                    "Production validation failed. Fix configuration before deploying. "
                    f"Errors: {'; '.join(validation_errors)}"
                )

            logger.info("✓ Production environment validation passed")

        # Load translations
        load_translations()
        logger.info("✓ Translations loaded (en, ar)")

        # Initialize Redis cache
        await get_redis_cache()

        # Initialize database
        await init_db()
        logger.info("✓ Database initialized")

        # Seed initial data
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await init_db_data(session)

        logger.info("✓ Database seeded with initial data")
        logger.info("=" * 70)
        logger.info(f"🚀 {settings.APP_NAME} is ready!")
        logger.info(f"📚 API docs: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"🔐 Admin: {settings.FIRST_SUPERUSER_EMAIL}")
        logger.info(f"🌍 Languages: en, ar")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_redis_cache()
    await close_db()
    logger.info("✓ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register rate limiter
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)

# Add Security Headers Middleware (should be early in chain)
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# Add Request Logging Middleware (after security headers)
from app.middleware.request_logging import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)

# Add Request ID Middleware (should be first for proper tracing)
app.add_middleware(RequestIDMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Accept-Language",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


# Global exception handler for custom exceptions
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    """
    Handle custom application exceptions.

    Converts AppException to proper HTTP response.
    Ensures UUIDs and other non-JSON types are converted to strings.
    """
    from uuid import UUID

    # Convert details to JSON-serializable format
    serializable_details = {}
    for key, value in exc.details.items():
        if isinstance(value, UUID):
            serializable_details[key] = str(value)
        else:
            serializable_details[key] = value

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": serializable_details,
        },
    )


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check if API is running and database is connected",
)
async def health_check(
    session: AsyncSession = Depends(get_session)
) -> HealthResponse:
    """
    Health check endpoint.

    Returns application health status with actual connectivity checks.

    Used by:
    - Load balancers
    - Monitoring systems
    - Docker health checks
    - Kubernetes liveness/readiness probes

    Checks:
    - Database connectivity (actual query)
    - Redis connectivity (if enabled)
    """
    from sqlalchemy import text

    # Check database connectivity
    db_status = "disconnected"
    try:
        await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check: Database failed - {e}")
        db_status = "disconnected"

    # Check Redis connectivity
    redis_status = "disabled"
    if settings.REDIS_ENABLED:
        try:
            cache = await get_redis_cache()
            if cache.redis_client:
                await cache.redis_client.ping()
                redis_status = "connected"
            else:
                redis_status = "disconnected"
        except Exception as e:
            logger.error(f"Health check: Redis failed - {e}")
            redis_status = "disconnected"

    # Determine overall status
    overall_status = "healthy" if db_status == "connected" else "unhealthy"
    if settings.REDIS_ENABLED and redis_status == "disconnected":
        overall_status = "degraded"  # App works but Redis is down

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    )


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    description="Get API information",
)
async def root():
    """API root endpoint with basic information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health",
        "api_v1": settings.API_V1_PREFIX,
    }


# Include API routers
app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)

logger.info(f"FastAPI application configured successfully")


if __name__ == "__main__":
    """Run application directly with uvicorn (development only)."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )

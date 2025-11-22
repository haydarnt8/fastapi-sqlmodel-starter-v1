"""
API v1 Router

Combines all v1 endpoints into a single router.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1 import auth, users, roles, audit, restaurants, suppliers, products, orders, deliveries
from app.db.session import get_session
from app.core.config import settings
from app.schemas.common import HealthResponse
from app.core.cache import get_redis_cache
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create API v1 router
api_router = APIRouter()

# Health check endpoint for Render
@api_router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="API health check",
    description="Check if API v1 is running and database is connected",
)
async def health_check_v1(
    session: AsyncSession = Depends(get_session)
) -> HealthResponse:
    """
    Health check endpoint for API v1.

    Used by Render and other monitoring systems.
    """
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
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    )

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(audit.router)

# Supply Chain routers
api_router.include_router(restaurants.router)
api_router.include_router(suppliers.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(deliveries.router)

# Add your custom domain-specific routers here:
# from app.api.v1 import products
# api_router.include_router(products.router)

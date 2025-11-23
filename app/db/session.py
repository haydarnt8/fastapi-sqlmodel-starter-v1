"""
Async Database Session Management

This module configures async database operations for better performance.

Why Async Database?
- Non-blocking I/O: Server can handle other requests while waiting for database
- Better performance: Can handle 10x more concurrent requests
- Scalability: Required for high-traffic applications
- Modern best practice: All new FastAPI apps should use async

Async vs Sync:
- Sync: wait for database → blocked → can't handle other requests
- Async: wait for database → handle other requests → come back when ready

Performance Example:
- 100 concurrent requests with sync DB: ~10 seconds
- 100 concurrent requests with async DB: ~1 second
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# Create async engine
# echo=True would log all SQL queries (useful for debugging)
# poolclass=NullPool is recommended for serverless (AWS Lambda, etc.)
# For traditional servers, remove poolclass for connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    # Connection pool settings (comment out for serverless)
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    # poolclass=NullPool,  # Uncomment for serverless/testing
)

# Create async session factory
# expire_on_commit=False: Don't expire objects after commit
# This allows accessing attributes after commit without refetching
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session.

    This is used in FastAPI endpoints with Depends().

    Usage:
        @app.get("/students")
        async def get_students(
            session: AsyncSession = Depends(get_session)
        ):
            result = await session.execute(select(Student))
            students = result.scalars().all()
            return students

    Why Generator?
    - Ensures session is properly closed even if exception occurs
    - FastAPI handles the lifecycle automatically
    - Clean, pythonic resource management

    Yields:
        AsyncSession: Database session

    Example:
        async with get_session() as session:
            # Use session
            result = await session.execute(select(Student))
        # Session automatically closed here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            # Rollback on any error
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            # Always close session
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.

    This should be called on application startup.

    Why async?
    - Non-blocking table creation
    - Fast application startup
    - Can create tables while handling requests

    Usage in main.py:
        @app.on_event("startup")
        async def on_startup():
            await init_db()

    Note: In production, use Alembic migrations instead!
    This is useful for:
    - Development
    - Testing
    - Quick prototypes
    """
    try:
        logger.info("Initializing database...")

        # Import all models to ensure they're registered with SQLModel
        # This must happen before create_all()
        # IMPORTANT: Import ALL table models including junction tables
        from app.models import (
            User,
            Role,
            Permission,
            UserRole,
            RolePermission,
        )
        # Import AuditLog after User to resolve foreign key
        from app.models.audit_log import AuditLog  # noqa: F401
        # Add your custom domain models here:
        # from app.models.product import Product
        # from app.models.order import Order

        # Create all tables
        # Wrap transaction in try-except to handle duplicate table/index errors
        # This can happen with concurrent Gunicorn workers or Railway redeployments
        try:
            async with engine.begin() as conn:
                # Drop all tables (ONLY for development!)
                # Comment this out in production!
                # await conn.run_sync(SQLModel.metadata.drop_all)

                # Create all tables if they don't exist
                await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
        except Exception as create_error:
            # Ignore duplicate table/index errors (happens with concurrent workers or redeployments)
            error_msg = str(create_error).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                logger.warning(f"Some database objects already exist (this is normal on redeployment): {create_error}")
            else:
                # Re-raise if it's not a duplicate error
                raise

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


async def close_db() -> None:
    """
    Close database connection.

    Called on application shutdown.

    Usage in main.py:
        @app.on_event("shutdown")
        async def on_shutdown():
            await close_db()
    """
    try:
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}", exc_info=True)


# Utility function for manual session management
async def get_db_session() -> AsyncSession:
    """
    Get a database session for manual use (outside FastAPI dependencies).

    Use this when you need a session outside of endpoint handlers.

    Usage:
        session = await get_db_session()
        try:
            result = await session.execute(select(Student))
            students = result.scalars().all()
        finally:
            await session.close()

    Better Usage (with context manager):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Student))
            students = result.scalars().all()
        # Session automatically closed

    Returns:
        AsyncSession: Database session
    """
    return AsyncSessionLocal()

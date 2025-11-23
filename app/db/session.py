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
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import ProgrammingError, OperationalError
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
    from app.models.product import Product  # noqa: F401
    from app.models.order import Order, OrderItem  # noqa: F401
    from app.models.restaurant import Restaurant  # noqa: F401
    from app.models.supplier import Supplier  # noqa: F401
    from app.models.delivery import Delivery  # noqa: F401

    # Check if ALL required tables exist to avoid race conditions with multiple workers
    # Use SQLAlchemy's inspector which works across all database backends
    from sqlalchemy import inspect

    async with engine.begin() as conn:
        # Use inspector to check if ALL core tables exist
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

        # Check for core tables - if ANY are missing, recreate all
        required_tables = {"user", "role", "permission", "user_role", "role_permission"}
        existing_tables = set(tables)
        missing_tables = required_tables - existing_tables

        if missing_tables:
            logger.warning(f"Missing tables detected: {missing_tables}. Recreating schema...")

            # NUCLEAR OPTION: Drop and recreate entire public schema
            # This ensures NO orphaned objects remain (tables, indexes, constraints, etc.)
            try:
                # Get database type from URL
                database_url = str(settings.DATABASE_URL)
                if "postgresql" in database_url:
                    logger.info("Dropping and recreating public schema (nuclear option)...")
                    await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
                    await conn.execute(text("CREATE SCHEMA public"))
                    await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
                    logger.info("Public schema recreated successfully")
            except Exception as schema_error:
                logger.error(f"Error recreating schema: {schema_error}")
                raise
            # Create all tables immediately in SAME transaction
            # NO checkfirst since we just dropped everything!
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database initialized successfully")
            return
        elif required_tables.issubset(existing_tables):
            logger.info("All required database tables exist, skipping creation")
            return

    # If we get here, no tables exist at all - create them with duplicate protection
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
            logger.info("Database initialized successfully")
    except (ProgrammingError, OperationalError) as create_error:
        # Catch duplicate object errors from both PostgreSQL and SQLite
        # PostgreSQL: ProgrammingError with DuplicateTableError
        # SQLite: OperationalError for duplicate tables/indexes
        error_msg = str(create_error).lower()
        if "already exists" in error_msg or "duplicate" in error_msg:
            logger.warning(
                "Database objects already exist (normal on redeployment with multiple workers). "
                "Skipping table creation."
            )
            # Continue without raising - this is expected with concurrent workers
        else:
            # Re-raise if it's a different error
            logger.error(f"Database error during initialization: {create_error}", exc_info=True)
            raise
    except Exception as create_error:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during database initialization: {create_error}", exc_info=True)
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

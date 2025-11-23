#!/usr/bin/env python3
"""
Wait for database to be ready before running migrations.

This script checks if the database is accessible and ready to accept
connections before proceeding with Alembic migrations. This prevents
migration failures when the database is still starting up.
"""

import asyncio
import sys
import time
from typing import Optional

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


async def wait_for_postgres(
    max_retries: int = 30,
    retry_interval: int = 2
) -> bool:
    """
    Wait for PostgreSQL database to be ready.

    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries

    Returns:
        True if database is ready, False otherwise
    """

    database_url = str(settings.DATABASE_URL)

    print(f"Waiting for database to be ready...")
    print(f"Database URL: {database_url.split('@')[0]}@***")
    print(f"Max retries: {max_retries}, Interval: {retry_interval}s")
    print()

    for attempt in range(1, max_retries + 1):
        try:
            # Try to connect to the database
            if database_url.startswith("postgresql+asyncpg://"):
                # Use asyncpg directly for faster connection check
                pg_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
                conn = await asyncpg.connect(pg_url, timeout=5)
                await conn.close()
            else:
                # Use SQLAlchemy engine for other databases
                engine = create_async_engine(database_url, echo=False)
                async with engine.begin() as conn:
                    await conn.execute("SELECT 1")
                await engine.dispose()

            print(f"✅ Database is ready! (attempt {attempt}/{max_retries})")
            return True

        except (OSError, asyncpg.PostgresError, Exception) as e:
            error_type = type(e).__name__
            error_msg = str(e)

            # Truncate long error messages
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."

            print(f"❌ Attempt {attempt}/{max_retries} failed: {error_type}: {error_msg}")

            if attempt < max_retries:
                print(f"   Retrying in {retry_interval} seconds...")
                await asyncio.sleep(retry_interval)
            else:
                print(f"\n❌ Failed to connect to database after {max_retries} attempts")
                print(f"\nTroubleshooting:")
                print(f"1. Check DATABASE_URL environment variable is set correctly")
                print(f"2. Verify PostgreSQL service is running")
                print(f"3. Check database credentials are correct")
                print(f"4. Ensure database host is reachable")
                return False

    return False


async def verify_database_config() -> Optional[str]:
    """
    Verify database configuration before attempting connection.

    Returns:
        Error message if configuration is invalid, None otherwise
    """

    database_url = str(settings.DATABASE_URL)

    # Check if DATABASE_URL is set
    if not database_url or database_url == "":
        return "DATABASE_URL environment variable is not set"

    # Check if using default SQLite in production
    if settings.ENVIRONMENT == "production" and "sqlite" in database_url.lower():
        return "Cannot use SQLite database in production! Please configure PostgreSQL."

    # Check if database URL format is correct
    valid_schemes = ["postgresql", "postgresql+asyncpg", "sqlite", "sqlite+aiosqlite"]
    scheme = database_url.split("://")[0] if "://" in database_url else ""

    if scheme not in valid_schemes:
        return f"Invalid database URL scheme: {scheme}. Expected one of: {valid_schemes}"

    return None


async def main():
    """Main entry point."""

    print("=" * 70)
    print("DATABASE CONNECTION CHECK")
    print("=" * 70)
    print()

    # Verify configuration first
    config_error = await verify_database_config()
    if config_error:
        print(f"❌ Configuration Error: {config_error}")
        print()
        print("Please set the DATABASE_URL environment variable correctly.")
        print()
        print("Example for Railway:")
        print('  DATABASE_URL=${{Postgres.DATABASE_URL}}')
        print()
        sys.exit(1)

    print(f"✅ Database configuration is valid")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Database: {settings.DATABASE_URL.scheme}")
    print()

    # Wait for database to be ready
    success = await wait_for_postgres()

    print()
    print("=" * 70)

    if success:
        print("✅ Database is ready for migrations!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ Database connection failed!")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)

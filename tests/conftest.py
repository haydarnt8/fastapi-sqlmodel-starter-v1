"""
Test Configuration and Fixtures

This file contains pytest fixtures that are shared across all tests.

Fixtures provide:
- Test database setup/teardown
- Test client for making HTTP requests
- Authentication helpers (create users, login tokens)
- Test data factories
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.db.session import get_session
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.models import User, Role, Permission, UserRole, RolePermission
from app.crud.user import user_crud
from app.crud.role import role_crud, permission_crud


# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the entire test session.

    This ensures all async tests run in the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """
    Create a test database engine.

    Uses in-memory SQLite for fast testing.
    StaticPool ensures the same connection is reused (important for :memory:).
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True to see SQL queries
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session for each test.

    Each test gets a fresh session that is rolled back after the test.
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client(test_session: AsyncSession) -> TestClient:
    """
    Create a test client with overridden database session.

    This client makes HTTP requests to the FastAPI app.
    All database operations use the test session.
    """
    def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    # Disable rate limiting for tests
    if hasattr(app.state, 'limiter'):
        original_enabled = app.state.limiter.enabled
        app.state.limiter.enabled = False

    # raise_server_exceptions=False ensures exceptions are handled by exception handlers
    # instead of being re-raised, which matches production behavior
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    # Re-enable rate limiting after tests
    if hasattr(app.state, 'limiter'):
        app.state.limiter.enabled = original_enabled

    app.dependency_overrides.clear()


# ==================== TEST DATA FACTORIES ====================


@pytest_asyncio.fixture
async def admin_permission(test_session: AsyncSession) -> Permission:
    """Create admin permission (*:*)."""
    permission = await permission_crud.create(
        test_session,
        obj_in={
            "code": "*:*",
            "name": "Admin Permission",
            "description": "Full admin access",
            "resource": "*",
            "action": "*",
        },
    )
    return permission


@pytest_asyncio.fixture
async def user_permissions(test_session: AsyncSession) -> dict:
    """Create user management permissions."""
    permissions = {}

    for action in ["create", "read", "update", "delete"]:
        perm = await permission_crud.create(
            test_session,
            obj_in={
                "code": f"user:{action}",
                "name": f"User {action.title()}",
                "description": f"Can {action} users",
                "resource": "user",
                "action": action,
            },
        )
        permissions[action] = perm

    return permissions


@pytest_asyncio.fixture
async def role_permissions(test_session: AsyncSession) -> dict:
    """Create role management permissions."""
    permissions = {}

    for action in ["create", "read", "update", "delete", "assign"]:
        perm = await permission_crud.create(
            test_session,
            obj_in={
                "code": f"role:{action}",
                "name": f"Role {action.title()}",
                "description": f"Can {action} roles",
                "resource": "role",
                "action": action,
            },
        )
        permissions[action] = perm

    return permissions


@pytest_asyncio.fixture
async def admin_role(
    test_session: AsyncSession,
    admin_permission: Permission
) -> Role:
    """Create admin role with full permissions."""
    role = await role_crud.create(
        test_session,
        obj_in={
            "code": "admin",
            "name": "Administrator",
            "description": "Full system access",
            "priority": 1,
        },
    )

    # Assign admin permission
    role.permissions.append(admin_permission)
    await test_session.commit()
    await test_session.refresh(role)

    return role


@pytest_asyncio.fixture
async def user_role(
    test_session: AsyncSession,
    user_permissions: dict
) -> Role:
    """Create user role with basic permissions."""
    role = await role_crud.create(
        test_session,
        obj_in={
            "code": "user",
            "name": "User",
            "description": "Basic user access",
            "priority": 10,
        },
    )

    # Assign read permission only
    role.permissions.append(user_permissions["read"])
    await test_session.commit()
    await test_session.refresh(role)

    return role


@pytest_asyncio.fixture
async def admin_user(
    test_session: AsyncSession,
    admin_role: Role
) -> User:
    """Create an admin user for testing."""
    user = await user_crud.create(
        test_session,
        obj_in={
            "email": "admin@test.com",
            "password": "AdminPass123!",
            "full_name": "Test Admin",
            "is_active": True,
            "is_verified": True,
        },
    )

    # Assign admin role
    user.roles.append(admin_role)
    await test_session.commit()
    await test_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def regular_user(
    test_session: AsyncSession,
    user_role: Role
) -> User:
    """Create a regular user for testing."""
    user = await user_crud.create(
        test_session,
        obj_in={
            "email": "user@test.com",
            "password": "UserPass123!",
            "full_name": "Test User",
            "is_active": True,
            "is_verified": True,
        },
    )

    # Assign user role
    user.roles.append(user_role)
    await test_session.commit()
    await test_session.refresh(user)

    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Generate access token for admin user."""
    return create_access_token(subject=str(admin_user.id))


@pytest.fixture
def user_token(regular_user: User) -> str:
    """Generate access token for regular user."""
    return create_access_token(subject=str(regular_user.id))


@pytest.fixture
def admin_refresh_token(admin_user: User) -> str:
    """Generate refresh token for admin user."""
    return create_refresh_token(subject=str(admin_user.id))


@pytest.fixture
def user_refresh_token(regular_user: User) -> str:
    """Generate refresh token for regular user."""
    return create_refresh_token(subject=str(regular_user.id))


@pytest.fixture
def auth_headers_admin(admin_token: str) -> dict:
    """Get authentication headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_user(user_token: str) -> dict:
    """Get authentication headers for regular user."""
    return {"Authorization": f"Bearer {user_token}"}


# ==================== HELPER FUNCTIONS ====================


@pytest.fixture
def make_user(test_session: AsyncSession):
    """Factory fixture for creating test users."""
    async def _make_user(
        email: str,
        password: str = "TestPass123!",
        full_name: str = "Test User",
        is_active: bool = True,
        is_verified: bool = True,
        roles: list[Role] = None,
    ) -> User:
        user = await user_crud.create(
            test_session,
            obj_in={
                "email": email,
                "password": password,
                "full_name": full_name,
                "is_active": is_active,
                "is_verified": is_verified,
            },
        )

        if roles:
            for role in roles:
                user.roles.append(role)
            await test_session.commit()
            await test_session.refresh(user)

        return user

    return _make_user


@pytest.fixture
def make_role(test_session: AsyncSession):
    """Factory fixture for creating test roles."""
    async def _make_role(
        code: str,
        name: str,
        description: str = "",
        priority: int = 5,
        permissions: list[Permission] = None,
    ) -> Role:
        role = await role_crud.create(
            test_session,
            obj_in={
                "code": code,
                "name": name,
                "description": description,
                "priority": priority,
            },
        )

        if permissions:
            for permission in permissions:
                role.permissions.append(permission)
            await test_session.commit()
            await test_session.refresh(role)

        return role

    return _make_role


@pytest.fixture
def make_permission(test_session: AsyncSession):
    """Factory fixture for creating test permissions."""
    async def _make_permission(
        code: str,
        name: str,
        description: str = "",
        category: str = "general",
    ) -> Permission:
        permission = await permission_crud.create(
            test_session,
            obj_in={
                "code": code,
                "name": name,
                "description": description,
                "category": category,
            },
        )
        return permission

    return _make_permission

"""
Test Delete Operations

Tests to verify that delete operations work correctly with AsyncSession.

Note: In SQLAlchemy AsyncSession, both delete() and flush() are async methods
and MUST be awaited. The original code was correct.

These tests verify the delete functionality works as expected.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import user_crud
from app.crud.role import role_crud
from app.models import User, Role
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_hard_delete_user(test_session: AsyncSession):
    """
    Test hard delete actually works.

    Verifies that hard delete permanently removes the record from the database.
    """
    # Create test user
    user = User(
        email="delete_test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Delete Test User",
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    user_id = user.id

    # Hard delete
    deleted = await user_crud.delete(
        test_session,
        id=user_id,
        hard_delete=True
    )

    assert deleted is not None
    assert deleted.id == user_id

    # After hard delete + commit, verify record is gone from database
    # We need to query directly to avoid any CRUD filtering
    from sqlalchemy import select
    result = await test_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    assert user is None, "User should be permanently deleted from database"


@pytest.mark.asyncio
async def test_soft_delete_user(test_session: AsyncSession):
    """Test soft delete marks user as deleted but doesn't remove from DB."""
    # Create test user
    user = User(
        email="soft_delete_test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Soft Delete Test User",
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    user_id = user.id

    # Soft delete
    deleted = await user_crud.delete(
        test_session,
        id=user_id,
        hard_delete=False,
        deleted_by_id=user_id
    )

    assert deleted is not None
    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.deleted_by_id == user_id

    # Clear session cache to reflect actual database state
    test_session.expire_all()

    # Verify still in database but marked as deleted
    # Note: user_crud.get() filters out soft-deleted records by default,
    # so we need to query directly to verify the record still exists
    from sqlalchemy import select
    result = await test_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    assert user is not None, "User should still exist in database"
    assert user.is_deleted is True


@pytest.mark.asyncio
async def test_hard_delete_role(test_session: AsyncSession):
    """
    Test hard delete for roles (different model, same CRUD base).

    Ensures delete works across all models using CRUDBase.
    """
    # Create test role
    role = Role(
        code="delete_test_role",
        name="Delete Test Role",
        description="Role for testing delete",
        priority=999
    )
    test_session.add(role)
    await test_session.commit()
    await test_session.refresh(role)
    role_id = role.id

    # Hard delete
    deleted = await role_crud.delete(
        test_session,
        id=role_id,
        hard_delete=True
    )

    assert deleted is not None

    # After hard delete + commit, verify record is gone from database
    # Query directly to avoid any CRUD filtering
    from sqlalchemy import select
    result = await test_session.execute(
        select(Role).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    assert role is None, "Role should be permanently deleted from database"


@pytest.mark.asyncio
async def test_delete_nonexistent_record(test_session: AsyncSession):
    """Test deleting a record that doesn't exist raises exception."""
    from uuid import uuid4
    from app.core.exceptions import ResourceNotFoundError

    fake_id = uuid4()

    # Should raise ResourceNotFoundError
    try:
        await user_crud.delete(
            test_session,
            id=fake_id,
            hard_delete=True
        )
        assert False, "Should raise ResourceNotFoundError"
    except ResourceNotFoundError:
        pass  # Expected behavior


@pytest.mark.asyncio
async def test_soft_delete_already_deleted(test_session: AsyncSession):
    """Test soft deleting an already soft-deleted record."""
    # Create and soft delete user
    user = User(
        email="double_delete@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Double Delete Test",
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    user_id = user.id

    # First soft delete
    await user_crud.delete(test_session, id=user_id, hard_delete=False)

    # Second soft delete - user_crud.get() will raise exception because user is deleted
    from app.core.exceptions import ResourceNotFoundError
    try:
        await user_crud.delete(test_session, id=user_id, hard_delete=False)
        assert False, "Should raise ResourceNotFoundError for already deleted user"
    except ResourceNotFoundError:
        pass  # Expected - user_crud filters out soft-deleted records

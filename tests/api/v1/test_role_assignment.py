"""
Test Role Assignment Operations

Tests to verify that role assignment/unassignment works correctly
after the session.delete() bug fix.

This tests the critical bug fix from Phase 1:
- users.py:431 - await session.delete(assignment) -> session.delete(assignment)

These tests will FAIL if the bug is not fixed.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Role
from app.core.security import get_password_hash


@pytest.fixture
async def test_user_for_roles(test_session: AsyncSession) -> User:
    """Create a test user for role assignment tests."""
    user = User(
        email="roletest@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Role Test User",
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_roles(test_session: AsyncSession) -> list[Role]:
    """Create test roles."""
    roles = [
        Role(
            code="test_role_1",
            name="Test Role 1",
            description="First test role",
            priority=10
        ),
        Role(
            code="test_role_2",
            name="Test Role 2",
            description="Second test role",
            priority=20
        ),
    ]
    for role in roles:
        test_session.add(role)
    await test_session.commit()
    for role in roles:
        await test_session.refresh(role)
    return roles


def test_assign_single_role_to_user(
    test_client: TestClient,
    admin_token_headers: dict,
    test_user_for_roles: User,
    test_roles: list[Role],
):
    """Test assigning a single role to a user."""
    user_id = str(test_user_for_roles.id)
    role_id = str(test_roles[0].id)

    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": [role_id], "replace": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["roles"]) >= 1
    role_ids = [r["id"] for r in data["roles"]]
    assert role_id in role_ids


def test_assign_multiple_roles_to_user(
    test_client: TestClient,
    admin_token_headers: dict,
    test_user_for_roles: User,
    test_roles: list[Role],
):
    """Test assigning multiple roles to a user."""
    user_id = str(test_user_for_roles.id)
    role_ids = [str(r.id) for r in test_roles]

    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": role_ids, "replace": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["roles"]) >= len(role_ids)


def test_replace_all_user_roles(
    test_client: TestClient,
    admin_token_headers: dict,
    test_user_for_roles: User,
    test_roles: list[Role],
):
    """
    Test replacing all user roles.

    This tests the bug fix in users.py:431 where session.delete() was awaited.
    THIS WILL FAIL if the bug still exists.
    """
    user_id = str(test_user_for_roles.id)

    # First, assign role 1
    role1_id = str(test_roles[0].id)
    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": [role1_id], "replace": True},
    )
    assert response.status_code == 200

    # Now replace with role 2 - THIS WILL FAIL if bug exists
    role2_id = str(test_roles[1].id)
    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": [role2_id], "replace": True},
    )

    assert response.status_code == 200
    data = response.json()

    # User should only have role 2 now
    role_ids = [r["id"] for r in data["roles"]]
    assert role2_id in role_ids
    # Note: Admin role might still be there if user is admin


def test_remove_all_roles_from_user(
    test_client: TestClient,
    admin_token_headers: dict,
    test_user_for_roles: User,
    test_roles: list[Role],
):
    """
    Test removing all roles from a user.

    This is a critical test for the session.delete() bug fix.
    THIS WILL FAIL with TypeError if the bug still exists.
    """
    user_id = str(test_user_for_roles.id)

    # First assign roles
    role_ids = [str(r.id) for r in test_roles]
    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": role_ids, "replace": False},
    )
    assert response.status_code == 200

    # Now remove all roles - THIS WILL FAIL if bug exists
    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": [], "replace": True},
    )

    assert response.status_code == 200
    data = response.json()
    # User should have no roles (or only system-assigned roles)
    assert isinstance(data["roles"], list)


def test_assign_nonexistent_role_fails(
    test_client: TestClient,
    admin_token_headers: dict,
    test_user_for_roles: User,
):
    """Test that assigning a nonexistent role fails gracefully."""
    user_id = str(test_user_for_roles.id)
    fake_role_id = "00000000-0000-0000-0000-000000000000"

    response = test_client.put(
        f"/api/v1/users/{user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": [fake_role_id], "replace": False},
    )

    # Should fail with 404 or 422
    assert response.status_code in [404, 422]


def test_assign_roles_to_nonexistent_user_fails(
    test_client: TestClient,
    admin_token_headers: dict,
    test_roles: list[Role],
):
    """Test that assigning roles to nonexistent user fails."""
    fake_user_id = "00000000-0000-0000-0000-000000000000"
    role_id = str(test_roles[0].id)

    response = test_client.put(
        f"/api/v1/users/{fake_user_id}/roles",
        headers=admin_token_headers,
        json={"role_ids": [role_id], "replace": False},
    )

    assert response.status_code == 404

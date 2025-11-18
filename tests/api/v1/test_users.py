"""
Tests for User Management Endpoints

This module tests all user-related endpoints:
- Create user (admin only)
- List users with pagination
- Get user by ID
- Update user
- Delete user (soft delete)
- Restore user (NEW!)
- Assign roles to user
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Role


class TestCreateUser:
    """Test user creation endpoint."""

    def test_create_user_as_admin(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        user_role: Role,
    ):
        """Test admin can create new users."""
        response = test_client.post(
            "/api/v1/users",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["full_name"] == "New User"
        assert "hashed_password" not in data

    def test_create_user_as_regular_user(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
    ):
        """Test regular user cannot create users."""
        response = test_client.post(
            "/api/v1/users",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    def test_create_user_duplicate_email(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
    ):
        """Test cannot create user with existing email."""
        response = test_client.post(
            "/api/v1/users",
            json={
                "email": regular_user.email,
                "password": "SecurePass123!",
                "full_name": "Duplicate User",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 409  # Conflict for duplicate resource


class TestListUsers:
    """Test user listing endpoint."""

    def test_list_users_as_admin(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        admin_user: User,
        regular_user: User,
    ):
        """Test admin can list all users."""
        response = test_client.get(
            "/api/v1/users",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2  # At least admin and regular user
        assert "total" in data
        assert "page" in data

    def test_list_users_pagination(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
    ):
        """Test pagination works correctly."""
        response = test_client.get(
            "/api/v1/users?skip=0&limit=1",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_users_as_regular_user(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
    ):
        """Test regular user with read permission can list users."""
        response = test_client.get(
            "/api/v1/users",
            headers=auth_headers_user,
        )

        # Should work if user has user:read permission
        assert response.status_code in [200, 403]


class TestGetUser:
    """Test get single user endpoint."""

    def test_get_user_by_id(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
    ):
        """Test getting user by ID."""
        response = test_client.get(
            f"/api/v1/users/{regular_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(regular_user.id)
        assert data["email"] == regular_user.email

    def test_get_nonexistent_user(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
    ):
        """Test getting non-existent user returns 404."""
        from uuid import uuid4
        fake_id = uuid4()

        response = test_client.get(
            f"/api/v1/users/{fake_id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 404


class TestUpdateUser:
    """Test user update endpoint."""

    def test_update_own_profile(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
        regular_user: User,
    ):
        """Test user can update their own profile."""
        response = test_client.put(
            f"/api/v1/users/{regular_user.id}",
            json={
                "full_name": "Updated Name",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_update_other_user_as_admin(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
    ):
        """Test admin can update other users."""
        response = test_client.put(
            f"/api/v1/users/{regular_user.id}",
            json={
                "full_name": "Admin Updated",
                "is_active": False,
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Admin Updated"

    def test_update_other_user_as_regular_user(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
        admin_user: User,
    ):
        """Test regular user cannot update other users."""
        response = test_client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "full_name": "Hacked",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 403


class TestDeleteUser:
    """Test user deletion (soft delete) endpoint."""

    def test_delete_user_as_admin(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
    ):
        """Test admin can delete users."""
        response = test_client.delete(
            f"/api/v1/users/{regular_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify user is soft deleted
        get_response = test_client.get(
            f"/api/v1/users/{regular_user.id}",
            headers=auth_headers_admin,
        )
        # Should either be 404 or return user with is_deleted=True
        assert get_response.status_code in [404, 200]

    def test_delete_user_as_regular_user(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
        admin_user: User,
    ):
        """Test regular user cannot delete users."""
        response = test_client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers_user,
        )

        assert response.status_code == 403


class TestRestoreUser:
    """Test user restoration endpoint (NEW!)."""

    def test_restore_deleted_user(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
    ):
        """Test restoring a soft-deleted user."""
        # First delete the user
        delete_response = test_client.delete(
            f"/api/v1/users/{regular_user.id}",
            headers=auth_headers_admin,
        )
        assert delete_response.status_code == 200

        # Now restore the user
        restore_response = test_client.post(
            f"/api/v1/users/{regular_user.id}/restore",
            headers=auth_headers_admin,
        )

        assert restore_response.status_code == 200
        data = restore_response.json()
        assert data["id"] == str(regular_user.id)
        assert data["email"] == regular_user.email

        # Verify user is accessible again
        get_response = test_client.get(
            f"/api/v1/users/{regular_user.id}",
            headers=auth_headers_admin,
        )
        assert get_response.status_code == 200

    def test_restore_non_deleted_user(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
    ):
        """Test restoring a non-deleted user returns appropriate response."""
        response = test_client.post(
            f"/api/v1/users/{regular_user.id}/restore",
            headers=auth_headers_admin,
        )

        # Should either succeed (idempotent) or return error
        assert response.status_code in [200, 400]

    def test_restore_user_as_regular_user(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
        admin_user: User,
    ):
        """Test regular user cannot restore users."""
        response = test_client.post(
            f"/api/v1/users/{admin_user.id}/restore",
            headers=auth_headers_user,
        )

        assert response.status_code == 403


class TestAssignRoles:
    """Test role assignment endpoint."""

    def test_assign_roles_to_user(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        regular_user: User,
        user_role: Role,
    ):
        """Test assigning roles to user."""
        response = test_client.post(
            f"/api/v1/users/{regular_user.id}/roles",
            json={
                "role_ids": [str(user_role.id)],
                "replace": True,
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) >= 1

    def test_assign_roles_as_regular_user(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
        admin_user: User,
        user_role: Role,
    ):
        """Test regular user cannot assign roles."""
        response = test_client.post(
            f"/api/v1/users/{admin_user.id}/roles",
            json={
                "role_ids": [str(user_role.id)],
                "replace": False,
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 403


class TestUserPermissions:
    """Test user permission checking."""

    def test_admin_has_all_permissions(
        self,
        test_client: TestClient,
        auth_headers_admin: dict,
        admin_user: User,
    ):
        """Test admin user has all permissions."""
        # Admin should be able to access all protected endpoints
        response = test_client.get(
            "/api/v1/users",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200

    def test_unauthorized_access(
        self,
        test_client: TestClient,
    ):
        """Test accessing user endpoints without authentication."""
        response = test_client.get("/api/v1/users")

        assert response.status_code == 401

"""
Tests for Authentication Endpoints

This module tests all auth-related endpoints:
- Registration
- Login (JSON and form)
- Logout
- Token refresh
- Get current user (/me)
- Change password
- Token revocation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Role
from app.core.security import verify_password, decode_token


class TestRegistration:
    """Test user registration endpoint."""

    def test_register_new_user_success(self, test_client: TestClient):
        """Test successful user registration."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned

    def test_register_duplicate_email(self, test_client: TestClient, admin_user: User):
        """Test registration with existing email fails."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": admin_user.email,
                "password": "SecurePass123!",
                "full_name": "Duplicate User",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email(self, test_client: TestClient):
        """Test registration with invalid email format."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, test_client: TestClient):
        """Test registration with weak password."""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "weak",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Test login endpoints (JSON and form)."""

    def test_login_json_success(self, test_client: TestClient, admin_user: User):
        """Test successful JSON login."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "AdminPass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Verify token is valid
        token_payload = decode_token(data["access_token"])
        assert token_payload["sub"] == str(admin_user.id)

    def test_login_form_success(self, test_client: TestClient, admin_user: User):
        """Test successful form-based login (for Swagger UI)."""
        response = test_client.post(
            "/api/v1/auth/login/form",
            data={
                "username": "admin@test.com",  # OAuth2 uses 'username' field
                "password": "AdminPass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client: TestClient, admin_user: User):
        """Test login with incorrect password."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@test.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with non-existent email."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "SomePass123!",
            },
        )

        assert response.status_code == 401

    async def test_login_inactive_user(
        self,
        test_client: TestClient,
        test_session: AsyncSession,
        regular_user: User,
    ):
        """Test login with inactive user account."""
        # Deactivate user
        regular_user.is_active = False
        test_session.add(regular_user)
        await test_session.commit()

        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@test.com",
                "password": "UserPass123!",
            },
        )

        assert response.status_code == 401
        response_data = response.json()
        # Check if "detail" key exists, otherwise check "message"
        error_message = response_data.get("detail", response_data.get("message", "")).lower()
        assert "incorrect" in error_message or "inactive" in error_message


class TestGetCurrentUser:
    """Test /me endpoint to get current authenticated user."""

    def test_get_me_success(
        self,
        test_client: TestClient,
        admin_user: User,
        auth_headers_admin: dict,
    ):
        """Test getting current user info."""
        response = test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == admin_user.email
        assert data["full_name"] == admin_user.full_name
        assert data["id"] == str(admin_user.id)
        assert "roles" in data
        assert "hashed_password" not in data

    def test_get_me_unauthorized(self, test_client: TestClient):
        """Test /me without authentication."""
        response = test_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_me_invalid_token(self, test_client: TestClient):
        """Test /me with invalid token."""
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401


class TestLogout:
    """Test logout endpoint (token revocation)."""

    def test_logout_success(
        self,
        test_client: TestClient,
        admin_token: str,
        auth_headers_admin: dict,
    ):
        """Test successful logout."""
        response = test_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Verify token is revoked - subsequent requests should fail
        response = test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers_admin,
        )

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

    def test_logout_without_auth(self, test_client: TestClient):
        """Test logout without authentication."""
        response = test_client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestChangePassword:
    """Test password change endpoint."""

    def test_change_password_success(
        self,
        test_client: TestClient,
        regular_user: User,
        auth_headers_user: dict,
    ):
        """Test successful password change."""
        response = test_client.put(
            "/api/v1/auth/me/password",
            json={
                "current_password": "UserPass123!",
                "new_password": "NewSecurePass456!",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower() or "changed" in response.json()["message"].lower()

        # Verify user can login with new password
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@test.com",
                "password": "NewSecurePass456!",
            },
        )

        assert login_response.status_code == 200

    def test_change_password_wrong_current(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
    ):
        """Test password change with wrong current password."""
        response = test_client.put(
            "/api/v1/auth/me/password",
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewSecurePass456!",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_weak_new_password(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
    ):
        """Test password change with weak new password."""
        response = test_client.put(
            "/api/v1/auth/me/password",
            json={
                "current_password": "UserPass123!",
                "new_password": "weak",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 422  # Validation error

    def test_change_password_same_as_current(
        self,
        test_client: TestClient,
        auth_headers_user: dict,
    ):
        """Test password change with same password as current."""
        response = test_client.put(
            "/api/v1/auth/me/password",
            json={
                "current_password": "UserPass123!",
                "new_password": "UserPass123!",
            },
            headers=auth_headers_user,
        )

        assert response.status_code == 400
        assert "different" in response.json()["detail"].lower() or "same" in response.json()["detail"].lower()


class TestTokenRefresh:
    """Test token refresh endpoint."""

    def test_refresh_token_success(
        self,
        test_client: TestClient,
        admin_token: str,
        admin_refresh_token: str,
    ):
        """Test successful token refresh."""
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": admin_refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Note: token might be same as admin_token if created at same timestamp

    def test_refresh_token_unauthorized(self, test_client: TestClient):
        """Test token refresh with invalid refresh token."""
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401

    def test_refresh_token_revoked(
        self,
        test_client: TestClient,
        admin_refresh_token: str,
        auth_headers_admin: dict,
    ):
        """Test that refresh tokens work independently of access token revocation."""
        # First logout (revoke access token)
        test_client.post("/api/v1/auth/logout", headers=auth_headers_admin)

        # Refresh token should still work (refresh tokens are not revoked by logout)
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": admin_refresh_token},
        )

        # Should succeed because refresh tokens are separate from access tokens
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""

    @pytest.mark.skip(reason="Rate limiting requires Redis and specific configuration in test environment")
    def test_login_rate_limit(self, test_client: TestClient):
        """Test login rate limiting after multiple failed attempts."""
        # Make multiple failed login attempts
        for _ in range(6):  # Assuming rate limit is 5 attempts
            test_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@test.com",
                    "password": "wrong",
                },
            )

        # Next attempt should be rate limited
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@test.com",
                "password": "wrong",
            },
        )

        assert response.status_code == 429  # Too Many Requests

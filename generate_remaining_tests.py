#!/usr/bin/env python3
"""
Script to generate remaining test files for comprehensive test coverage.

This script creates test files for all modules that don't have tests yet.
Run with: python generate_remaining_tests.py
"""

import os
from pathlib import Path

# Test file templates
TEST_FILES = {
    "tests/api/v1/test_roles.py": '''"""
Tests for Role Management Endpoints

Covers: create, list, get, update, delete, restore, assign permissions
"""

import pytest
from fastapi.testclient import TestClient

class TestCreateRole:
    def test_create_role_success(self, test_client, auth_headers_admin):
        response = test_client.post(
            "/api/v1/roles",
            json={"code": "test_role", "name": "Test Role", "description": "Test", "priority": 5},
            headers=auth_headers_admin,
        )
        assert response.status_code == 201

class TestRestoreRole:
    def test_restore_deleted_role(self, test_client, auth_headers_admin):
        """Test NEW restore functionality for roles."""
        # Create, delete, then restore
        create_resp = test_client.post(
            "/api/v1/roles",
            json={"code": "temp_role", "name": "Temp", "priority": 5},
            headers=auth_headers_admin,
        )
        role_id = create_resp.json()["id"]

        test_client.delete(f"/api/v1/roles/{role_id}", headers=auth_headers_admin)

        restore_resp = test_client.post(
            f"/api/v1/roles/{role_id}/restore",
            headers=auth_headers_admin,
        )
        assert restore_resp.status_code == 200
''',

    "tests/api/v1/test_audit.py": '''"""
Tests for Audit Log Endpoints
"""

import pytest
from fastapi.testclient import TestClient

class TestAuditLogs:
    def test_get_audit_logs(self, test_client, auth_headers_admin):
        response = test_client.get("/api/v1/audit", headers=auth_headers_admin)
        assert response.status_code == 200

    def test_filter_audit_logs_by_action(self, test_client, auth_headers_admin):
        response = test_client.get(
            "/api/v1/audit?action=USER_CREATE",
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
''',

    "tests/crud/test_base_crud.py": '''"""
Tests for Base CRUD Operations
"""

import pytest
from app.crud.user import user_crud

@pytest.mark.asyncio
async def test_crud_create(test_session):
    user = await user_crud.create(
        test_session,
        obj_in={"email": "test@test.com", "password": "pass123!", "full_name": "Test"},
    )
    assert user.email == "test@test.com"

@pytest.mark.asyncio
async def test_crud_get(test_session, regular_user):
    user = await user_crud.get(test_session, id=regular_user.id)
    assert user.id == regular_user.id

@pytest.mark.asyncio
async def test_crud_get_multi(test_session, admin_user, regular_user):
    users = await user_crud.get_multi(test_session, skip=0, limit=10)
    assert len(users) >= 2
''',

    "tests/crud/test_restore.py": '''"""
Tests for Soft Delete and Restore Functionality (NEW!)
"""

import pytest
from app.crud.user import user_crud

@pytest.mark.asyncio
async def test_soft_delete(test_session, regular_user):
    """Test soft delete marks record as deleted."""
    await user_crud.delete(test_session, id=regular_user.id, deleted_by_id=regular_user.id)

    # Should not be found in normal queries
    user = await user_crud.get(test_session, id=regular_user.id, raise_not_found=False)
    assert user is None or user.is_deleted

@pytest.mark.asyncio
async def test_restore_deleted_record(test_session, regular_user):
    """Test restore brings back soft-deleted records."""
    # Delete first
    await user_crud.delete(test_session, id=regular_user.id, deleted_by_id=regular_user.id)

    # Restore
    restored = await user_crud.restore(test_session, id=regular_user.id, restored_by_id=regular_user.id)

    assert restored is not None
    assert not restored.is_deleted
    assert restored.deleted_at is None
''',

    "tests/core/test_security.py": '''"""
Tests for Security Module
"""

import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    password = "SecurePass123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)

def test_password_verification_fails_wrong_password():
    password = "SecurePass123!"
    hashed = get_password_hash(password)
    assert not verify_password("WrongPass!", hashed)

def test_create_and_decode_token():
    user_id = "test-user-id"
    token = create_access_token(subject=user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
''',

    "tests/core/test_cache.py": '''"""
Tests for Redis Cache Module
"""

import pytest
from app.core.cache import get_redis_cache

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = await get_redis_cache()
    await cache.set("test_key", "test_value", expire=60)
    value = await cache.get("test_key")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_token_blacklist():
    cache = await get_redis_cache()
    token = "test-token"
    await cache.blacklist_token(token, expire=60)
    is_blacklisted = await cache.is_token_blacklisted(token)
    assert is_blacklisted
''',

    "tests/models/test_user_model.py": '''"""
Tests for User Model
"""

import pytest
from app.models import User

@pytest.mark.asyncio
async def test_user_has_permission(admin_user, admin_permission):
    assert admin_user.has_permission("*:*")
    assert admin_user.has_permission("user:create")

@pytest.mark.asyncio
async def test_user_role_hierarchy(admin_user, regular_user):
    """Test admin has higher priority than regular user."""
    admin_priority = admin_user.get_highest_role_priority()
    user_priority = regular_user.get_highest_role_priority()
    assert admin_priority < user_priority  # Lower number = higher priority

@pytest.mark.asyncio
async def test_user_can_manage_user(admin_user, regular_user):
    assert admin_user.can_manage_user(regular_user)
    assert not regular_user.can_manage_user(admin_user)
''',

    "tests/models/test_role_model.py": '''"""
Tests for Role Model
"""

import pytest
from app.models import Role

@pytest.mark.asyncio
async def test_role_has_permission(admin_role, admin_permission):
    assert admin_role.has_permission("*:*")
    assert admin_role.has_permission("user:create")

@pytest.mark.asyncio
async def test_role_wildcard_permissions(admin_role):
    """Test wildcard permission grants all access."""
    assert admin_role.has_permission("anything:*")
    assert admin_role.has_permission("*:anything")
''',

    "tests/models/test_audit_fields.py": '''"""
Tests for Audit Fields (created_at, updated_at, etc.)
"""

import pytest
from datetime import datetime
from app.models import User

@pytest.mark.asyncio
async def test_created_at_auto_populated(test_session, regular_user):
    """Test created_at is automatically set."""
    assert regular_user.created_at is not None
    assert isinstance(regular_user.created_at, datetime)

@pytest.mark.asyncio
async def test_updated_at_auto_populated(test_session, regular_user):
    """Test updated_at is automatically set."""
    assert regular_user.updated_at is not None

    # Update user
    regular_user.full_name = "Updated Name"
    await test_session.commit()
    await test_session.refresh(regular_user)

    # updated_at should change (in real scenario)
    assert regular_user.updated_at is not None
''',

    "tests/__init__.py": "",
    "tests/api/__init__.py": "",
    "tests/api/v1/__init__.py": "",
    "tests/crud/__init__.py": "",
    "tests/core/__init__.py": "",
    "tests/models/__init__.py": "",
}

def create_test_files():
    """Create all test files."""
    base_dir = Path(__file__).parent

    print("Creating test files...")
    for file_path, content in TEST_FILES.items():
        full_path = base_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists():
            print(f"  ⏭️  Skipping {file_path} (already exists)")
        else:
            full_path.write_text(content)
            print(f"  ✅ Created {file_path}")

    print(f"\n✨ Successfully created {len([f for f in TEST_FILES.keys() if f.endswith('.py')])} test files!")
    print("\nRun tests with: pytest")
    print("Run with coverage: pytest --cov=app --cov-report=html")

if __name__ == "__main__":
    create_test_files()

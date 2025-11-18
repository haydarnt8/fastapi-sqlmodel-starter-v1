"""
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

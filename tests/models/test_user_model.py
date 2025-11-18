"""
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

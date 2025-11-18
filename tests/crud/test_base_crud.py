"""
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

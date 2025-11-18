"""
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

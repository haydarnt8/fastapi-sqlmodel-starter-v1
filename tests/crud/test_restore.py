"""
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

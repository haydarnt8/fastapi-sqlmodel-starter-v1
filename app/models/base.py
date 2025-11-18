"""
Base Models with Audit Fields

This module provides base models that all other models inherit from.

Why audit fields?
- Track WHO created/modified records
- Track WHEN changes happened
- Enable soft delete (mark as deleted without actually deleting)
- Required for compliance (GDPR, SOC2, etc.)
- Essential for debugging and auditing

Audit Fields:
- created_at: When the record was created
- updated_at: When the record was last modified
- created_by_id: User ID who created the record
- updated_by_id: User ID who last modified the record
- is_deleted: Soft delete flag
- deleted_at: When the record was deleted

Why soft delete?
- Can restore accidentally deleted data
- Keep referential integrity (foreign keys still work)
- Audit trail (know what was deleted and when)
- Compliance requirements (some data can't be permanently deleted)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """
    Mixin for timestamp fields (created_at, updated_at).

    Usage:
        class MyModel(TimestampMixin, SQLModel, table=True):
            name: str
            # Automatically gets created_at and updated_at
    """

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Timestamp when the record was created",
        sa_column_kwargs={"index": True},  # Index for faster queries
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Timestamp when the record was last updated",
        sa_column_kwargs={
            "onupdate": datetime.utcnow,  # Auto-update on modifications
            "index": True,
        },
    )


class AuditMixin(TimestampMixin):
    """
    Mixin for audit fields (who created/updated).

    Extends TimestampMixin with user tracking.

    Usage:
        class MyModel(AuditMixin, SQLModel, table=True):
            name: str
            # Gets created_at, updated_at, created_by_id, updated_by_id
    """

    created_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="ID of user who created this record",
        sa_column_kwargs={"index": True},
    )
    updated_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="ID of user who last updated this record",
    )


class SoftDeleteMixin(SQLModel):
    """
    Mixin for soft delete functionality.

    Instead of deleting records, we mark them as deleted.

    Usage:
        class MyModel(SoftDeleteMixin, SQLModel, table=True):
            name: str
            # Gets is_deleted and deleted_at fields

        # In your code:
        model.is_deleted = True
        model.deleted_at = datetime.utcnow()

        # Query only non-deleted records:
        select(MyModel).where(MyModel.is_deleted == False)
    """

    is_deleted: bool = Field(
        default=False,
        nullable=False,
        description="Whether this record has been soft-deleted",
        sa_column_kwargs={"index": True},  # Index for faster queries
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Timestamp when the record was deleted",
    )
    deleted_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="ID of user who deleted this record",
    )


class BaseModel(AuditMixin, SoftDeleteMixin):
    """
    Base model with all audit fields.

    All application models should inherit from this.

    Includes:
    - created_at: When created
    - updated_at: When last modified
    - created_by_id: Who created it
    - updated_by_id: Who modified it
    - is_deleted: Soft delete flag
    - deleted_at: When deleted
    - deleted_by_id: Who deleted it

    Usage:
        class Student(BaseModel, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            name: str
            # Automatically gets all audit fields!

    Example:
        # Creating a record (in CRUD layer):
        student = Student(name="John", created_by_id=current_user.id)

        # Updating a record:
        student.name = "Jane"
        student.updated_by_id = current_user.id
        student.updated_at = datetime.utcnow()

        # Soft deleting:
        student.is_deleted = True
        student.deleted_at = datetime.utcnow()
        student.deleted_by_id = current_user.id

        # Querying (only active records):
        statement = select(Student).where(Student.is_deleted == False)
    """

    pass


class UUIDMixin(SQLModel):
    """
    Mixin for UUID primary keys instead of integer IDs.

    Why UUIDs?
    - No sequential IDs (security - can't guess next ID)
    - Can generate on client side
    - Distributed systems friendly
    - No ID collision across databases

    Usage:
        import uuid
        from sqlmodel import Field

        class MyModel(UUIDMixin, BaseModel, table=True):
            id: uuid.UUID = Field(
                default_factory=uuid.uuid4,
                primary_key=True,
                nullable=False
            )
            name: str

    Note: This is optional. Use integer IDs for simplicity,
          UUIDs for security/scalability.
    """

    pass

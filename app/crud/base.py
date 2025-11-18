"""
Base CRUD Operations

This module provides a generic CRUD (Create, Read, Update, Delete) class that
can be reused for all models.

Why CRUD base class?
- DRY principle: Write once, use everywhere
- Consistent behavior across all models
- Easy to add common functionality (pagination, soft delete, etc.)
- Reduces bugs by centralizing logic
- Easy to test

CRUD Pattern:
Model (Database) → CRUD (Business Logic) → Router (API)

This separates concerns:
- Models: What data looks like
- CRUD: How to manipulate data
- Routers: How to expose data via API
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Union
from uuid import UUID
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel
from pydantic import BaseModel

from app.core.exceptions import ResourceNotFoundError, BusinessLogicError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic CRUD
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.

    Generic parameters:
    - ModelType: SQLModel database model
    - CreateSchemaType: Pydantic schema for creating
    - UpdateSchemaType: Pydantic schema for updating

    Usage:
        class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
            pass

        student_crud = CRUDStudent(Student)
        student = await student_crud.create(session, obj_in=StudentCreate(...))
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD object with model class.

        Args:
            model: SQLModel model class
        """
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        id: Union[UUID, Any],
        raise_not_found: bool = True,
        allow_deleted: bool = False,
    ) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            session: Database session
            id: Record ID
            raise_not_found: If True, raise exception if not found
            allow_deleted: If True, include soft-deleted records in search

        Returns:
            Model instance or None

        Raises:
            ResourceNotFoundError: If record not found and raise_not_found=True

        Example:
            student = await student_crud.get(session, id=123)
            deleted_student = await student_crud.get(session, id=123, allow_deleted=True)
        """
        statement = select(self.model).where(self.model.id == id)

        # Filter out soft-deleted records if model supports it (unless allow_deleted=True)
        if hasattr(self.model, "is_deleted") and not allow_deleted:
            statement = statement.where(self.model.is_deleted == False)

        result = await session.execute(statement)
        obj = result.scalar_one_or_none()

        if obj is None and raise_not_found:
            raise ResourceNotFoundError(
                resource_name=self.model.__name__,
                id=id,
            )

        return obj

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        allow_deleted: bool = False,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.

        Args:
            session: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            filters: Dictionary of field:value filters
            order_by: Field name to order by (prefix with - for descending)
            allow_deleted: If True, include soft-deleted records in results

        Returns:
            List of model instances

        Example:
            # Get active records only (default):
            students = await student_crud.get_multi(
                session,
                skip=0,
                limit=20,
                filters={"grade_level": "10th Grade"},
                order_by="-created_at"
            )

            # Get all records including deleted:
            all_students = await student_crud.get_multi(
                session,
                skip=0,
                limit=20,
                allow_deleted=True
            )
        """
        statement = select(self.model)

        # Filter out soft-deleted records (unless allow_deleted=True)
        if hasattr(self.model, "is_deleted") and not allow_deleted:
            statement = statement.where(self.model.is_deleted == False)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    statement = statement.where(getattr(self.model, field) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                # Descending order
                field = order_by[1:]
                if hasattr(self.model, field):
                    statement = statement.order_by(getattr(self.model, field).desc())
            else:
                # Ascending order
                if hasattr(self.model, order_by):
                    statement = statement.order_by(getattr(self.model, order_by))

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        created_by_id: Optional[UUID] = None,
    ) -> ModelType:
        """
        Create a new record.

        Args:
            session: Database session
            obj_in: Pydantic schema with data to create
            created_by_id: ID of user creating the record (for audit)

        Returns:
            Created model instance

        Example:
            student_data = StudentCreate(full_name="John Doe", ...)
            student = await student_crud.create(
                session,
                obj_in=student_data,
                created_by_id=current_user.id
            )
        """
        # Convert Pydantic schema or dict to dict
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump(exclude_unset=True)

        # Add audit fields if model supports them
        if created_by_id:
            if hasattr(self.model, "created_by_id"):
                obj_in_data["created_by_id"] = created_by_id
            if hasattr(self.model, "updated_by_id"):
                obj_in_data["updated_by_id"] = created_by_id

        # Create model instance
        db_obj = self.model(**obj_in_data)

        # Add to session
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        logger.info(
            f"Created {self.model.__name__}",
            extra={"id": db_obj.id, "created_by": created_by_id},
        )

        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        updated_by_id: Optional[UUID] = None,
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            session: Database session
            db_obj: Existing model instance from database
            obj_in: Pydantic schema with updated data
            updated_by_id: ID of user updating the record (for audit)

        Returns:
            Updated model instance

        Example:
            student = await student_crud.get(session, id=123)
            update_data = StudentUpdate(full_name="Jane Doe")
            student = await student_crud.update(
                session,
                db_obj=student,
                obj_in=update_data,
                updated_by_id=current_user.id
            )
        """
        # Get update data (only fields that were set)
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Update audit fields
        if updated_by_id and hasattr(db_obj, "updated_by_id"):
            obj_data["updated_by_id"] = updated_by_id

        # Update model fields
        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        logger.info(
            f"Updated {self.model.__name__}",
            extra={"id": db_obj.id, "updated_by": updated_by_id},
        )

        return db_obj

    async def delete(
        self,
        session: AsyncSession,
        *,
        id: Union[UUID, int],
        deleted_by_id: Optional[UUID] = None,
        hard_delete: bool = False,
    ) -> Optional[ModelType]:
        """
        Delete a record (soft delete by default).

        Args:
            session: Database session
            id: Record ID to delete
            deleted_by_id: ID of user deleting the record (for audit)
            hard_delete: If True, permanently delete. If False, soft delete.

        Returns:
            Deleted model instance or None

        Example:
            # Soft delete (default):
            await student_crud.delete(session, id=123, deleted_by_id=current_user.id)

            # Hard delete:
            await student_crud.delete(session, id=123, hard_delete=True)
        """
        obj = await self.get(session, id=id)

        if obj is None:
            return None

        if hard_delete or not hasattr(obj, "is_deleted"):
            # Permanent deletion
            await session.delete(obj)
            logger.warning(
                f"Hard deleted {self.model.__name__}",
                extra={"id": id, "deleted_by": deleted_by_id},
            )
        else:
            # Soft delete
            from datetime import datetime, timezone

            obj.is_deleted = True
            if hasattr(obj, "deleted_at"):
                obj.deleted_at = datetime.now(timezone.utc)
            if hasattr(obj, "deleted_by_id") and deleted_by_id:
                obj.deleted_by_id = deleted_by_id
            session.add(obj)
            logger.info(
                f"Soft deleted {self.model.__name__}",
                extra={"id": id, "deleted_by": deleted_by_id},
            )

        await session.commit()
        return obj

    async def restore(
        self,
        session: AsyncSession,
        *,
        id: Union[UUID, int],
        restored_by_id: Optional[UUID] = None,
    ) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.

        Args:
            session: Database session
            id: Record ID to restore
            restored_by_id: ID of user restoring the record (for audit)

        Returns:
            Restored model instance or None

        Raises:
            ValueError: If record is not soft-deleted or model doesn't support soft delete

        Example:
            # Restore a deleted record:
            restored = await student_crud.restore(session, id=123, restored_by_id=current_user.id)
        """
        # Get the record including deleted ones
        obj = await self.get(session, id=id, allow_deleted=True)

        if obj is None:
            return None

        # Check if model supports soft delete
        if not hasattr(obj, "is_deleted"):
            raise ValueError(
                f"{self.model.__name__} does not support soft delete, cannot restore"
            )

        # Check if record is actually deleted
        if not obj.is_deleted:
            logger.warning(
                f"Attempted to restore non-deleted {self.model.__name__}",
                extra={"id": id, "restored_by": restored_by_id},
            )
            return obj

        # Restore the record
        obj.is_deleted = False
        obj.deleted_at = None
        obj.deleted_by_id = None

        # Set updated_by for audit trail
        if hasattr(obj, "updated_by_id") and restored_by_id:
            obj.updated_by_id = restored_by_id

        session.add(obj)
        await session.commit()
        await session.refresh(obj)

        logger.info(
            f"Restored {self.model.__name__}",
            extra={"id": id, "restored_by": restored_by_id},
        )

        return obj

    async def count(
        self,
        session: AsyncSession,
        *,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count records matching filters.

        Args:
            session: Database session
            filters: Dictionary of field:value filters

        Returns:
            Count of matching records

        Example:
            count = await student_crud.count(
                session,
                filters={"grade_level": "10th Grade"}
            )
        """
        statement = select(func.count()).select_from(self.model)

        # Filter out soft-deleted records
        if hasattr(self.model, "is_deleted"):
            statement = statement.where(self.model.is_deleted == False)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    statement = statement.where(getattr(self.model, field) == value)

        result = await session.execute(statement)
        return result.scalar_one()

    async def exists(
        self,
        session: AsyncSession,
        *,
        id: Union[UUID, int],
    ) -> bool:
        """
        Check if record exists by ID.

        Args:
            session: Database session
            id: Record ID

        Returns:
            True if exists, False otherwise

        Example:
            if await student_crud.exists(session, id=123):
                print("Student exists")
        """
        obj = await self.get(session, id=id, raise_not_found=False)
        return obj is not None

    async def search(
        self,
        session: AsyncSession,
        *,
        query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        allow_deleted: bool = False,
    ) -> List[ModelType]:
        """
        Search records across multiple fields.

        Args:
            session: Database session
            query: Search query string
            search_fields: List of field names to search in
            skip: Number of records to skip
            limit: Maximum records to return
            allow_deleted: If True, include soft-deleted records in search results

        Returns:
            List of matching records

        Example:
            # Search active records only (default):
            students = await student_crud.search(
                session,
                query="john",
                search_fields=["full_name", "email"],
                skip=0,
                limit=20
            )

            # Search including deleted records:
            all_students = await student_crud.search(
                session,
                query="john",
                search_fields=["full_name", "email"],
                skip=0,
                limit=20,
                allow_deleted=True
            )
        """
        statement = select(self.model)

        # Filter out soft-deleted records (unless allow_deleted=True)
        if hasattr(self.model, "is_deleted") and not allow_deleted:
            statement = statement.where(self.model.is_deleted == False)

        # Build OR conditions for search
        conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                conditions.append(field_attr.ilike(f"%{query}%"))

        if conditions:
            statement = statement.where(or_(*conditions))

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

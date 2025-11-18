"""Role and Permission CRUD Operations"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate, PermissionCreate

class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """CRUD operations for Role model."""

    async def get(
        self,
        session: AsyncSession,
        id: UUID,
        raise_not_found: bool = True,
    ) -> Optional[Role]:
        """
        Get role by ID with eager loading of permissions.

        Overrides base get() to include relationship loading.
        """
        statement = select(Role).where(Role.id == id).options(
            selectinload(Role.permissions)
        )
        result = await session.execute(statement)
        role = result.scalar_one_or_none()

        if role is None and raise_not_found:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(
                resource_name="Role",
                id=id,
            )

        return role

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Role]:
        """
        Get multiple roles with eager loading of permissions.

        Overrides base get_multi() to include relationship loading.
        """
        statement = select(Role).options(selectinload(Role.permissions))

        # Filter out soft-deleted records
        if hasattr(Role, "is_deleted"):
            statement = statement.where(Role.is_deleted == False)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(Role, field) and value is not None:
                    statement = statement.where(getattr(Role, field) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                # Descending order
                field = order_by[1:]
                if hasattr(Role, field):
                    statement = statement.order_by(getattr(Role, field).desc())
            else:
                # Ascending order
                if hasattr(Role, order_by):
                    statement = statement.order_by(getattr(Role, order_by))

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def search(
        self,
        session: AsyncSession,
        *,
        query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[Role]:
        """
        Search roles with eager loading of permissions.

        Overrides base search() to include relationship loading.
        """
        from sqlalchemy import or_

        statement = select(Role).options(selectinload(Role.permissions))

        # Filter out soft-deleted records
        if hasattr(Role, "is_deleted"):
            statement = statement.where(Role.is_deleted == False)

        # Build OR conditions for search
        conditions = []
        for field in search_fields:
            if hasattr(Role, field):
                field_attr = getattr(Role, field)
                conditions.append(field_attr.ilike(f"%{query}%"))

        if conditions:
            statement = statement.where(or_(*conditions))

        # Apply pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionCreate]):
    """CRUD operations for Permission model."""
    pass

role_crud = CRUDRole(Role)
permission_crud = CRUDPermission(Permission)

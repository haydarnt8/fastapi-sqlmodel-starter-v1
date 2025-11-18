"""User CRUD Operations"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import DuplicateResourceError, AuthenticationError

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""

    async def get(
        self,
        session: AsyncSession,
        id: UUID,
        raise_not_found: bool = True,
        allow_deleted: bool = False,
    ) -> Optional[User]:
        """
        Get user by ID with eager loading of roles.

        Overrides base get() to include relationship loading.
        """
        statement = select(User).where(User.id == id).options(
            selectinload(User.roles)
        )

        # Filter out soft-deleted records (unless allow_deleted=True)
        if not allow_deleted:
            statement = statement.where(User.is_deleted == False)

        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if user is None and raise_not_found:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(
                resource_name="User",
                id=id,
            )

        return user

    async def get_by_email(
        self,
        session: AsyncSession,
        *,
        email: str,
    ) -> Optional[User]:
        """Get user by email address."""
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: UserCreate,
        created_by_id: Optional[UUID] = None,
    ) -> User:
        """Create new user with hashed password."""
        # Handle both dict and Pydantic schema inputs
        if isinstance(obj_in, dict):
            email = obj_in.get("email")
            password = obj_in.get("password")
            role_ids = obj_in.get("role_ids")
            user_data = {k: v for k, v in obj_in.items() if k not in {"password", "role_ids"}}
        else:
            email = obj_in.email
            password = obj_in.password
            role_ids = obj_in.role_ids
            user_data = obj_in.model_dump(exclude={"password", "role_ids"})

        # Check if email already exists
        existing = await self.get_by_email(session, email=email)
        if existing:
            raise DuplicateResourceError("User", email=email)

        # Hash password
        hashed_password = get_password_hash(password)

        # Create user
        user = User(
            **user_data,
            hashed_password=hashed_password,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Assign roles if provided (bulk operation to avoid N+1)
        if role_ids:
            from app.models.user import UserRole
            from app.models.role import Role

            # Bulk fetch all roles in one query
            roles_statement = select(Role).where(Role.id.in_(role_ids))
            roles_result = await session.execute(roles_statement)
            roles = list(roles_result.scalars().all())

            # Create UserRole assignments in bulk
            user_role_assignments = [
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    assigned_by_id=created_by_id
                )
                for role in roles
            ]
            session.add_all(user_role_assignments)
            await session.commit()

        # Reload user with eager loading of roles for proper serialization
        statement = select(User).where(User.id == user.id).options(
            selectinload(User.roles)
        )
        result = await session.execute(statement)
        user = result.scalar_one()

        return user

    async def authenticate(
        self,
        session: AsyncSession,
        *,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate user with email and password.

        Eagerly loads roles to avoid lazy loading issues during serialization.
        """
        # Query with eager loading of roles
        statement = select(User).where(User.email == email).options(
            selectinload(User.roles)
        )
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    async def update_password(
        self,
        session: AsyncSession,
        *,
        user: User,
        new_password: str,
        updated_by_id: Optional[UUID] = None,
    ) -> User:
        """
        Update user password.

        Args:
            session: Database session
            user: User object to update
            new_password: New plain text password (will be hashed)
            updated_by_id: ID of user making the change (for audit)

        Returns:
            Updated user object
        """
        from datetime import datetime, timezone

        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)
        if updated_by_id:
            user.updated_by_id = updated_by_id

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

user_crud = CRUDUser(User)

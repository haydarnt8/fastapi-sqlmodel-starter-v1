"""
Database Initialization and Seeding

This script:
1. Creates all database tables
2. Seeds initial roles and permissions
3. Creates the first superuser account

Why seed data?
- New installations need default roles/permissions
- Can't use the system without at least one user
- Provides a consistent starting point
- Essential for development and testing

This runs automatically on first startup.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import get_logger
from app.models import (
    User,
    Role,
    Permission,
    PERMISSIONS,
    ROLES,
)

logger = get_logger(__name__)


async def create_permissions(session: AsyncSession) -> dict[str, Permission]:
    """
    Create all predefined permissions.

    Returns:
        dict: Mapping of permission codes to Permission objects
    """
    logger.info("Creating permissions...")
    permission_map = {}

    for perm_key, (code, name, resource, action) in PERMISSIONS.items():
        # Check if permission already exists
        result = await session.execute(
            select(Permission).where(Permission.code == code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            permission_map[code] = existing
            logger.debug(f"Permission already exists: {code}")
        else:
            # Create new permission
            permission = Permission(
                code=code,
                name=name,
                resource=resource,
                action=action,
                description=f"Allows {action} operations on {resource}",
            )
            session.add(permission)
            permission_map[code] = permission
            logger.info(f"Created permission: {code}")

    await session.commit()
    logger.info(f"Created/verified {len(permission_map)} permissions")
    return permission_map


async def create_roles(
    session: AsyncSession,
    permission_map: dict[str, Permission]
) -> dict[str, Role]:
    """
    Create predefined roles with their permissions.

    Args:
        session: Database session
        permission_map: Mapping of permission codes to Permission objects

    Returns:
        dict: Mapping of role codes to Role objects
    """
    from app.models.role import RolePermission

    logger.info("Creating roles...")
    role_map = {}

    # Define role permissions
    # Add your custom role permissions here based on your domain
    role_permissions = {
        "admin": ["*:*"],  # All permissions
        # Example custom role permissions:
        # "teacher": [
        #     "student:*",
        #     "subject:*",
        #     "grade:*",
        # ],
        # "manager": [
        #     "product:*",
        #     "order:read",
        #     "order:update",
        # ],
    }

    for role_key, (code, name, description) in ROLES.items():
        # Check if role already exists
        result = await session.execute(
            select(Role).where(Role.code == code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            role = existing
            logger.debug(f"Role already exists: {code}")
        else:
            # Create new role with hierarchy (1 = highest/strongest)
            role_priorities = {
                "admin": 1,        # Highest - full system access
                "manager": 5,      # Can manage users
                "user": 10,        # Standard users
            }
            role = Role(
                code=code,
                name=name,
                description=description,
                priority=role_priorities.get(code, 999),  # Default: weakest
            )
            session.add(role)
            await session.flush()  # Get ID assigned
            logger.info(f"Created role: {code}")

        # Assign permissions using direct junction table inserts to avoid lazy loading
        perm_codes = role_permissions.get(code, [])

        if not existing:  # New role - add all permissions
            for perm_code in perm_codes:
                if perm_code in permission_map:
                    permission = permission_map[perm_code]
                    # Insert into junction table directly
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                    session.add(role_perm)
                    logger.debug(f"Assigned permission {perm_code} to role {code}")
        else:  # Existing role - check which permissions are missing
            # Get existing permission IDs for this role
            existing_result = await session.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
            )
            existing_perm_ids = {row[0] for row in existing_result.all()}

            for perm_code in perm_codes:
                if perm_code in permission_map:
                    permission = permission_map[perm_code]
                    if permission.id not in existing_perm_ids:
                        # Insert into junction table directly
                        role_perm = RolePermission(
                            role_id=role.id,
                            permission_id=permission.id
                        )
                        session.add(role_perm)
                        logger.debug(f"Assigned permission {perm_code} to role {code}")

        role_map[code] = role

    await session.commit()
    logger.info(f"Created/verified {len(role_map)} roles")
    return role_map


async def create_superuser(
    session: AsyncSession,
    role_map: dict[str, Role]
) -> User:
    """
    Create the first superuser account.

    This account has full system access and can create other users.

    Args:
        session: Database session
        role_map: Mapping of role codes to Role objects

    Returns:
        User: The created/existing superuser
    """
    from app.models.user import UserRole

    logger.info("Creating superuser...")

    # Check if superuser already exists
    result = await session.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.info(f"Superuser already exists: {settings.FIRST_SUPERUSER_EMAIL}")
        return existing_user

    # Create superuser
    user = User(
        email=settings.FIRST_SUPERUSER_EMAIL,
        hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
        full_name=settings.FIRST_SUPERUSER_FULLNAME,
        is_active=True,
        is_verified=True,
    )

    session.add(user)
    await session.flush()  # Get ID assigned

    # Assign admin role using direct junction table insert
    if "admin" in role_map:
        admin_role = role_map["admin"]
        user_role = UserRole(
            user_id=user.id,
            role_id=admin_role.id
        )
        session.add(user_role)
        logger.info("Assigned admin role to superuser")

    await session.commit()
    await session.refresh(user)

    logger.info(f"✓ Created superuser: {user.email}")
    logger.warning("⚠️  CHANGE THE SUPERUSER PASSWORD IN PRODUCTION! ⚠️")
    logger.warning("⚠️  Password is set from FIRST_SUPERUSER_PASSWORD environment variable")

    return user


async def init_db_data(session: AsyncSession) -> None:
    """
    Initialize database with seed data.

    This is the main function called on startup.

    Steps:
    1. Create all permissions
    2. Create all roles and assign permissions
    3. Create first superuser account

    Args:
        session: Database session
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting database initialization...")
        logger.info("=" * 60)

        # Create permissions
        permission_map = await create_permissions(session)

        # Create roles with permissions
        role_map = await create_roles(session, permission_map)

        # Create superuser
        await create_superuser(session, role_map)

        logger.info("=" * 60)
        logger.info("Database initialization completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Login credentials:")
        logger.info(f"  Email: {settings.FIRST_SUPERUSER_EMAIL}")
        logger.info(f"  Password: {settings.FIRST_SUPERUSER_PASSWORD}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        await session.rollback()
        raise


# Example of creating sample data (for development/testing)
async def create_sample_data(session: AsyncSession) -> None:
    """
    Create sample data for development/testing.

    This is optional and should NOT be called in production.

    Add your custom sample data creation logic here based on your domain.

    Usage:
        from app.db.init_db import create_sample_data
        from app.db.session import get_db_session

        session = await get_db_session()
        await create_sample_data(session)
        await session.close()

    Example:
        # Create sample products
        product = Product(
            name="Sample Product",
            price=99.99,
            description="A sample product",
        )
        session.add(product)
        await session.commit()
    """
    logger.info("Creating sample data...")

    # Add your custom sample data creation logic here
    # Example:
    # from app.models import Product
    # product = Product(name="Sample", price=99.99)
    # session.add(product)
    # await session.commit()

    logger.info("Sample data creation completed")

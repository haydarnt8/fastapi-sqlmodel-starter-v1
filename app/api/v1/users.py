"""
User Management Endpoints

Admin-only endpoints for managing users.

Permission Requirements:
- List/Read: "user:read" or "user:*"
- Create: "user:create" or "user:*"
- Update: "user:update" or "user:*"
- Delete: "user:delete" or "user:*"
- Assign Roles: "role:assign"

Roles with access:
- Admin: Full access (has "*:*")
- Others: No access by default
"""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import (
    PermissionChecker,
    get_current_active_user,
    get_current_superuser,
    get_current_user,
    get_pagination_params,
    get_sort_params,
)
from app.crud.user import user_crud
from app.db.session import get_session
from app.models import User
from app.models.user import UserRole
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_user_action, log_role_action
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserRead,
    UserList,
    UserRoleAssignment,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    SortParams,
    MessageResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user account. Requires 'user:create' permission (Admin only).",
)
async def create_user(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("user:create")),
) -> UserRead:
    """
    Create a new user (Admin only).

    Permission required: user:create

    Request Body:
    - email: User's email address (unique)
    - password: User's password (min 8 chars)
    - full_name: User's full name
    - phone: User's phone number
    - is_active: Whether user account is active
    - role_ids: List of role IDs to assign

    Returns:
    - Created user record with roles
    """
    user = await user_crud.create(
        session,
        obj_in=user_data,
        created_by_id=current_user.id,
    )

    # Audit: User creation
    await log_user_action(
        session=session,
        action=AuditAction.USER_CREATE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_user_id=user.id,
        target_user_email=user.email,
        changes={"email": user.email, "full_name": user.full_name, "is_active": user.is_active},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return user


@router.get(
    "",
    response_model=PaginatedResponse[UserList],
    summary="List all users",
    description="Get paginated list of users. Requires 'user:read' permission (Admin only).",
)
async def list_users(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    current_user: User = Depends(PermissionChecker("user:read")),
    search: str = Query(None, description="Search in name or email"),
    is_active: bool = Query(None, description="Filter by active status"),
    allow_deleted: bool = Query(False, description="Include soft-deleted users in results"),
) -> PaginatedResponse[UserList]:
    """
    List users with pagination, sorting, and filtering.

    Permission required: user:read

    Query Parameters:
    - skip_count: Number of records to skip (default: 0)
    - max_count: Maximum records to return (default: 20, max: 100)
    - sort_by: Field to sort by (default: created_at)
    - sort_order: Sort order asc/desc (default: asc)
    - search: Search term for name or email
    - is_active: Filter by active status
    - allow_deleted: Include soft-deleted users (default: false)

    Returns:
    - Paginated list of users
    """
    # Build filters
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active

    # Prepare order_by parameter (add - prefix for descending)
    order_by = f"-{sort.sort_by}" if sort.sort_order == "desc" else sort.sort_by

    # Get users
    if search:
        users = await user_crud.search(
            session,
            query=search,
            search_fields=["full_name", "email"],
            skip=pagination.skip,
            limit=pagination.limit,
            allow_deleted=allow_deleted,
        )
    else:
        users = await user_crud.get_multi(
            session,
            skip=pagination.skip,
            limit=pagination.limit,
            filters=filters,
            order_by=order_by,
            allow_deleted=allow_deleted,
        )

    # Count total
    total = await user_crud.count(session, filters=filters)

    return PaginatedResponse(
        items=users,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        page=pagination.skip // pagination.limit + 1,
        pages=(total + pagination.limit - 1) // pagination.limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID",
    description="Get specific user details. Requires 'user:read' permission.",
)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("user:read")),
) -> UserRead:
    """
    Get user by ID.

    Permission required: user:read

    Path Parameters:
    - user_id: User ID

    Returns:
    - User details with roles
    """
    user = await user_crud.get(session, id=user_id)
    return user


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user",
    description="Update user information. Users can update their own profile. Updating other users requires 'user:update' permission.",
)
async def update_user(
    request: Request,
    user_id: UUID,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Update user information.

    Permission required: user:update (or updating own profile)

    Path Parameters:
    - user_id: User ID

    Request Body:
    - email: New email (optional)
    - full_name: New full name (optional)
    - phone: New phone (optional)
    - is_active: Active status (optional)
    - avatar_url: Avatar URL (optional)

    Returns:
    - Updated user record
    """
    user = await user_crud.get(session, id=user_id)

    # Check permission: users can update their own profile OR have user:update permission
    if current_user.id != user_id:
        # Updating another user's profile - check permission
        if not current_user.has_permission("user:update"):
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError("You don't have permission to update other users")

    # Track changes for audit
    changes = {}
    if user_data.email and user_data.email != user.email:
        changes["email"] = {"old": user.email, "new": user_data.email}
    if user_data.full_name and user_data.full_name != user.full_name:
        changes["full_name"] = {"old": user.full_name, "new": user_data.full_name}
    if user_data.is_active is not None and user_data.is_active != user.is_active:
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}

    user = await user_crud.update(
        session,
        db_obj=user,
        obj_in=user_data,
        updated_by_id=current_user.id,
    )

    # Audit: User update
    await log_user_action(
        session=session,
        action=AuditAction.USER_UPDATE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_user_id=user.id,
        target_user_email=user.email,
        changes=changes if changes else None,
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return user


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user",
    description="Delete a user account. Requires 'user:delete' permission (Admin only).",
)
async def delete_user(
    request: Request,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("user:delete")),
) -> MessageResponse:
    """
    Delete user account (soft delete).

    Permission required: user:delete

    Path Parameters:
    - user_id: User ID

    Returns:
    - Success message

    Note: This performs a soft delete. User is marked as deleted
    but not removed from database.
    """
    # Get user before deletion for audit log
    user = await user_crud.get(session, id=user_id)

    await user_crud.delete(
        session,
        id=user_id,
        deleted_by_id=current_user.id,
    )

    # Audit: User deletion
    await log_user_action(
        session=session,
        action=AuditAction.USER_DELETE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_user_id=user.id,
        target_user_email=user.email,
        changes=None,
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message=f"User {user_id} deleted successfully")


@router.post(
    "/{user_id}/restore",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Restore deleted user",
    description="Restore a soft-deleted user. Requires 'user:delete' permission (Admin only).",
)
async def restore_user(
    request: Request,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("user:delete")),
) -> UserRead:
    """
    Restore a soft-deleted user.

    Permission required: user:delete (same as delete)

    Path Parameters:
    - user_id: User ID to restore

    Returns:
    - Restored user record

    Raises:
    - 404: User not found
    - 403: Permission denied
    - 400: User is not deleted
    """
    # Restore the user
    restored_user = await user_crud.restore(
        session,
        id=user_id,
        restored_by_id=current_user.id,
    )

    if restored_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Audit: User restoration
    await log_user_action(
        session=session,
        action=AuditAction.USER_UPDATE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_user_id=restored_user.id,
        target_user_email=restored_user.email,
        changes={"is_deleted": False},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return UserRead.model_validate(restored_user)


@router.post(
    "/{user_id}/roles",
    response_model=UserRead,
    summary="Assign roles to user",
    description="Assign or update user roles. Requires 'role:assign' permission (Admin only).",
)
async def assign_user_roles(
    request: Request,
    user_id: UUID,
    role_assignment: UserRoleAssignment,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:assign")),
) -> UserRead:
    """
    Assign roles to user.

    Permission required: role:assign

    Path Parameters:
    - user_id: User ID

    Request Body:
    - role_ids: List of role IDs to assign
    - replace: If true, replace all roles. If false, add to existing roles.

    Returns:
    - Updated user record with new roles
    """
    from app.crud.role import role_crud

    # Get user
    user = await user_crud.get(session, id=user_id)

    # If replace, remove all existing roles
    if role_assignment.replace:
        # Delete existing role assignments
        result = await session.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        existing_assignments = result.scalars().all()
        for assignment in existing_assignments:
            await session.delete(assignment)
        await session.flush()

    # Bulk fetch all requested roles to validate they exist (avoid N+1)
    from app.models.role import Role
    roles_statement = select(Role).where(Role.id.in_(role_assignment.role_ids))
    roles_result = await session.execute(roles_statement)
    roles = {role.id: role for role in roles_result.scalars().all()}

    # Validate all roles exist
    for role_id in role_assignment.role_ids:
        if role_id not in roles:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(resource_name="Role", id=role_id)

    # If not replacing, bulk fetch existing assignments to check duplicates (avoid N+1)
    existing_role_ids = set()
    if not role_assignment.replace:
        existing_result = await session.execute(
            select(UserRole.role_id).where(
                UserRole.user_id == user_id,
                UserRole.role_id.in_(role_assignment.role_ids)
            )
        )
        existing_role_ids = {row[0] for row in existing_result.all()}

    # Bulk create new role assignments
    new_assignments = [
        UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by_id=current_user.id,
        )
        for role_id in role_assignment.role_ids
        if role_id not in existing_role_ids
    ]
    session.add_all(new_assignments)

    await session.commit()

    # Audit: Role assignment (log each role assignment)
    role_names = [roles[role_id].code for role_id in role_assignment.role_ids]
    await log_user_action(
        session=session,
        action=AuditAction.ROLE_ASSIGN,
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_user_id=user.id,
        target_user_email=user.email,
        changes={"roles": role_names, "replace": role_assignment.replace},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    # Reload user with roles
    user = await user_crud.get(session, id=user_id)
    return user

"""
Role Management Endpoints

Admin-only endpoints for managing roles and permissions.

Permission Requirements:
- List/Read: "role:read" or "role:*"
- Create: "role:create" or "role:*"
- Update: "role:update" or "role:*"
- Delete: "role:delete" or "role:*"

Roles with access:
- Admin: Full access (has "*:*")
- Others: Read-only access to view roles
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
    get_pagination_params,
    get_sort_params,
)
from app.crud.role import role_crud
from app.db.session import get_session
from app.models import User, Role, Permission
from app.models.role import RolePermission
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_role_action
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleRead,
    RoleList,
    PermissionRead,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    SortParams,
    MessageResponse,
)

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


# ==================== ROLE ENDPOINTS ====================

@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="Create a new role. Requires 'role:create' permission (Admin only).",
)
async def create_role(
    request: Request,
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:create")),
) -> RoleRead:
    """
    Create a new role (Admin only).

    Permission required: role:create

    Request Body:
    - code: Unique role code (e.g., "manager", "supervisor")
    - name: Human-readable role name
    - description: Role description
    - is_active: Whether role is active
    - priority: Role priority (higher = more permissions)

    Returns:
    - Created role record
    """
    from sqlalchemy.exc import IntegrityError
    from fastapi import HTTPException

    try:
        role = await role_crud.create(
            session,
            obj_in=role_data,
            created_by_id=current_user.id,
        )

        # Audit: Role creation
        await log_role_action(
            session=session,
            action=AuditAction.ROLE_CREATE,
            actor_id=current_user.id,
            actor_email=current_user.email,
            role_id=role.id,
            role_code=role.code,
            changes={"name": role.name, "priority": role.priority},
            status=AuditStatus.SUCCESS,
            request=request,
        )

        return role
    except IntegrityError as e:
        await session.rollback()
        # Check if it's a duplicate code error
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with code '{role_data.code}' already exists"
            )
        # Re-raise other integrity errors
        raise


@router.get(
    "",
    response_model=PaginatedResponse[RoleList],
    summary="List all roles",
    description="Get paginated list of roles. Anyone can view roles.",
)
async def list_roles(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    current_user: User = Depends(get_current_active_user),
    search: str = Query(None, description="Search in role name or code"),
) -> PaginatedResponse[RoleList]:
    """
    List roles with pagination, sorting, and filtering.

    Query Parameters:
    - skip_count: Number of records to skip (default: 0)
    - max_count: Maximum records to return (default: 20, max: 100)
    - sort_by: Field to sort by (default: created_at)
    - sort_order: Sort order asc/desc (default: asc)
    - search: Search term for name or code

    Returns:
    - Paginated list of roles
    """
    # Build filters
    filters = {}

    # Prepare order_by parameter (add - prefix for descending)
    order_by = f"-{sort.sort_by}" if sort.sort_order == "desc" else sort.sort_by

    # Get roles
    if search:
        roles = await role_crud.search(
            session,
            query=search,
            search_fields=["name", "code"],
            skip=pagination.skip,
            limit=pagination.limit,
        )
    else:
        roles = await role_crud.get_multi(
            session,
            skip=pagination.skip,
            limit=pagination.limit,
            filters=filters,
            order_by=order_by,
        )

    # Count total
    total = await role_crud.count(session, filters=filters)

    # Transform roles to RoleList schema
    role_list_items = [
        RoleList(
            id=role.id,
            code=role.code,
            name=role.name,
            priority=role.priority,
        )
        for role in roles
    ]

    return PaginatedResponse(
        items=role_list_items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        page=pagination.skip // pagination.limit + 1,
        pages=(total + pagination.limit - 1) // pagination.limit,
    )


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    summary="Get role by ID",
    description="Get specific role details with permissions.",
)
async def get_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> RoleRead:
    """
    Get role by ID with permissions.

    Path Parameters:
    - role_id: Role ID

    Returns:
    - Role details with all assigned permissions
    """
    # Get role with permissions eagerly loaded
    statement = select(Role).where(Role.id == role_id).options(
        selectinload(Role.permissions)
    )
    result = await session.execute(statement)
    role = result.scalar_one_or_none()

    if not role:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(resource_name="Role", id=role_id)

    return role


@router.put(
    "/{role_id}",
    response_model=RoleRead,
    summary="Update role",
    description="Update role information. Requires 'role:update' permission.",
)
async def update_role(
    request: Request,
    role_id: UUID,
    role_data: RoleUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:update")),
) -> RoleRead:
    """
    Update role information.

    Permission required: role:update

    Path Parameters:
    - role_id: Role ID

    Request Body:
    - name: New role name (optional)
    - description: New description (optional)
    - is_active: Active status (optional)
    - priority: New priority (optional)

    Returns:
    - Updated role record
    """
    role = await role_crud.get(session, id=role_id)

    # Track changes for audit
    changes = {}
    if role_data.name and role_data.name != role.name:
        changes["name"] = {"old": role.name, "new": role_data.name}
    if role_data.priority is not None and role_data.priority != role.priority:
        changes["priority"] = {"old": role.priority, "new": role_data.priority}

    role = await role_crud.update(
        session,
        db_obj=role,
        obj_in=role_data,
        updated_by_id=current_user.id,
    )

    # Audit: Role update
    await log_role_action(
        session=session,
        action=AuditAction.ROLE_UPDATE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        role_id=role.id,
        role_code=role.code,
        changes=changes if changes else None,
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return role


@router.delete(
    "/{role_id}",
    response_model=MessageResponse,
    summary="Delete role",
    description="Delete a role. Requires 'role:delete' permission (Admin only).",
)
async def delete_role(
    request: Request,
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:delete")),
) -> MessageResponse:
    """
    Delete role.

    Permission required: role:delete

    Path Parameters:
    - role_id: Role ID

    Returns:
    - Success message

    Note: Cannot delete system roles (admin, teacher, assistant, student)
    """
    role = await role_crud.get(session, id=role_id)

    # Prevent deletion of system roles
    system_roles = ["admin", "teacher", "assistant", "student"]
    if role.code in system_roles:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete system role: {role.code}"
        )

    await role_crud.delete(
        session,
        id=role_id,
        deleted_by_id=current_user.id,
    )

    # Audit: Role deletion
    await log_role_action(
        session=session,
        action=AuditAction.ROLE_DELETE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        role_id=role.id,
        role_code=role.code,
        changes=None,
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message=f"Role {role.code} deleted successfully")


@router.post(
    "/{role_id}/restore",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Restore deleted role",
    description="Restore a soft-deleted role. Requires 'role:delete' permission (Admin only).",
)
async def restore_role(
    request: Request,
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:delete")),
) -> RoleRead:
    """
    Restore a soft-deleted role.

    Permission required: role:delete (same as delete)

    Path Parameters:
    - role_id: Role ID to restore

    Returns:
    - Restored role record

    Raises:
    - 404: Role not found
    - 403: Permission denied
    - 400: Role is not deleted
    """
    # Restore the role
    restored_role = await role_crud.restore(
        session,
        id=role_id,
        restored_by_id=current_user.id,
    )

    if restored_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found",
        )

    # Audit: Role restoration
    await log_role_action(
        session=session,
        action=AuditAction.ROLE_UPDATE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        role_id=restored_role.id,
        role_code=restored_role.code,
        changes={"is_deleted": False},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return RoleRead.model_validate(restored_role)


# ==================== PERMISSION ENDPOINTS ====================

@router.get(
    "/{role_id}/permissions",
    response_model=List[PermissionRead],
    summary="Get role permissions",
    description="Get all permissions assigned to a role.",
)
async def get_role_permissions(
    role_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> List[PermissionRead]:
    """
    Get all permissions for a specific role.

    Path Parameters:
    - role_id: Role ID

    Returns:
    - List of permissions assigned to the role
    """
    # Get role with permissions
    statement = select(Role).where(Role.id == role_id).options(
        selectinload(Role.permissions)
    )
    result = await session.execute(statement)
    role = result.scalar_one_or_none()

    if not role:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(resource_name="Role", id=role_id)

    return role.permissions


@router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleRead,
    summary="Add permission to role",
    description="Add a permission to a role. Requires 'role:update' permission.",
)
async def add_permission_to_role(
    request: Request,
    role_id: UUID,
    permission_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:update")),
) -> RoleRead:
    """
    Add a permission to a role.

    Permission required: role:update

    Path Parameters:
    - role_id: Role ID
    - permission_id: Permission ID

    Returns:
    - Updated role with permissions
    """
    # Check if role exists
    role = await role_crud.get(session, id=role_id)

    # Check if permission exists
    permission_result = await session.execute(
        select(Permission).where(Permission.id == permission_id)
    )
    permission = permission_result.scalar_one_or_none()
    if not permission:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(resource_name="Permission", id=permission_id)

    # Check if already assigned
    existing = await session.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
    )
    if existing.scalar_one_or_none():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission {permission.code} already assigned to role {role.code}"
        )

    # Add permission to role
    role_permission = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
        assigned_by_id=current_user.id,
    )
    session.add(role_permission)
    await session.commit()

    # Audit: Permission granted to role
    await log_role_action(
        session=session,
        action=AuditAction.PERMISSION_GRANT,
        actor_id=current_user.id,
        actor_email=current_user.email,
        role_id=role.id,
        role_code=role.code,
        changes={"permission": permission.code},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    # Reload role with permissions
    statement = select(Role).where(Role.id == role_id).options(
        selectinload(Role.permissions)
    )
    result = await session.execute(statement)
    role = result.scalar_one()

    return role


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleRead,
    summary="Remove permission from role",
    description="Remove a permission from a role. Requires 'role:update' permission.",
)
async def remove_permission_from_role(
    request: Request,
    role_id: UUID,
    permission_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("role:update")),
) -> RoleRead:
    """
    Remove a permission from a role.

    Permission required: role:update

    Path Parameters:
    - role_id: Role ID
    - permission_id: Permission ID

    Returns:
    - Updated role with permissions
    """
    # Check if role exists
    role = await role_crud.get(session, id=role_id)

    # Get permission for audit log
    permission_result = await session.execute(
        select(Permission).where(Permission.id == permission_id)
    )
    permission = permission_result.scalar_one_or_none()

    # Find and delete the assignment
    result = await session.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
    )
    role_permission = result.scalar_one_or_none()

    if not role_permission:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission not assigned to this role"
        )

    await session.delete(role_permission)
    await session.commit()

    # Audit: Permission revoked from role
    await log_role_action(
        session=session,
        action=AuditAction.PERMISSION_REVOKE,
        actor_id=current_user.id,
        actor_email=current_user.email,
        role_id=role.id,
        role_code=role.code,
        changes={"permission": permission.code if permission else str(permission_id)},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    # Reload role with permissions
    statement = select(Role).where(Role.id == role_id).options(
        selectinload(Role.permissions)
    )
    result = await session.execute(statement)
    role = result.scalar_one()

    return role


@router.get(
    "/permissions/all",
    response_model=List[PermissionRead],
    summary="List all permissions",
    description="Get list of all available permissions in the system.",
)
async def list_all_permissions(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> List[PermissionRead]:
    """
    List all available permissions.

    Returns:
    - List of all permissions in the system
    """
    result = await session.execute(
        select(Permission).order_by(Permission.resource, Permission.action)
    )
    permissions = result.scalars().all()
    return list(permissions)

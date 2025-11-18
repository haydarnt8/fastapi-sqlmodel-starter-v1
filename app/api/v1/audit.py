"""
Audit Log Query Endpoints

Admin-only endpoints for querying and analyzing audit logs.

Permission Requirements:
- All endpoints: "audit:read" or "audit:*" or "*:*" (Admin only)

Roles with access:
- Admin: Full access (has "*:*")

Security Considerations:
- Audit logs contain sensitive information about system activity
- Only administrators should have access to audit logs
- Audit logs should never be modified or deleted via API
- Rate limiting should be applied to prevent abuse
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.api.deps import PermissionChecker, get_pagination_params
from app.db.session import get_session
from app.models import User
from app.models.audit_log import AuditLog, AuditAction, AuditStatus
from app.schemas.audit import AuditLogRead, AuditLogList, AuditLogStats
from app.schemas.common import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


# ==================== AUDIT LOG QUERY ENDPOINTS ====================

@router.get(
    "/logs",
    response_model=PaginatedResponse[AuditLogList],
    summary="Query audit logs",
    description="Query audit logs with filtering and pagination. Requires 'audit:read' permission (Admin only).",
)
async def query_audit_logs(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(PermissionChecker("audit:read")),
    # Filter parameters
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    action: Optional[str] = Query(None, description="Filter by exact action"),
    action_prefix: Optional[str] = Query(None, description="Filter by action prefix (e.g., 'auth', 'user')"),
    status: Optional[str] = Query(None, description="Filter by status (success/failure/error)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    user_email: Optional[str] = Query(None, description="Filter by user email (partial match)"),
    request_id: Optional[str] = Query(None, description="Filter by request ID"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
) -> PaginatedResponse[AuditLogList]:
    """
    Query audit logs with comprehensive filtering.

    Permission required: audit:read

    Query Parameters:
    - skip_count: Number of records to skip (default: 0)
    - max_count: Maximum records to return (default: 20, max: 100)
    - start_date: Filter logs after this date
    - end_date: Filter logs before this date
    - action: Filter by exact action (e.g., "auth.login.success")
    - action_prefix: Filter by action prefix (e.g., "auth", "user", "role")
    - status: Filter by status (success/failure/error)
    - resource_type: Filter by resource type
    - resource_id: Filter by resource ID
    - user_id: Filter by user ID
    - user_email: Filter by user email (partial match)
    - request_id: Filter by request ID
    - ip_address: Filter by IP address

    Returns:
    - Paginated list of audit logs

    Examples:
    - GET /api/v1/audit/logs?action_prefix=auth&status=failure
    - GET /api/v1/audit/logs?user_email=admin&start_date=2025-01-01
    - GET /api/v1/audit/logs?request_id=abc-123-def
    """
    # Build filters
    filters = []

    if start_date:
        filters.append(AuditLog.timestamp >= start_date)
    if end_date:
        filters.append(AuditLog.timestamp <= end_date)
    if action:
        filters.append(AuditLog.action == action)
    if action_prefix:
        filters.append(AuditLog.action.startswith(action_prefix))
    if status:
        filters.append(AuditLog.status == status)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if resource_id:
        filters.append(AuditLog.resource_id == resource_id)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if user_email:
        filters.append(AuditLog.user_email.contains(user_email))
    if request_id:
        filters.append(AuditLog.request_id == request_id)
    if ip_address:
        filters.append(AuditLog.ip_address == ip_address)

    # Build query
    statement = select(AuditLog)
    if filters:
        statement = statement.where(and_(*filters))

    # Order by timestamp descending (most recent first)
    statement = statement.order_by(AuditLog.timestamp.desc())

    # Apply pagination
    statement = statement.offset(pagination.skip).limit(pagination.limit)

    # Execute query
    result = await session.execute(statement)
    logs = result.scalars().all()

    # Count total
    count_statement = select(func.count()).select_from(AuditLog)
    if filters:
        count_statement = count_statement.where(and_(*filters))
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Transform to AuditLogList schema
    log_list_items = [
        AuditLogList(
            id=log.id,
            timestamp=log.timestamp,
            user_email=log.user_email,
            action=log.action,
            status=log.status,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
        )
        for log in logs
    ]

    return PaginatedResponse(
        items=log_list_items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        page=pagination.skip // pagination.limit + 1,
        pages=(total + pagination.limit - 1) // pagination.limit,
    )


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogRead,
    summary="Get audit log by ID",
    description="Get detailed audit log entry. Requires 'audit:read' permission (Admin only).",
)
async def get_audit_log(
    log_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("audit:read")),
) -> AuditLogRead:
    """
    Get detailed audit log entry by ID.

    Permission required: audit:read

    Path Parameters:
    - log_id: Audit log ID

    Returns:
    - Full audit log entry with all details including changes, error messages, and request metadata
    """
    statement = select(AuditLog).where(AuditLog.id == log_id)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if not log:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(resource_name="AuditLog", id=log_id)

    return log


@router.get(
    "/stats",
    response_model=AuditLogStats,
    summary="Get audit log statistics",
    description="Get statistics about audit logs. Requires 'audit:read' permission (Admin only).",
)
async def get_audit_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("audit:read")),
    start_date: Optional[datetime] = Query(None, description="Stats from this date"),
    end_date: Optional[datetime] = Query(None, description="Stats until this date"),
) -> AuditLogStats:
    """
    Get aggregate statistics about audit logs.

    Permission required: audit:read

    Query Parameters:
    - start_date: Calculate stats from this date (optional)
    - end_date: Calculate stats until this date (optional)

    Returns:
    - Statistics including:
      - Total log count
      - Count by status (success/failure/error)
      - Count by action type
      - Count by resource type
      - Failed login attempts
      - Recent activity summary
    """
    # Build base filter for date range
    filters = []
    if start_date:
        filters.append(AuditLog.timestamp >= start_date)
    if end_date:
        filters.append(AuditLog.timestamp <= end_date)

    # Total count
    total_statement = select(func.count()).select_from(AuditLog)
    if filters:
        total_statement = total_statement.where(and_(*filters))
    total_result = await session.execute(total_statement)
    total_logs = total_result.scalar()

    # Count by status
    status_statement = select(
        AuditLog.status,
        func.count(AuditLog.id).label("count")
    ).group_by(AuditLog.status)
    if filters:
        status_statement = status_statement.where(and_(*filters))
    status_result = await session.execute(status_statement)
    status_counts = {row.status: row.count for row in status_result}

    # Count by action (top 10)
    action_statement = select(
        AuditLog.action,
        func.count(AuditLog.id).label("count")
    ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10)
    if filters:
        action_statement = action_statement.where(and_(*filters))
    action_result = await session.execute(action_statement)
    action_counts = {row.action: row.count for row in action_result}

    # Count by resource type
    resource_statement = select(
        AuditLog.resource_type,
        func.count(AuditLog.id).label("count")
    ).group_by(AuditLog.resource_type)
    if filters:
        resource_statement = resource_statement.where(and_(*filters))
    resource_result = await session.execute(resource_statement)
    resource_counts = {row.resource_type: row.count for row in resource_result}

    # Failed login attempts
    failed_login_filters = [AuditLog.action == AuditAction.LOGIN_FAILURE]
    if filters:
        failed_login_filters.extend(filters)
    failed_login_statement = select(func.count()).select_from(AuditLog).where(
        and_(*failed_login_filters)
    )
    failed_login_result = await session.execute(failed_login_statement)
    failed_logins = failed_login_result.scalar()

    # Unique users who performed actions
    unique_users_statement = select(func.count(func.distinct(AuditLog.user_id))).select_from(AuditLog)
    if filters:
        unique_users_statement = unique_users_statement.where(and_(*filters))
    unique_users_result = await session.execute(unique_users_statement)
    unique_users = unique_users_result.scalar()

    return AuditLogStats(
        total_logs=total_logs,
        status_counts=status_counts,
        action_counts=action_counts,
        resource_counts=resource_counts,
        failed_logins=failed_logins,
        unique_users=unique_users,
    )


@router.get(
    "/actions",
    response_model=List[str],
    summary="List all action types",
    description="Get list of all unique action types in audit logs. Requires 'audit:read' permission.",
)
async def list_action_types(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("audit:read")),
) -> List[str]:
    """
    Get list of all unique action types that exist in audit logs.

    Permission required: audit:read

    Returns:
    - List of unique action strings (e.g., ["auth.login.success", "user.create", ...])

    This is useful for building filters or understanding what actions are being logged.
    """
    statement = select(AuditLog.action).distinct().order_by(AuditLog.action)
    result = await session.execute(statement)
    actions = [row[0] for row in result.all()]
    return actions


@router.get(
    "/user/{user_id}/activity",
    response_model=PaginatedResponse[AuditLogList],
    summary="Get user activity history",
    description="Get all audit logs for a specific user. Requires 'audit:read' permission.",
)
async def get_user_activity(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(PermissionChecker("audit:read")),
    start_date: Optional[datetime] = Query(None, description="Activity from this date"),
    end_date: Optional[datetime] = Query(None, description="Activity until this date"),
) -> PaginatedResponse[AuditLogList]:
    """
    Get activity history for a specific user.

    Permission required: audit:read

    Path Parameters:
    - user_id: User ID to query activity for

    Query Parameters:
    - skip_count: Number of records to skip (default: 0)
    - max_count: Maximum records to return (default: 20, max: 100)
    - start_date: Activity from this date (optional)
    - end_date: Activity until this date (optional)

    Returns:
    - Paginated list of all actions performed by the user
    """
    # Build filters
    filters = [AuditLog.user_id == user_id]
    if start_date:
        filters.append(AuditLog.timestamp >= start_date)
    if end_date:
        filters.append(AuditLog.timestamp <= end_date)

    # Build query
    statement = select(AuditLog).where(and_(*filters)).order_by(AuditLog.timestamp.desc())
    statement = statement.offset(pagination.skip).limit(pagination.limit)

    # Execute query
    result = await session.execute(statement)
    logs = result.scalars().all()

    # Count total
    count_statement = select(func.count()).select_from(AuditLog).where(and_(*filters))
    count_result = await session.execute(count_statement)
    total = count_result.scalar()

    # Transform to AuditLogList schema
    log_list_items = [
        AuditLogList(
            id=log.id,
            timestamp=log.timestamp,
            user_email=log.user_email,
            action=log.action,
            status=log.status,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
        )
        for log in logs
    ]

    return PaginatedResponse(
        items=log_list_items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        page=pagination.skip // pagination.limit + 1,
        pages=(total + pagination.limit - 1) // pagination.limit,
    )

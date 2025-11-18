"""
Audit Logging Service

Provides easy-to-use functions and decorators for logging audit events.

Usage:
    from app.core.audit import audit_log, create_audit_log

    # Direct logging
    await create_audit_log(
        session=session,
        action="user.create",
        user_id=current_user.id,
        resource_type="user",
        resource_id=str(new_user.id),
        changes={"email": new_user.email}
    )

    # With decorator
    @audit_log(action="user.delete", resource_type="user")
    async def delete_user(user_id: UUID, ...):
        ...

Design principles:
- Async: Non-blocking audit logging
- Background tasks: Don't slow down requests
- Fail-safe: Audit failures don't break the application
- Contextual: Automatically captures request metadata
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from uuid import UUID
from functools import wraps

from fastapi import Request, BackgroundTasks
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.audit_log import AuditLog, AuditStatus

logger = logging.getLogger(__name__)


async def create_audit_log(
    session: AsyncSession,
    action: str,
    status: str = AuditStatus.SUCCESS,
    resource_type: str = "unknown",
    resource_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
    user_email: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Create an audit log entry.

    Args:
        session: Database session
        action: Action performed (e.g., "user.create")
        status: Result status (success/failure/error)
        resource_type: Type of resource affected
        resource_id: ID of affected resource
        user_id: ID of user who performed action
        user_email: Email of user (for easier queries)
        changes: Before/after state or additional context
        error_message: Error message if applicable
        request_id: X-Request-ID for correlation
        ip_address: Client IP address
        user_agent: User agent string

    Returns:
        Created AuditLog instance, or None if creation failed
    """
    try:
        audit_entry = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            error_message=error_message,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        session.add(audit_entry)

        # Use flush instead of commit to avoid double-commit issues
        # The endpoint will handle the final commit
        try:
            await session.flush()
        except Exception:
            # If session is already committed/closed, try commit instead
            await session.commit()

        await session.refresh(audit_entry)

        logger.debug(
            f"Audit log created: {action} by user {user_email or user_id} "
            f"on {resource_type}:{resource_id} - {status}"
        )

        return audit_entry

    except Exception as e:
        logger.error(f"Failed to create audit log: {e}", exc_info=True)
        # Don't fail the main operation if audit logging fails
        try:
            await session.rollback()
        except Exception:
            pass
        return None


def extract_request_metadata(request: Request) -> Dict[str, Optional[str]]:
    """
    Extract metadata from FastAPI request.

    Args:
        request: FastAPI Request object

    Returns:
        Dictionary with request_id, ip_address, user_agent
    """
    # Get request ID from headers (set by RequestIDMiddleware)
    request_id = request.headers.get("X-Request-ID")

    # Get client IP (handle proxies)
    ip_address = request.headers.get("X-Forwarded-For")
    if ip_address:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    # Get user agent
    user_agent = request.headers.get("User-Agent")

    return {
        "request_id": request_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }


async def log_auth_event(
    session: AsyncSession,
    action: str,
    user_email: str,
    status: str = AuditStatus.SUCCESS,
    error_message: Optional[str] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Log authentication-related events.

    Uses a separate database session to ensure audit logs are committed
    even when the main endpoint raises an exception.

    Args:
        session: Database session (not used, kept for compatibility)
        action: Auth action (e.g., "auth.login.success")
        user_email: Email of user attempting auth
        status: Result status
        error_message: Error message if failed
        request: FastAPI request for metadata
    """
    from app.db.session import get_db_session

    metadata = extract_request_metadata(request) if request else {}

    # Use a separate session to ensure audit log is committed
    # even if the main endpoint raises an exception
    audit_session = await get_db_session()
    try:
        await create_audit_log(
            session=audit_session,
            action=action,
            status=status,
            resource_type="auth",
            resource_id=user_email,
            user_email=user_email,
            error_message=error_message,
            **metadata,
        )
    finally:
        await audit_session.close()


async def log_user_action(
    session: AsyncSession,
    action: str,
    actor_id: UUID,
    actor_email: str,
    target_user_id: UUID,
    target_user_email: str,
    changes: Optional[Dict[str, Any]] = None,
    status: str = AuditStatus.SUCCESS,
    error_message: Optional[str] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Log user management actions.

    Args:
        session: Database session
        action: Action (e.g., "user.create", "user.update")
        actor_id: ID of user performing the action
        actor_email: Email of actor
        target_user_id: ID of user being acted upon
        target_user_email: Email of target user
        changes: Changes made
        status: Result status
        error_message: Error message if failed
        request: FastAPI request for metadata
    """
    metadata = extract_request_metadata(request) if request else {}

    await create_audit_log(
        session=session,
        action=action,
        status=status,
        resource_type="user",
        resource_id=str(target_user_id),
        user_id=actor_id,
        user_email=actor_email,
        changes=changes,
        error_message=error_message,
        **metadata,
    )


async def log_role_action(
    session: AsyncSession,
    action: str,
    actor_id: UUID,
    actor_email: str,
    role_id: UUID,
    role_code: str,
    changes: Optional[Dict[str, Any]] = None,
    status: str = AuditStatus.SUCCESS,
    error_message: Optional[str] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Log role management actions.

    Args:
        session: Database session
        action: Action (e.g., "role.assign", "role.create")
        actor_id: ID of user performing the action
        actor_email: Email of actor
        role_id: ID of role
        role_code: Code of role
        changes: Changes made
        status: Result status
        error_message: Error message if failed
        request: FastAPI request for metadata
    """
    metadata = extract_request_metadata(request) if request else {}

    await create_audit_log(
        session=session,
        action=action,
        status=status,
        resource_type="role",
        resource_id=str(role_id),
        user_id=actor_id,
        user_email=actor_email,
        changes={**changes, "role_code": role_code} if changes else {"role_code": role_code},
        error_message=error_message,
        **metadata,
    )


async def log_access_denied(
    session: AsyncSession,
    user_id: UUID,
    user_email: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    permission_required: Optional[str] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Log unauthorized access attempts.

    Args:
        session: Database session
        user_id: ID of user who was denied
        user_email: Email of user
        resource_type: Type of resource they tried to access
        resource_id: ID of resource
        permission_required: Permission that was required
        request: FastAPI request for metadata
    """
    metadata = extract_request_metadata(request) if request else {}

    await create_audit_log(
        session=session,
        action="access.denied",
        status=AuditStatus.FAILURE,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_email=user_email,
        changes={"permission_required": permission_required} if permission_required else None,
        error_message="Insufficient permissions",
        **metadata,
    )


# Background task helper for non-blocking audit logging
def audit_in_background(
    background_tasks: BackgroundTasks,
    session_factory: Callable,
    **audit_kwargs
) -> None:
    """
    Schedule audit logging as a background task.

    This allows audit logging to happen without blocking the response.

    Args:
        background_tasks: FastAPI BackgroundTasks
        session_factory: Function that creates a database session
        **audit_kwargs: Arguments to pass to create_audit_log

    Usage:
        audit_in_background(
            background_tasks=background_tasks,
            session_factory=get_session,
            action="user.create",
            ...
        )
    """
    async def _audit_task():
        async for session in session_factory():
            await create_audit_log(session=session, **audit_kwargs)

    background_tasks.add_task(_audit_task)

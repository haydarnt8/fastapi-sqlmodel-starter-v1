"""
Audit Log Schemas

Schemas for audit log API responses and filtering.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.common import base_config


class AuditLogBase(BaseModel):
    """Base audit log fields."""

    model_config = base_config

    timestamp: datetime = Field(description="When the action occurred (UTC)")
    action: str = Field(description="Action performed (e.g., 'user.create', 'auth.login')")
    status: str = Field(description="Result status: 'success', 'failure', 'error'")
    resource_type: str = Field(description="Type of resource (e.g., 'user', 'role')")
    resource_id: Optional[str] = Field(
        default=None,
        description="ID of the affected resource",
    )
    user_email: Optional[str] = Field(
        default=None,
        description="Email of user who performed the action",
    )


class AuditLogRead(AuditLogBase):
    """Full audit log entry for reading."""

    model_config = base_config

    id: UUID
    user_id: Optional[UUID] = Field(
        default=None,
        description="User who performed the action",
    )
    changes: Optional[dict] = Field(
        default=None,
        description="Before/after state or additional details",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status is 'failure' or 'error'",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="X-Request-ID for correlation with logs",
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="Client IP address",
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="User agent string from request",
    )


class AuditLogList(AuditLogBase):
    """Simplified audit log for list endpoints."""

    model_config = base_config

    id: UUID
    ip_address: Optional[str] = Field(
        default=None,
        description="Client IP address",
    )


class AuditLogFilter(BaseModel):
    """Filter parameters for querying audit logs."""

    model_config = base_config

    # Time range
    start_date: Optional[datetime] = Field(
        default=None,
        description="Filter logs after this timestamp",
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Filter logs before this timestamp",
    )

    # Action filters
    action: Optional[str] = Field(
        default=None,
        description="Filter by specific action (e.g., 'user.create')",
    )
    action_prefix: Optional[str] = Field(
        default=None,
        description="Filter by action prefix (e.g., 'user.' for all user actions)",
    )

    # Status filter
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: 'success', 'failure', 'error'",
    )

    # Resource filters
    resource_type: Optional[str] = Field(
        default=None,
        description="Filter by resource type (e.g., 'user', 'role')",
    )
    resource_id: Optional[str] = Field(
        default=None,
        description="Filter by specific resource ID",
    )

    # User filters
    user_id: Optional[UUID] = Field(
        default=None,
        description="Filter by user who performed the action",
    )
    user_email: Optional[str] = Field(
        default=None,
        description="Filter by user email (partial match)",
    )

    # Request tracing
    request_id: Optional[str] = Field(
        default=None,
        description="Filter by request ID",
    )

    # Pagination
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
    )


class AuditLogStats(BaseModel):
    """Statistics about audit logs."""

    model_config = base_config

    total_logs: int = Field(description="Total number of audit log entries")
    status_counts: dict = Field(
        description="Count by status (success/failure/error)",
        examples=[{"success": 100, "failure": 20, "error": 5}],
    )
    action_counts: dict = Field(
        description="Count by action type (top 10)",
        examples=[{"auth.login.success": 50, "user.create": 10}],
    )
    resource_counts: dict = Field(
        description="Count by resource type",
        examples=[{"auth": 60, "user": 30, "role": 10}],
    )
    failed_logins: int = Field(description="Number of failed login attempts")
    unique_users: int = Field(description="Number of unique users who performed actions")


class AuditLogResponse(BaseModel):
    """Response wrapper for paginated audit logs."""

    model_config = base_config

    items: List[AuditLogRead] = Field(description="List of audit log entries")
    total: int = Field(description="Total number of matching records")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum records per page")
    has_more: bool = Field(description="Whether there are more records")

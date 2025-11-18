"""
Audit Log Model

Tracks all significant actions in the system for compliance, security, and debugging.

Why audit logging?
- Compliance: Meet FERPA, GDPR, and other regulatory requirements
- Security: Detect suspicious patterns and investigate incidents
- Accountability: Know who did what and when
- Debugging: Trace issues back to specific actions
- Analytics: Understand usage patterns

What gets audited?
- Authentication events (login, logout, password changes)
- User management (create, update, delete)
- Role/permission changes
- Authorization failures
- Sensitive data access
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import Index


class AuditLog(SQLModel, table=True):
    """
    Audit log for tracking user actions and system events.

    Design decisions:
    - Immutable: Audit logs are never updated or deleted (append-only)
    - Indexed: Fast queries by user, action, resource, and timestamp
    - JSON metadata: Flexible storage for before/after states
    - Request tracing: Links to request ID for full context
    """

    __tablename__ = "audit_logs"

    # Primary identification
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
        description="When the action occurred (UTC)",
    )

    # Who performed the action
    user_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        index=True,
        description="User who performed the action (None for system actions)",
    )
    user_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Email at time of action (denormalized for easier queries)",
    )

    # What action was performed
    action: str = Field(
        max_length=100,
        nullable=False,
        index=True,
        description="Action performed (e.g., 'user.create', 'auth.login', 'role.assign')",
    )
    status: str = Field(
        max_length=20,
        nullable=False,
        index=True,
        description="Result status: 'success', 'failure', 'error'",
    )

    # What resource was affected
    resource_type: str = Field(
        max_length=50,
        nullable=False,
        index=True,
        description="Type of resource (e.g., 'user', 'role', 'permission')",
    )
    resource_id: Optional[str] = Field(
        default=None,
        max_length=255,
        index=True,
        description="ID of the affected resource",
    )

    # Additional context
    changes: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Before/after state or additional details (JSON)",
    )
    error_message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Error message if status is 'failure' or 'error'",
    )

    # Request metadata
    request_id: Optional[str] = Field(
        default=None,
        max_length=36,
        index=True,
        description="X-Request-ID for correlation with logs",
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="Client IP address (IPv4 or IPv6)",
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string from request",
    )

    # Database configuration
    __table_args__ = (
        # Composite indexes for common queries
        Index("ix_audit_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_action_timestamp", "action", "timestamp"),
        Index("ix_audit_resource_timestamp", "resource_type", "resource_id", "timestamp"),
        Index("ix_audit_status_timestamp", "status", "timestamp"),
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "action": "user.create",
                "status": "success",
                "resource_type": "user",
                "resource_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_email": "admin@example.com",
                "changes": {
                    "email": "newuser@example.com",
                    "roles": ["user"],
                },
                "ip_address": "192.168.1.100",
            }
        }


# Common action constants for consistency
class AuditAction:
    """Standard audit action names."""

    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET_REQUEST = "auth.password.reset_request"
    PASSWORD_RESET_COMPLETE = "auth.password.reset_complete"

    # User management
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"

    # Role management
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"
    ROLE_REVOKE = "role.revoke"

    # Permission management
    PERMISSION_CREATE = "permission.create"
    PERMISSION_UPDATE = "permission.update"
    PERMISSION_DELETE = "permission.delete"
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"

    # Authorization
    ACCESS_DENIED = "access.denied"
    PERMISSION_CHECK = "permission.check"


# Status constants
class AuditStatus:
    """Audit log status values."""

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"

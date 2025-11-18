"""
Role and Permission Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.schemas.common import base_config
from app.core.validators import validate_permission_code, validate_role_code
from datetime import datetime

# ============= Permission Schemas =============

class PermissionBase(BaseModel):
    """Base permission fields."""

    model_config = base_config

    code: str = Field(
        description="Permission code (e.g., 'student:create')",
        examples=["student:create", "grade:update", "*:*"],
    )
    name: str = Field(
        description="Human-readable permission name",
        examples=["Create Student", "Update Grade"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description",
    )
    resource: str = Field(
        description="Resource type",
        examples=["student", "teacher", "grade"],
    )
    action: str = Field(
        description="Action type",
        examples=["create", "read", "update", "delete", "*"],
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """
        Validate permission code format using shared validator.

        Requirements (enforced by validate_permission_code):
        - Must be in format 'resource:action'
        - Supports wildcards: '*:*', 'resource:*', '*:action'
        - Both parts must be 1-50 characters
        - Only alphanumeric, underscore, hyphen, or * allowed
        """
        return validate_permission_code(v)

class PermissionCreate(PermissionBase):
    """Schema for creating a permission."""
    model_config = base_config

    pass

class PermissionRead(PermissionBase):
    """Schema for reading permission data."""

    model_config = base_config

    id: UUID
    created_at: datetime

class PermissionList(BaseModel):
    """Simplified permission for lists."""

    model_config = base_config

    id: UUID
    code: str
    name: str
    resource: str
    action: str

# ============= Role Schemas =============

class RoleBase(BaseModel):
    """Base role fields."""

    model_config = base_config

    code: str = Field(
        min_length=2,
        max_length=50,
        description="Unique role code",
        examples=["admin", "teacher", "student"],
    )
    name: str = Field(
        min_length=2,
        max_length=255,
        description="Human-readable role name",
        examples=["Administrator", "Teacher", "Student"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Role description",
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Role priority (higher = more permissions)",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """
        Validate role code format using shared validator.

        Requirements (enforced by validate_role_code):
        - 2-50 characters
        - Must start with a letter
        - Only alphanumeric, underscore, and hyphen allowed
        - No colons (reserved for permission codes)
        """
        return validate_role_code(v)

class RoleCreate(RoleBase):
    """
    Schema for creating a role.

    Optionally assign permissions during creation.
    """

    model_config = base_config

    permission_ids: Optional[List[UUID]] = Field(
        default=None,
        description="List of permission IDs to assign",
    )

class RoleUpdate(BaseModel):
    """
    Schema for updating a role.

    All fields optional (partial update).
    """

    model_config = base_config

    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=100)

class RoleRead(RoleBase):
    """Schema for reading role data with permissions."""

    model_config = base_config

    id: UUID
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionList] = Field(default_factory=list)

class RoleList(BaseModel):
    """Simplified role for lists."""

    model_config = base_config

    id: UUID
    code: str
    name: str
    priority: int

# ============= Role-Permission Management =============

class RolePermissionAssignment(BaseModel):
    """
    Assign permissions to a role.

    Can add or replace permissions.
    """

    model_config = base_config

    permission_ids: List[UUID] = Field(description="List of permission IDs")
    replace: bool = Field(
        default=False,
        description="If True, replace all permissions. If False, add to existing.",
    )

class PermissionCheck(BaseModel):
    """
    Check if user/role has a permission.

    Request schema for permission checking.
    """

    model_config = base_config

    permission_code: str = Field(
        description="Permission code to check",
        examples=["student:create"],
    )

class PermissionCheckResponse(BaseModel):
    """Response for permission check."""

    model_config = base_config

    has_permission: bool = Field(description="Whether user has the permission")
    permission_code: str = Field(description="The permission code checked")
    granted_by: Optional[str] = Field(
        default=None,
        description="Role that granted the permission",
    )

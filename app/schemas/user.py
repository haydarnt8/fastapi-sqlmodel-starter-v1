"""
User Schemas

Request/response schemas for User operations.

Why separate schemas from models?
- Models = Database structure
- Schemas = API contract
- Can expose different fields for create/read/update
- API can change without changing database
- Security: Never expose hashed_password in responses!
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.common import base_config
from app.core.validators import validate_password_strength
from datetime import datetime

# ============= Base Schemas =============

class UserBase(BaseModel):
    """Base user fields (common to all operations)."""

    model_config = base_config

    email: EmailStr = Field(
        description="User's email address",
        examples=["john.doe@example.com"],
    )
    full_name: str = Field(
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=20,
        description="User's phone number in E.164 format",
        examples=["+9647901234567"],
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Legacy phone field",
        examples=["+1234567890"],
    )
    language_preference: str = Field(
        default="ar",
        max_length=5,
        description="User's preferred language (ar, en, ku)",
        examples=["ar"],
    )
    currency: str = Field(
        default="IQD",
        max_length=3,
        description="User's preferred currency",
        examples=["IQD"],
    )

# ============= Create Schemas =============

class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Requires password.
    Optionally specify initial roles.
    """

    model_config = base_config

    password: str = Field(
        min_length=8,
        max_length=100,
        description="User's password (min 8 characters)",
        examples=["SecurePassword123!"],
    )
    is_active: bool = Field(
        default=True,
        description="Whether user account is active",
    )
    role_ids: Optional[List[UUID]] = Field(
        default=None,
        description="List of role IDs to assign to user",
        examples=[["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength using shared validator.

        Requirements (enforced by validate_password_strength):
        - At least 8 characters
        - Contains uppercase and lowercase
        - Contains at least one number
        """
        return validate_password_strength(v)

class UserRegister(BaseModel):
    """
    Schema for user self-registration.

    Simpler than UserCreate - users self-register without admin privileges.
    """

    model_config = base_config

    email: EmailStr = Field(
        description="User's email address",
        examples=["john.doe@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=100,
        description="User's password (min 8 characters)",
        examples=["SecurePassword123!"],
    )
    full_name: str = Field(
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="User's phone number",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength using shared validator."""
        return validate_password_strength(v)

# ============= Update Schemas =============

class UserUpdate(BaseModel):
    """
    Schema for updating user information.

    All fields are optional (partial update).
    """

    model_config = base_config

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    language_preference: Optional[str] = Field(default=None, max_length=5)
    currency: Optional[str] = Field(default=None, max_length=3)
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    restaurant_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None

class UserUpdatePassword(BaseModel):
    """
    Schema for changing user password.

    Requires both current and new password.
    """

    model_config = base_config

    current_password: str = Field(description="Current password")
    new_password: str = Field(
        min_length=8,
        max_length=100,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate new password strength using shared validator."""
        return validate_password_strength(v)

# ============= Read Schemas =============

class RoleInfo(BaseModel):
    """
    Minimal role information for user response.

    Prevents circular dependencies and keeps responses lean.
    """

    model_config = base_config

    id: UUID
    code: str
    name: str
    description: Optional[str] = None

class UserRead(UserBase):
    """
    Schema for reading user data.

    NOTE: Never includes hashed_password!
    """

    model_config = base_config

    id: UUID
    is_active: bool
    is_verified: bool
    phone_verified: bool = False
    avatar_url: Optional[str] = None
    restaurant_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    email_verified_at: Optional[datetime] = None
    phone_verified_at: Optional[datetime] = None
    roles: List[RoleInfo] = Field(default_factory=list)

class UserProfile(UserRead):
    """
    Extended user profile with additional information.

    Used for /me endpoint (current user's profile).
    """

    model_config = base_config

    # Can add additional fields here that shouldn't be in UserRead
    # For example: preferences, settings, etc.
    pass

class UserList(BaseModel):
    """
    Simplified user info for list endpoints.

    Less detail than UserRead for better performance.
    """

    model_config = base_config

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

# ============= Authentication Schemas =============

class Token(BaseModel):
    """
    JWT token response.

    Returned after successful login.
    """

    model_config = base_config

    access_token: str = Field(description="JWT access token", title="Access Token")
    refresh_token: str = Field(description="JWT refresh token", title="Refresh Token")
    token_type: str = Field(default="bearer", description="Token type", title="Token Type")
    expires_in: int = Field(description="Token expiration time in seconds", title="Expires In")

class TokenPayload(BaseModel):
    """
    JWT token payload (decoded).

    Contains user ID and token metadata.
    """

    model_config = base_config

    sub: str = Field(description="Subject (user ID)")
    exp: int = Field(description="Expiration timestamp")
    iat: int = Field(description="Issued at timestamp")
    type: str = Field(description="Token type: access or refresh")

class LoginRequest(BaseModel):
    """
    Login request schema.

    Email + password authentication.
    """

    model_config = base_config

    email: EmailStr = Field(description="User's email address")
    password: str = Field(description="User's password")

class LoginResponse(BaseModel):
    """
    Login response with token and user info.

    Contains everything frontend needs after login.
    """

    model_config = base_config

    access_token: str = Field(title="Access Token")
    refresh_token: str = Field(title="Refresh Token")
    token_type: str = Field(default="bearer", title="Token Type")
    expires_in: int = Field(title="Expires In")
    user: UserProfile = Field(title="User")

class RefreshTokenRequest(BaseModel):
    """
    Request to refresh access token.

    Requires valid refresh token.
    """

    model_config = base_config

    refresh_token: str = Field(description="Valid refresh token", title="Refresh Token")

# ============= Role Assignment Schemas =============

class UserRoleAssignment(BaseModel):
    """
    Assign roles to a user.

    Can add or remove roles.
    """

    model_config = base_config

    role_ids: List[UUID] = Field(description="List of role IDs to assign")
    replace: bool = Field(
        default=False,
        description="If True, replace all roles. If False, add to existing roles.",
    )

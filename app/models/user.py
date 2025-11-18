"""
User Model for Authentication

This model represents users in the system with authentication capabilities.

Why separate User from other models?
- Authentication is a cross-cutting concern
- Users need special security handling (password hashing)
- User permissions affect all other models
- Need to track who does what in the system
"""

from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel
from pydantic import EmailStr

from app.models.base import BaseModel

# Avoid circular imports
if TYPE_CHECKING:
    from app.models.role import Role
    # Add your custom model imports here if needed:
    # from app.models.product import Product


class UserRole(SQLModel, table=True):
    """
    Junction table for many-to-many relationship between Users and Roles.

    Why a junction table?
    - A user can have multiple roles (e.g., Teacher AND Administrator)
    - A role can be assigned to multiple users
    - Allows flexible permission assignment

    This is automatically managed by SQLModel's Relationship.
    """

    __tablename__ = "user_role"

    user_id: UUID = Field(
        foreign_key="user.id",
        primary_key=True,
        nullable=False,
    )
    role_id: UUID = Field(
        foreign_key="role.id",
        primary_key=True,
        nullable=False,
    )

    # Optional: Track when role was assigned
    assigned_at: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Timestamp when role was assigned to user",
    )
    assigned_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="User ID who assigned this role",
    )


class User(BaseModel, table=True):
    """
    User model for authentication and authorization.

    This is the central model for the auth system. Every user who can
    log into the system needs a User record.

    Fields:
    - email: Unique email address (used for login)
    - hashed_password: bcrypt-hashed password (NEVER store plain passwords!)
    - full_name: User's display name
    - is_active: Can this user log in?
    - roles: List of roles assigned to this user

    Security Notes:
    - Password is HASHED, never stored in plain text
    - Email is unique (can't have duplicate users)
    - is_active allows disabling accounts without deleting
    - Permissions are determined by roles with hierarchical priority

    Usage:
        # Creating a new user (in CRUD layer):
        from app.core.security import get_password_hash

        user = User(
            email="john@example.com",
            hashed_password=get_password_hash("SecurePassword123"),
            full_name="John Doe",
            is_active=True
        )
    """

    __tablename__ = "user"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Authentication Fields
    email: EmailStr = Field(
        unique=True,
        index=True,
        nullable=False,
        description="User's email address (used for login)",
        sa_column_kwargs={"unique": True},
    )
    hashed_password: str = Field(
        nullable=False,
        description="bcrypt-hashed password (never store plain passwords!)",
    )

    # Profile Fields
    full_name: str = Field(
        max_length=255,
        nullable=False,
        description="User's full name",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        description="User's phone number",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        nullable=True,
        description="URL to user's profile picture",
    )

    # Status Fields
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether this user can log in",
        sa_column_kwargs={"index": True},
    )
    is_verified: bool = Field(
        default=False,
        nullable=False,
        description="Whether user's email has been verified",
    )

    # Optional: Password reset
    reset_token: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Token for password reset (temporary)",
    )
    reset_token_expires: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Timestamp when reset token expires",
    )

    # Relationships
    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,  # Many-to-many through UserRole table
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserRole.user_id",
            "secondaryjoin": "Role.id==UserRole.role_id",
            "lazy": "selectin",  # Always eager-load to avoid MissingGreenlet in async
        }
    )

    # Optional: Add custom relationships to your domain models here
    # Example:
    # customer_profile: Optional["Customer"] = Relationship(
    #     back_populates="user",
    #     sa_relationship_kwargs={
    #         "uselist": False,  # One-to-one
    #         "foreign_keys": "[Customer.user_id]",
    #     },
    # )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User {self.email}>"

    @property
    def display_name(self) -> str:
        """Get display name (fallback to email if no full_name)."""
        return self.full_name or self.email.split("@")[0]

    def get_highest_role_priority(self) -> int:
        """
        Get the user's highest role priority (lowest number = highest strength).

        Returns:
            int: Lowest priority number among user's roles (1 = strongest)
                 Returns 999 if user has no roles

        Example:
            user with roles [priority=1, priority=5] → returns 1 (strongest)
        """
        if not self.roles:
            return 999  # No roles = weakest

        return min(role.priority for role in self.roles)

    def can_manage_user(self, other_user: "User") -> bool:
        """
        Check if this user can manage another user based on role hierarchy.

        A user can manage another user if they have a LOWER priority number
        (higher strength) than the target user's highest role.

        Args:
            other_user: The user to check management permissions for

        Returns:
            bool: True if this user can manage the other user

        Example:
            admin (priority=1) can manage teacher (priority=5) → True
            teacher (priority=5) cannot manage admin (priority=1) → False
            teacher (priority=5) can manage student (priority=10) → True
        """
        my_priority = self.get_highest_role_priority()
        their_priority = other_user.get_highest_role_priority()

        # Lower number = higher strength = can manage users with higher numbers
        return my_priority < their_priority

    def can_assign_role(self, role: "Role") -> bool:
        """
        Check if this user can assign a specific role to others.

        A user can assign roles that have a HIGHER priority number (lower strength)
        than their own highest role.

        Args:
            role: The role to check assignment permission for

        Returns:
            bool: True if this user can assign this role

        Example:
            admin (priority=1) can assign teacher role (priority=5) → True
            teacher (priority=5) cannot assign admin role (priority=1) → False
        """
        from app.models.role import Role

        my_priority = self.get_highest_role_priority()

        # Can only assign roles with higher priority numbers (lower strength)
        return my_priority < role.priority

    def has_permission(self, permission_code: str) -> bool:
        """
        Check if user has a specific permission.

        This checks all roles assigned to the user.

        Args:
            permission_code: Permission code to check (e.g., "student:create")

        Returns:
            bool: True if user has the permission

        Example:
            if user.has_permission("student:delete"):
                # Allow deletion
        """
        # Check all roles for the permission
        for role in self.roles:
            if role.has_permission(permission_code):
                return True

        return False

    def has_any_permission(self, permission_codes: List[str]) -> bool:
        """
        Check if user has ANY of the specified permissions.

        Args:
            permission_codes: List of permission codes

        Returns:
            bool: True if user has at least one permission

        Example:
            if user.has_any_permission(["student:read", "student:create"]):
                # User can read OR create students
        """
        return any(self.has_permission(code) for code in permission_codes)

    def has_all_permissions(self, permission_codes: List[str]) -> bool:
        """
        Check if user has ALL specified permissions.

        Args:
            permission_codes: List of permission codes

        Returns:
            bool: True if user has all permissions

        Example:
            if user.has_all_permissions(["student:read", "student:create"]):
                # User can both read AND create students
        """
        return all(self.has_permission(code) for code in permission_codes)

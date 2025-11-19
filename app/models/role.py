"""
Role and Permission Models - Dynamic RBAC System

This module implements a flexible, dynamic Role-Based Access Control (RBAC) system.

What is RBAC?
- Users are assigned Roles (e.g., "Teacher", "Admin", "Student")
- Roles have Permissions (e.g., "student:create", "grade:update")
- Users inherit all permissions from their roles
- Can be configured at runtime (no code changes needed!)

Why Dynamic RBAC?
- Flexible: Add new roles/permissions without code changes
- Maintainable: Permissions are data, not hardcoded
- Scalable: Easy to add new features with new permissions
- Auditable: Track who has what permissions
- Enterprise-grade: Used by most SaaS applications

Permission Format: "resource:action"
Examples:
- "student:read" - Can view students
- "student:create" - Can create students
- "student:update" - Can modify students
- "student:delete" - Can delete students
- "grade:update" - Can update grades
- "*:*" - All permissions (superuser)

Common Roles:
- Admin: Full access to everything
- Teacher: Create/read/update students and grades
- Assistant: Read students and grades
- Student: Read their own data only
"""

from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

if TYPE_CHECKING:
    from app.models.user import User

# Import UserRole for link_model - must be imported at runtime
from app.models.user import UserRole


class RolePermission(SQLModel, table=True):
    """
    Junction table for many-to-many relationship between Roles and Permissions.

    This allows:
    - A role to have multiple permissions
    - A permission to be in multiple roles
    - Dynamic assignment of permissions to roles

    This is managed automatically by SQLModel, but having explicit
    control allows us to add metadata (like when permission was assigned).
    """

    __tablename__ = "role_permission"

    role_id: UUID = Field(
        foreign_key="role.id",
        primary_key=True,
        nullable=False,
    )
    permission_id: UUID = Field(
        foreign_key="permission.id",
        primary_key=True,
        nullable=False,
    )

    # Optional: Track when permission was added to role
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="When this permission was added to the role",
    )
    assigned_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="User ID who assigned this permission",
    )


class Permission(SQLModel, table=True):
    """
    Permission model - represents a single permission in the system.

    Permissions are the atomic units of access control.
    Each permission allows a specific action on a specific resource.

    Format: "resource:action"
    - resource: The entity being accessed (e.g., "student", "teacher", "grade")
    - action: The operation (e.g., "read", "create", "update", "delete")

    Examples:
        Permission(
            code="student:create",
            name="Create Student",
            description="Allows creating new student records"
        )

        Permission(
            code="grade:update",
            name="Update Grade",
            description="Allows modifying student grades"
        )

    Special Permissions:
        - "*:*" - All permissions (superuser)
        - "student:*" - All student permissions
        - "*:read" - Read all resources
    """

    __tablename__ = "permission"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Permission code (unique identifier)
    code: str = Field(
        unique=True,
        index=True,
        nullable=False,
        max_length=100,
        description="Unique permission code (e.g., 'student:create')",
        sa_column_kwargs={"unique": True},
    )

    # Human-readable information
    name: str = Field(
        nullable=False,
        max_length=255,
        description="Human-readable permission name",
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Detailed description of what this permission allows",
    )

    # Categorization
    resource: str = Field(
        nullable=False,
        max_length=50,
        description="Resource this permission applies to (e.g., 'student', 'teacher')",
        sa_column_kwargs={"index": True},
    )
    action: str = Field(
        nullable=False,
        max_length=50,
        description="Action this permission allows (e.g., 'create', 'read', 'update', 'delete')",
        sa_column_kwargs={"index": True},
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    roles: List["Role"] = Relationship(
        back_populates="permissions",
        link_model=RolePermission,
        sa_relationship_kwargs={
            "lazy": "selectin",  # Always eager-load to avoid MissingGreenlet in async
        }
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"

    @classmethod
    def parse_code(cls, code: str) -> tuple[str, str]:
        """
        Parse permission code into resource and action.

        Args:
            code: Permission code (e.g., "student:create")

        Returns:
            tuple: (resource, action)

        Example:
            resource, action = Permission.parse_code("student:create")
            # resource = "student", action = "create"
        """
        parts = code.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid permission code: {code}. Expected format: 'resource:action'")
        return parts[0], parts[1]

    @classmethod
    def create_code(cls, resource: str, action: str) -> str:
        """
        Create permission code from resource and action.

        Args:
            resource: Resource name
            action: Action name

        Returns:
            str: Permission code

        Example:
            code = Permission.create_code("student", "create")
            # code = "student:create"
        """
        return f"{resource}:{action}"


class Role(SQLModel, table=True):
    """
    Role model - represents a role that can be assigned to users.

    Roles are collections of permissions. Users are assigned roles,
    and inherit all permissions from those roles.

    This allows flexible permission management:
    - Create new roles without code changes
    - Assign different permissions to different roles
    - Users can have multiple roles
    - Easy to promote/demote users by changing roles

    Common Roles:
        Role(
            name="Administrator",
            code="admin",
            description="Full system access",
            permissions=[all_permissions]
        )

        Role(
            name="Teacher",
            code="teacher",
            description="Can manage students and grades",
            permissions=["student:*", "grade:*", "subject:read"]
        )

        Role(
            name="Assistant",
            code="assistant",
            description="Can view students and grades",
            permissions=["student:read", "grade:read", "subject:read"]
        )

        Role(
            name="Student",
            code="student",
            description="Can view own data",
            permissions=["student:read_own", "grade:read_own"]
        )
    """

    __tablename__ = "role"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Role identification
    code: str = Field(
        unique=True,
        index=True,
        nullable=False,
        max_length=50,
        description="Unique role code (e.g., 'admin', 'teacher', 'student')",
        sa_column_kwargs={"unique": True},
    )
    name: str = Field(
        nullable=False,
        max_length=255,
        description="Human-readable role name",
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Description of what this role can do",
    )

    # Hierarchy - Role strength/level (ascending: 1 = highest, higher numbers = lower)
    priority: int = Field(
        default=999,
        nullable=False,
        description="Role strength (1 = highest/strongest, 10 = weakest). Users can only manage users with higher priority numbers.",
        sa_column_kwargs={"index": True},
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

    # Relationships
    users: List["User"] = Relationship(
        back_populates="roles",
        link_model=UserRole,
        sa_relationship_kwargs={
            "primaryjoin": "Role.id==UserRole.role_id",
            "secondaryjoin": "User.id==UserRole.user_id",
            "lazy": "selectin",  # Always eager-load to avoid MissingGreenlet in async
        }
    )
    permissions: List["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermission,
        sa_relationship_kwargs={
            "lazy": "selectin",  # Always eager-load to avoid MissingGreenlet in async
        }
    )

    def __repr__(self) -> str:
        return f"<Role {self.code}>"

    def has_permission(self, permission_code: str) -> bool:
        """
        Check if this role has a specific permission.

        Supports wildcards:
        - "*:*" matches everything
        - "student:*" matches all student permissions
        - "*:read" matches all read permissions

        Args:
            permission_code: Permission code to check

        Returns:
            bool: True if role has the permission

        Example:
            if role.has_permission("student:create"):
                # This role can create students
        """
        for permission in self.permissions:
            # Exact match
            if permission.code == permission_code:
                return True

            # Wildcard matching
            perm_resource, perm_action = Permission.parse_code(permission.code)
            req_resource, req_action = Permission.parse_code(permission_code)

            # *:* matches everything
            if perm_resource == "*" and perm_action == "*":
                return True

            # resource:* matches all actions on that resource
            if perm_resource == req_resource and perm_action == "*":
                return True

            # *:action matches that action on all resources
            if perm_resource == "*" and perm_action == req_action:
                return True

        return False

    def get_permission_codes(self) -> List[str]:
        """
        Get list of all permission codes for this role.

        Returns:
            List[str]: List of permission codes

        Example:
            codes = role.get_permission_codes()
            # ["student:read", "student:create", "grade:read"]
        """
        return [p.code for p in self.permissions]


# Predefined Permission Constants (for code reference)
# These will be seeded into the database on first run
# Format: ("code", "name", "resource", "action")
#
# NOTE: Only include permissions for models/tables that actually exist in your application.
# When you add new models, add corresponding permissions here following the same pattern.
PERMISSIONS = {
    # User management permissions
    "USER_CREATE": ("user:create", "Create User", "user", "create"),
    "USER_READ": ("user:read", "Read User", "user", "read"),
    "USER_UPDATE": ("user:update", "Update User", "user", "update"),
    "USER_DELETE": ("user:delete", "Delete User", "user", "delete"),
    "USER_ALL": ("user:*", "All User Permissions", "user", "*"),

    # Role management permissions
    "ROLE_CREATE": ("role:create", "Create Role", "role", "create"),
    "ROLE_READ": ("role:read", "Read Role", "role", "read"),
    "ROLE_UPDATE": ("role:update", "Update Role", "role", "update"),
    "ROLE_DELETE": ("role:delete", "Delete Role", "role", "delete"),
    "ROLE_ASSIGN": ("role:assign", "Assign Role to User", "role", "assign"),
    "ROLE_ALL": ("role:*", "All Role Permissions", "role", "*"),

    # Audit log permissions
    "AUDIT_READ": ("audit:read", "Read Audit Logs", "audit", "read"),
    "AUDIT_ALL": ("audit:*", "All Audit Permissions", "audit", "*"),

    # Restaurant management permissions
    "RESTAURANT_CREATE": ("restaurant:create", "Create Restaurant", "restaurant", "create"),
    "RESTAURANT_READ": ("restaurant:read", "Read Restaurant", "restaurant", "read"),
    "RESTAURANT_UPDATE": ("restaurant:update", "Update Restaurant", "restaurant", "update"),
    "RESTAURANT_DELETE": ("restaurant:delete", "Delete Restaurant", "restaurant", "delete"),
    "RESTAURANT_VERIFY": ("restaurant:verify", "Verify Restaurant", "restaurant", "verify"),
    "RESTAURANT_ALL": ("restaurant:*", "All Restaurant Permissions", "restaurant", "*"),

    # Supplier management permissions
    "SUPPLIER_CREATE": ("supplier:create", "Create Supplier", "supplier", "create"),
    "SUPPLIER_READ": ("supplier:read", "Read Supplier", "supplier", "read"),
    "SUPPLIER_UPDATE": ("supplier:update", "Update Supplier", "supplier", "update"),
    "SUPPLIER_DELETE": ("supplier:delete", "Delete Supplier", "supplier", "delete"),
    "SUPPLIER_VERIFY": ("supplier:verify", "Verify Supplier", "supplier", "verify"),
    "SUPPLIER_ALL": ("supplier:*", "All Supplier Permissions", "supplier", "*"),

    # Product management permissions
    "PRODUCT_CREATE": ("product:create", "Create Product", "product", "create"),
    "PRODUCT_READ": ("product:read", "Read Product", "product", "read"),
    "PRODUCT_UPDATE": ("product:update", "Update Product", "product", "update"),
    "PRODUCT_DELETE": ("product:delete", "Delete Product", "product", "delete"),
    "PRODUCT_ALL": ("product:*", "All Product Permissions", "product", "*"),

    # Order management permissions
    "ORDER_CREATE": ("order:create", "Create Order", "order", "create"),
    "ORDER_READ": ("order:read", "Read Order", "order", "read"),
    "ORDER_UPDATE": ("order:update", "Update Order", "order", "update"),
    "ORDER_DELETE": ("order:delete", "Delete Order", "order", "delete"),
    "ORDER_APPROVE": ("order:approve", "Approve Order", "order", "approve"),
    "ORDER_CANCEL": ("order:cancel", "Cancel Order", "order", "cancel"),
    "ORDER_ALL": ("order:*", "All Order Permissions", "order", "*"),

    # Delivery management permissions
    "DELIVERY_CREATE": ("delivery:create", "Create Delivery", "delivery", "create"),
    "DELIVERY_READ": ("delivery:read", "Read Delivery", "delivery", "read"),
    "DELIVERY_UPDATE": ("delivery:update", "Update Delivery", "delivery", "update"),
    "DELIVERY_DELETE": ("delivery:delete", "Delete Delivery", "delivery", "delete"),
    "DELIVERY_ASSIGN": ("delivery:assign", "Assign Delivery to Driver", "delivery", "assign"),
    "DELIVERY_COMPLETE": ("delivery:complete", "Complete Delivery", "delivery", "complete"),
    "DELIVERY_ALL": ("delivery:*", "All Delivery Permissions", "delivery", "*"),

    # Review management permissions
    "REVIEW_CREATE": ("review:create", "Create Review", "review", "create"),
    "REVIEW_READ": ("review:read", "Read Review", "review", "read"),
    "REVIEW_UPDATE": ("review:update", "Update Review", "review", "update"),
    "REVIEW_DELETE": ("review:delete", "Delete Review", "review", "delete"),
    "REVIEW_ALL": ("review:*", "All Review Permissions", "review", "*"),

    # Payment management permissions
    "PAYMENT_CREATE": ("payment:create", "Create Payment", "payment", "create"),
    "PAYMENT_READ": ("payment:read", "Read Payment", "payment", "read"),
    "PAYMENT_UPDATE": ("payment:update", "Update Payment", "payment", "update"),
    "PAYMENT_VERIFY": ("payment:verify", "Verify Payment", "payment", "verify"),
    "PAYMENT_ALL": ("payment:*", "All Payment Permissions", "payment", "*"),

    # System-wide permissions
    "SYSTEM_ADMIN": ("*:*", "System Administrator", "*", "*"),
    "SYSTEM_READ_ALL": ("*:read", "Read All Resources", "*", "read"),
}

# Example: When you add new models, add permissions like this:
# "PRODUCT_CREATE": ("product:create", "Create Product", "product", "create"),
# "PRODUCT_READ": ("product:read", "Read Product", "product", "read"),
# "PRODUCT_UPDATE": ("product:update", "Update Product", "product", "update"),
# "PRODUCT_DELETE": ("product:delete", "Delete Product", "product", "delete"),
# "PRODUCT_ALL": ("product:*", "All Product Permissions", "product", "*"),

# Predefined Role Constants
# Format: ("code", "name", "description", priority)
# Priority: 1 = highest (admin), higher numbers = lower priority
ROLES = {
    "ADMIN": ("admin", "Administrator", "Full system access with all permissions", 1),
    "MANAGER": ("manager", "Manager", "Can manage users and assign roles", 2),

    # Supply Chain Roles
    "RESTAURANT_OWNER": ("restaurant_owner", "Restaurant Owner", "Owner of a restaurant, can manage restaurant profile and staff", 5),
    "RESTAURANT_MANAGER": ("restaurant_manager", "Restaurant Manager", "Restaurant manager, can create orders and manage inventory", 6),
    "RESTAURANT_STAFF": ("restaurant_staff", "Restaurant Staff", "Restaurant staff member with basic access", 7),

    "SUPPLIER_ADMIN": ("supplier_admin", "Supplier Administrator", "Administrator of a supplier company, full control over products and orders", 5),
    "SUPPLIER_MANAGER": ("supplier_manager", "Supplier Manager", "Supplier manager, can manage products and fulfill orders", 6),
    "SUPPLIER_STAFF": ("supplier_staff", "Supplier Staff", "Supplier staff member with limited access", 7),

    "DRIVER": ("driver", "Delivery Driver", "Delivery driver, can view and update delivery status", 8),
    "ACCOUNTANT": ("accountant", "Accountant", "Financial staff, can view orders and manage payments", 6),

    # Basic user role
    "USER": ("user", "User", "Standard user with basic access", 10),
}

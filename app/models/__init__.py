"""
Models Module

This module exports all database models.

Import Order is Important!
- Base models first
- Models with no dependencies
- Models with foreign keys last

This prevents circular import issues.
"""

# Base models
from app.models.base import (
    BaseModel,
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
    UUIDMixin,
)

# Auth models (core template models)
from app.models.role import (
    Permission,
    Role,
    RolePermission,
    PERMISSIONS,
    ROLES,
)
from app.models.user import User, UserRole

# Add your custom domain models here:
# from app.models.product import Product
# from app.models.order import Order

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    "AuditMixin",
    "SoftDeleteMixin",
    "UUIDMixin",
    # Auth (Core template)
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
    "PERMISSIONS",
    "ROLES",
    # Add your custom models to __all__ here:
    # "Product",
    # "Order",
]

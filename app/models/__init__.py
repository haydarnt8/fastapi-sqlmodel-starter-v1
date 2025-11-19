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

# Supply Chain models (must be imported before User due to relationships)
from app.models.restaurant import Restaurant
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.delivery import Delivery, DeliveryStatus, DeliveryPriority

# User model (must be after Restaurant and Supplier due to foreign keys)
from app.models.user import User, UserRole

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
    # Supply Chain models
    "Restaurant",
    "Supplier",
    "Product",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "Delivery",
    "DeliveryStatus",
    "DeliveryPriority",
]

"""
CRUD Operations Module

Contains all CRUD (Create, Read, Update, Delete) operations for the application.

Core Template CRUD:
- user_crud: User management operations
- role_crud: Role management operations
- permission_crud: Permission management operations
"""
from app.crud.user import user_crud
from app.crud.role import role_crud, permission_crud

# Add your custom domain-specific CRUD operations here:
# from app.crud.product import product_crud
# from app.crud.order import order_crud

__all__ = [
    "user_crud",
    "role_crud",
    "permission_crud",
    # Add your custom CRUD operations to this list:
    # "product_crud",
    # "order_crud",
]

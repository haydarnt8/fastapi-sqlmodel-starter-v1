"""Schemas Module - API Request/Response Validation"""

# Common
from app.schemas.common import (
    PaginationParams,
    SortParams,
    PaginatedResponse,
    MessageResponse,
    ErrorResponse,
    ErrorDetail,
    IDResponse,
    StatusResponse,
    HealthResponse,
    FilterParams,
)

# User & Auth (Core template schemas)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserRead,
    UserList,
    UserProfile,
    UserRegister,
    UserUpdatePassword,
    UserRoleAssignment,
    Token,
    TokenPayload,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
)

# Role & Permission (Core template schemas)
from app.schemas.role import (
    PermissionCreate,
    PermissionRead,
    PermissionList,
    RoleCreate,
    RoleUpdate,
    RoleRead,
    RoleList,
    RolePermissionAssignment,
    PermissionCheck,
    PermissionCheckResponse,
)

# Add your custom domain schemas here:
# from app.schemas.product import ProductCreate, ProductUpdate, ProductRead, ProductList
# from app.schemas.order import OrderCreate, OrderUpdate, OrderRead, OrderList

__all__ = [
    # Common
    "PaginationParams",
    "SortParams",
    "PaginatedResponse",
    "MessageResponse",
    "ErrorResponse",
    "ErrorDetail",
    "IDResponse",
    "StatusResponse",
    "HealthResponse",
    "FilterParams",
    # User & Auth (Core template)
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserList",
    "UserProfile",
    "UserRegister",
    "UserUpdatePassword",
    "UserRoleAssignment",
    "Token",
    "TokenPayload",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    # Role & Permission (Core template)
    "PermissionCreate",
    "PermissionRead",
    "PermissionList",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
    "RoleList",
    "RolePermissionAssignment",
    "PermissionCheck",
    "PermissionCheckResponse",
    # Add your custom schemas to __all__ here:
    # "ProductCreate",
    # "ProductUpdate",
    # "ProductRead",
    # "ProductList",
]

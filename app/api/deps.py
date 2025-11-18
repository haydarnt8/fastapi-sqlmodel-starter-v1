"""
API Dependencies

These dependencies are used throughout the API for:
- Authentication (checking JWT tokens)
- Authorization (checking permissions)
- Pagination
- Database sessions

Why dependencies?
- Reusable across all endpoints
- Clean separation of concerns
- Easy to test
- FastAPI automatically injects them

Usage in endpoint:
    @router.get("/students")
    async def get_students(
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_session),
    ):
        # current_user is automatically provided by FastAPI
        # session is automatically provided by FastAPI
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.cache import get_redis_cache
from app.db.session import get_session
from app.models import User
from app.crud.user import user_crud
from app.schemas.common import PaginationParams, SortParams
from app.i18n import Translator, get_translator

# OAuth2 scheme for token authentication
# This tells FastAPI where to look for the token
# tokenUrl points to the form-based login endpoint for Swagger UI compatibility
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login/form",
    auto_error=True,  # Automatically return 401 if token is missing
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Get current authenticated user from JWT token.

    This is the CORE authentication dependency.
    Every protected endpoint should use this!

    Args:
        token: JWT token from Authorization header
        session: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    try:
        # Check if token is blacklisted (revoked)
        cache = await get_redis_cache()
        if await cache.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode JWT token
        payload = decode_token(token)
        user_id_str = payload.get("sub")

        if user_id_str is None:
            raise AuthenticationError("Could not validate credentials")

        # Convert string UUID to UUID object
        from uuid import UUID
        user_id = UUID(user_id_str)

    except HTTPException:
        # Re-raise HTTP exceptions (like token revoked)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    # Relationships are eager-loaded automatically via lazy='selectin' configuration
    user = await user_crud.get(session, id=user_id, raise_not_found=False)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (must be active).

    This adds an extra check on top of get_current_user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current active user

    Raises:
        HTTPException: 403 if user is inactive

    Usage:
        @router.get("/students")
        async def get_students(
            current_user: User = Depends(get_current_active_user)
        ):
            # Only active users can access this
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    DEPRECATED: Use PermissionChecker instead.

    The is_superuser field has been removed in favor of hierarchical role-based
    permissions. Use PermissionChecker("*:*") for admin-level access.

    Args:
        current_user: Current active user

    Returns:
        User: Current user

    Raises:
        HTTPException: 403 if user doesn't have admin role
    """
    # Check if user has admin role (priority 1)
    if current_user.get_highest_role_priority() > 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


class PermissionChecker:
    """
    Permission checker dependency.

    This is THE KEY to RBAC! It checks if user has a specific permission.

    Usage:
        # Require permission to create students:
        @router.post("/students")
        async def create_student(
            student_data: StudentCreate,
            current_user: User = Depends(PermissionChecker("student:create"))
        ):
            # Only users with "student:create" permission can access this

    This works with:
    - Exact permissions: "student:create"
    - Wildcard permissions: "student:*", "*:*"
    - Multiple roles: User can have multiple roles
    - Dynamic: Add new permissions without code changes!
    """

    def __init__(self, permission: str):
        """
        Initialize permission checker.

        Args:
            permission: Required permission code (e.g., "student:create")
        """
        self.permission = permission

    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Check if user has the required permission.

        Args:
            current_user: Current active user

        Returns:
            User: Current user (if has permission)

        Raises:
            HTTPException: 403 if user doesn't have permission

        This is called automatically by FastAPI!
        """
        # Check if user has the permission
        if not current_user.has_permission(self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {self.permission}",
            )

        return current_user


class MultiPermissionChecker:
    """
    Check if user has ANY of multiple permissions.

    Usage:
        @router.get("/students")
        async def get_students(
            current_user: User = Depends(
                MultiPermissionChecker(["student:read", "student:*"])
            )
        ):
            # User needs "student:read" OR "student:*"
    """

    def __init__(self, permissions: List[str]):
        """
        Initialize with list of acceptable permissions.

        Args:
            permissions: List of permission codes
        """
        self.permissions = permissions

    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if user has any of the required permissions."""
        if not current_user.has_any_permission(self.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(self.permissions)}",
            )

        return current_user


# Pagination dependency
def get_pagination_params(
    skip_count: int = Query(0, ge=0, description="Number of records to skip"),
    max_count: int = Query(20, ge=1, le=100, description="Max records to return"),
) -> PaginationParams:
    """
    Pagination parameters dependency.

    Usage:
        @router.get("/students")
        async def get_students(
            pagination: PaginationParams = Depends(get_pagination_params)
        ):
            students = await student_crud.get_multi(
                session,
                skip=pagination.skip,
                limit=pagination.limit
            )
    """
    return PaginationParams(skip_count=skip_count, max_count=max_count)


# Sort dependency
def get_sort_params(
    sort_by: str = Query("created_at", description="Field name to sort by"),
    sort_order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
) -> SortParams:
    """
    Sort parameters dependency.

    Usage:
        @router.get("/students")
        async def get_students(
            sort: SortParams = Depends(get_sort_params)
        ):
            # Use sort.sort_by and sort.sort_order
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)


# Optional user (for endpoints that work with or without auth)
async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Use for endpoints that behave differently for authenticated users
    but don't require authentication.

    Usage:
        @router.get("/public/students")
        async def get_public_students(
            current_user: Optional[User] = Depends(get_optional_user)
        ):
            if current_user:
                # Show more data for authenticated users
            else:
                # Show limited public data
    """
    if token is None:
        return None

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if user_id_str:
            from uuid import UUID
            user_id = UUID(user_id_str)
            user = await user_crud.get(session, id=user_id, raise_not_found=False)
            return user
        return None
    except Exception:
        return None


def get_translation(request: Request) -> Translator:
    """
    Get translator for current request based on language preference.

    Language detection priority:
    1. Query parameter: ?lang=ar or ?lang=en
    2. Accept-Language header
    3. Default: en

    Usage:
        @router.get("/example")
        async def example(
            request: Request,
            t: Translator = Depends(get_translation)
        ):
            return {"message": t("common.success")}

    Or inline:
        @router.get("/example")
        async def example(request: Request):
            t = get_translator(request)
            return {"message": t("common.success")}
    """
    return get_translator(request)


# Export commonly used dependencies
__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "PermissionChecker",
    "MultiPermissionChecker",
    "get_pagination_params",
    "get_sort_params",
    "get_optional_user",
    "get_translation",
]

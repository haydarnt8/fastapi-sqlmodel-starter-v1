"""
Authentication Endpoints

Handles user authentication:
- Login (email + password → JWT tokens)
- Register (create new user account)
- Refresh token (get new access token)
- Get current user profile
- Change password
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, extract_token_data
from app.core.exceptions import AuthenticationError, DuplicateResourceError
from app.crud.user import user_crud
from app.db.session import get_session
from app.models import User
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_auth_event
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    UserRegister,
    UserProfile,
    UserUpdatePassword,
    RefreshTokenRequest,
    Token,
)
from app.schemas.common import MessageResponse
from app.middleware.rate_limit import get_limiter, RateLimits

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = get_limiter()


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.AUTH_REGISTER)
async def register(
    request: Request,
    response: Response,
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Register a new user account.

    Anyone can register (no authentication required).
    New users automatically get the "User" role assigned.
    New users are NOT superusers by default.

    Request Body:
    - email: Valid email address
    - password: Strong password (min 8 chars, uppercase, lowercase, number)
    - full_name: User's full name
    - phone: Optional phone number

    Returns:
    - Created user profile with "User" role assigned

    Errors:
    - 409: Email already registered
    - 422: Validation error (weak password, invalid email, etc.)
    """
    try:
        # Create user (user_crud checks for duplicate email)
        from app.schemas.user import UserCreate
        from app.models.role import Role
        from sqlalchemy import select

        # Get the default "User" role
        result = await session.execute(
            select(Role).where(Role.code == "user")
        )
        user_role = result.scalar_one_or_none()

        # Create user with default "User" role
        user_create = UserCreate(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            is_active=True,
            role_ids=[user_role.id] if user_role else None,
        )

        user = await user_crud.create(session, obj_in=user_create)

        # Audit: Successful registration
        await log_auth_event(
            session=session,
            action="auth.register",
            user_email=user.email,
            status=AuditStatus.SUCCESS,
            error_message=None,
            request=request,
        )

        return user

    except DuplicateResourceError as e:
        # Audit: Failed registration (duplicate email)
        await log_auth_event(
            session=session,
            action="auth.register",
            user_email=user_data.email,
            status=AuditStatus.FAILURE,
            error_message=f"Email already registered: {user_data.email}",
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    """
    Login with email and password.

    Returns JWT access token and refresh token.

    Request Body:
    - email: User's email
    - password: User's password

    Returns:
    - access_token: JWT token for API authentication (expires in 30 min)
    - refresh_token: JWT token to get new access token (expires in 7 days)
    - token_type: "bearer"
    - expires_in: Token expiration in seconds
    - user: User profile information

    Errors:
    - 401: Invalid credentials
    - 403: User account is inactive

    Usage:
        1. Call this endpoint with email/password
        2. Store access_token in frontend
        3. Include in all API calls: Authorization: Bearer {access_token}
        4. When access_token expires, use refresh_token to get new one
    """
    # Authenticate user
    user = await user_crud.authenticate(
        session,
        email=login_data.email,
        password=login_data.password,
    )

    if not user:
        # Audit: Failed login (invalid credentials)
        await log_auth_event(
            session=session,
            action=AuditAction.LOGIN_FAILURE,
            user_email=login_data.email,
            status=AuditStatus.FAILURE,
            error_message="Invalid credentials",
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        # Audit: Failed login (inactive account)
        await log_auth_event(
            session=session,
            action=AuditAction.LOGIN_FAILURE,
            user_email=user.email,
            status=AuditStatus.FAILURE,
            error_message="Account is inactive",
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # Audit: Successful login
    await log_auth_event(
        session=session,
        action=AuditAction.LOGIN_SUCCESS,
        user_email=user.email,
        status=AuditStatus.SUCCESS,
        error_message=None,
        request=request,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/login/form", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login_form(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    """
    Login using OAuth2 password flow (for Swagger UI).

    This is the same as /login but uses form data instead of JSON.
    Required for Swagger UI's "Authorize" button to work.

    Form Fields:
    - username: User's email (called 'username' for OAuth2 compatibility)
    - password: User's password

    Returns:
    - access_token: JWT token
    - refresh_token: JWT token
    - token_type: "bearer"
    """
    user = await user_crud.authenticate(
        session,
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
@limiter.limit(RateLimits.AUTH_REFRESH)
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> Token:
    """
    Get new access token using refresh token.

    When access token expires, use this to get a new one
    without requiring the user to log in again.

    Request Body:
    - refresh_token: Valid refresh token from login

    Returns:
    - New access_token and refresh_token

    Errors:
    - 401: Invalid or expired refresh token
    - 401: User not found

    Usage:
        1. Access token expires after 30 minutes
        2. Call this endpoint with refresh_token
        3. Get new access_token
        4. Continue making API calls
    """
    try:
        # Decode and validate refresh token
        payload = extract_token_data(refresh_data.refresh_token, token_type="refresh")
        user_id_str = payload.get("sub")

        if not user_id_str:
            raise ValueError("No user ID in token")

        # Convert string UUID to UUID object
        from uuid import UUID
        user_id = UUID(user_id_str)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user = await user_crud.get(session, id=user_id, raise_not_found=False)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user's profile.

    Requires authentication.

    Returns:
    - Current user's complete profile including roles

    Usage:
        GET /api/v1/auth/me
        Authorization: Bearer {access_token}
    """
    return current_user


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    request: Request,
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """
    Change current user's password.

    Requires authentication and current password.

    Request Body:
    - current_password: User's current password
    - new_password: New password (must meet strength requirements)

    Returns:
    - Success message

    Errors:
    - 401: Current password is incorrect
    - 422: New password doesn't meet requirements
    """
    # Verify current password
    from app.core.security import verify_password

    if not verify_password(password_data.current_password, current_user.hashed_password):
        # Audit: Failed password change (incorrect current password)
        await log_auth_event(
            session=session,
            action=AuditAction.PASSWORD_CHANGE,
            user_email=current_user.email,
            status=AuditStatus.FAILURE,
            error_message="Incorrect current password",
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Check if new password is same as current password
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    await user_crud.update_password(
        session,
        user=current_user,
        new_password=password_data.new_password,
        updated_by_id=current_user.id,
    )

    # Audit: Successful password change
    await log_auth_event(
        session=session,
        action=AuditAction.PASSWORD_CHANGE,
        user_email=current_user.email,
        status=AuditStatus.SUCCESS,
        error_message=None,
        request=request,
    )

    return MessageResponse(message="Password updated successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """
    Logout current user.

    Blacklists the current access token so it cannot be used again.
    The token remains blacklisted until its natural expiration.

    How it works:
    1. Extract token from Authorization header
    2. Decode token to get expiration time
    3. Add token to Redis blacklist with TTL = time until expiration
    4. Token is automatically removed from blacklist after expiration

    Returns:
    - Success message

    Notes:
    - If Redis is unavailable, logout still returns 200 but token isn't blacklisted
    - Client should delete token regardless of server-side blacklisting
    - Token blacklisting is an additional security layer
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # This shouldn't happen since we already authenticated,
        # but handle gracefully
        return MessageResponse(message="Logged out successfully")

    token = auth_header.replace("Bearer ", "")

    # Blacklist the token
    from app.core.cache import get_redis_cache
    from datetime import datetime

    try:
        # Decode token to get expiration time
        payload = extract_token_data(token, token_type="access")
        exp = payload.get("exp")

        if exp:
            # Calculate TTL (time until token expires naturally)
            now = int(datetime.utcnow().timestamp())
            ttl = exp - now

            if ttl > 0:
                # Add token to blacklist
                cache = await get_redis_cache()
                await cache.blacklist_token(token, ttl=ttl)

    except Exception as e:
        # If Redis is down or token decode fails, log it but don't fail the logout
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Failed to blacklist token during logout: {e}")

    # Audit: Successful logout
    await log_auth_event(
        session=session,
        action=AuditAction.LOGOUT,
        user_email=current_user.email,
        status=AuditStatus.SUCCESS,
        error_message=None,
        request=request,
    )

    return MessageResponse(message="Logged out successfully")

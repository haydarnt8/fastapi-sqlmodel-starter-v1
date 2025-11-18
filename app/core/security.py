"""
Security Utilities

This module provides security-related utilities:
- Password hashing and verification
- JWT token creation and validation
- Security helpers

Why these security measures?
- Password hashing: Never store plain text passwords
- JWT tokens: Stateless authentication (no server-side sessions)
- Secure algorithms: Using industry-standard bcrypt and HS256

Security Best Practices:
1. Always hash passwords (never store plain text)
2. Use strong hashing algorithms (bcrypt with cost factor)
3. Use secure random tokens
4. Set reasonable token expiration times
5. Validate tokens on every protected endpoint
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError

# Password hashing context
# argon2 is the modern standard for password hashing (winner of Password Hashing Competition 2015)
# More secure than bcrypt and doesn't have the 72-byte limit
# deprecated="auto" automatically migrates to new hash if needed
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # argon2 preferred, bcrypt for backward compat
    deprecated="auto"
)


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user ID or email)
        expires_delta: Token expiration time (default from settings)
        additional_claims: Additional data to include in token

    Returns:
        str: Encoded JWT token

    Example:
        token = create_access_token(subject=user.id, additional_claims={"role": "admin"})
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Prepare token payload
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow(),  # Issued at
    }

    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)

    # Encode and return token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens are used to get new access tokens without re-authentication.
    They typically have longer expiration times.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Token expiration time (default from settings)

    Returns:
        str: Encoded JWT refresh token

    Example:
        refresh_token = create_refresh_token(subject=user.id)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Dict[str, Any]: Token payload

    Raises:
        AuthenticationError: If token is invalid or expired

    Example:
        try:
            payload = decode_token(token)
            user_id = payload["sub"]
        except AuthenticationError:
            # Handle invalid token
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Could not validate credentials: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password: Plain text password from user
        hashed_password: Hashed password from database

    Returns:
        bool: True if password matches, False otherwise

    Example:
        if verify_password(input_password, user.hashed_password):
            # Password is correct
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password

    Example:
        hashed = get_password_hash("MySecurePassword123")
        # Store hashed in database, never store plain password
    """
    return pwd_context.hash(password)


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> None:
    """
    Verify that a token is of the expected type.

    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")

    Raises:
        AuthenticationError: If token type doesn't match

    Example:
        payload = decode_token(token)
        verify_token_type(payload, "access")  # Ensure it's an access token
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise AuthenticationError(
            f"Invalid token type. Expected {expected_type}, got {token_type}"
        )


def extract_token_data(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Decode token and verify its type in one operation.

    Args:
        token: JWT token string
        token_type: Expected token type (default: "access")

    Returns:
        Dict[str, Any]: Token payload

    Raises:
        AuthenticationError: If token is invalid or wrong type

    Example:
        data = extract_token_data(token)
        user_id = int(data["sub"])
    """
    payload = decode_token(token)
    verify_token_type(payload, token_type)
    return payload

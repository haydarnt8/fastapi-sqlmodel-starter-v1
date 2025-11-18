"""
Custom Exception Classes

This module defines custom exceptions for the application.
Custom exceptions allow for:
- Better error handling and categorization
- Consistent error responses
- Easier debugging and logging
- Clear error messages to users

Why custom exceptions?
- Standard exceptions are generic
- Custom exceptions carry business logic context
- Easier to handle different error types differently
- Better API documentation
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    """
    Base exception for all application exceptions.

    All custom exceptions should inherit from this class.
    This allows catching all app exceptions with a single except clause.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(AppException):
    """
    Raised when a requested resource doesn't exist.

    Example:
        raise ResourceNotFoundError("Student", student_id=123)
    """

    def __init__(self, resource_name: str, **kwargs):
        details = {k: v for k, v in kwargs.items()}
        message = f"{resource_name} not found"
        if details:
            message += f": {details}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class DuplicateResourceError(AppException):
    """
    Raised when trying to create a resource that already exists.

    Example:
        raise DuplicateResourceError("User", email=email)
    """

    def __init__(self, resource_name: str, **kwargs):
        details = {k: v for k, v in kwargs.items()}
        message = f"{resource_name} already exists"
        if details:
            message += f": {details}"
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationError(AppException):
    """
    Raised when business logic validation fails.

    Example:
        raise ValidationError("Grade must be between 0 and 100", grade=grade)
    """

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=kwargs,
        )


class AuthenticationError(AppException):
    """
    Raised when authentication fails.

    Example:
        raise AuthenticationError("Invalid credentials")
    """

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=kwargs,
        )


class AuthorizationError(AppException):
    """
    Raised when user doesn't have permission to perform an action.

    Example:
        raise AuthorizationError("Insufficient permissions")
    """

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=kwargs,
        )


class DatabaseError(AppException):
    """
    Raised when a database operation fails.

    Example:
        raise DatabaseError("Failed to connect to database", error=str(e))
    """

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=kwargs,
        )


class BusinessLogicError(AppException):
    """
    Raised when business rules are violated.

    Example:
        raise BusinessLogicError("Cannot delete teacher with active subjects")
    """

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=kwargs,
        )


class RateLimitError(AppException):
    """
    Raised when rate limit is exceeded.

    Example:
        raise RateLimitError("Too many requests")
    """

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=kwargs,
        )


class ExternalServiceError(AppException):
    """
    Raised when an external service (API, email, etc.) fails.

    Example:
        raise ExternalServiceError("Email service unavailable")
    """

    def __init__(self, service_name: str, message: str, **kwargs):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=kwargs,
        )


# Utility function to convert our custom exceptions to HTTPException
def to_http_exception(exc: AppException) -> HTTPException:
    """
    Convert custom exception to FastAPI HTTPException.

    Args:
        exc: Custom application exception

    Returns:
        HTTPException with proper status code and details
    """
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "details": exc.details},
    )

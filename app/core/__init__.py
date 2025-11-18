"""
Core Module

This module exports core functionality used throughout the application.
"""

from app.core.config import get_settings, settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_token_data,
    get_password_hash,
    verify_password,
    verify_token_type,
)
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    DatabaseError,
    DuplicateResourceError,
    ExternalServiceError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
    to_http_exception,
)

__all__ = [
    # Config
    "get_settings",
    "settings",
    # Security
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "extract_token_data",
    "get_password_hash",
    "verify_password",
    "verify_token_type",
    # Logging
    "get_logger",
    "setup_logging",
    # Exceptions
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "BusinessLogicError",
    "DatabaseError",
    "DuplicateResourceError",
    "ExternalServiceError",
    "RateLimitError",
    "ResourceNotFoundError",
    "ValidationError",
    "to_http_exception",
]

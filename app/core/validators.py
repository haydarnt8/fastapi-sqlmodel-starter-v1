"""
Shared Validation Functions

Common validators used across multiple schemas to ensure consistency
and avoid code duplication.

Why centralized validators?
- DRY (Don't Repeat Yourself): Single source of truth
- Consistency: All password fields use same validation logic
- Maintainability: Change once, apply everywhere
- Testability: Easy to unit test in isolation
- Flexibility: Can easily adjust requirements across the app
"""

import re
from typing import Optional


def validate_password_strength(password: str) -> str:
    """
    Validate password strength with comprehensive security requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - Optionally: Special characters (recommended but not required)

    Args:
        password: The password string to validate

    Returns:
        The validated password (unchanged)

    Raises:
        ValueError: If password doesn't meet strength requirements

    Examples:
        >>> validate_password_strength("SecurePass123")
        'SecurePass123'
        >>> validate_password_strength("weak")  # doctest: +SKIP
        ValueError: Password must be at least 8 characters

    Security Note:
        These are basic requirements. For high-security applications,
        consider adding:
        - Minimum 12+ characters
        - Required special characters
        - Entropy/complexity checking
        - Password blacklist checking (common passwords)
        - pwned password checking (haveibeenpwned.com API)
    """
    # Check minimum length
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    # Check for at least one uppercase letter
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")

    # Check for at least one lowercase letter
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter")

    # Check for at least one digit
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number")

    # Optional: Check for special characters (uncomment to enable)
    # special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?")
    # if not any(char in special_chars for char in password):
    #     raise ValueError("Password must contain at least one special character")

    # Optional: Check for common weak passwords (uncomment to enable)
    # weak_passwords = {"password", "password123", "12345678", "qwerty123"}
    # if password.lower() in weak_passwords:
    #     raise ValueError("Password is too common. Please choose a stronger password.")

    return password


def validate_email_format(email: str) -> str:
    """
    Additional email validation beyond Pydantic's EmailStr.

    Args:
        email: Email address to validate

    Returns:
        The validated email (lowercased and stripped)

    Raises:
        ValueError: If email doesn't meet additional requirements

    Note:
        Pydantic's EmailStr already handles basic RFC validation.
        This is for additional business rules if needed.
    """
    # Strip whitespace and lowercase
    email = email.strip().lower()

    # Optional: Block disposable email domains
    # disposable_domains = {"tempmail.com", "throwaway.email", "10minutemail.com"}
    # domain = email.split("@")[1] if "@" in email else ""
    # if domain in disposable_domains:
    #     raise ValueError("Disposable email addresses are not allowed")

    return email


def validate_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Validate phone number format.

    Accepts international format with optional + prefix.

    Args:
        phone: Phone number to validate (can be None)

    Returns:
        The validated phone number (normalized)

    Raises:
        ValueError: If phone number format is invalid

    Examples:
        >>> validate_phone_number("+1234567890")
        '+1234567890'
        >>> validate_phone_number("123-456-7890")
        '+1234567890'
    """
    if phone is None:
        return None

    # Strip whitespace and common separators
    cleaned = re.sub(r"[\s\-\(\)\.]+", "", phone)

    # Ensure it starts with + for international format
    if not cleaned.startswith("+"):
        # Assume US number if no country code
        cleaned = "+1" + cleaned

    # Validate format: + followed by 10-15 digits
    if not re.match(r"^\+\d{10,15}$", cleaned):
        raise ValueError(
            "Phone number must be in international format (e.g., +1234567890)"
        )

    return cleaned


def validate_username(username: str) -> str:
    """
    Validate username format.

    Requirements:
    - 3-30 characters
    - Alphanumeric plus underscore and hyphen
    - Must start with letter
    - Case-insensitive (stored lowercase)

    Args:
        username: Username to validate

    Returns:
        The validated username (lowercased)

    Raises:
        ValueError: If username format is invalid

    Examples:
        >>> validate_username("john_doe")
        'john_doe'
        >>> validate_username("user-123")
        'user-123'
    """
    # Strip whitespace and lowercase
    username = username.strip().lower()

    # Check length
    if len(username) < 3 or len(username) > 30:
        raise ValueError("Username must be between 3 and 30 characters")

    # Check format: alphanumeric plus underscore/hyphen, must start with letter
    if not re.match(r"^[a-z][a-z0-9_-]*$", username):
        raise ValueError(
            "Username must start with a letter and contain only letters, "
            "numbers, underscores, and hyphens"
        )

    # Optional: Check against reserved usernames
    # reserved = {"admin", "root", "system", "api", "support"}
    # if username in reserved:
    #     raise ValueError("This username is reserved")

    return username


def validate_permission_code(code: str) -> str:
    """
    Validate permission code format.

    Permission codes follow the format "resource:action" where both parts
    can be alphanumeric with underscores/hyphens, or wildcard (*).

    Valid formats:
    - "resource:action" - Specific permission (e.g., "user:create", "post:read")
    - "*:action" - All resources with specific action (e.g., "*:read")
    - "resource:*" - Specific resource with all actions (e.g., "user:*")
    - "*:*" - All permissions (superuser)

    Requirements:
    - Must contain exactly one colon (:)
    - Resource and action parts can contain: letters, numbers, underscore, hyphen, or *
    - Resource and action must be 1-50 characters each
    - Case-insensitive (stored lowercase)

    Args:
        code: Permission code to validate

    Returns:
        The validated permission code (lowercased and stripped)

    Raises:
        ValueError: If code doesn't match required format

    Examples:
        >>> validate_permission_code("user:create")
        'user:create'
        >>> validate_permission_code("*:*")
        '*:*'
        >>> validate_permission_code("post:read")
        'post:read'
        >>> validate_permission_code("invalid")  # doctest: +SKIP
        ValueError: Permission code must be in format 'resource:action'
    """
    # Strip whitespace and lowercase
    code = code.strip().lower()

    # Check for exactly one colon
    if ":" not in code:
        raise ValueError(
            "Permission code must be in format 'resource:action' (e.g., 'user:create')"
        )

    # Split into resource and action
    parts = code.split(":", 1)
    if len(parts) != 2:
        raise ValueError(
            "Permission code must be in format 'resource:action' (e.g., 'user:create')"
        )

    resource, action = parts

    # Validate resource part
    if not resource:
        raise ValueError("Resource part cannot be empty")
    if len(resource) > 50:
        raise ValueError("Resource part must be 50 characters or less")
    if not re.match(r"^[a-z0-9_*-]+$", resource):
        raise ValueError(
            "Resource must contain only letters, numbers, underscores, hyphens, or * (wildcard)"
        )

    # Validate action part
    if not action:
        raise ValueError("Action part cannot be empty")
    if len(action) > 50:
        raise ValueError("Action part must be 50 characters or less")
    if not re.match(r"^[a-z0-9_*-]+$", action):
        raise ValueError(
            "Action must contain only letters, numbers, underscores, hyphens, or * (wildcard)"
        )

    return code


def validate_role_code(code: str) -> str:
    """
    Validate role code format.

    Role codes are unique identifiers for roles in the system.

    Requirements:
    - 2-50 characters
    - Alphanumeric plus underscore and hyphen
    - Must start with letter
    - Case-insensitive (stored lowercase)
    - No colons (reserved for permission codes)

    Args:
        code: Role code to validate

    Returns:
        The validated role code (lowercased and stripped)

    Raises:
        ValueError: If code doesn't match required format

    Examples:
        >>> validate_role_code("admin")
        'admin'
        >>> validate_role_code("teacher")
        'teacher'
        >>> validate_role_code("super-admin")
        'super-admin'
    """
    # Strip whitespace and lowercase
    code = code.strip().lower()

    # Check length
    if len(code) < 2 or len(code) > 50:
        raise ValueError("Role code must be between 2 and 50 characters")

    # Check for colon (reserved for permission codes)
    if ":" in code:
        raise ValueError(
            "Role code cannot contain ':' (colon is reserved for permission codes)"
        )

    # Check format: alphanumeric plus underscore/hyphen, must start with letter
    if not re.match(r"^[a-z][a-z0-9_-]*$", code):
        raise ValueError(
            "Role code must start with a letter and contain only letters, "
            "numbers, underscores, and hyphens"
        )

    # Optional: Check against reserved role codes
    # reserved = {"system", "internal", "service"}
    # if code in reserved:
    #     raise ValueError("This role code is reserved for system use")

    return code

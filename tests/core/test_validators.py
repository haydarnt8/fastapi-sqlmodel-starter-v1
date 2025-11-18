"""
Tests for Validation Functions

Tests all shared validators for password, email, permission format, etc.
"""

import pytest
from app.core.validators import (
    validate_password_strength,
    validate_email_format,
    validate_permission_code,
    validate_role_code,
)


class TestPasswordStrengthValidation:
    """Test password strength validation."""

    def test_valid_strong_password(self):
        """Test that strong passwords pass validation."""
        valid_passwords = [
            "SecurePass123",
            "MyP@ssw0rd",
            "Strong1Pass",
            "Test1234Password",
            "Abcd1234",
        ]
        for password in valid_passwords:
            result = validate_password_strength(password)
            assert result == password

    def test_password_too_short(self):
        """Test that passwords shorter than 8 characters fail."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_strength("Short1")

    def test_password_no_uppercase(self):
        """Test that passwords without uppercase letters fail."""
        with pytest.raises(ValueError, match="uppercase letter"):
            validate_password_strength("lowercase123")

    def test_password_no_lowercase(self):
        """Test that passwords without lowercase letters fail."""
        with pytest.raises(ValueError, match="lowercase letter"):
            validate_password_strength("UPPERCASE123")

    def test_password_no_digit(self):
        """Test that passwords without digits fail."""
        with pytest.raises(ValueError, match="number"):
            validate_password_strength("NoDigitsHere")

    def test_password_empty_string(self):
        """Test that empty passwords fail."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_strength("")

    def test_password_with_spaces(self):
        """Test that passwords with spaces are allowed if other requirements met."""
        result = validate_password_strength("Pass Word 123")
        assert result == "Pass Word 123"


class TestEmailValidation:
    """Test email format validation."""

    def test_valid_emails(self):
        """Test that valid email formats pass and are normalized."""
        test_cases = [
            ("user@example.com", "user@example.com"),
            ("test.user@domain.co.uk", "test.user@domain.co.uk"),
            ("firstname+lastname@company.com", "firstname+lastname@company.com"),
            ("user123@test-domain.com", "user123@test-domain.com"),
            ("a@b.co", "a@b.co"),
        ]
        for email, expected in test_cases:
            result = validate_email_format(email)
            assert result == expected

    def test_email_normalization(self):
        """Test that emails are lowercased and stripped."""
        result = validate_email_format("  User@Example.COM  ")
        assert result == "user@example.com"

    def test_email_with_whitespace(self):
        """Test that whitespace is stripped."""
        result = validate_email_format("  test@example.com  ")
        assert result == "test@example.com"

    def test_email_case_insensitive(self):
        """Test that email validation handles different cases."""
        email = "User@Example.COM"
        result = validate_email_format(email)
        assert result == email.lower()


class TestPermissionCodeValidation:
    """Test permission code validation."""

    def test_valid_permission_codes(self):
        """Test that valid permission codes pass."""
        valid_codes = [
            "user:create",
            "user:read",
            "role:update",
            "audit:delete",
            "*:*",
            "user:*",
            "*:read",
        ]
        for code in valid_codes:
            result = validate_permission_code(code)
            assert result == code

    def test_invalid_permission_no_colon(self):
        """Test that permission codes without colon fail."""
        with pytest.raises(ValueError, match="resource:action"):
            validate_permission_code("usercreate")

    def test_invalid_permission_too_many_colons(self):
        """Test that permission codes with multiple colons are treated as resource:action."""
        # The code splits on first colon, so "user:create:extra" becomes resource="user", action="create:extra"
        # This will fail the regex validation on action part
        with pytest.raises(ValueError):
            validate_permission_code("user:create:extra")

    def test_invalid_permission_empty_resource(self):
        """Test that permission codes with empty resource fail."""
        with pytest.raises(ValueError, match="Resource part cannot be empty"):
            validate_permission_code(":create")

    def test_invalid_permission_empty_action(self):
        """Test that permission codes with empty action fail."""
        with pytest.raises(ValueError, match="Action part cannot be empty"):
            validate_permission_code("user:")

    def test_invalid_permission_spaces(self):
        """Test that permission codes with spaces fail."""
        with pytest.raises(ValueError):
            validate_permission_code("user : create")

    def test_invalid_permission_empty(self):
        """Test that empty permission code fails."""
        with pytest.raises(ValueError, match="resource:action"):
            validate_permission_code("")


class TestRoleCodeValidation:
    """Test role code validation."""

    def test_valid_role_codes(self):
        """Test that valid role codes pass."""
        valid_codes = [
            "admin",
            "user",
            "manager",
            "supervisor",
            "guest_user",
            "role123",
        ]
        for code in valid_codes:
            result = validate_role_code(code)
            assert result == code

    def test_invalid_role_code_uppercase(self):
        """Test that role codes with uppercase letters are converted to lowercase."""
        # Role codes are normalized to lowercase
        result = validate_role_code("Admin")
        assert result == "admin"

    def test_invalid_role_code_spaces(self):
        """Test that role codes with spaces fail."""
        with pytest.raises(ValueError):
            validate_role_code("admin user")

    def test_invalid_role_code_special_chars(self):
        """Test that role codes accept hyphens."""
        # Hyphens are allowed per the regex ^[a-z][a-z0-9_-]*$
        result = validate_role_code("admin-role")
        assert result == "admin-role"

    def test_invalid_role_code_too_short(self):
        """Test that role codes shorter than 2 characters fail."""
        with pytest.raises(ValueError, match="between 2 and 50 characters"):
            validate_role_code("a")

    def test_invalid_role_code_empty(self):
        """Test that empty role code fails."""
        with pytest.raises(ValueError, match="between 2 and 50 characters"):
            validate_role_code("")

    def test_valid_role_code_with_underscore(self):
        """Test that role codes with underscores are allowed."""
        result = validate_role_code("admin_user")
        assert result == "admin_user"

    def test_valid_role_code_with_numbers(self):
        """Test that role codes with numbers are allowed."""
        result = validate_role_code("role123")
        assert result == "role123"

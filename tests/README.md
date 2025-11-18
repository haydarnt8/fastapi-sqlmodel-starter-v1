# Test Suite Documentation

This directory contains comprehensive tests for the FastAPI SQLModel Starter application.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test configuration
├── README.md                   # This file
├── api/
│   └── v1/
│       ├── test_auth.py       # Authentication endpoint tests
│       ├── test_users.py      # User management endpoint tests
│       ├── test_roles.py      # Role management endpoint tests
│       ├── test_permissions.py # Permission endpoint tests
│       └── test_audit.py      # Audit log endpoint tests
├── crud/
│   ├── test_base_crud.py      # Base CRUD operations tests
│   ├── test_user_crud.py      # User CRUD tests
│   ├── test_role_crud.py      # Role CRUD tests
│   └── test_restore.py        # Soft delete & restore tests
├── core/
│   ├── test_security.py       # Security utilities tests
│   ├── test_permissions.py    # Permission checking tests
│   ├── test_config.py         # Configuration tests
│   └── test_cache.py          # Redis cache tests
└── models/
    ├── test_user_model.py     # User model tests
    ├── test_role_model.py     # Role model tests
    └── test_audit_fields.py   # Audit field tests
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test File
```bash
pytest tests/api/v1/test_auth.py
```

### Run Specific Test Class
```bash
pytest tests/api/v1/test_auth.py::TestLogin
```

### Run Specific Test Function
```bash
pytest tests/api/v1/test_auth.py::TestLogin::test_login_json_success
```

### Run Tests in Parallel (faster)
```bash
pytest -n auto
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Only Failed Tests from Last Run
```bash
pytest --lf
```

## Test Coverage Areas

### 1. Authentication Tests (test_auth.py)
- ✅ User registration
  - Valid registration
  - Duplicate email
  - Invalid email format
  - Weak password
- ✅ Login (JSON and form)
  - Successful login
  - Wrong password
  - Non-existent user
  - Inactive user
- ✅ Get current user (/me)
  - Authenticated access
  - Unauthorized access
  - Invalid token
- ✅ Logout
  - Successful logout
  - Token revocation
  - Subsequent requests fail
- ✅ Password change
  - Successful change
  - Wrong current password
  - Weak new password
  - Same as current
- ✅ Token refresh
  - Successful refresh
  - With revoked token
- ✅ Rate limiting
  - Multiple failed login attempts

### 2. User Management Tests (test_users.py)
- Create user (admin only)
- List users with pagination
- Get user by ID
- Update user
  - Own profile
  - Other users (admin only)
- Delete user (soft delete)
- Restore user (NEW!)
- Assign roles to user
- Permission checks

### 3. Role Management Tests (test_roles.py)
- Create role
- List roles
- Get role by ID
- Update role
- Delete role (soft delete)
- Restore role (NEW!)
- Assign permissions to role
- Role hierarchy checks

### 4. Permission Tests (test_permissions.py)
- Create permission
- List permissions
- Permission inheritance
- Wildcard permissions (*:*)
- Category-based permissions

### 5. Audit Log Tests (test_audit.py)
- Create audit logs
- Query audit logs
- Filter by action
- Filter by user
- Filter by date range

### 6. CRUD Tests (test_*_crud.py)
- Create operations
- Read operations (single, multiple)
- Update operations
- Delete operations (soft delete)
- Restore operations (NEW!)
- Pagination
- Filtering
- Sorting
- Audit field population

### 7. Soft Delete & Restore Tests (test_restore.py)
- Soft delete records
- Restore deleted records
- Cannot restore non-deleted records
- Audit trail for restoration
- Filter deleted records
- Include/exclude deleted in queries

### 8. Security Tests (test_security.py)
- Password hashing
- Password verification
- Token generation
- Token decoding
- Token expiration
- Token revocation
- Permission checking

### 9. Model Tests (test_*_model.py)
- Model creation
- Field validation
- Relationship loading
- Audit field auto-population
- Soft delete behavior
- Model methods (has_permission, etc.)

### 10. Cache Tests (test_cache.py)
- Redis connection
- Cache set/get
- Cache expiration
- Token blacklist
- Cache invalidation

## Test Fixtures

### Database Fixtures
- `test_engine` - In-memory SQLite database engine
- `test_session` - Fresh database session for each test
- `test_client` - FastAPI test client with overridden DB

### User Fixtures
- `admin_user` - Admin user with full permissions
- `regular_user` - Regular user with limited permissions
- `admin_token` - JWT token for admin user
- `user_token` - JWT token for regular user
- `auth_headers_admin` - Authorization headers for admin
- `auth_headers_user` - Authorization headers for regular user

### Role & Permission Fixtures
- `admin_role` - Admin role with *:* permission
- `user_role` - Basic user role
- `admin_permission` - Admin permission (*:*)
- `user_permissions` - Dict of user management permissions
- `role_permissions` - Dict of role management permissions

### Factory Fixtures
- `make_user` - Create test users dynamically
- `make_role` - Create test roles dynamically
- `make_permission` - Create test permissions dynamically

## Writing New Tests

### Test Class Structure
```python
class TestFeatureName:
    """Test description."""

    def test_success_case(self, test_client, auth_headers_admin):
        """Test successful operation."""
        response = test_client.post(
            "/api/v1/endpoint",
            json={"data": "value"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["field"] == "expected"

    def test_error_case(self, test_client):
        """Test error handling."""
        response = test_client.post("/api/v1/endpoint")

        assert response.status_code == 401
        assert "error" in response.json()["detail"].lower()
```

### Best Practices
1. **One assertion per concept** - Test one thing at a time
2. **Clear test names** - Describe what is being tested
3. **Use fixtures** - Reuse common setup code
4. **Test both success and failure** - Cover happy path and errors
5. **Test edge cases** - Null values, empty strings, etc.
6. **Test permissions** - Ensure authorization works
7. **Test audit trails** - Verify logging and tracking
8. **Clean test data** - Use fixtures that auto-cleanup

### Async Test Example
```python
@pytest.mark.asyncio
async def test_async_operation(test_session):
    """Test async database operation."""
    user = await user_crud.create(
        test_session,
        obj_in={"email": "test@test.com", "password": "pass"},
    )

    assert user.email == "test@test.com"
```

## Test Coverage Goals

Target: **90%+ code coverage**

Current coverage by module:
- app/api/v1/auth.py: ✅ 95%
- app/api/v1/users.py: ✅ 90%
- app/api/v1/roles.py: ✅ 90%
- app/crud/base.py: ✅ 95%
- app/core/security.py: ✅ 100%
- app/models/: ✅ 85%

## Continuous Integration

Tests run automatically on:
- Every commit (pre-commit hook)
- Every pull request (GitHub Actions)
- Every merge to main branch

### CI Configuration (.github/workflows/test.yml)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests Failing Locally
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Ensure Redis is running (for cache tests): `docker-compose up redis -d`
3. Clear pytest cache: `pytest --cache-clear`
4. Run with verbose output: `pytest -vv`

### Slow Tests
1. Use in-memory SQLite (already configured)
2. Run tests in parallel: `pytest -n auto`
3. Skip slow tests: `pytest -m "not slow"`

### Database Issues
1. Tests use in-memory SQLite, not your dev database
2. Each test gets a fresh database session
3. Transactions are rolled back after each test

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
- [Project README](../README.md)

# Development Guide

This guide covers local development setup, coding standards, testing, and debugging for the FastAPI Starter Template.

## Table of Contents

- [Local Development Setup](#local-development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Database Development](#database-development)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Development Tasks](#common-development-tasks)
- [Git Workflow](#git-workflow)
- [Code Review Checklist](#code-review-checklist)
- [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- PostgreSQL (optional, SQLite works for development)
- Redis (optional, but recommended)
- Code editor (VS Code recommended)

### Initial Setup

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd fastapi-sqlmodel-starter-v1
```

2. **Create virtual environment**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

3. **Install dependencies**

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
python --version  # Should be 3.11+
pip list
```

4. **Configure environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
nano .env  # or your preferred editor
```

**Minimal development .env:**

```bash
ENVIRONMENT=development
DEBUG=true
RELOAD=true

DATABASE_URL=sqlite+aiosqlite:///./dev.db
DB_ECHO=true  # See SQL queries in console

SECRET_KEY=dev-secret-key-not-for-production
ALGORITHM=HS256

REDIS_ENABLED=false  # Can work without Redis in dev

LOG_LEVEL=DEBUG
LOG_FORMAT=text  # Human-readable logs
```

5. **Run the application**

```bash
# Run with auto-reload
python -m uvicorn app.main:app --reload

# Or with custom port
python -m uvicorn app.main:app --reload --port 8001

# Or with host binding
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the application**

- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

### IDE Setup (VS Code)

1. **Install recommended extensions**

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker"
  ]
}
```

2. **Configure VS Code settings**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.rulers": [88]
  }
}
```

3. **Create launch configuration**

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true,
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

---

## Project Structure

```
fastapi-sqlmodel-starter-v1/
├── app/                        # Application code
│   ├── __init__.py
│   ├── main.py                # Application entry point
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── deps.py           # Dependencies (auth, db session)
│   │   └── v1/               # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py       # Authentication endpoints
│   │       ├── users.py      # User management
│   │       ├── roles.py      # Role management
│   │       └── audit.py      # Audit log queries
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration (Pydantic Settings)
│   │   ├── security.py       # Auth & security utilities
│   │   ├── logging.py        # Logging configuration
│   │   └── cache.py          # Redis cache service
│   ├── db/                    # Database
│   │   ├── __init__.py
│   │   ├── session.py        # Database connection & session
│   │   └── init_db.py        # Database initialization & seeding
│   ├── models/                # SQLModel database models
│   │   ├── __init__.py
│   │   ├── user.py           # User model
│   │   ├── role.py           # Role model
│   │   ├── permission.py     # Permission definitions
│   │   └── audit_log.py      # Audit log model
│   ├── schemas/               # Pydantic schemas (API contracts)
│   │   ├── __init__.py
│   │   ├── common.py         # Common schemas (responses, pagination)
│   │   ├── user.py           # User schemas
│   │   ├── role.py           # Role schemas
│   │   ├── auth.py           # Auth schemas (login, token)
│   │   └── audit.py          # Audit log schemas
│   ├── middleware/            # Custom middleware
│   │   ├── __init__.py
│   │   ├── rate_limit.py     # Rate limiting
│   │   ├── request_logging.py # Request logging
│   │   └── security_headers.py # Security headers
│   └── i18n/                  # Internationalization
│       ├── __init__.py
│       ├── translator.py     # Translation logic
│       └── locales/          # Translation files
│           ├── en.json       # English
│           └── ar.json       # Arabic
├── docs/                      # Documentation
│   ├── API.md                # API usage examples
│   ├── DEPLOYMENT.md         # Production deployment
│   └── DEVELOPMENT.md        # This file
├── tests/                     # Test files (to be created)
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration
│   ├── test_auth.py          # Auth endpoint tests
│   ├── test_users.py         # User endpoint tests
│   └── test_security.py      # Security tests
├── .env.example               # Example environment variables
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
└── README.md                 # Project overview
```

### Key Directories Explained

- **app/api/**: All API endpoints organized by version (v1, v2, etc.)
- **app/core/**: Core utilities and configuration
- **app/models/**: Database models (SQLModel - combines SQLAlchemy and Pydantic)
- **app/schemas/**: API request/response schemas (pure Pydantic)
- **app/middleware/**: Custom middleware for cross-cutting concerns
- **app/i18n/**: Internationalization and translation support

---

## Coding Standards

### Python Style Guide

Follow **PEP 8** with these tools:

1. **Black** - Code formatter (line length: 88)
2. **isort** - Import sorting
3. **flake8** - Linting
4. **mypy** - Type checking (optional but recommended)

### Code Formatting

```bash
# Install dev dependencies
pip install black isort flake8 mypy

# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type check
mypy app/
```

### Type Hints

Always use type hints:

```python
# Good
def get_user(user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

# Bad
def get_user(user_id):
    return db.query(User).filter(User.id == user_id).first()
```

### Docstrings

Use Google-style docstrings:

```python
def create_user(email: str, password: str, full_name: str) -> User:
    """
    Create a new user.

    Args:
        email: User's email address
        password: User's password (will be hashed)
        full_name: User's full name

    Returns:
        User: The created user object

    Raises:
        ValueError: If email already exists
    """
    # Implementation
```

### Naming Conventions

```python
# Classes: PascalCase
class UserRole:
    pass

# Functions/Methods: snake_case
def get_current_user():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 5

# Private: prefix with underscore
def _internal_helper():
    pass

# Modules: lowercase
# user_service.py (not UserService.py)
```

### Import Order

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party packages
from fastapi import FastAPI, HTTPException
from sqlmodel import select

# 3. Local imports
from app.core.config import settings
from app.models.user import User
```

---

## Database Development

### Using SQLite (Development)

SQLite is perfect for development - no installation required:

```bash
# In .env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
DB_ECHO=true  # See all SQL queries
```

View database:

```bash
# Install SQLite CLI
brew install sqlite  # macOS
sudo apt-get install sqlite3  # Linux

# Open database
sqlite3 dev.db

# Useful commands
.tables          # List all tables
.schema users    # Show table schema
SELECT * FROM users LIMIT 5;
.quit
```

### Using PostgreSQL (Recommended for Production-like Development)

```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt-get install postgresql  # Linux

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# Create database
createdb dev_db

# In .env
DATABASE_URL=postgresql+asyncpg://localhost/dev_db
DB_ECHO=true
```

### Database Migrations with Alembic

Alembic tracks database schema changes:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic (first time only)
alembic init migrations

# Edit alembic.ini to use your DATABASE_URL
# Or better: Configure to read from env

# Create migration
alembic revision --autogenerate -m "Add user roles"

# Review migration file in migrations/versions/

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View history
alembic history
```

**Configure Alembic to use app config:**

Edit `migrations/env.py`:

```python
from app.core.config import settings
from app.models import *  # Import all models

# Set target metadata
target_metadata = SQLModel.metadata

# Set database URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

### Seeding Data

The app auto-creates an admin user on startup. To add more seed data:

Edit `app/db/init_db.py`:

```python
async def seed_data(session: AsyncSession):
    """Seed development data."""
    # Add test users
    test_user = User(
        email="test@test.com",
        full_name="Test User",
        hashed_password=get_password_hash("test123")
    )
    session.add(test_user)
    await session.commit()
```

---

## Testing

### Setting Up Tests

```bash
# Install pytest and dependencies
pip install pytest pytest-asyncio httpx

# Create tests directory
mkdir -p tests
```

### Example Test Structure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, SQLModel, Session
from app.main import app
from app.api.deps import get_session

# Test database
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

```python
# tests/test_auth.py
def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "secure123",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@test.com"

def test_login(client):
    # First register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@test.com",
            "password": "password123",
            "full_name": "Test User"
        }
    )

    # Then login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Test Database

Always use a separate test database:

```python
# tests/conftest.py
TEST_DATABASE_URL = "sqlite:///./test.db"
# or
TEST_DATABASE_URL = "postgresql://localhost/test_db"
```

---

## Debugging

### Debugging with Print Statements

```python
# Use logging instead of print
from app.core.logging import get_logger

logger = get_logger(__name__)

@app.get("/debug")
async def debug_endpoint():
    logger.debug("Debug information")
    logger.info("Informational message")
    logger.warning("Warning message")
    logger.error("Error message")
    return {"status": "ok"}
```

### Debugging with VS Code

1. Set breakpoints in your code (click left of line number)
2. Press F5 to start debugging
3. Use Debug Console to inspect variables

### Debugging SQL Queries

```bash
# In .env
DB_ECHO=true
```

This will print all SQL queries to console.

### Debugging Async Code

```python
import asyncio

# Print async context
async def debug_async():
    current_task = asyncio.current_task()
    logger.debug(f"Current task: {current_task}")

    # Get all tasks
    all_tasks = asyncio.all_tasks()
    logger.debug(f"All tasks: {all_tasks}")
```

### Using Python Debugger (pdb)

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()

# Commands:
# n - next line
# s - step into function
# c - continue
# p variable - print variable
# l - list code
# q - quit
```

### Debug HTTP Requests

```bash
# Use curl with verbose output
curl -v http://localhost:8000/api/v1/users

# Or use httpie
http -v GET http://localhost:8000/api/v1/users
```

---

## Common Development Tasks

### Adding a New Endpoint

1. **Create schema** in `app/schemas/`

```python
# app/schemas/product.py
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str | None = None

class ProductRead(BaseModel):
    id: int
    name: str
    price: float
    description: str | None
```

2. **Create model** in `app/models/`

```python
# app/models/product.py
from sqlmodel import Field, SQLModel

class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float
    description: str | None = None
```

3. **Create endpoint** in `app/api/v1/`

```python
# app/api/v1/products.py
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.deps import get_session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter()

@router.post("/", response_model=ProductRead)
async def create_product(
    product: ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    db_product = Product.model_validate(product)
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product
```

4. **Register router** in `app/main.py`

```python
from app.api.v1 import products

app.include_router(
    products.router,
    prefix=f"{settings.API_V1_PREFIX}/products",
    tags=["products"]
)
```

### Adding a New Permission

1. **Define permission** in `app/models/permission.py`

```python
PERMISSIONS = {
    "PRODUCT_CREATE": ("product:create", "Create Product", "product", "create"),
    "PRODUCT_READ": ("product:read", "Read Product", "product", "read"),
    "PRODUCT_UPDATE": ("product:update", "Update Product", "product", "update"),
    "PRODUCT_DELETE": ("product:delete", "Delete Product", "product", "delete"),
}
```

2. **Use in endpoint**

```python
from app.core.security import require_permission

@router.delete("/{product_id}")
@require_permission("product:delete")
async def delete_product(product_id: int):
    # Implementation
    pass
```

### Resetting Database

```bash
# Delete SQLite database
rm dev.db

# Or truncate all tables (PostgreSQL)
python -c "from app.db.session import engine; from app.models import SQLModel; SQLModel.metadata.drop_all(engine); SQLModel.metadata.create_all(engine)"

# Restart app to recreate tables and seed data
python -m uvicorn app.main:app --reload
```

---

## Git Workflow

### Branch Naming

```bash
# Features
git checkout -b feature/user-profile

# Bug fixes
git checkout -b fix/login-error

# Hotfixes
git checkout -b hotfix/security-patch

# Refactoring
git checkout -b refactor/auth-module
```

### Commit Messages

Follow conventional commits:

```bash
# Format: <type>: <description>

# Examples:
git commit -m "feat: add product CRUD endpoints"
git commit -m "fix: resolve rate limiting bug"
git commit -m "docs: update API documentation"
git commit -m "refactor: simplify auth logic"
git commit -m "test: add user endpoint tests"
git commit -m "chore: update dependencies"
```

### Before Committing

```bash
# Format code
black app/
isort app/

# Run linter
flake8 app/

# Run tests
pytest

# Check for security issues
pip-audit

# Then commit
git add .
git commit -m "feat: add new feature"
```

---

## Code Review Checklist

When reviewing code (or before submitting):

### Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all endpoints
- [ ] Proper authorization checks
- [ ] No SQL injection vulnerabilities
- [ ] No sensitive data in logs

### Code Quality
- [ ] Follows PEP 8 style guide
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] No code duplication
- [ ] Proper error handling

### Testing
- [ ] Tests added for new features
- [ ] All tests passing
- [ ] Edge cases covered
- [ ] Error cases tested

### Documentation
- [ ] API docs updated (if endpoints changed)
- [ ] README updated (if major changes)
- [ ] Comments explain "why", not "what"

### Performance
- [ ] No N+1 queries
- [ ] Database indexes on frequently queried fields
- [ ] Async/await used correctly
- [ ] No blocking operations

---

## Troubleshooting

### "Module not found" errors

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check PYTHONPATH
echo $PYTHONPATH
```

### Database connection errors

```bash
# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# For PostgreSQL, ensure it's running
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# For SQLite, check file permissions
ls -la dev.db
```

### Redis connection errors

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Or disable Redis for development
# In .env:
REDIS_ENABLED=false
```

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
python -m uvicorn app.main:app --reload --port 8001
```

### Import errors

```bash
# Ensure you're in project root
pwd

# Run from project root
python -m uvicorn app.main:app --reload

# Not from app directory:
cd app
python -m uvicorn main:app --reload  # This won't work!
```

---

## Performance Tips

### Database Query Optimization

```python
# Bad: N+1 query
users = await session.exec(select(User))
for user in users:
    roles = await user.roles  # Separate query per user!

# Good: Eager loading
from sqlmodel import selectinload

users = await session.exec(
    select(User).options(selectinload(User.roles))
)
for user in users:
    roles = user.roles  # Already loaded!
```

### Caching

```python
from app.core.cache import get_redis_cache

cache = await get_redis_cache()

# Cache expensive operations
cached_result = await cache.get(f"user:{user_id}")
if cached_result:
    return cached_result

result = await expensive_operation()
await cache.set(f"user:{user_id}", result, ttl=300)
return result
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [Python AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [PEP 8 Style Guide](https://pep8.org)

---

**Happy Coding!**

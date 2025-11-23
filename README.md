# FastAPI Starter Template

A production-grade FastAPI starter template with authentication, RBAC, audit logging, and security best practices.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![SQLModel](https://img.shields.io/badge/SQLModel-latest-orange.svg)](https://sqlmodel.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Restaurant Supply Chain Project

This starter is being extended to build a **Restaurant Supply Chain Ordering System** for the Iraqi market. See the complete product documentation:

- **[Product Requirements Document (PRD)](docs/PRD_RESTAURANT_SUPPLY_CHAIN.md)** - Complete product vision and requirements
- **[Work Breakdown Structure](docs/WORK_BREAKDOWN.md)** - Detailed phase-by-phase task breakdown (3 phases × 4 weeks each)
- **[Feature Mapping](docs/FEATURE_MAPPING.md)** - How existing features map to new requirements
- **[Database Schema](docs/DATABASE_SCHEMA_SUPPLY_CHAIN.md)** - Complete database design with SQL
- **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - 12-week sprint-by-sprint plan
- **[Quick Start Guide](docs/QUICK_START_SUPPLY_CHAIN.md)** - Developer onboarding (30 minutes)

## Features

### Core Features
- **FastAPI Framework** - Modern, fast, async Python web framework
- **SQLModel ORM** - Type-safe database models with Pydantic validation
- **Async/Await** - Full async support for high performance
- **Auto-generated API Docs** - Interactive Swagger UI and ReDoc

### Authentication & Authorization
- **JWT Authentication** - Access and refresh token support
- **Token Blacklisting** - Redis-based token revocation on logout
- **Role-Based Access Control (RBAC)** - Dynamic permission system with wildcard matching
- **Hierarchical Roles** - Priority-based role inheritance
- **Password Security** - Argon2 hashing (OWASP recommended)

### Security
- **OWASP Security Headers** - CSP, HSTS, X-Frame-Options, etc.
- **Rate Limiting** - Redis-backed request throttling (SlowAPI)
- **CORS Configuration** - Configurable cross-origin policies
- **Input Validation** - Pydantic models for all endpoints
- **SQL Injection Protection** - SQLModel ORM with parameterized queries
- **Secret Key Validation** - Production safety checks

### Observability & Monitoring
- **Comprehensive Audit Logging** - Track all user actions with full context
- **Structured Logging** - JSON logs with request tracing
- **Admin Audit API** - Query and analyze audit logs
- **Request/Response Logging** - Configurable request tracing middleware

### Data Integrity & Audit Trail
- **Automatic Audit Fields** - Track who created/updated/deleted every record
- **Timestamp Tracking** - Automatic created_at and updated_at on all models
- **Soft Delete** - Recoverable deletion with full audit trail
- **User Tracking** - Foreign keys to track created_by_id, updated_by_id, deleted_by_id
- **Compliance Ready** - GDPR, SOC2, HIPAA audit requirements built-in

### Developer Experience
- **Type Safety** - Full type hints throughout codebase
- **Environment-based Config** - Pydantic settings with .env support
- **Code Documentation** - Extensive inline comments explaining "why"
- **Database Migrations** - Alembic for schema versioning and migrations
- **Pre-commit Hooks** - Automated code quality checks (formatting, linting, security)
- **Error Handling** - Consistent error responses

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Redis (optional, but recommended for production)
- PostgreSQL or SQLite (SQLite included for development)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd fastapi-sqlmodel-starter-v1
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

### First Login

On first startup, a superuser account is automatically created:

- **Email**: `admin@example.com`
- **Password**: `changeme123`

**IMPORTANT**: Change this password immediately in production!

## Project Structure

```
fastapi-sqlmodel-starter-v1/
├── app/
│   ├── api/              # API endpoints
│   │   └── v1/           # API version 1
│   │       ├── auth.py   # Authentication endpoints
│   │       ├── users.py  # User management
│   │       ├── roles.py  # Role management
│   │       └── audit.py  # Audit log queries
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration management
│   │   ├── security.py   # Authentication & security
│   │   ├── logging.py    # Logging configuration
│   │   └── cache.py      # Redis cache service
│   ├── db/               # Database
│   │   ├── session.py    # Database connection
│   │   └── init_db.py    # Database initialization & seeding
│   ├── models/           # SQLModel database models
│   │   ├── user.py       # User model
│   │   ├── role.py       # Role & permission models
│   │   └── audit_log.py  # Audit log model
│   ├── schemas/          # Pydantic schemas (request/response)
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── auth.py
│   │   └── audit.py
│   ├── middleware/       # Custom middleware
│   │   ├── rate_limit.py        # Rate limiting
│   │   ├── request_logging.py   # Request logging
│   │   └── security_headers.py  # Security headers
│   └── main.py           # Application entry point
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | deployment environment (development/staging/production) | `development` |
| `SECRET_KEY` | JWT signing key (MUST change in production!) | (insecure default) |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./dev.db` |
| `REDIS_ENABLED` | Enable Redis for caching and rate limiting | `True` |
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `True` |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |

## Database Migrations

This project uses **Alembic** for database schema management. Migrations allow you to version control your database schema changes and apply them incrementally.

### Quick Start

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Apply all pending migrations
alembic upgrade head
```

### Common Migration Tasks

**Create a new migration** after modifying models:
```bash
alembic revision --autogenerate -m "Add new field to user table"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback last migration**:
```bash
alembic downgrade -1
```

### For Detailed Instructions

See the complete migration guide: [docs/MIGRATIONS.md](docs/MIGRATIONS.md)

The migration guide covers:
- Creating and applying migrations
- Data migrations
- Production deployment
- Troubleshooting common issues
- Best practices

## Audit Fields & Soft Delete

Every model in this template automatically tracks WHO created/modified/deleted records and WHEN these changes happened.

### Quick Example

```python
from app.models.base import BaseModel
from sqlmodel import Field
from uuid import uuid4

class Product(BaseModel, table=True):
    """Product model - automatically gets all audit fields!"""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    price: float

# Automatically included (no code needed):
# - created_at: datetime
# - updated_at: datetime
# - created_by_id: UUID
# - updated_by_id: UUID
# - is_deleted: bool
# - deleted_at: datetime
# - deleted_by_id: UUID
```

### Using Audit Fields in Endpoints

```python
@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:create")),
):
    # Pass current_user.id to track who created it
    product = await product_crud.create(
        session,
        obj_in=product_data,
        created_by_id=current_user.id,  # Audit tracking!
    )
    return product
```

### Soft Delete (Recoverable)

```python
# Soft delete (default) - recoverable
await product_crud.delete(
    session,
    id=product_id,
    deleted_by_id=current_user.id,
)
# Record still exists with is_deleted=True

# Hard delete (permanent) - use sparingly!
await product_crud.delete(
    session,
    id=product_id,
    deleted_by_id=current_user.id,
    hard_delete=True,
)
```

### What You Get

- **Automatic timestamps** - created_at and updated_at on every record
- **User tracking** - Know who created, modified, and deleted each record
- **Soft delete** - Mark as deleted without losing data (recoverable)
- **Compliance ready** - GDPR, SOC2, HIPAA audit requirements built-in
- **Query filtering** - Deleted records automatically excluded from queries
- **Zero overhead** - Just inherit from `BaseModel` and it's done!

### For Complete Documentation

See the complete audit fields guide: [docs/AUDIT_FIELDS.md](docs/AUDIT_FIELDS.md)

The guide covers:
- Detailed field descriptions
- CRUD operation examples
- Endpoint implementation patterns
- Soft delete vs hard delete
- Querying and restoring deleted records
- Best practices and common patterns

## Code Quality & Pre-commit Hooks

This project uses **pre-commit hooks** to automatically check code quality before each commit. Hooks include code formatting, linting, type checking, and security scanning.

### Quick Start

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Hooks will now run automatically on git commit
git add .
git commit -m "Your changes"
```

### Manual Execution

Run all hooks on all files:
```bash
pre-commit run --all-files
```

Run specific hooks:
```bash
pre-commit run black --all-files     # Format code
pre-commit run ruff --all-files      # Lint code
pre-commit run mypy --all-files      # Type check
```

### Available Hooks

- **Black** - Code formatting (auto-fixes)
- **isort** - Import sorting (auto-fixes)
- **Ruff** - Fast Python linting (auto-fixes many issues)
- **mypy** - Static type checking
- **Bandit** - Security vulnerability scanning
- **YAML/JSON/TOML validators** - Config file validation
- **Trailing whitespace removal** - File cleanup

### For Detailed Instructions

See the complete pre-commit guide: [docs/PRE_COMMIT.md](docs/PRE_COMMIT.md)

The guide covers:
- Installation and setup
- Hook configuration
- Troubleshooting common issues
- Best practices for team workflows
- Customizing hooks

## API Documentation

### Authentication Endpoints

```http
POST /api/v1/auth/register     # Register new user
POST /api/v1/auth/login        # Login (returns access + refresh tokens)
POST /api/v1/auth/refresh      # Refresh access token
POST /api/v1/auth/logout       # Logout (blacklist token)
GET  /api/v1/auth/me           # Get current user info
```

### User Management (Admin Only)

```http
GET    /api/v1/users           # List users (with pagination)
POST   /api/v1/users           # Create user
GET    /api/v1/users/{id}      # Get user details
PUT    /api/v1/users/{id}      # Update user
DELETE /api/v1/users/{id}      # Delete user
PUT    /api/v1/users/{id}/roles # Update user roles
```

### Role Management (Admin Only)

```http
GET    /api/v1/roles           # List roles
POST   /api/v1/roles           # Create role
GET    /api/v1/roles/{id}      # Get role details
PUT    /api/v1/roles/{id}      # Update role
DELETE /api/v1/roles/{id}      # Delete role
PUT    /api/v1/roles/{id}/permissions # Update role permissions
```

### Audit Logs (Admin Only)

```http
GET /api/v1/audit/logs         # Query audit logs (with filters)
GET /api/v1/audit/logs/{id}    # Get specific audit log
GET /api/v1/audit/stats        # Get audit statistics
GET /api/v1/audit/actions      # List all audit action types
GET /api/v1/audit/user/{id}/activity # Get user activity history
```

For detailed examples, see [docs/API.md](docs/API.md).

## Security Best Practices

This template implements security best practices out of the box:

1. **Password Security**
   - Argon2 hashing (OWASP recommended)
   - Strong password validation (min 8 chars)
   - No password logging

2. **Token Security**
   - Short-lived access tokens (30 min)
   - Long-lived refresh tokens (7 days)
   - Token revocation on logout (Redis blacklist)
   - Token validation on every request

3. **API Security**
   - Rate limiting to prevent brute force
   - CORS configuration
   - Security headers (OWASP)
   - Input validation on all endpoints

4. **Database Security**
   - Parameterized queries (SQLModel)
   - No raw SQL execution
   - Soft deletes for audit trail

5. **Production Safety**
   - SECRET_KEY validation (prevents weak keys in production)
   - Environment-based configuration
   - Secure defaults

## RBAC System

The template includes a flexible RBAC system with:

### Predefined Roles

- **admin**: Full system access (`*:*` permission)
- **manager**: User management capabilities
- **user**: Standard user access

### Permission Format

Permissions follow the pattern: `resource:action`

Examples:
- `user:create` - Create users
- `user:*` - All user operations
- `*:read` - Read all resources
- `*:*` - Full access (superadmin)

### Custom Permissions

Easily add custom permissions in `app/models/permission.py`:

```python
PERMISSIONS = {
    "PRODUCT_CREATE": ("product:create", "Create Product", "product", "create"),
    "PRODUCT_READ": ("product:read", "Read Product", "product", "read"),
    # ... more permissions
}
```

## Audit Logging

All significant actions are automatically logged:

- User authentication (login/logout)
- User management (create/update/delete)
- Role management
- Permission changes

Each audit log includes:
- Actor (who performed the action)
- Action type
- Resource affected
- IP address and user agent
- Timestamp
- Before/after values for updates
- Success/failure status

Query audit logs via the `/api/v1/audit/*` endpoints.

## Development

### Running in Development Mode

```bash
# With auto-reload
python -m uvicorn app.main:app --reload

# With debug logging
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

### Database Migrations

This template is ready for Alembic migrations:

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for more development tips.

## Production Deployment

### Environment Variables

Before deploying to production, configure these critical variables:

```bash
ENVIRONMENT=production
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_ENABLED=true
REDIS_HOST=your-redis-host
REDIS_PASSWORD=your-redis-password
```

### Production Checklist

- [ ] Change `SECRET_KEY` to a cryptographically secure value
- [ ] Update `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Enable Redis for caching and rate limiting
- [ ] Set up HTTPS/TLS
- [ ] Configure CORS origins for your frontend
- [ ] Review rate limit settings
- [ ] Set up monitoring and log aggregation
- [ ] Configure backup strategy
- [ ] Review security headers for your use case

See deployment guides:

- [Production Deployment Guide](docs/DEPLOYMENT.md) - Docker, Kubernetes, traditional servers
- [Railway Deployment](docs/QUICKSTART_RAILWAY.md) - $5 free credit, best performance
- [Replit Deployment](docs/QUICKSTART_REPLIT.md) - 100% FREE, no credit card required

## Customization

This template is designed to be easily customized for your specific needs:

1. **Add Your Domain Models**
   - Create models in `app/models/`
   - Add schemas in `app/schemas/`
   - Create API endpoints in `app/api/v1/`

2. **Customize Permissions**
   - Update `PERMISSIONS` in `app/models/permission.py`
   - Update `ROLES` in `app/models/role.py`

3. **Add Middleware**
   - Create middleware in `app/middleware/`
   - Register in `app/main.py`

4. **Extend Audit Logging**
   - Add custom actions in `app/models/audit_log.py`
   - Use `create_audit_log()` helper in your endpoints

## Technology Stack

- **[FastAPI](https://fastapi.tiangolo.com)** - Web framework
- **[SQLModel](https://sqlmodel.tiangolo.com)** - ORM (SQLAlchemy + Pydantic)
- **[Pydantic](https://docs.pydantic.dev)** - Data validation
- **[Uvicorn](https://www.uvicorn.org)** - ASGI server
- **[Redis](https://redis.io)** - Caching and token blacklisting
- **[Argon2](https://pypi.org/project/argon2-cffi/)** - Password hashing
- **[SlowAPI](https://github.com/laurentS/slowapi)** - Rate limiting
- **[python-jose](https://github.com/mpdavis/python-jose)** - JWT handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on GitHub.

## Acknowledgments

Built with best practices from:
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [OWASP Security Guidelines](https://owasp.org)
- [12 Factor App](https://12factor.net)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Star this repo if you find it helpful!**

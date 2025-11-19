# Quick Start Guide: Restaurant Supply Chain Development

**Welcome to the team!** This guide will get you up and running in 30 minutes.

---

## What We're Building

A **B2B marketplace** connecting restaurants with food suppliers in Iraq, replacing WhatsApp-based ordering with a modern digital platform.

**Key Features:**
- Digital ordering with order history
- Real-time pricing transparency
- Delivery scheduling and tracking
- Multi-language support (Arabic, English)
- Payment integration (Cash, Bank Transfer)

---

## Prerequisites

Before you begin, install:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **PostgreSQL 15+** ([Download](https://www.postgresql.org/download/))
- **Redis 7+** ([Download](https://redis.io/download))
- **Git** ([Download](https://git-scm.com/downloads))

**Optional (for full stack):**
- Node.js 18+ (for mobile app development)
- Docker Desktop (for containerized development)

---

## Step 1: Clone & Setup (5 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd fastapi-sqlmodel-starter-v1

# Checkout the supply chain branch
git checkout Supply-Chain

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (code quality)
pre-commit install
```

---

## Step 2: Configure Environment (5 minutes)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your favorite editor
```

**Minimum required settings:**

```env
# Application
APP_NAME="Supply Chain API"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-min-32-chars  # Generate with: openssl rand -hex 32

# Database (Development - SQLite)
DATABASE_URL=sqlite+aiosqlite:///./dev.db

# Database (Production - PostgreSQL)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/supply_chain

# Redis (optional for development)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# First superuser account
FIRST_SUPERUSER_EMAIL=admin@example.com
FIRST_SUPERUSER_PASSWORD=changeme123

# CORS (allow frontend)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:19006"]
```

---

## Step 3: Database Setup (5 minutes)

```bash
# Run migrations (creates all tables)
alembic upgrade head

# Seed initial data (roles, permissions, admin user)
python -m app.db.init_db

# Verify database
sqlite3 dev.db  # or psql for PostgreSQL
> .tables  # Should see: users, roles, permissions, etc.
> SELECT * FROM users;  # Should see admin user
> .quit
```

---

## Step 4: Start the Server (2 minutes)

```bash
# Start the API server
uvicorn app.main:app --reload

# Server will start at:
# http://localhost:8000
```

**Test it's working:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","database":"connected","redis":"connected"}
```

---

## Step 5: Explore the API (5 minutes)

Open your browser to:

- **Swagger UI (Interactive Docs):** http://localhost:8000/docs
- **ReDoc (Alternative Docs):** http://localhost:8000/redoc

**Try the authentication:**

1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/auth/login`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "email": "admin@example.com",
     "password": "changeme123"
   }
   ```
5. Click "Execute"
6. Copy the `access_token` from the response
7. Click "Authorize" button (top right)
8. Paste token: `Bearer <your-token>`
9. Now you can test protected endpoints!

---

## Step 6: Run Tests (5 minutes)

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/api/v1/test_auth.py -v

# Run with coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

---

## Step 7: Development Workflow (3 minutes)

### Create a New Feature

```bash
# 1. Create a feature branch
git checkout -b feature/product-catalog

# 2. Make your changes
# - Add models: app/models/product.py
# - Add schemas: app/schemas/product.py
# - Add CRUD: app/crud/product.py
# - Add endpoints: app/api/v1/products.py

# 3. Create migration
alembic revision --autogenerate -m "Add product table"

# 4. Apply migration
alembic upgrade head

# 5. Run tests
pytest tests/api/v1/test_products.py -v

# 6. Pre-commit checks (runs automatically on commit)
pre-commit run --all-files

# 7. Commit changes
git add .
git commit -m "feat: add product catalog endpoints"

# 8. Push and create PR
git push origin feature/product-catalog
```

---

## Project Structure Overview

```
fastapi-sqlmodel-starter-v1/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── auth.py          # ✅ Authentication (login, register)
│   │   ├── users.py         # ✅ User management
│   │   ├── roles.py         # ✅ Role management
│   │   ├── restaurants.py   # ⏳ TODO: Restaurant endpoints
│   │   ├── suppliers.py     # ⏳ TODO: Supplier endpoints
│   │   ├── products.py      # ⏳ TODO: Product catalog
│   │   └── orders.py        # ⏳ TODO: Order management
│   │
│   ├── core/                # Core functionality
│   │   ├── config.py        # ✅ Configuration
│   │   ├── security.py      # ✅ JWT, password hashing
│   │   ├── cache.py         # ✅ Redis service
│   │   └── logging.py       # ✅ Logging setup
│   │
│   ├── db/                  # Database
│   │   ├── session.py       # ✅ Database connection
│   │   └── init_db.py       # ✅ Database seeding
│   │
│   ├── models/              # SQLModel database models
│   │   ├── base.py          # ✅ Base model with audit fields
│   │   ├── user.py          # ✅ User model
│   │   ├── role.py          # ✅ Role/Permission models
│   │   ├── restaurant.py    # ⏳ TODO: Restaurant model
│   │   ├── supplier.py      # ⏳ TODO: Supplier model
│   │   ├── product.py       # ⏳ TODO: Product model
│   │   └── order.py         # ⏳ TODO: Order model
│   │
│   ├── schemas/             # Pydantic schemas (API)
│   │   ├── user.py          # ✅ User DTOs
│   │   ├── auth.py          # ✅ Auth DTOs
│   │   └── ...              # More schemas
│   │
│   ├── crud/                # CRUD operations
│   │   ├── base.py          # ✅ Generic CRUD class
│   │   ├── user.py          # ✅ User CRUD
│   │   └── ...              # More CRUD
│   │
│   ├── middleware/          # Custom middleware
│   │   ├── rate_limit.py    # ✅ Rate limiting
│   │   └── ...
│   │
│   └── main.py              # ✅ Application entry point
│
├── tests/                   # Tests
│   ├── api/v1/              # API endpoint tests
│   ├── core/                # Core functionality tests
│   └── models/              # Model tests
│
├── docs/                    # Documentation
│   ├── PRD_RESTAURANT_SUPPLY_CHAIN.md        # 📋 Product requirements
│   ├── FEATURE_MAPPING.md                     # 🗺️ Feature mapping
│   ├── DATABASE_SCHEMA_SUPPLY_CHAIN.md        # 🗄️ Database design
│   ├── IMPLEMENTATION_ROADMAP.md              # 🚀 12-week roadmap
│   └── QUICK_START_SUPPLY_CHAIN.md            # 👋 This file
│
├── alembic/                 # Database migrations
│   └── versions/            # Migration files
│
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md                # Main documentation
```

---

## Common Commands Cheatsheet

### Development

```bash
# Start API server (with auto-reload)
uvicorn app.main:app --reload

# Start API server (with debug logs)
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Start on custom port
uvicorn app.main:app --reload --port 8001

# Start Celery worker (for background tasks)
celery -A app.tasks worker --loglevel=info
```

### Database

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check current migration
alembic current

# View migration history
alembic history
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/api/v1/test_auth.py

# Run specific test function
pytest tests/api/v1/test_auth.py::test_login_success

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run only failed tests
pytest --lf
```

### Code Quality

```bash
# Run pre-commit checks
pre-commit run --all-files

# Format code (Black)
black app/ tests/

# Sort imports (isort)
isort app/ tests/

# Lint code (Ruff)
ruff check app/ tests/

# Type check (mypy)
mypy app/

# Security scan (Bandit)
bandit -r app/
```

### Git

```bash
# Create feature branch
git checkout -b feature/my-feature

# Commit with conventional commit message
git commit -m "feat: add new feature"
git commit -m "fix: fix bug"
git commit -m "docs: update documentation"

# Push and create PR
git push origin feature/my-feature
```

---

## Essential Documentation

**Must Read (30 min):**
1. [PRD - Product Requirements](./PRD_RESTAURANT_SUPPLY_CHAIN.md) - Understand what we're building
2. [Feature Mapping](./FEATURE_MAPPING.md) - What exists vs what's needed
3. [Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md) - 12-week plan

**When Needed:**
4. [Database Schema](./DATABASE_SCHEMA_SUPPLY_CHAIN.md) - Complete DB design
5. [API Documentation](./API.md) - API examples
6. [Development Guide](./DEVELOPMENT.md) - Advanced development topics
7. [Deployment Guide](./DEPLOYMENT.md) - Production deployment

---

## Your First Task: Hello World Endpoint

Let's create a simple endpoint to verify everything works:

**1. Create endpoint file:** `app/api/v1/hello.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
async def hello_world():
    """Simple hello world endpoint"""
    return {
        "message": "مرحباً بك في نظام سلسلة التوريد للمطاعم!",
        "message_en": "Welcome to Restaurant Supply Chain!",
    }
```

**2. Register router:** Edit `app/main.py`

```python
# Add this import
from app.api.v1 import hello

# Add this line after other router includes
app.include_router(hello.router, prefix="/api/v1", tags=["hello"])
```

**3. Test it:**

```bash
# Restart server
# Ctrl+C to stop, then:
uvicorn app.main:app --reload

# Test the endpoint
curl http://localhost:8000/api/v1/hello
```

**Expected output:**
```json
{
  "message": "مرحباً بك في نظام سلسلة التوريد للمطاعم!",
  "message_en": "Welcome to Restaurant Supply Chain!"
}
```

**4. Create a test:** `tests/api/v1/test_hello.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_hello_world():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/hello")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "message_en" in data
```

**5. Run the test:**

```bash
pytest tests/api/v1/test_hello.py -v
```

---

## Troubleshooting

### Issue: Database connection error

**Solution:**
```bash
# Check PostgreSQL is running
pg_ctl status

# Start PostgreSQL
# macOS (Homebrew):
brew services start postgresql@15

# Windows:
# Use Services app to start PostgreSQL

# Verify connection
psql -U postgres -c "SELECT version();"
```

### Issue: Redis connection error

**Solution:**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Start Redis
# macOS (Homebrew):
brew services start redis

# Linux:
sudo systemctl start redis

# Windows:
# Download Redis for Windows or use WSL
```

### Issue: Import errors

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Migration conflicts

**Solution:**
```bash
# Check current migration
alembic current

# Downgrade to base
alembic downgrade base

# Re-run migrations
alembic upgrade head
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port 8000
# macOS/Linux:
lsof -i :8000

# Windows:
netstat -ano | findstr :8000

# Kill the process (replace PID)
kill <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

---

## Development Tips

### 1. Use the Debugger

Add breakpoints in VS Code:
```python
import pdb; pdb.set_trace()  # Debugger will stop here
```

Or use VS Code's built-in debugger (F5).

### 2. Watch Database Changes

```bash
# PostgreSQL
watch -n 1 'psql -U postgres supply_chain -c "SELECT COUNT(*) FROM orders;"'

# SQLite
watch -n 1 'sqlite3 dev.db "SELECT COUNT(*) FROM orders;"'
```

### 3. Format on Save

**VS Code:** Add to `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

### 4. Use API Client

Instead of curl, use:
- **Postman** ([Download](https://www.postman.com/downloads/))
- **Insomnia** ([Download](https://insomnia.rest/download))
- **HTTPie** (CLI): `brew install httpie`

### 5. Monitor Logs

```bash
# Tail logs in real-time
tail -f logs/app.log

# Filter for errors
tail -f logs/app.log | grep ERROR

# Pretty print JSON logs
tail -f logs/app.log | jq
```

---

## Getting Help

**Stuck? Here's how to get help:**

1. **Check documentation** (docs/ folder)
2. **Search existing issues** (GitHub Issues)
3. **Ask in Slack** (#supply-chain-dev channel)
4. **Create a GitHub issue** (with details: error message, steps to reproduce)

**When asking for help, include:**
- What you're trying to do
- What you expected to happen
- What actually happened
- Error messages (full stack trace)
- Your environment (OS, Python version, etc.)

---

## Next Steps

Once you're set up:

1. **Read the PRD** - Understand the product vision
2. **Check the roadmap** - See current sprint tasks
3. **Pick a task** - Jira board or GitHub Issues
4. **Create a branch** - `feature/your-task-name`
5. **Start coding!** - Follow the workflow above

**Suggested first tasks for new developers:**

- **Backend:** Implement Restaurant CRUD endpoints
- **Backend:** Add phone verification (Twilio SMS)
- **Frontend:** Build login screen (React Native)
- **Frontend:** Create product list component
- **DevOps:** Set up CI/CD pipeline
- **QA:** Write integration tests for auth flow

---

## Welcome Aboard! 🚀

You're now ready to contribute to the Restaurant Supply Chain platform. If you have any questions, don't hesitate to ask the team!

**Happy coding!**

---

*Last Updated: January 2025*

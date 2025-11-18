# Database Migrations Guide

This guide explains how to work with database migrations using Alembic in this FastAPI + SQLModel application.

## Table of Contents
- [Overview](#overview)
- [Migration Basics](#migration-basics)
- [Common Migration Tasks](#common-migration-tasks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Overview

This project uses **Alembic** for database schema migrations. Alembic is a lightweight database migration tool for SQLAlchemy (which SQLModel is built on).

### Why Use Migrations?

- **Version Control**: Track database schema changes alongside code changes
- **Team Collaboration**: Share database changes with your team
- **Safe Deployments**: Apply incremental database changes in production
- **Rollback Support**: Revert database changes if needed
- **Reproducibility**: Recreate database schema in any environment

### Project Setup

The Alembic configuration in this project:
- Configuration file: `alembic.ini`
- Migration scripts: `alembic/`
- Environment setup: `alembic/env.py` (configured for SQLModel)
- Versions folder: `alembic/versions/` (contains migration files)

## Migration Basics

### Database URL Configuration

Alembic automatically loads the database URL from your application settings (`app.core.config`). The URL is determined by your `.env` file:

```bash
# .env
DATABASE_URL=sqlite+aiosqlite:///./dev.db  # Development
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname  # Production
```

### Understanding Migration Files

Each migration file contains two functions:

```python
def upgrade() -> None:
    """Apply the migration (forward)"""
    # SQL commands to modify database

def downgrade() -> None:
    """Revert the migration (backward)"""
    # SQL commands to undo changes
```

## Common Migration Tasks

### 1. Check Current Migration Status

See which migrations have been applied:

```bash
alembic current
```

### 2. View Migration History

```bash
alembic history --verbose
```

### 3. Create a New Migration

After modifying your SQLModel models, generate a migration:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user profile fields"
```

**Important**: Always review auto-generated migrations before applying them!

### 4. Apply Migrations

Apply all pending migrations:

```bash
alembic upgrade head
```

Apply migrations one step at a time:

```bash
alembic upgrade +1
```

Apply to a specific revision:

```bash
alembic upgrade <revision_id>
```

### 5. Rollback Migrations

Revert the last migration:

```bash
alembic downgrade -1
```

Revert all migrations:

```bash
alembic downgrade base
```

Revert to a specific revision:

```bash
alembic downgrade <revision_id>
```

### 6. Create Empty Migration

For data migrations or custom SQL:

```bash
alembic revision -m "Migrate user data to new schema"
```

Then edit the generated file manually.

## Migration Workflow

### Adding a New Field to a Model

1. **Modify the Model** (`app/models/user.py`):
   ```python
   class User(SQLModel, table=True):
       id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       email: EmailStr = Field(unique=True, index=True)
       full_name: str
       # New field added:
       phone_number: str | None = None
   ```

2. **Generate Migration**:
   ```bash
   alembic revision --autogenerate -m "Add phone_number to user"
   ```

3. **Review the Migration** (`alembic/versions/xxxxx_add_phone_number_to_user.py`):
   ```python
   def upgrade() -> None:
       op.add_column('user', sa.Column('phone_number', sa.String(), nullable=True))

   def downgrade() -> None:
       op.drop_column('user', 'phone_number')
   ```

4. **Apply the Migration**:
   ```bash
   alembic upgrade head
   ```

### Adding a New Table

1. **Create the Model** (`app/models/product.py`):
   ```python
   from sqlmodel import SQLModel, Field
   import uuid

   class Product(SQLModel, table=True):
       id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       name: str = Field(index=True)
       price: float
       stock: int = 0
   ```

2. **Import in `app/models/__init__.py`**:
   ```python
   from app.models.product import Product

   __all__ = [
       # ... existing exports
       "Product",
   ]
   ```

3. **Update `alembic/env.py`** to import the new model:
   ```python
   # Import all models so they're registered with SQLModel.metadata
   from app.models import (
       User, Role, Permission, RolePermission, UserRole,
       Product,  # Add new model here
   )
   ```

4. **Generate and Apply Migration**:
   ```bash
   alembic revision --autogenerate -m "Add product table"
   alembic upgrade head
   ```

### Data Migration Example

For complex data transformations:

```python
# alembic/versions/xxxxx_migrate_user_data.py
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()

    # Perform data migration
    connection.execute(
        sa.text("""
            UPDATE user
            SET full_name = CONCAT(first_name, ' ', last_name)
            WHERE full_name IS NULL
        """)
    )

def downgrade() -> None:
    # Define how to revert data changes
    pass
```

## Best Practices

### 1. Always Review Auto-Generated Migrations

Alembic's auto-detection isn't perfect. Always review generated migrations:

```bash
alembic revision --autogenerate -m "Description"
# Review the file in alembic/versions/ before running upgrade!
```

### 2. Test Migrations

Test both upgrade and downgrade:

```bash
# Upgrade
alembic upgrade head

# Test rollback
alembic downgrade -1

# Re-apply
alembic upgrade head
```

### 3. Descriptive Migration Messages

Use clear, descriptive messages:

```bash
# Good
alembic revision --autogenerate -m "Add email verification fields to user"

# Bad
alembic revision --autogenerate -m "Update user"
```

### 4. One Logical Change Per Migration

Don't mix unrelated changes:

```bash
# Good: Separate migrations
alembic revision --autogenerate -m "Add product table"
alembic revision --autogenerate -m "Add user preferences table"

# Bad: One large migration
alembic revision --autogenerate -m "Add multiple tables"
```

### 5. Backup Before Production Migrations

Always backup production database before running migrations:

```bash
# PostgreSQL example
pg_dump -U user -d dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# Then run migration
alembic upgrade head
```

### 6. Handle Nullable Fields Carefully

When adding non-nullable fields to existing tables, use a two-step approach:

```python
# Migration 1: Add field as nullable
def upgrade():
    op.add_column('user', sa.Column('required_field', sa.String(), nullable=True))
    # Set default values
    op.execute("UPDATE user SET required_field = 'default'")

# Migration 2: Make field non-nullable
def upgrade():
    op.alter_column('user', 'required_field', nullable=False)
```

## Troubleshooting

### Migration Shows No Changes

**Problem**: `alembic revision --autogenerate` creates empty migration

**Solutions**:
1. Ensure model is imported in `alembic/env.py`
2. Verify model has `table=True`
3. Check that model is in `SQLModel.metadata`

```python
# alembic/env.py - Make sure all models are imported!
from app.models import (
    User, Role, Permission, RolePermission, UserRole,
    # Your new models must be imported here!
)
```

### Migration Conflicts

**Problem**: Multiple developers create migrations simultaneously

**Solution**: Merge migrations or create a merge revision:

```bash
alembic merge <rev1> <rev2> -m "Merge migrations"
```

### Database Out of Sync

**Problem**: Database state doesn't match migration state

**Solutions**:

1. **For Development**: Reset database
   ```bash
   # Delete database
   rm dev.db

   # Recreate with migrations
   alembic upgrade head
   ```

2. **For Production**: Manually sync
   ```bash
   # Check current state
   alembic current

   # Stamp to specific revision (CAUTION!)
   alembic stamp <revision_id>
   ```

### Downgrade Fails

**Problem**: Cannot rollback a migration

**Common causes**:
- Data loss would occur (e.g., dropping a column)
- Constraints prevent rollback
- Incomplete downgrade logic

**Solution**: Implement proper downgrade logic or backup/restore database

## Production Deployment

### Pre-Deployment Checklist

- [ ] Backup production database
- [ ] Test migrations in staging environment
- [ ] Review all pending migrations
- [ ] Check for data migrations that may take time
- [ ] Plan for potential rollback

### Deployment Process

1. **Backup Database**:
   ```bash
   # PostgreSQL
   pg_dump -U user -d prod_db > backup_before_migration.sql
   ```

2. **Check Pending Migrations**:
   ```bash
   alembic current
   alembic history
   ```

3. **Apply Migrations**:
   ```bash
   # Production migration
   alembic upgrade head
   ```

4. **Verify Success**:
   ```bash
   alembic current
   # Should show "head" revision
   ```

### Rollback Plan

If something goes wrong:

1. **Quick Rollback** (if safe):
   ```bash
   alembic downgrade -1
   ```

2. **Full Restore** (if data is corrupted):
   ```bash
   # Restore from backup
   psql -U user -d prod_db < backup_before_migration.sql

   # Update migration state
   alembic stamp <previous_revision>
   ```

### Docker Deployment

In Docker, run migrations as part of startup:

```dockerfile
# Dockerfile
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use a separate migration container:

```yaml
# docker-compose.yml
services:
  migrate:
    build: .
    command: alembic upgrade head
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db:5432/dbname
```

## Advanced Topics

### Custom Naming Conventions

Alembic uses naming conventions for constraints. Configured in `alembic/env.py`:

```python
target_metadata = SQLModel.metadata
target_metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
```

### Offline Migrations

Generate SQL without database connection:

```bash
# Generate SQL for all migrations
alembic upgrade head --sql > migration.sql

# Review and apply manually
psql -U user -d dbname < migration.sql
```

### Multiple Database Support

For projects with multiple databases:

1. Create separate alembic directories
2. Use different `alembic.ini` configs
3. Specify config with `-c` flag:

```bash
alembic -c alembic_main.ini upgrade head
alembic -c alembic_analytics.ini upgrade head
```

## Quick Reference

```bash
# Common Commands
alembic current                           # Show current revision
alembic history                          # Show all revisions
alembic revision --autogenerate -m "msg" # Create migration
alembic upgrade head                     # Apply all migrations
alembic downgrade -1                     # Rollback one migration
alembic stamp head                       # Mark DB as up-to-date
alembic show <revision>                  # Show migration details

# Advanced Commands
alembic upgrade <revision>               # Upgrade to specific revision
alembic downgrade <revision>             # Downgrade to specific revision
alembic upgrade +2                       # Upgrade 2 steps
alembic downgrade -2                     # Downgrade 2 steps
alembic merge <rev1> <rev2>             # Merge conflicting migrations
alembic upgrade head --sql              # Generate SQL (offline mode)
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- Project README: [../README.md](../README.md)
- Development Guide: [DEVELOPMENT.md](DEVELOPMENT.md)

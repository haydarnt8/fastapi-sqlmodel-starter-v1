# Audit Fields & Soft Delete Guide

This guide explains how to use the built-in audit tracking and soft delete features in this FastAPI starter template.

## Table of Contents
- [Overview](#overview)
- [Available Audit Fields](#available-audit-fields)
- [How It Works](#how-it-works)
- [Using Audit Fields in Your Models](#using-audit-fields-in-your-models)
- [CRUD Operations](#crud-operations)
- [Endpoint Implementation](#endpoint-implementation)
- [Soft Delete](#soft-delete)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Overview

This starter template includes production-grade audit tracking and soft delete functionality built into every model. These features help you:

- **Track WHO** created, modified, or deleted records
- **Track WHEN** changes happened
- **Implement soft delete** (mark as deleted without permanent removal)
- **Maintain compliance** (GDPR, SOC2, HIPAA)
- **Enable audit trails** for security and debugging
- **Restore accidentally deleted data**

All models that inherit from `BaseModel` automatically get these features without any additional code!

## Available Audit Fields

### Timestamp Fields (`TimestampMixin`)

```python
created_at: datetime  # When the record was created
updated_at: datetime  # When the record was last modified
```

- **Automatically populated** on creation
- **Automatically updated** on modification
- **Indexed** for fast queries
- Uses UTC timestamps (`datetime.utcnow()`)

### Audit Fields (`AuditMixin`)

```python
created_by_id: Optional[UUID]   # User ID who created this record
updated_by_id: Optional[UUID]   # User ID who last modified this record
```

- **Foreign keys** to the `user` table
- **Nullable** (can be None for system operations)
- **Indexed** for fast queries
- Populated by passing `current_user.id` to CRUD operations

### Soft Delete Fields (`SoftDeleteMixin`)

```python
is_deleted: bool                # Whether record is soft-deleted
deleted_at: Optional[datetime]  # When the record was deleted
deleted_by_id: Optional[UUID]   # User ID who deleted this record
```

- **Indexed** for fast filtering
- Automatically filtered out in `get()` and `get_multi()` queries
- Can be restored by setting `is_deleted = False`

## How It Works

### Inheritance Hierarchy

```python
# In app/models/base.py

TimestampMixin (SQLModel)
├── created_at
└── updated_at

AuditMixin (extends TimestampMixin)
├── created_at          # Inherited
├── updated_at          # Inherited
├── created_by_id       # New
└── updated_by_id       # New

SoftDeleteMixin (SQLModel)
├── is_deleted
├── deleted_at
└── deleted_by_id

BaseModel (extends AuditMixin + SoftDeleteMixin)
├── created_at          # From AuditMixin → TimestampMixin
├── updated_at          # From AuditMixin → TimestampMixin
├── created_by_id       # From AuditMixin
├── updated_by_id       # From AuditMixin
├── is_deleted          # From SoftDeleteMixin
├── deleted_at          # From SoftDeleteMixin
└── deleted_by_id       # From SoftDeleteMixin
```

### Automatic Behavior

1. **Timestamps** - Auto-populated via SQLAlchemy `default_factory` and `onupdate`
2. **Audit IDs** - You pass `current_user.id` to CRUD methods
3. **Soft Delete Filtering** - CRUD base class automatically filters `is_deleted=False`

## Using Audit Fields in Your Models

### Basic Usage

Simply inherit from `BaseModel` and you get all audit fields:

```python
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseModel

class Product(BaseModel, table=True):
    """Product model with automatic audit tracking."""
    __tablename__ = "product"

    # Your fields
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    price: float = Field(nullable=False)

    # Audit fields are inherited automatically!
    # created_at, updated_at, created_by_id, updated_by_id,
    # is_deleted, deleted_at, deleted_by_id
```

That's it! Your model now has full audit tracking.

### Using Only Timestamps

If you only need timestamps without user tracking:

```python
from app.models.base import TimestampMixin

class Log(TimestampMixin, table=True):
    """Log model with only timestamps."""
    __tablename__ = "log"

    id: int = Field(default=None, primary_key=True)
    message: str

    # Only has: created_at, updated_at
```

### Using Timestamps + Audit

If you want timestamps and user tracking, but not soft delete:

```python
from app.models.base import AuditMixin

class AuditLog(AuditMixin, table=True):
    """Audit log - should never be deleted."""
    __tablename__ = "audit_log"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action: str

    # Has: created_at, updated_at, created_by_id, updated_by_id
    # But NOT: is_deleted, deleted_at, deleted_by_id
```

## CRUD Operations

The `BaseCRUD` class in [app/crud/base.py](../app/crud/base.py) automatically handles audit fields.

### Creating Records

```python
# In your CRUD file (e.g., app/crud/product.py)
from app.crud.base import BaseCRUD
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

class ProductCRUD(BaseCRUD[Product, ProductCreate, ProductUpdate]):
    """CRUD operations for products."""
    pass

product_crud = ProductCRUD(Product)
```

### Using CRUD Methods

#### Create

```python
# Pass created_by_id to automatically set audit fields
product = await product_crud.create(
    session,
    obj_in=product_data,
    created_by_id=current_user.id,  # ← Audit field
)

# Result:
# - created_at: auto-set to now
# - updated_at: auto-set to now
# - created_by_id: current_user.id
# - updated_by_id: current_user.id (same as created_by on create)
```

#### Read (Get by ID)

```python
# Automatically filters out soft-deleted records
product = await product_crud.get(session, id=product_id)

# To include deleted records, use allow_deleted=True
product = await product_crud.get(
    session,
    id=product_id,
    allow_deleted=True  # ← Include soft-deleted records
)
```

#### Read (Get Multiple)

```python
# Automatically filters is_deleted=False
products = await product_crud.get_multi(
    session,
    skip=0,
    limit=20,
)

# Result: Only active (non-deleted) products
```

#### Update

```python
# Pass updated_by_id to track who modified it
product = await product_crud.update(
    session,
    db_obj=product,
    obj_in=update_data,
    updated_by_id=current_user.id,  # ← Audit field
)

# Result:
# - updated_at: auto-updated to now
# - updated_by_id: current_user.id
```

#### Delete (Soft Delete)

```python
# Soft delete by default
product = await product_crud.delete(
    session,
    id=product_id,
    deleted_by_id=current_user.id,  # ← Audit field
)

# Result:
# - is_deleted: True
# - deleted_at: now
# - deleted_by_id: current_user.id
# Record still exists in database!
```

#### Delete (Hard Delete)

```python
# Permanently delete from database
product = await product_crud.delete(
    session,
    id=product_id,
    deleted_by_id=current_user.id,
    hard_delete=True,  # ← Permanent deletion
)

# Result: Record removed from database (use with caution!)
```

## Endpoint Implementation

### Creating Endpoints with Audit Fields

Here's how to implement endpoints that properly utilize audit fields:

#### Create Endpoint

```python
# app/api/v1/products.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PermissionChecker
from app.crud.product import product_crud
from app.db.session import get_session
from app.models import User
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["Products"])

@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:create")),
) -> ProductRead:
    """Create a new product."""

    # Pass current_user.id to track who created it
    product = await product_crud.create(
        session,
        obj_in=product_data,
        created_by_id=current_user.id,  # ← Important!
    )

    return product
```

#### Update Endpoint

```python
@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID,
    update_data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:update")),
) -> ProductRead:
    """Update a product."""

    # Get existing product
    product = await product_crud.get(session, id=product_id)

    # Update with audit tracking
    product = await product_crud.update(
        session,
        db_obj=product,
        obj_in=update_data,
        updated_by_id=current_user.id,  # ← Important!
    )

    return product
```

#### Delete Endpoint

```python
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:delete")),
):
    """Soft delete a product."""

    await product_crud.delete(
        session,
        id=product_id,
        deleted_by_id=current_user.id,  # ← Important!
    )

    return None
```

### Complete Example

See [app/api/v1/users.py](../app/api/v1/users.py) or [app/api/v1/roles.py](../app/api/v1/roles.py) for complete working examples.

## Soft Delete

### Why Soft Delete?

Soft delete marks records as deleted without removing them from the database.

**Benefits:**
- **Restore accidentally deleted data** - "Undo" deletions
- **Maintain referential integrity** - Foreign keys still work
- **Audit trail** - Know what was deleted and when
- **Compliance** - Some regulations require data retention
- **Historical data** - Keep deleted records for reporting

**When to use hard delete:**
- User requests data deletion (GDPR "right to be forgotten")
- Sensitive data that must be permanently removed
- Test data or truly temporary records
- Database cleanup/maintenance

### Soft Delete Behavior

```python
# Create a product
product = await product_crud.create(
    session,
    obj_in=ProductCreate(name="Widget", price=9.99),
    created_by_id=current_user.id,
)

# Soft delete it
await product_crud.delete(
    session,
    id=product.id,
    deleted_by_id=current_user.id,
)

# Query won't find it (automatically filtered)
product = await product_crud.get(session, id=product.id)
# Result: None (not found)

# But it still exists in database!
product = await product_crud.get(session, id=product.id, allow_deleted=True)
# Result: Product object with is_deleted=True

# Restore it
product.is_deleted = False
product.deleted_at = None
product.deleted_by_id = None
await session.commit()

# Now it's back
product = await product_crud.get(session, id=product.id)
# Result: Product object (restored)
```

### Querying Deleted Records

```python
# Get all products including deleted
from sqlmodel import select

statement = select(Product)  # No filters
results = await session.exec(statement)
all_products = results.all()

# Get only deleted products
statement = select(Product).where(Product.is_deleted == True)
results = await session.exec(statement)
deleted_products = results.all()

# Get with deleted status
statement = select(Product).where(Product.is_deleted == False)
results = await session.exec(statement)
active_products = results.all()
```

### Restoring Deleted Records

```python
@router.post("/{product_id}/restore", response_model=ProductRead)
async def restore_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:delete")),
) -> ProductRead:
    """Restore a soft-deleted product."""

    # Get the deleted product (allow_deleted=True)
    product = await product_crud.get(
        session,
        id=product_id,
        allow_deleted=True,
    )

    if not product.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not deleted"
        )

    # Restore it
    product.is_deleted = False
    product.deleted_at = None
    product.deleted_by_id = None

    session.add(product)
    await session.commit()
    await session.refresh(product)

    return product
```

## Best Practices

### 1. Always Pass Audit User IDs

```python
# ✅ Good: Track who did the action
product = await product_crud.create(
    session,
    obj_in=product_data,
    created_by_id=current_user.id,
)

# ❌ Bad: No audit trail
product = await product_crud.create(
    session,
    obj_in=product_data,
)
```

### 2. Use Soft Delete by Default

```python
# ✅ Good: Soft delete (recoverable)
await product_crud.delete(
    session,
    id=product_id,
    deleted_by_id=current_user.id,
)

# ⚠️ Use sparingly: Hard delete (permanent)
await product_crud.delete(
    session,
    id=product_id,
    deleted_by_id=current_user.id,
    hard_delete=True,
)
```

### 3. Include Audit Fields in Schemas

```python
# app/schemas/product.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ProductRead(BaseModel):
    """Schema for reading products."""
    id: UUID
    name: str
    price: float

    # Include audit fields for transparency
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[UUID] = None
    updated_by_id: Optional[UUID] = None

    # Optionally include soft delete info
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[UUID] = None
```

### 4. Query Efficiency

Audit fields are indexed for fast queries:

```python
# ✅ Fast: Indexed field
statement = select(Product).where(Product.is_deleted == False)

# ✅ Fast: Indexed field
statement = select(Product).where(
    Product.created_at >= start_date
)

# ✅ Fast: Indexed field
statement = select(Product).where(
    Product.created_by_id == user_id
)
```

### 5. System Operations

For automated/system operations without a user:

```python
# System operation (no current user)
product = await product_crud.create(
    session,
    obj_in=product_data,
    # created_by_id=None (default)
)

# Result:
# - created_at: auto-set
# - updated_at: auto-set
# - created_by_id: None (system operation)
# - updated_by_id: None (system operation)
```

### 6. Expose Audit Info to API Clients

Let clients see who did what:

```python
class ProductRead(BaseModel):
    id: UUID
    name: str
    price: float
    created_at: datetime
    updated_at: datetime

    # Expand audit IDs to show user info
    created_by: Optional[UserSummary] = None
    updated_by: Optional[UserSummary] = None

class UserSummary(BaseModel):
    id: UUID
    email: str
    full_name: str
```

## Common Patterns

### Pattern 1: Get Who Created/Updated a Record

```python
# In your CRUD or endpoint
from sqlalchemy.orm import selectinload

# Eager-load creator and updater
statement = (
    select(Product)
    .where(Product.id == product_id)
    .options(
        selectinload(Product.created_by),
        selectinload(Product.updated_by),
    )
)
result = await session.exec(statement)
product = result.first()

# Now you can access:
# product.created_by → User object
# product.updated_by → User object
```

**Note:** This requires adding relationships to your model:

```python
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class Product(BaseModel, table=True):
    # ... fields ...

    # Relationships to users
    created_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Product.created_by_id]",
            "lazy": "selectin",
        }
    )
    updated_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Product.updated_by_id]",
            "lazy": "selectin",
        }
    )
```

### Pattern 2: Audit History Endpoint

```python
@router.get("/{product_id}/history")
async def get_product_history(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:read")),
):
    """Get audit history for a product."""

    product = await product_crud.get(
        session,
        id=product_id,
        allow_deleted=True,  # Include even if deleted
    )

    return {
        "id": product.id,
        "is_deleted": product.is_deleted,
        "created": {
            "at": product.created_at,
            "by_id": product.created_by_id,
        },
        "updated": {
            "at": product.updated_at,
            "by_id": product.updated_by_id,
        },
        "deleted": {
            "at": product.deleted_at,
            "by_id": product.deleted_by_id,
        } if product.is_deleted else None,
    }
```

### Pattern 3: Filter by Creator

```python
@router.get("/my-products")
async def get_my_products(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get products created by current user."""

    statement = select(Product).where(
        Product.created_by_id == current_user.id,
        Product.is_deleted == False,
    )
    results = await session.exec(statement)
    products = results.all()

    return products
```

### Pattern 4: Recent Changes

```python
@router.get("/recent-changes")
async def get_recent_changes(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("product:read")),
):
    """Get recently modified products."""

    from datetime import datetime, timedelta

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    statement = (
        select(Product)
        .where(
            Product.updated_at >= one_hour_ago,
            Product.is_deleted == False,
        )
        .order_by(Product.updated_at.desc())
    )
    results = await session.exec(statement)
    products = results.all()

    return products
```

## Troubleshooting

### Problem: Audit fields are None

**Symptom:** `created_by_id` and `updated_by_id` are always `None`

**Solution:** Make sure you're passing the user ID to CRUD methods:

```python
# ❌ Wrong
product = await product_crud.create(session, obj_in=product_data)

# ✅ Correct
product = await product_crud.create(
    session,
    obj_in=product_data,
    created_by_id=current_user.id
)
```

### Problem: Deleted records still appear

**Symptom:** Soft-deleted records show up in queries

**Solution:** Make sure you're using CRUD methods, not raw queries:

```python
# ❌ Wrong: Raw query doesn't filter
statement = select(Product).where(Product.id == product_id)
result = await session.exec(statement)
product = result.first()

# ✅ Correct: CRUD method filters automatically
product = await product_crud.get(session, id=product_id)
```

### Problem: Can't find deleted record

**Symptom:** `get()` returns `None` for a deleted record

**Solution:** Use `allow_deleted=True`:

```python
# ❌ Wrong: Filters out deleted records
product = await product_crud.get(session, id=product_id)

# ✅ Correct: Include deleted records
product = await product_crud.get(
    session,
    id=product_id,
    allow_deleted=True
)
```

### Problem: Timestamps not updating

**Symptom:** `updated_at` doesn't change on update

**Cause:** SQLAlchemy's `onupdate` only triggers on actual column changes

**Solution:** This is normal SQLAlchemy behavior. Ensure you're actually modifying fields:

```python
# This triggers update
product.name = "New Name"
session.add(product)
await session.commit()
# updated_at will be updated

# This doesn't trigger update (no changes)
product.name = product.name  # Same value
session.add(product)
await session.commit()
# updated_at stays the same
```

### Problem: Foreign key constraint errors

**Symptom:** Error creating records with audit fields

**Cause:** The `created_by_id` user doesn't exist

**Solution:** Ensure the user ID is valid:

```python
# ✅ Use authenticated user (guaranteed to exist)
product = await product_crud.create(
    session,
    obj_in=product_data,
    created_by_id=current_user.id,
)

# ❌ Don't use arbitrary UUIDs
product = await product_crud.create(
    session,
    obj_in=product_data,
    created_by_id=uuid4(),  # This user probably doesn't exist!
)
```

## Related Documentation

- [Base Models Source](../app/models/base.py) - Model definitions
- [CRUD Base Source](../app/crud/base.py) - CRUD implementation
- [User Endpoints Example](../app/api/v1/users.py) - Complete working example
- [Role Endpoints Example](../app/api/v1/roles.py) - Another complete example
- [Development Guide](DEVELOPMENT.md) - General development guidelines

## Summary

The audit field system provides:

✅ **Automatic timestamps** - No code needed
✅ **User tracking** - Just pass `current_user.id`
✅ **Soft delete** - Recoverable by default
✅ **Production-ready** - Indexed, compliant, battle-tested
✅ **Zero overhead** - Inherit from `BaseModel` and you're done

Every model in your application gets comprehensive audit tracking with minimal effort!

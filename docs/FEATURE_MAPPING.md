# Feature Mapping: Starter → Supply Chain System

This document maps existing features from the FastAPI SQLModel Starter to the Restaurant Supply Chain Ordering System requirements.

---

## ✅ Already Implemented (Use As-Is)

These features are production-ready and can be used directly:

### 1. Authentication & Authorization ✅

**Existing Implementation:**
- JWT-based authentication (access + refresh tokens)
- Token blacklisting on logout (Redis)
- Password hashing (Argon2/bcrypt)
- RBAC with hierarchical roles
- Wildcard permission matching

**Supply Chain Usage:**
```python
# Existing roles can be extended:
ROLES = {
    "SUPER_ADMIN": ("super_admin", "*:*", 1),
    "RESTAURANT_OWNER": ("restaurant_owner", "order:*,product:read", 20),
    "SUPPLIER_ADMIN": ("supplier_admin", "product:*,order:read,order:update", 15),
    "DRIVER": ("driver", "delivery:*", 25),
}
```

**Files:**
- ✅ `app/core/security.py` - JWT, password hashing
- ✅ `app/api/v1/auth.py` - Login, register, logout, refresh
- ✅ `app/models/user.py` - User model
- ✅ `app/models/role.py` - Role/permission models

---

### 2. Audit Logging ✅

**Existing Implementation:**
- Automatic audit fields on all models (`BaseModel`)
- Comprehensive audit log table
- Track WHO, WHAT, WHEN for all actions
- Immutable append-only logs

**Supply Chain Usage:**
- Track all order placements, status changes
- Monitor supplier product updates
- Log payment events
- Delivery proof tracking

**Audit Fields Auto-Included:**
```python
# All models inherit from BaseModel get:
created_at: datetime
updated_at: datetime
created_by_id: UUID
updated_by_id: UUID
is_deleted: bool
deleted_at: datetime | None
deleted_by_id: UUID | None
```

**Files:**
- ✅ `app/models/base.py` - BaseModel with audit fields
- ✅ `app/models/audit_log.py` - Audit log model
- ✅ `app/core/audit.py` - Audit helper functions
- ✅ `app/api/v1/audit.py` - Audit query endpoints

---

### 3. Database Layer ✅

**Existing Implementation:**
- SQLModel ORM (async)
- PostgreSQL/SQLite support
- Connection pooling
- Alembic migrations
- Generic CRUD operations

**Supply Chain Usage:**
- Ready for complex joins (orders ↔ products ↔ suppliers)
- Supports JSON columns (for metadata, translations)
- Async operations (high throughput)

**Files:**
- ✅ `app/db/session.py` - Async database session
- ✅ `app/db/init_db.py` - Database initialization
- ✅ `app/crud/base.py` - Generic CRUD class
- ✅ `alembic/` - Migration system

---

### 4. Security Features ✅

**Existing Implementation:**
- OWASP security headers
- Rate limiting (Redis-backed)
- CORS configuration
- Input validation (Pydantic)
- SQL injection protection

**Supply Chain Usage:**
- Prevent order manipulation attacks
- Rate limit order placement
- Secure payment endpoints
- Validate product prices

**Files:**
- ✅ `app/middleware/security_headers.py`
- ✅ `app/middleware/rate_limit.py`
- ✅ `app/core/validators.py`

---

### 5. Configuration Management ✅

**Existing Implementation:**
- Pydantic Settings
- Environment-based config
- `.env` support
- Production validation

**Supply Chain Usage:**
```python
# Add new config:
class Settings(BaseSettings):
    # ... existing fields ...

    # SMS/Notifications
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Payments
    QI_CARD_API_KEY: str | None
    ZAINCASH_MERCHANT_ID: str | None

    # Maps
    GOOGLE_MAPS_API_KEY: str

    # Business Logic
    ORDER_COMMISSION_RATE: float = 0.05  # 5%
    MIN_ORDER_VALUE: Decimal = 10000  # IQD
```

**Files:**
- ✅ `app/core/config.py`
- ✅ `.env.example`

---

### 6. Logging & Monitoring ✅

**Existing Implementation:**
- Structured JSON logging
- Request ID tracking
- Request/response logging middleware
- Configurable log levels

**Supply Chain Usage:**
- Track order flow
- Monitor payment events
- Debug delivery issues

**Files:**
- ✅ `app/core/logging.py`
- ✅ `app/middleware/request_logging.py`
- ✅ `app/middleware/request_id.py`

---

### 7. Caching Layer ✅

**Existing Implementation:**
- Redis integration
- Cache service with TTL
- Graceful fallback if Redis unavailable

**Supply Chain Usage:**
- Cache product catalog
- Cache supplier info
- Session management
- Real-time order updates (pub/sub)

**Files:**
- ✅ `app/core/cache.py`

---

### 8. Internationalization (i18n) ✅

**Existing Implementation:**
- Multi-language support (English, Arabic)
- Accept-Language header detection
- JSON translation files
- Easy to extend

**Supply Chain Usage:**
- Arabic (primary), English (secondary), Kurdish (future)
- RTL layout support needed (frontend)
- Database fields: `name_ar`, `name_en`

**Files:**
- ✅ `app/i18n/translator.py`
- ✅ `app/i18n/locales/en.json`
- ✅ `app/i18n/locales/ar.json`

---

### 9. Testing Infrastructure ✅

**Existing Implementation:**
- pytest with async support
- Test fixtures
- Coverage reporting
- Isolated test database

**Supply Chain Usage:**
- Write tests for new models (Restaurant, Supplier, Order, etc.)
- Integration tests for order flow
- Payment processing tests

**Files:**
- ✅ `tests/` directory structure
- ✅ `conftest.py` - Test fixtures

---

### 10. API Documentation ✅

**Existing Implementation:**
- Auto-generated Swagger UI
- ReDoc alternative docs
- Pydantic schema validation

**Supply Chain Usage:**
- Document all new endpoints
- API versioning already in place (`/api/v1/`)

**Files:**
- ✅ `app/main.py` - FastAPI app setup
- ✅ `app/schemas/` - Request/response schemas

---

## ⏳ Needs Extension

These features exist but need to be extended for supply chain:

### 1. User Model ⏳

**Existing:**
```python
class User(BaseModel):
    id: UUID
    email: str
    hashed_password: str
    full_name: str
    is_active: bool
```

**Extend With:**
```python
class User(BaseModel):
    # ... existing fields ...

    # Supply Chain additions:
    phone_number: str  # Required for SMS
    phone_verified: bool = False
    language_preference: str = "ar"  # ar, en, ku

    # Role-specific foreign keys
    restaurant_id: UUID | None  # If user is restaurant staff
    supplier_id: UUID | None    # If user is supplier staff
```

**Migration:**
```bash
alembic revision --autogenerate -m "Add phone and language to users"
```

---

### 2. Role System ⏳

**Existing:**
- 3 roles: admin, manager, user
- 11 permissions: user:*, role:*, audit:read

**Extend With:**
```python
# New roles needed:
- restaurant_owner
- restaurant_manager
- restaurant_staff
- supplier_admin
- supplier_manager
- supplier_staff
- driver
- super_admin

# New permissions needed:
- restaurant:*
- supplier:*
- product:create/read/update/delete
- order:create/read/update/cancel
- delivery:*
- review:*
- payment:*
```

**Files to Update:**
- `app/models/role.py` - Add new roles
- `app/models/permission.py` - Add new permissions
- `app/db/init_db.py` - Seed new roles/permissions

---

### 3. CRUD Operations ⏳

**Existing:**
- Generic `CRUDBase` class with standard operations
- Soft delete support
- Search functionality

**Extend With:**
```python
# Specialized CRUD classes:

class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    async def search_by_category(self, session, category: str):
        ...

    async def get_by_supplier(self, session, supplier_id: UUID):
        ...

    async def update_stock(self, session, product_id: UUID, quantity: Decimal):
        ...

class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    async def get_by_restaurant(self, session, restaurant_id: UUID, status: str):
        ...

    async def get_by_supplier(self, session, supplier_id: UUID, status: str):
        ...

    async def calculate_totals(self, items: list[OrderItem]) -> Decimal:
        ...
```

**Files to Create:**
- `app/crud/restaurant.py`
- `app/crud/supplier.py`
- `app/crud/product.py`
- `app/crud/order.py`
- `app/crud/delivery.py`

---

## 🆕 Needs Implementation

These are entirely new features:

### 1. Restaurant Management 🆕

**New Models:**
```python
# app/models/restaurant.py

class Restaurant(BaseModel, table=True):
    id: UUID
    name_ar: str
    name_en: str
    business_registration: str | None
    phone_primary: str
    # ... (see PRD for full schema)

# app/schemas/restaurant.py

class RestaurantCreate(SQLModel):
    name_ar: str
    name_en: str
    phone_primary: str
    # ...

class RestaurantRead(SQLModel):
    id: UUID
    name_ar: str
    name_en: str
    # ...

# app/api/v1/restaurants.py

@router.post("/restaurants")
async def create_restaurant(...):
    pass

@router.get("/restaurants")
async def list_restaurants(...):
    pass
```

---

### 2. Supplier Management 🆕

**New Models:**
```python
# app/models/supplier.py

class Supplier(BaseModel, table=True):
    id: UUID
    company_name_ar: str
    company_name_en: str
    # ... (see PRD)

# app/api/v1/suppliers.py
```

---

### 3. Product Catalog 🆕

**New Models:**
```python
# app/models/product.py

class Product(BaseModel, table=True):
    id: UUID
    supplier_id: UUID
    name_ar: str
    name_en: str
    category: str
    price_per_unit: Decimal
    stock_quantity: Decimal
    # ...

class Category(BaseModel, table=True):
    id: UUID
    name_ar: str
    name_en: str
    parent_id: UUID | None  # For subcategories
```

---

### 4. Order Management 🆕

**New Models:**
```python
# app/models/order.py

class Order(BaseModel, table=True):
    id: UUID
    order_number: str
    restaurant_id: UUID
    supplier_id: UUID
    status: str
    total_amount: Decimal
    # ... (see PRD)

class OrderItem(BaseModel, table=True):
    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: Decimal
    price_per_unit: Decimal
    subtotal: Decimal
```

---

### 5. Delivery Tracking 🆕

**New Models:**
```python
# app/models/delivery.py

class Delivery(BaseModel, table=True):
    id: UUID
    order_id: UUID
    driver_id: UUID
    status: str
    pickup_address: str
    delivery_address: str
    # ...
```

---

### 6. Payment Processing 🆕

**New Models:**
```python
# app/models/payment.py

class Payment(BaseModel, table=True):
    id: UUID
    order_id: UUID
    payment_method: str
    amount: Decimal
    status: str
    # ...
```

---

### 7. Reviews & Ratings 🆕

**New Models:**
```python
# app/models/review.py

class Review(BaseModel, table=True):
    id: UUID
    order_id: UUID
    restaurant_id: UUID
    supplier_id: UUID
    overall_rating: int  # 1-5
    review_text: str | None
    # ...
```

---

### 8. Notification System 🆕

**New Models:**
```python
# app/models/notification.py

class Notification(BaseModel, table=True):
    id: UUID
    user_id: UUID
    title: str
    body: str
    type: str
    is_read: bool
    # ...
```

**New Service:**
```python
# app/services/notification.py

class NotificationService:
    async def send_push(self, user_id: UUID, title: str, body: str):
        # Firebase Cloud Messaging
        pass

    async def send_sms(self, phone: str, message: str):
        # Twilio
        pass

    async def send_email(self, email: str, subject: str, body: str):
        # SendGrid
        pass
```

---

### 9. Real-time Updates 🆕

**WebSocket Implementation:**
```python
# app/api/v1/websockets.py

from fastapi import WebSocket

@router.websocket("/ws/orders/{order_id}")
async def order_updates(websocket: WebSocket, order_id: UUID):
    await websocket.accept()
    # Subscribe to Redis pub/sub for order updates
    # Push updates to client
    pass
```

---

### 10. Analytics & Reporting 🆕

**New Endpoints:**
```python
# app/api/v1/analytics.py

@router.get("/analytics/restaurant/{id}")
async def restaurant_analytics(id: UUID):
    # Total spend, top suppliers, most ordered products
    pass

@router.get("/analytics/supplier/{id}")
async def supplier_analytics(id: UUID):
    # Revenue, top customers, best-selling products
    pass
```

---

### 11. File Upload (Images) 🆕

**New Service:**
```python
# app/services/storage.py

import boto3

class StorageService:
    async def upload_image(self, file: UploadFile) -> str:
        # Upload to S3
        # Return URL
        pass

    async def delete_image(self, url: str):
        pass
```

**New Endpoint:**
```python
# app/api/v1/upload.py

@router.post("/upload/image")
async def upload_image(file: UploadFile):
    url = await storage_service.upload_image(file)
    return {"url": url}
```

---

### 12. Background Tasks (Celery) 🆕

**New Tasks:**
```python
# app/tasks/notifications.py

from celery import Celery

celery_app = Celery("tasks", broker="redis://localhost:6379/0")

@celery_app.task
def send_order_confirmation_sms(phone: str, order_number: str):
    # Send SMS via Twilio
    pass

@celery_app.task
def generate_invoice_pdf(order_id: UUID):
    # Generate PDF
    # Upload to S3
    # Update order with invoice URL
    pass
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Week 1-2)

- [ ] **Database Schema**
  - [ ] Extend User model (phone, language)
  - [ ] Create Restaurant model
  - [ ] Create Supplier model
  - [ ] Create migration
  - [ ] Run migration

- [ ] **Authentication**
  - [ ] Add phone verification (SMS OTP)
  - [ ] Update registration flow
  - [ ] Add new roles/permissions
  - [ ] Seed database

- [ ] **Basic CRUD**
  - [ ] Restaurant CRUD endpoints
  - [ ] Supplier CRUD endpoints
  - [ ] Test endpoints

### Phase 2: Product Catalog (Week 3-4)

- [ ] **Models**
  - [ ] Product model
  - [ ] Category model
  - [ ] Migration

- [ ] **Endpoints**
  - [ ] Product CRUD
  - [ ] Category CRUD
  - [ ] Search/filter
  - [ ] File upload (images)

- [ ] **Business Logic**
  - [ ] Stock management
  - [ ] Pricing logic
  - [ ] Bulk discounts

### Phase 3: Order System (Week 5-6)

- [ ] **Models**
  - [ ] Order model
  - [ ] OrderItem model
  - [ ] Migration

- [ ] **Endpoints**
  - [ ] Create order
  - [ ] Update order status
  - [ ] List orders (restaurant/supplier views)
  - [ ] Order details

- [ ] **Business Logic**
  - [ ] Order validation
  - [ ] Stock deduction
  - [ ] Pricing calculation
  - [ ] Order status workflow

### Phase 4: Delivery & Payments (Week 7-8)

- [ ] **Delivery**
  - [ ] Delivery model
  - [ ] Driver assignment
  - [ ] Proof of delivery
  - [ ] Tracking endpoints

- [ ] **Payments**
  - [ ] Payment model
  - [ ] COD implementation
  - [ ] Bank transfer
  - [ ] Invoice generation (PDF)

### Phase 5: Notifications & Reviews (Week 9-10)

- [ ] **Notifications**
  - [ ] Notification model
  - [ ] Push notification service (FCM)
  - [ ] SMS service (Twilio)
  - [ ] Email service
  - [ ] Background tasks (Celery)

- [ ] **Reviews**
  - [ ] Review model
  - [ ] Review endpoints
  - [ ] Rating aggregation

### Phase 6: Analytics & Polish (Week 11-12)

- [ ] **Analytics**
  - [ ] Restaurant dashboard
  - [ ] Supplier dashboard
  - [ ] Admin dashboard

- [ ] **Real-time**
  - [ ] WebSocket implementation
  - [ ] Redis pub/sub
  - [ ] Live order updates

- [ ] **Testing & Optimization**
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] Load testing
  - [ ] Performance optimization

---

## 🛠️ Development Commands

### Create New Migration
```bash
alembic revision --autogenerate -m "Add restaurant and supplier models"
alembic upgrade head
```

### Run Tests
```bash
pytest -v
pytest tests/api/v1/test_restaurants.py
```

### Seed Database
```bash
python scripts/seed_data.py
```

### Start Celery Worker
```bash
celery -A app.tasks worker --loglevel=info
```

### Start Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📚 Documentation to Create

- [ ] **API Documentation**
  - [ ] Update `docs/API.md` with new endpoints
  - [ ] Add request/response examples
  - [ ] Document error codes

- [ ] **Database Schema**
  - [ ] Create `docs/DATABASE_SCHEMA.md`
  - [ ] ER diagram
  - [ ] Table descriptions

- [ ] **Developer Guide**
  - [ ] Update `docs/DEVELOPMENT.md`
  - [ ] Add supply chain specific setup
  - [ ] Testing guide

- [ ] **Deployment Guide**
  - [ ] Update `docs/DEPLOYMENT.md`
  - [ ] Add SMS/payment provider setup
  - [ ] Environment variables

---

## 🎯 Quick Wins (Low Effort, High Impact)

1. **Extend User Model** (1 hour)
   - Add phone, language fields
   - Quick migration

2. **Create Basic Models** (4 hours)
   - Restaurant, Supplier, Product models
   - Basic relationships

3. **Set up SMS** (2 hours)
   - Twilio integration
   - Phone verification

4. **File Upload** (2 hours)
   - S3 integration
   - Image upload endpoint

5. **Seed Data** (2 hours)
   - Create seed script
   - Sample restaurants, suppliers, products

---

**Total Existing Code Reuse:** ~60%
**New Code Required:** ~40%
**Estimated Development Time:** 10-12 weeks (MVP)

---

*This mapping shows that the existing FastAPI SQLModel Starter provides a solid foundation for the Restaurant Supply Chain system, significantly reducing development time and ensuring production-ready security, authentication, and infrastructure from day one.*

# Work Breakdown Structure (WBS)
## Restaurant Supply Chain Ordering System

**Version:** 1.0
**Date:** January 2025
**Project Duration:** 12 weeks (3 phases)

---

## Overview

This document breaks down the entire project into **3 Major Phases**, each containing **multiple parts** that can be worked on independently or in parallel.

### Phase Summary

| Phase | Duration | Focus | Deliverable |
|-------|----------|-------|-------------|
| **Phase 1: Foundation** | Weeks 1-4 | Core infrastructure & user management | Working auth, restaurant/supplier profiles |
| **Phase 2: Marketplace** | Weeks 5-8 | Product catalog & ordering system | Browse products, place orders |
| **Phase 3: Operations** | Weeks 9-12 | Delivery, payments, notifications | Complete order fulfillment flow |

---

## Phase 1: Foundation (Weeks 1-4)

**Goal:** Extend existing system for supply chain domain with multi-role management

### Part 1.1: Database Foundation (Week 1)

**Priority:** Critical
**Dependencies:** None
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**1.1.1 Extend User Model** (2 days)
```python
# app/models/user.py - Add fields:
- phone_number: str (E.164 format)
- phone_verified: bool
- phone_verified_at: datetime
- language_preference: str (ar, en, ku)
- currency: str (IQD, USD)
- avatar_url: str
- restaurant_id: UUID (FK to restaurants)
- supplier_id: UUID (FK to suppliers)
```

**Migration:**
```bash
alembic revision --autogenerate -m "001_extend_user_model"
```

**Deliverables:**
- [ ] Updated User model
- [ ] Migration file
- [ ] Unit tests for new fields
- [ ] Update user schemas (UserCreate, UserUpdate, UserRead)

---

**1.1.2 Create Restaurant Model** (1.5 days)
```python
# app/models/restaurant.py
class Restaurant(BaseModel, table=True):
    - Basic info (name_ar, name_en, business_registration)
    - Contact (email, phone_primary, phone_secondary)
    - Address (with GPS coordinates)
    - Business details (type, cuisine, capacity)
    - Verification status
    - Media (logo, cover image)
```

**Deliverables:**
- [ ] Restaurant model
- [ ] Restaurant schemas (Create, Read, Update)
- [ ] Migration: `002_create_restaurants`
- [ ] Unit tests

---

**1.1.3 Create Supplier Model** (1.5 days)
```python
# app/models/supplier.py
class Supplier(BaseModel, table=True):
    - Company info (name_ar, name_en, trade_license)
    - Contact details
    - Address
    - Product categories (JSONB)
    - Delivery areas (JSONB)
    - Payment settings
    - Ratings
```

**Deliverables:**
- [ ] Supplier model
- [ ] Supplier schemas
- [ ] Migration: `003_create_suppliers`
- [ ] Unit tests

---

### Part 1.2: Authentication Extension (Week 1)

**Priority:** Critical
**Dependencies:** Part 1.1 (User model)
**Team:** Backend (1 dev)
**Estimated Effort:** 3 days

#### Tasks

**1.2.1 Phone Verification (SMS OTP)** (2 days)

**Setup Twilio:**
```python
# app/services/sms.py
class SMSService:
    async def send_otp(phone: str, code: str)
    async def verify_otp(phone: str, code: str)
```

**New Endpoints:**
```python
# app/api/v1/auth.py - Add:
POST /api/v1/auth/send-otp       # Send verification code
POST /api/v1/auth/verify-phone   # Verify code
```

**Deliverables:**
- [ ] SMS service (Twilio integration)
- [ ] OTP generation/storage (Redis with TTL)
- [ ] Phone verification endpoints
- [ ] Integration tests
- [ ] Environment config (TWILIO_*)

---

**1.2.2 Update Registration Flow** (1 day)

**Modified Flow:**
1. User registers with email + phone
2. Send SMS OTP
3. User verifies phone
4. Account activated

**Deliverables:**
- [ ] Updated registration endpoint
- [ ] Phone validation
- [ ] Tests for registration flow

---

### Part 1.3: RBAC Extension (Week 2)

**Priority:** Critical
**Dependencies:** None (extends existing RBAC)
**Team:** Backend (1 dev)
**Estimated Effort:** 2 days

#### Tasks

**1.3.1 Add New Roles** (1 day)

**New Roles:**
```python
# app/models/role.py - Add to ROLES dict:
RESTAURANT_OWNER    (priority 20)
RESTAURANT_MANAGER  (priority 25)
RESTAURANT_STAFF    (priority 30)
SUPPLIER_ADMIN      (priority 15)
SUPPLIER_MANAGER    (priority 20)
SUPPLIER_STAFF      (priority 25)
DRIVER              (priority 30)
SUPER_ADMIN         (priority 1)
```

**Deliverables:**
- [ ] Updated role definitions
- [ ] Migration: `004_add_supply_chain_roles`
- [ ] Seed data update

---

**1.3.2 Add New Permissions** (1 day)

**New Permissions:**
```python
# app/models/permission.py - Add:
# Restaurant Management
restaurant:create, restaurant:read, restaurant:update, restaurant:delete

# Supplier Management
supplier:create, supplier:read, supplier:update, supplier:delete

# Product Management
product:create, product:read, product:update, product:delete

# Order Management
order:create, order:read, order:update, order:cancel

# Delivery Management
delivery:create, delivery:read, delivery:update

# Review Management
review:create, review:read

# Payment Management
payment:create, payment:read
```

**Deliverables:**
- [ ] Permission definitions
- [ ] Migration: `005_add_supply_chain_permissions`
- [ ] Role-permission assignments
- [ ] Tests

---

### Part 1.4: Restaurant Management (Week 3)

**Priority:** High
**Dependencies:** Part 1.1.2 (Restaurant model)
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**1.4.1 Restaurant CRUD** (3 days)

**Create CRUD Class:**
```python
# app/crud/restaurant.py
class CRUDRestaurant(CRUDBase[Restaurant, RestaurantCreate, RestaurantUpdate]):
    async def get_by_owner(session, owner_id: UUID)
    async def search(session, query: str, city: str)
    async def get_nearby(session, lat: float, lon: float, radius_km: float)
```

**API Endpoints:**
```python
# app/api/v1/restaurants.py
POST   /api/v1/restaurants              # Create restaurant
GET    /api/v1/restaurants              # List restaurants (admin)
GET    /api/v1/restaurants/my           # My restaurants (owner)
GET    /api/v1/restaurants/search       # Search restaurants
GET    /api/v1/restaurants/{id}         # Get restaurant
PUT    /api/v1/restaurants/{id}         # Update restaurant
DELETE /api/v1/restaurants/{id}         # Soft delete
```

**Deliverables:**
- [ ] CRUD class
- [ ] API endpoints
- [ ] Permission checks
- [ ] Integration tests

---

**1.4.2 Team Management** (1 day)

**API Endpoints:**
```python
# app/api/v1/restaurants.py - Add:
POST   /api/v1/restaurants/{id}/staff        # Add staff member
GET    /api/v1/restaurants/{id}/staff        # List staff
DELETE /api/v1/restaurants/{id}/staff/{uid}  # Remove staff
PUT    /api/v1/restaurants/{id}/staff/{uid}  # Update role
```

**Deliverables:**
- [ ] Team management endpoints
- [ ] Staff invitation system
- [ ] Tests

---

**1.4.3 Verification Workflow** (1 day)

**Admin Endpoints:**
```python
# app/api/v1/admin/verification.py
GET  /api/v1/admin/verifications/pending     # List pending
PUT  /api/v1/admin/verifications/{id}/approve
PUT  /api/v1/admin/verifications/{id}/reject
```

**Deliverables:**
- [ ] Verification endpoints
- [ ] Email notifications
- [ ] Admin dashboard data
- [ ] Tests

---

### Part 1.5: Supplier Management (Week 4)

**Priority:** High
**Dependencies:** Part 1.1.3 (Supplier model)
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**1.5.1 Supplier CRUD** (3 days)

**Create CRUD Class:**
```python
# app/crud/supplier.py
class CRUDSupplier(CRUDBase[Supplier, SupplierCreate, SupplierUpdate]):
    async def search(session, query: str, categories: list[str])
    async def filter_by_delivery_area(session, area: str)
    async def get_top_rated(session, limit: int)
```

**API Endpoints:**
```python
# app/api/v1/suppliers.py
POST   /api/v1/suppliers              # Create supplier
GET    /api/v1/suppliers              # List suppliers
GET    /api/v1/suppliers/search       # Search suppliers
GET    /api/v1/suppliers/{id}         # Get supplier
PUT    /api/v1/suppliers/{id}         # Update supplier
DELETE /api/v1/suppliers/{id}         # Soft delete
```

**Deliverables:**
- [ ] CRUD class
- [ ] API endpoints
- [ ] Search functionality
- [ ] Integration tests

---

**1.5.2 Supplier Dashboard** (1 day)

**Endpoints:**
```python
# app/api/v1/suppliers.py - Add:
GET /api/v1/suppliers/{id}/stats
# Returns: total_orders, revenue, top_products, ratings
```

**Deliverables:**
- [ ] Dashboard endpoint
- [ ] Metrics calculation
- [ ] Tests

---

**1.5.3 Supplier Team & Verification** (1 day)

Similar to restaurant team management and verification.

**Deliverables:**
- [ ] Team management
- [ ] Verification workflow
- [ ] Tests

---

### Phase 1 Completion Criteria

- [ ] All database models created and migrated
- [ ] User authentication with phone verification working
- [ ] Restaurant CRUD complete with verification
- [ ] Supplier CRUD complete with verification
- [ ] RBAC with all new roles/permissions
- [ ] 80%+ test coverage for Phase 1
- [ ] API documentation updated

**Milestone:** Can register restaurants and suppliers, manage teams, verify accounts

---

## Phase 2: Marketplace (Weeks 5-8)

**Goal:** Build product catalog and ordering system

### Part 2.1: Product Catalog (Week 5)

**Priority:** Critical
**Dependencies:** Part 1.5 (Supplier model)
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**2.1.1 Category System** (1 day)

**Create Models:**
```python
# app/models/category.py
class Category(BaseModel, table=True):
    - name_ar, name_en
    - slug (URL-friendly)
    - parent_id (hierarchical)
    - icon_url, image_url
    - sort_order
```

**API Endpoints:**
```python
# app/api/v1/categories.py
GET    /api/v1/categories              # List all (tree structure)
GET    /api/v1/categories/{id}         # Get category
POST   /api/v1/categories              # Create (admin)
PUT    /api/v1/categories/{id}         # Update (admin)
DELETE /api/v1/categories/{id}         # Delete (admin)
```

**Deliverables:**
- [ ] Category model
- [ ] Hierarchical category support
- [ ] CRUD endpoints
- [ ] Seed data (common categories)
- [ ] Tests

---

**2.1.2 Product Model** (2 days)

**Create Models:**
```python
# app/models/product.py
class Product(BaseModel, table=True):
    - Basic info (name_ar, name_en, description, SKU)
    - Pricing (price_per_unit, bulk_discount)
    - Inventory (stock_quantity, low_stock_threshold)
    - Media (image_urls, thumbnail_url)
    - Specifications (origin, grade, certifications)
    - Metrics (total_sold, average_rating)
```

**Deliverables:**
- [ ] Product model + schemas
- [ ] Migration: `006_create_categories_products`
- [ ] Unit tests

---

**2.1.3 Product CRUD** (2 days)

**Create CRUD Class:**
```python
# app/crud/product.py
class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    async def get_by_supplier(session, supplier_id: UUID)
    async def search(session, query: str, lang: str)  # Full-text search
    async def filter(session, category: str, min_price, max_price)
    async def update_stock(session, product_id: UUID, quantity: Decimal)
```

**API Endpoints:**
```python
# app/api/v1/products.py
POST   /api/v1/products                   # Create (supplier only)
GET    /api/v1/products                   # List all (with filters)
GET    /api/v1/products/search            # Search products
GET    /api/v1/products/{id}              # Get product details
PUT    /api/v1/products/{id}              # Update (supplier only)
DELETE /api/v1/products/{id}              # Soft delete
GET    /api/v1/suppliers/{id}/products    # Supplier's catalog
```

**Deliverables:**
- [ ] CRUD class
- [ ] API endpoints
- [ ] Permission checks (only supplier can edit their products)
- [ ] Tests

---

### Part 2.2: Search & Media (Week 6)

**Priority:** High
**Dependencies:** Part 2.1 (Products)
**Team:** Backend (1 dev) + DevOps (0.5 dev)
**Estimated Effort:** 5 days

#### Tasks

**2.2.1 Full-Text Search** (2 days)

**PostgreSQL Setup:**
```sql
-- Create full-text search indexes
CREATE INDEX idx_products_search_ar
ON products USING gin(to_tsvector('arabic', name_ar || ' ' || description_ar));

CREATE INDEX idx_products_search_en
ON products USING gin(to_tsvector('english', name_en || ' ' || description_en));
```

**Search Implementation:**
```python
# app/crud/product.py - Enhance search method:
async def search(
    session,
    query: str,
    language: str = "ar",
    category: str = None,
    min_price: Decimal = None,
    max_price: Decimal = None,
    supplier_id: UUID = None,
    is_available: bool = True,
    sort_by: str = "relevance",  # relevance, price_asc, price_desc, rating
)
```

**Deliverables:**
- [ ] Full-text search (Arabic + English)
- [ ] Advanced filtering
- [ ] Sorting options
- [ ] Search ranking
- [ ] Tests

---

**2.2.2 Image Upload (AWS S3)** (2 days)

**Setup S3:**
```python
# app/services/storage.py
class StorageService:
    async def upload_image(file: UploadFile, folder: str) -> str
    async def delete_image(url: str) -> bool
    async def resize_image(file: UploadFile, sizes: list) -> dict
```

**API Endpoint:**
```python
# app/api/v1/upload.py
POST /api/v1/upload/image
# Accepts: multipart/form-data
# Returns: {"url": "https://s3.../image.jpg"}
```

**Image Processing:**
- Resize to multiple sizes (thumbnail, medium, large)
- Convert to WebP for efficiency
- Upload to S3 with proper ACLs

**Deliverables:**
- [ ] S3 integration
- [ ] Image upload endpoint
- [ ] Image resize/optimization (Pillow)
- [ ] Upload to multiple sizes
- [ ] Tests (mocked S3)

**Environment Variables:**
```env
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_S3_BUCKET=supply-chain-images
AWS_REGION=me-south-1
```

---

**2.2.3 Stock Management** (1 day)

**Stock Operations:**
```python
# app/api/v1/products.py - Add:
PUT /api/v1/products/{id}/stock
# Update stock quantity

GET /api/v1/products/low-stock
# Get products below threshold (supplier view)
```

**Background Job:**
```python
# app/tasks/inventory.py
@celery_app.task
def check_low_stock():
    # Find products below threshold
    # Notify supplier via SMS/email
```

**Deliverables:**
- [ ] Stock update endpoint
- [ ] Low stock alerts
- [ ] Background task (Celery)
- [ ] Tests

---

### Part 2.3: Order System (Week 7)

**Priority:** Critical
**Dependencies:** Part 2.1 (Products)
**Team:** Backend (2 devs)
**Estimated Effort:** 5 days

#### Tasks

**2.3.1 Order Models** (1 day)

**Create Models:**
```python
# app/models/order.py
class Order(BaseModel, table=True):
    - order_number (ORD-20250119-0001)
    - restaurant_id, supplier_id
    - status (pending, confirmed, preparing, etc.)
    - delivery details
    - pricing (subtotal, delivery_fee, tax, total)
    - payment info
    - timestamps for each status

class OrderItem(BaseModel, table=True):
    - order_id, product_id
    - product snapshot (name, SKU, price at time of order)
    - quantity, unit_type
    - subtotal
```

**Deliverables:**
- [ ] Order models + schemas
- [ ] Migration: `007_create_orders`
- [ ] Unit tests

---

**2.3.2 Order Creation** (2 days)

**Order Creation Flow:**
1. Validate products exist and are available
2. Check stock availability
3. Calculate totals (subtotal, tax, delivery fee)
4. Create order + order items
5. Deduct stock
6. Generate order number
7. Send notifications

**API Endpoint:**
```python
# app/api/v1/orders.py
POST /api/v1/orders
{
  "supplier_id": "uuid",
  "items": [
    {"product_id": "uuid", "quantity": 10}
  ],
  "delivery_address": "...",
  "preferred_delivery_date": "2025-01-20",
  "preferred_delivery_slot": "09:00-12:00",
  "payment_method": "cash",
  "notes": "Please call before delivery"
}
```

**Deliverables:**
- [ ] Order creation service
- [ ] Stock validation
- [ ] Stock deduction (atomic)
- [ ] Order number generation (Redis counter)
- [ ] API endpoint
- [ ] Tests (including concurrent orders)

---

**2.3.3 Order Retrieval** (1 day)

**API Endpoints:**
```python
# app/api/v1/orders.py
GET /api/v1/orders
# Filters: status, date_from, date_to, supplier_id, restaurant_id
# Returns different data based on role:
# - Restaurant: their orders
# - Supplier: orders to fulfill
# - Driver: assigned deliveries
# - Admin: all orders

GET /api/v1/orders/{id}
# Full order details with items
```

**Deliverables:**
- [ ] Order list endpoint (role-based filtering)
- [ ] Order details endpoint
- [ ] Pagination
- [ ] Tests

---

**2.3.4 Reorder Functionality** (1 day)

**API Endpoint:**
```python
# app/api/v1/orders.py
POST /api/v1/orders/{id}/reorder
# Clones past order (validates products still available)
# Returns: new order ID
```

**Deliverables:**
- [ ] Reorder endpoint
- [ ] Product availability check
- [ ] Price update check (warn if price changed)
- [ ] Tests

---

### Part 2.4: Order Workflow (Week 8)

**Priority:** Critical
**Dependencies:** Part 2.3 (Orders)
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**2.4.1 Order Status Management** (2 days)

**Status Workflow:**
```
pending → confirmed → preparing → out_for_delivery → delivered
   ↓
cancelled (possible before out_for_delivery)
```

**Who Can Update:**
- `pending → confirmed`: Supplier
- `confirmed → preparing`: Supplier
- `preparing → out_for_delivery`: Supplier (when driver assigned)
- `out_for_delivery → delivered`: Driver
- `* → cancelled`: Restaurant or Supplier

**API Endpoints:**
```python
# app/api/v1/orders.py
PUT /api/v1/orders/{id}/status
{
  "status": "confirmed",
  "notes": "We'll prepare your order"
}

POST /api/v1/orders/{id}/confirm    # Supplier confirms
POST /api/v1/orders/{id}/reject     # Supplier rejects
{
  "reason": "Product out of stock"
}

POST /api/v1/orders/{id}/cancel     # Restaurant cancels
{
  "reason": "Ordered by mistake"
}
```

**Deliverables:**
- [ ] Status workflow validation
- [ ] Permission checks (who can update)
- [ ] Status update endpoints
- [ ] Audit logging for status changes
- [ ] Tests

---

**2.4.2 Stock Rollback on Cancel** (1 day)

**Logic:**
- When order cancelled, restore stock quantities
- Only if order not yet delivered

**Deliverables:**
- [ ] Stock restoration logic
- [ ] Tests (cancel scenarios)

---

**2.4.3 Supplier Order Dashboard** (2 days)

**API Endpoints:**
```python
# app/api/v1/suppliers.py - Add:
GET /api/v1/suppliers/me/orders/pending      # Pending orders
GET /api/v1/suppliers/me/orders/active       # Confirmed/preparing
GET /api/v1/suppliers/me/orders/completed    # Delivered
GET /api/v1/suppliers/me/orders/stats        # Today's stats
```

**Deliverables:**
- [ ] Supplier dashboard endpoints
- [ ] Order statistics
- [ ] Tests

---

### Phase 2 Completion Criteria

- [ ] Product catalog with search (Arabic/English)
- [ ] Image upload working (S3)
- [ ] Order placement functional
- [ ] Order status workflow complete
- [ ] Stock management working
- [ ] Supplier can manage orders
- [ ] Restaurant can view order history
- [ ] 80%+ test coverage for Phase 2

**Milestone:** Restaurants can browse products and place orders; Suppliers can fulfill orders

---

## Phase 3: Operations (Weeks 9-12)

**Goal:** Complete order fulfillment with delivery, payments, and notifications

### Part 3.1: Delivery Management (Week 9)

**Priority:** Critical
**Dependencies:** Part 2.3 (Orders)
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**3.1.1 Delivery Model** (1 day)

**Create Model:**
```python
# app/models/delivery.py
class Delivery(BaseModel, table=True):
    - order_id, driver_id
    - status (assigned, picked_up, in_transit, delivered, failed)
    - pickup/delivery addresses (with GPS)
    - timestamps
    - proof of delivery (signature, photo)
    - distance, delivery_fee
```

**Deliverables:**
- [ ] Delivery model + schemas
- [ ] Migration: `008_create_deliveries`
- [ ] Unit tests

---

**3.1.2 Delivery Assignment** (2 days)

**API Endpoints:**
```python
# app/api/v1/deliveries.py
POST /api/v1/deliveries
{
  "order_id": "uuid",
  "driver_id": "uuid"
}
# Assigns driver to order, creates delivery record

GET /api/v1/deliveries              # List deliveries
GET /api/v1/deliveries/{id}         # Delivery details
GET /api/v1/deliveries/my           # Driver's assigned deliveries
```

**Deliverables:**
- [ ] Delivery assignment endpoint
- [ ] Driver availability check
- [ ] Auto-assignment logic (future: assign nearest driver)
- [ ] Tests

---

**3.1.3 Delivery Tracking** (1 day)

**API Endpoints:**
```python
# app/api/v1/deliveries.py
PUT /api/v1/deliveries/{id}/status
{
  "status": "picked_up"  # or in_transit, delivered
}

GET /api/v1/deliveries/{id}/location
# Returns: driver's current GPS location (for real-time tracking)
```

**Deliverables:**
- [ ] Status update endpoint
- [ ] Location tracking (store in Redis)
- [ ] Tests

---

**3.1.4 Proof of Delivery** (1 day)

**API Endpoint:**
```python
# app/api/v1/deliveries.py
POST /api/v1/deliveries/{id}/proof
{
  "signature_url": "s3://...",
  "photo_url": "s3://...",
  "notes": "Delivered to reception"
}
# Marks delivery as completed
```

**Deliverables:**
- [ ] Proof of delivery endpoint
- [ ] Image upload integration
- [ ] Delivery completion logic
- [ ] Tests

---

### Part 3.2: Google Maps Integration (Week 9)

**Priority:** Medium
**Dependencies:** Part 3.1 (Delivery)
**Team:** Backend (0.5 dev)
**Estimated Effort:** 2 days

#### Tasks

**3.2.1 Maps Service** (2 days)

**Create Service:**
```python
# app/services/maps.py
class MapsService:
    async def geocode_address(address: str) -> tuple[float, float]
    # Convert address to lat/lon

    async def calculate_distance(origin: tuple, dest: tuple) -> float
    # Distance in km

    async def calculate_delivery_fee(distance_km: float) -> Decimal
    # Based on distance tiers

    async def optimize_route(deliveries: list) -> list
    # For multiple deliveries (future feature)
```

**Deliverables:**
- [ ] Google Maps API integration
- [ ] Geocoding service
- [ ] Distance calculation
- [ ] Delivery fee calculation
- [ ] Tests (mocked API)

**Environment Variables:**
```env
GOOGLE_MAPS_API_KEY=xxxxx
```

---

### Part 3.3: Payment System (Week 10)

**Priority:** Critical
**Dependencies:** Part 2.3 (Orders)
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**3.3.1 Payment Model** (1 day)

**Create Model:**
```python
# app/models/payment.py
class Payment(BaseModel, table=True):
    - order_id
    - payment_method (cash, bank_transfer, credit_card)
    - amount, currency
    - status (pending, completed, failed, refunded)
    - transaction_id, gateway_name
    - receipt_url (for bank transfers)
    - timestamps
```

**Deliverables:**
- [ ] Payment model + schemas
- [ ] Migration: `009_create_payments`
- [ ] Unit tests

---

**3.3.2 Cash on Delivery** (1 day)

**API Endpoint:**
```python
# app/api/v1/payments.py
POST /api/v1/payments
{
  "order_id": "uuid",
  "payment_method": "cash",
  "amount": 150000  # IQD
}
# Driver records cash payment
```

**Deliverables:**
- [ ] Cash payment endpoint
- [ ] Update order payment status
- [ ] Tests

---

**3.3.3 Bank Transfer** (1 day)

**Flow:**
1. Restaurant initiates bank transfer
2. Uploads receipt (image/PDF)
3. Admin/Supplier verifies payment
4. Order payment status updated

**API Endpoints:**
```python
# app/api/v1/payments.py
POST /api/v1/payments/bank-transfer
{
  "order_id": "uuid",
  "amount": 150000,
  "receipt_url": "s3://..."
}

PUT /api/v1/payments/{id}/verify
# Admin/Supplier verifies payment
```

**Deliverables:**
- [ ] Bank transfer endpoint
- [ ] Receipt upload
- [ ] Verification workflow
- [ ] Tests

---

**3.3.4 Invoice Generation (PDF)** (2 days)

**PDF Generation:**
```python
# app/services/invoice.py
class InvoiceService:
    async def generate_invoice(order: Order) -> str
    # Returns: S3 URL of PDF invoice

    # Supports:
    # - Arabic/English language
    # - Company logo
    # - Line items with pricing
    # - Tax calculation
    # - QR code (for verification)
```

**Libraries:**
```bash
pip install reportlab
pip install arabic-reshaper python-bidi  # Arabic text support
pip install qrcode  # QR code generation
```

**API Endpoint:**
```python
# app/api/v1/orders.py - Add:
GET /api/v1/orders/{id}/invoice
# Returns: PDF invoice URL or direct PDF download
```

**Deliverables:**
- [ ] Invoice generation service (ReportLab)
- [ ] Arabic PDF support
- [ ] Email invoice to restaurant
- [ ] Invoice download endpoint
- [ ] Tests

---

### Part 3.4: Notification System (Week 11)

**Priority:** High
**Dependencies:** All previous parts
**Team:** Backend (1 dev)
**Estimated Effort:** 5 days

#### Tasks

**3.4.1 Notification Model** (0.5 day)

**Create Model:**
```python
# app/models/notification.py
class Notification(BaseModel, table=True):
    - user_id
    - title, body
    - type (order_update, payment, promotion, system)
    - is_read, read_at
    - action_url (deep link)
    - channels (push, sms, email)
```

**Deliverables:**
- [ ] Notification model + schemas
- [ ] Migration: `010_create_notifications`
- [ ] Unit tests

---

**3.4.2 Celery Setup** (1 day)

**Setup Task Queue:**
```python
# app/core/celery_app.py
from celery import Celery

celery_app = Celery(
    "supply_chain",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
```

**Base Tasks:**
```python
# app/tasks/__init__.py
@celery_app.task
def send_notification_async(user_id, title, body, type, channels):
    pass
```

**Deliverables:**
- [ ] Celery configuration
- [ ] Base task structure
- [ ] Worker startup script
- [ ] Tests

---

**3.4.3 SMS Notifications** (1 day)

**Notification Types:**
- Order confirmed by supplier
- Order status updates
- Delivery on the way
- Delivery completed

**Implementation:**
```python
# app/tasks/notifications.py
@celery_app.task
def send_order_confirmation_sms(order_id: UUID):
    order = get_order(order_id)
    restaurant = get_restaurant(order.restaurant_id)

    message_ar = f"تم تأكيد طلبك #{order.order_number}. سيتم التوصيل في {order.preferred_delivery_date}"

    sms_service.send_sms(restaurant.phone_primary, message_ar)
```

**Deliverables:**
- [ ] SMS notification tasks
- [ ] Template messages (Arabic/English)
- [ ] Integration with order workflow
- [ ] Tests

---

**3.4.4 Push Notifications** (1.5 days)

**Firebase Cloud Messaging:**
```python
# app/services/push.py
import firebase_admin
from firebase_admin import messaging

class PushService:
    async def send_push(
        user_id: UUID,
        title: str,
        body: str,
        data: dict = None
    ):
        # Get user's FCM token from database
        # Send push notification via Firebase
        pass
```

**Setup:**
1. Create Firebase project
2. Download service account JSON
3. Store FCM tokens when users login (mobile app)

**Deliverables:**
- [ ] Firebase setup
- [ ] Push service
- [ ] FCM token storage (User model)
- [ ] Push notification tasks
- [ ] Tests (mocked Firebase)

**Environment Variables:**
```env
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

---

**3.4.5 Email Notifications** (1 day)

**Email Service:**
```python
# app/services/email.py
class EmailService:
    async def send_email(
        to: str,
        subject: str,
        body_html: str,
        attachments: list = None
    ):
        # SendGrid or AWS SES
        pass
```

**Email Templates:**
- Order confirmation
- Invoice (with PDF attachment)
- Verification approved/rejected
- Password reset

**Deliverables:**
- [ ] Email service (SendGrid/SES)
- [ ] HTML email templates
- [ ] Email tasks
- [ ] Tests

**Environment Variables:**
```env
SENDGRID_API_KEY=xxxxx
# or
AWS_SES_REGION=me-south-1
```

---

### Part 3.5: Reviews & Ratings (Week 11)

**Priority:** Medium
**Dependencies:** Part 2.3 (Orders)
**Team:** Backend (0.5 dev)
**Estimated Effort:** 2 days

#### Tasks

**3.5.1 Review Model** (0.5 day)

**Create Model:**
```python
# app/models/review.py
class Review(BaseModel, table=True):
    - order_id (one review per order)
    - restaurant_id, supplier_id
    - overall_rating (1-5)
    - dimension ratings (quality, speed, service, pricing)
    - review_text, photo_urls
    - supplier_response
    - helpful votes
```

**Deliverables:**
- [ ] Review model + schemas
- [ ] Migration: `011_create_reviews`
- [ ] Unique constraint (one review per order)
- [ ] Unit tests

---

**3.5.2 Review Endpoints** (1 day)

**API Endpoints:**
```python
# app/api/v1/reviews.py
POST   /api/v1/reviews                   # Create review (verified purchase only)
GET    /api/v1/reviews                   # List reviews
GET    /api/v1/suppliers/{id}/reviews    # Supplier's reviews
PUT    /api/v1/reviews/{id}/response     # Supplier responds
POST   /api/v1/reviews/{id}/helpful      # Mark as helpful
```

**Deliverables:**
- [ ] Review CRUD endpoints
- [ ] Verified purchase check
- [ ] Supplier response
- [ ] Tests

---

**3.5.3 Rating Aggregation** (0.5 day)

**Background Task:**
```python
# app/tasks/ratings.py
@celery_app.task
def update_supplier_rating(supplier_id: UUID):
    # Calculate average rating
    # Update supplier.average_rating
    pass
```

**Trigger:**
- After review created
- After review updated/deleted

**Deliverables:**
- [ ] Rating calculation task
- [ ] Trigger on review changes
- [ ] Tests

---

### Part 3.6: Analytics & WebSockets (Week 12)

**Priority:** Medium
**Dependencies:** All previous parts
**Team:** Backend (2 devs)
**Estimated Effort:** 5 days

#### Tasks

**3.6.1 Analytics Endpoints** (2 days)

**Restaurant Analytics:**
```python
# app/api/v1/analytics.py
GET /api/v1/analytics/restaurant/{id}
{
  "total_spent": 1500000,  # IQD
  "total_orders": 45,
  "average_order_value": 33333,
  "top_suppliers": [...],
  "most_ordered_products": [...],
  "spending_trend": {  # Last 30 days
    "2025-01-01": 50000,
    "2025-01-02": 75000,
    ...
  }
}
```

**Supplier Analytics:**
```python
GET /api/v1/analytics/supplier/{id}
{
  "total_revenue": 5000000,
  "total_orders": 120,
  "average_order_value": 41666,
  "top_customers": [...],
  "best_selling_products": [...],
  "revenue_trend": {...}
}
```

**Admin Analytics:**
```python
GET /api/v1/analytics/admin
{
  "total_gmv": 10000000,
  "total_orders": 500,
  "active_restaurants": 50,
  "active_suppliers": 10,
  "order_volume_trend": {...},
  "top_performing_suppliers": [...]
}
```

**Deliverables:**
- [ ] Analytics service
- [ ] Restaurant dashboard endpoint
- [ ] Supplier dashboard endpoint
- [ ] Admin dashboard endpoint
- [ ] Caching (Redis)
- [ ] Tests

---

**3.6.2 WebSocket for Real-Time Updates** (2 days)

**WebSocket Endpoints:**
```python
# app/api/v1/websockets.py
@router.websocket("/ws/orders/{order_id}")
async def order_updates(websocket: WebSocket, order_id: UUID):
    await websocket.accept()

    # Subscribe to Redis pub/sub channel
    channel = f"order:{order_id}:updates"

    # Push updates to client
    while True:
        message = await redis.subscribe(channel)
        await websocket.send_json(message)
```

**Redis Pub/Sub:**
```python
# When order status changes:
await redis.publish(
    f"order:{order_id}:updates",
    json.dumps({"status": "confirmed", "timestamp": now()})
)
```

**Deliverables:**
- [ ] WebSocket setup
- [ ] Redis pub/sub integration
- [ ] Order status broadcasts
- [ ] Delivery tracking broadcasts
- [ ] Tests

---

**3.6.3 Testing & Documentation** (1 day)

**End-to-End Tests:**
```python
# tests/e2e/test_order_flow.py
async def test_complete_order_flow():
    # 1. Restaurant browses products
    # 2. Adds to cart
    # 3. Places order
    # 4. Supplier confirms
    # 5. Driver picks up
    # 6. Driver delivers
    # 7. Restaurant reviews
    pass
```

**API Documentation:**
- Update `docs/API.md` with all new endpoints
- Add request/response examples
- Document error codes

**Deliverables:**
- [ ] E2E tests for complete order flow
- [ ] API documentation updated
- [ ] Postman collection exported
- [ ] Deployment guide updated

---

### Phase 3 Completion Criteria

- [ ] Delivery assignment and tracking working
- [ ] Payment system functional (COD + Bank Transfer)
- [ ] Notifications working (SMS, Push, Email)
- [ ] Reviews and ratings functional
- [ ] Analytics dashboards complete
- [ ] Real-time updates via WebSockets
- [ ] 80%+ test coverage for Phase 3
- [ ] Complete API documentation
- [ ] Production deployment ready

**Milestone:** Complete order fulfillment flow from browsing to delivery to payment

---

## Parallel Workstreams

### Mobile App Development (Weeks 1-12)

**Team:** Mobile (2 devs)

#### Week 1-4: Setup & Authentication
- [ ] React Native project setup (Expo)
- [ ] Navigation structure
- [ ] Login/Register screens
- [ ] Phone verification
- [ ] Language switcher (Arabic RTL / English)
- [ ] JWT token management

#### Week 5-8: Core Features
- [ ] Restaurant App:
  - [ ] Browse products (with search/filter)
  - [ ] Product details
  - [ ] Shopping cart
  - [ ] Checkout
  - [ ] Order history
  - [ ] Order tracking
- [ ] Supplier App:
  - [ ] Order dashboard
  - [ ] Product management
  - [ ] Order status updates

#### Week 9-12: Advanced Features
- [ ] Push notifications (Firebase)
- [ ] Real-time updates (Socket.io)
- [ ] Image upload (camera/gallery)
- [ ] Maps integration (delivery tracking)
- [ ] PDF invoice viewer
- [ ] Offline mode (basic)
- [ ] Beta testing
- [ ] App store submission

---

### DevOps & Infrastructure (Weeks 1-12)

**Team:** DevOps (1 dev)

#### Week 1: Cloud Setup
- [ ] AWS/DigitalOcean account
- [ ] VPC and security groups
- [ ] PostgreSQL (RDS or managed)
- [ ] Redis (ElastiCache or managed)
- [ ] S3 bucket setup

#### Week 2-3: CI/CD
- [ ] Docker images (backend, Celery worker)
- [ ] Docker Compose for local dev
- [ ] GitHub Actions workflows
  - [ ] Run tests on PR
  - [ ] Build Docker images
  - [ ] Deploy to staging

#### Week 4-8: Staging Environment
- [ ] Staging server setup
- [ ] Auto-deploy on merge to `develop`
- [ ] Monitoring (Sentry, DataDog)
- [ ] Log aggregation (CloudWatch, Papertrail)

#### Week 9-12: Production Deployment
- [ ] Production server setup
- [ ] Load balancer (ALB or DigitalOcean LB)
- [ ] SSL certificates (Let's Encrypt)
- [ ] Auto-scaling (if needed)
- [ ] Database backups (automated)
- [ ] Disaster recovery plan
- [ ] Production deployment
- [ ] Monitoring & alerts

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Database performance issues | Medium | High | Proper indexing, query optimization, caching | Backend Lead |
| SMS delivery failures (Iraq) | Medium | High | Use reliable provider (Twilio), fallback to email | Backend Dev |
| Concurrent order race conditions | Low | High | Database transactions, optimistic locking | Backend Lead |
| Mobile app crashes | Medium | Medium | Comprehensive testing, error tracking (Sentry) | Mobile Lead |
| Third-party API downtime (Twilio, AWS) | Low | High | Graceful degradation, retry logic | Backend Lead |

### Business Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Low supplier adoption | High | Critical | White-glove onboarding, free trial, incentives | Product Manager |
| Payment fraud | Medium | High | Start with verified suppliers, manual review | Operations |
| Regulatory issues | Low | Medium | Legal compliance team, proper licenses | CEO |

---

## Resource Allocation

### Team Structure

**Backend Team (2 developers):**
- Dev 1: Core models, CRUD, order system
- Dev 2: Notifications, payments, analytics

**Mobile Team (2 developers):**
- Dev 1: Restaurant app
- Dev 2: Supplier app + Driver app

**QA Engineer (1):**
- Write test plans
- Manual testing
- Automated E2E tests
- Load testing

**DevOps Engineer (1):**
- Infrastructure setup
- CI/CD pipelines
- Monitoring & alerts
- Production deployment

**Product Manager (1):**
- Requirements clarification
- Sprint planning
- Stakeholder communication
- User acceptance testing

---

## Dependencies & Prerequisites

### External Services Required

**Week 1:**
- [ ] Twilio account (SMS for Iraq)
- [ ] Firebase project (push notifications)

**Week 6:**
- [ ] AWS account (S3, RDS, SES)
- [ ] Google Maps API key

**Week 10:**
- [ ] SendGrid account (email) or AWS SES

**Week 12:**
- [ ] Domain name registration
- [ ] SSL certificate
- [ ] App Store developer account (iOS)
- [ ] Google Play developer account (Android)

---

## Testing Strategy

### Test Coverage Goals

| Type | Target Coverage | Tools |
|------|----------------|-------|
| Unit Tests | 80%+ | pytest |
| Integration Tests | 70%+ | pytest, httpx |
| E2E Tests | Critical paths | pytest, Playwright |
| Load Tests | 1000 orders/hour | Locust |

### Test Environments

1. **Local:** Developer machines
2. **CI:** GitHub Actions (on every PR)
3. **Staging:** Auto-deploy from `develop` branch
4. **Production:** Manual deploy from `main` branch

---

## Launch Checklist

### Week 12: Pre-Launch

**Technical:**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Security audit completed
- [ ] Load testing passed (1000 orders/hour)
- [ ] Database backups configured
- [ ] Monitoring & alerts active
- [ ] SSL certificates installed
- [ ] API rate limiting configured

**Content:**
- [ ] 20+ test restaurants onboarded
- [ ] 5+ test suppliers onboarded
- [ ] 100+ products in catalog
- [ ] Categories populated
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] User guides (Arabic/English)

**Mobile Apps:**
- [ ] iOS app submitted to App Store
- [ ] Android app submitted to Google Play
- [ ] App screenshots & descriptions ready

**Business:**
- [ ] Customer support email setup
- [ ] Support team trained
- [ ] Pricing finalized
- [ ] Legal compliance verified
- [ ] Bank account for payouts

---

## Post-Launch (Weeks 13-16)

### Immediate Priorities (Week 13)
- [ ] Monitor error rates
- [ ] Fix critical bugs
- [ ] Gather user feedback
- [ ] Performance optimization

### Month 2 (Weeks 14-17)
- [ ] Onboard more suppliers/restaurants
- [ ] Implement feedback
- [ ] Add payment gateways (Qi Card, ZainCash)
- [ ] Build marketing features (promotions, discounts)

### Month 3 (Weeks 18-21)
- [ ] Inventory management features
- [ ] Advanced analytics
- [ ] Mobile app improvements
- [ ] Expand to second city (Basra or Erbil)

---

## Success Metrics

### Week 4 (Phase 1 Complete)
- [ ] 5+ restaurants registered
- [ ] 2+ suppliers registered
- [ ] All auth flows working

### Week 8 (Phase 2 Complete)
- [ ] 20+ restaurants registered
- [ ] 5+ suppliers registered
- [ ] 100+ products in catalog
- [ ] 10+ orders placed

### Week 12 (Phase 3 Complete - Launch)
- [ ] 50+ active restaurants
- [ ] 10+ active suppliers
- [ ] 50+ orders completed
- [ ] Mobile apps in stores
- [ ] < 5% error rate
- [ ] < 200ms API response time (p95)

### Month 3 Post-Launch
- [ ] 200+ active restaurants
- [ ] 25+ active suppliers
- [ ] 500+ monthly orders
- [ ] $100K+ monthly GMV
- [ ] 60%+ user retention

---

## Communication Plan

### Daily Standups (15 min)
- What did you do yesterday?
- What will you do today?
- Any blockers?

### Weekly Sprint Reviews (Friday)
- Demo completed work
- Review sprint goals
- Gather feedback

### Bi-weekly Sprint Planning (Monday)
- Plan next sprint tasks
- Estimate effort
- Assign tasks

### Monthly Stakeholder Updates
- Progress report
- Metrics review
- Next month priorities

---

## Contact & Resources

**Project Manager:** [Name]
**Backend Lead:** [Name]
**Mobile Lead:** [Name]
**DevOps Lead:** [Name]

**Slack Channels:**
- #supply-chain-general
- #supply-chain-backend
- #supply-chain-mobile
- #supply-chain-devops

**Tools:**
- GitHub: [Repo URL]
- Jira: [Board URL]
- Figma: [Design URL]
- Postman: [Workspace URL]

---

**Let's build this! 🚀**

*Last Updated: January 2025*

# Database Schema: Restaurant Supply Chain System

**Version:** 1.0
**Date:** January 2025
**DBMS:** PostgreSQL 15+ (SQLite for development)

---

## Overview

This document defines the complete database schema for the Restaurant Supply Chain Ordering System. All tables inherit audit fields from `BaseModel`.

### Audit Fields (Inherited by All Tables)

Every table automatically includes:

```sql
created_at        TIMESTAMP    NOT NULL  DEFAULT NOW()
updated_at        TIMESTAMP    NOT NULL  DEFAULT NOW()
created_by_id     UUID         NULL      REFERENCES users(id)
updated_by_id     UUID         NULL      REFERENCES users(id)
is_deleted        BOOLEAN      NOT NULL  DEFAULT FALSE
deleted_at        TIMESTAMP    NULL
deleted_by_id     UUID         NULL      REFERENCES users(id)
```

---

## Core Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    User     │────────>│ Restaurant  │────────>│    Order    │
└─────────────┘         └─────────────┘         └─────────────┘
       │                                               │
       │                                               │
       │                ┌─────────────┐                │
       └───────────────>│  Supplier   │<───────────────┘
                        └─────────────┘
                               │
                               │
                        ┌─────────────┐
                        │   Product   │
                        └─────────────┘
                               │
                               │
                        ┌─────────────┐
                        │  OrderItem  │
                        └─────────────┘
```

---

## 1. User Management

### 1.1 `users` (Extended)

Extends existing user table for supply chain needs.

```sql
CREATE TABLE users (
    -- Primary Key
    id                  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Authentication
    email               VARCHAR(255)  NOT NULL UNIQUE,
    hashed_password     VARCHAR(255)  NOT NULL,
    phone_number        VARCHAR(20)   NOT NULL UNIQUE,  -- NEW: E.164 format
    phone_verified      BOOLEAN       NOT NULL DEFAULT FALSE,  -- NEW

    -- Profile
    full_name           VARCHAR(255)  NOT NULL,
    avatar_url          VARCHAR(500)  NULL,  -- NEW

    -- Preferences
    language_preference VARCHAR(5)    NOT NULL DEFAULT 'ar',  -- NEW: ar, en, ku
    currency            VARCHAR(3)    NOT NULL DEFAULT 'IQD',  -- NEW

    -- Status
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    is_superuser        BOOLEAN       NOT NULL DEFAULT FALSE,

    -- Relationships (NEW)
    restaurant_id       UUID          NULL REFERENCES restaurants(id) ON DELETE SET NULL,
    supplier_id         UUID          NULL REFERENCES suppliers(id) ON DELETE SET NULL,

    -- Verification (NEW)
    email_verified      BOOLEAN       NOT NULL DEFAULT FALSE,
    email_verified_at   TIMESTAMP     NULL,
    phone_verified_at   TIMESTAMP     NULL,

    -- Audit fields (inherited from BaseModel)
    created_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id       UUID          NULL REFERENCES users(id),
    updated_by_id       UUID          NULL REFERENCES users(id),
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMP     NULL,
    deleted_by_id       UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE NOT is_deleted;
CREATE INDEX idx_users_phone ON users(phone_number) WHERE NOT is_deleted;
CREATE INDEX idx_users_restaurant ON users(restaurant_id) WHERE NOT is_deleted;
CREATE INDEX idx_users_supplier ON users(supplier_id) WHERE NOT is_deleted;
```

**Changes from Original:**
- Added `phone_number` (required, unique)
- Added `phone_verified`, `phone_verified_at`
- Added `language_preference` (ar, en, ku)
- Added `restaurant_id`, `supplier_id` foreign keys
- Added `avatar_url`, `currency`
- Added `email_verified`, `email_verified_at`

---

### 1.2 `roles` (Existing - Extended)

```sql
-- Existing table, add new roles via seed data:
-- restaurant_owner, restaurant_manager, restaurant_staff
-- supplier_admin, supplier_manager, supplier_staff
-- driver, super_admin
```

---

### 1.3 `permissions` (Existing - Extended)

```sql
-- Existing table, add new permissions via seed data:
-- restaurant:create, restaurant:read, restaurant:update, restaurant:delete
-- supplier:create, supplier:read, supplier:update, supplier:delete
-- product:create, product:read, product:update, product:delete
-- order:create, order:read, order:update, order:cancel
-- delivery:create, delivery:read, delivery:update
-- review:create, review:read
-- payment:create, payment:read
```

---

## 2. Restaurant Management

### 2.1 `restaurants`

```sql
CREATE TABLE restaurants (
    -- Primary Key
    id                      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Info
    name_ar                 VARCHAR(255)  NOT NULL,
    name_en                 VARCHAR(255)  NOT NULL,
    business_registration   VARCHAR(100)  NULL,  -- Tax ID / Trade License

    -- Contact
    email                   VARCHAR(255)  NOT NULL,
    phone_primary           VARCHAR(20)   NOT NULL,
    phone_secondary         VARCHAR(20)   NULL,

    -- Address
    address_line1           VARCHAR(255)  NOT NULL,
    address_line2           VARCHAR(255)  NULL,
    city                    VARCHAR(100)  NOT NULL,
    district                VARCHAR(100)  NOT NULL,  -- Neighborhood/district
    postal_code             VARCHAR(20)   NULL,
    latitude                DECIMAL(10,8) NULL,  -- For delivery routing
    longitude               DECIMAL(11,8) NULL,

    -- Business Details
    restaurant_type         VARCHAR(50)   NOT NULL,  -- fast_food, fine_dining, cafe, bakery
    cuisine_type            VARCHAR(100)  NOT NULL,  -- iraqi, lebanese, turkish, international
    seating_capacity        INTEGER       NULL,
    operating_hours         JSONB         NULL,  -- {"monday": {"open": "09:00", "close": "23:00"}}

    -- Media
    logo_url                VARCHAR(500)  NULL,
    cover_image_url         VARCHAR(500)  NULL,

    -- Verification
    is_verified             BOOLEAN       NOT NULL DEFAULT FALSE,
    verification_status     VARCHAR(50)   NOT NULL DEFAULT 'pending',  -- pending, approved, rejected
    verification_document_url VARCHAR(500) NULL,  -- Trade license upload
    verified_at             TIMESTAMP     NULL,
    verified_by_id          UUID          NULL REFERENCES users(id),

    -- Settings
    auto_accept_orders      BOOLEAN       NOT NULL DEFAULT TRUE,
    preferred_payment_method VARCHAR(50)  NOT NULL DEFAULT 'cash',

    -- Relationships
    owner_id                UUID          NOT NULL REFERENCES users(id),

    -- Audit fields (inherited)
    created_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id           UUID          NULL REFERENCES users(id),
    updated_by_id           UUID          NULL REFERENCES users(id),
    is_deleted              BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at              TIMESTAMP     NULL,
    deleted_by_id           UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_restaurants_owner ON restaurants(owner_id) WHERE NOT is_deleted;
CREATE INDEX idx_restaurants_city ON restaurants(city) WHERE NOT is_deleted;
CREATE INDEX idx_restaurants_type ON restaurants(restaurant_type) WHERE NOT is_deleted;
CREATE INDEX idx_restaurants_verified ON restaurants(is_verified) WHERE NOT is_deleted;
CREATE INDEX idx_restaurants_location ON restaurants USING gist(
    ll_to_earth(latitude, longitude)
) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;  -- For geospatial queries
```

**Storage:** ~500 bytes per row
**Estimated Rows (Year 1):** 500-1,000

---

## 3. Supplier Management

### 3.1 `suppliers`

```sql
CREATE TABLE suppliers (
    -- Primary Key
    id                      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Company Info
    company_name_ar         VARCHAR(255)  NOT NULL,
    company_name_en         VARCHAR(255)  NOT NULL,
    trade_license           VARCHAR(100)  NULL,
    tax_id                  VARCHAR(100)  NULL,

    -- Contact
    email                   VARCHAR(255)  NOT NULL,
    phone_primary           VARCHAR(20)   NOT NULL,
    phone_secondary         VARCHAR(20)   NULL,

    -- Main Address (Warehouse/Office)
    address_line1           VARCHAR(255)  NOT NULL,
    address_line2           VARCHAR(255)  NULL,
    city                    VARCHAR(100)  NOT NULL,
    district                VARCHAR(100)  NOT NULL,
    postal_code             VARCHAR(20)   NULL,
    latitude                DECIMAL(10,8) NULL,
    longitude               DECIMAL(11,8) NULL,

    -- Business Details
    product_categories      JSONB         NOT NULL,  -- ["produce", "meat", "dairy"]
    delivery_areas          JSONB         NOT NULL,  -- ["karada", "mansour", "jadiriya"]
    minimum_order_value     DECIMAL(10,2) NOT NULL DEFAULT 0,
    delivery_schedule       JSONB         NULL,  -- {"monday": ["09:00-12:00", "14:00-18:00"]}

    -- Media
    logo_url                VARCHAR(500)  NULL,
    banner_url              VARCHAR(500)  NULL,

    -- Verification
    is_verified             BOOLEAN       NOT NULL DEFAULT FALSE,
    verification_status     VARCHAR(50)   NOT NULL DEFAULT 'pending',
    trade_license_url       VARCHAR(500)  NULL,
    verified_at             TIMESTAMP     NULL,
    verified_by_id          UUID          NULL REFERENCES users(id),

    -- Payment Settings
    accepts_cash            BOOLEAN       NOT NULL DEFAULT TRUE,
    accepts_credit          BOOLEAN       NOT NULL DEFAULT FALSE,
    allows_installments     BOOLEAN       NOT NULL DEFAULT FALSE,
    payment_terms_days      INTEGER       NULL,  -- Net-30, Net-60

    -- Business Metrics
    total_orders            INTEGER       NOT NULL DEFAULT 0,
    average_rating          DECIMAL(3,2)  NULL,  -- 0.00 - 5.00
    total_reviews           INTEGER       NOT NULL DEFAULT 0,

    -- Settings
    auto_accept_orders      BOOLEAN       NOT NULL DEFAULT FALSE,
    response_time_hours     INTEGER       NULL,  -- Average response time

    -- Relationships
    owner_id                UUID          NOT NULL REFERENCES users(id),

    -- Audit fields (inherited)
    created_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id           UUID          NULL REFERENCES users(id),
    updated_by_id           UUID          NULL REFERENCES users(id),
    is_deleted              BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at              TIMESTAMP     NULL,
    deleted_by_id           UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_suppliers_owner ON suppliers(owner_id) WHERE NOT is_deleted;
CREATE INDEX idx_suppliers_city ON suppliers(city) WHERE NOT is_deleted;
CREATE INDEX idx_suppliers_verified ON suppliers(is_verified) WHERE NOT is_deleted;
CREATE INDEX idx_suppliers_rating ON suppliers(average_rating DESC) WHERE NOT is_deleted;
```

**Storage:** ~800 bytes per row
**Estimated Rows (Year 1):** 50-100

---

## 4. Product Catalog

### 4.1 `categories`

```sql
CREATE TABLE categories (
    -- Primary Key
    id                  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Category Info
    name_ar             VARCHAR(255)  NOT NULL,
    name_en             VARCHAR(255)  NOT NULL,
    slug                VARCHAR(255)  NOT NULL UNIQUE,  -- For URLs: "fresh-produce"
    description_ar      TEXT          NULL,
    description_en      TEXT          NULL,

    -- Hierarchy
    parent_id           UUID          NULL REFERENCES categories(id) ON DELETE CASCADE,
    level               INTEGER       NOT NULL DEFAULT 0,  -- 0 = root, 1 = subcategory, etc.
    sort_order          INTEGER       NOT NULL DEFAULT 0,

    -- Media
    icon_url            VARCHAR(500)  NULL,
    image_url           VARCHAR(500)  NULL,

    -- Status
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,

    -- Audit fields (inherited)
    created_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id       UUID          NULL REFERENCES users(id),
    updated_by_id       UUID          NULL REFERENCES users(id),
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMP     NULL,
    deleted_by_id       UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_categories_parent ON categories(parent_id) WHERE NOT is_deleted;
CREATE INDEX idx_categories_slug ON categories(slug) WHERE NOT is_deleted;
CREATE INDEX idx_categories_active ON categories(is_active) WHERE NOT is_deleted;
```

**Example Categories:**
```
Produce (Level 0)
├── Vegetables (Level 1)
│   ├── Leafy Greens (Level 2)
│   └── Root Vegetables (Level 2)
├── Fruits (Level 1)
└── Herbs (Level 1)

Meat & Poultry (Level 0)
├── Beef (Level 1)
├── Chicken (Level 1)
└── Lamb (Level 1)
```

---

### 4.2 `products`

```sql
CREATE TABLE products (
    -- Primary Key
    id                      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    supplier_id             UUID          NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    category_id             UUID          NOT NULL REFERENCES categories(id),

    -- Product Info
    name_ar                 VARCHAR(255)  NOT NULL,
    name_en                 VARCHAR(255)  NOT NULL,
    description_ar          TEXT          NULL,
    description_en          TEXT          NULL,
    sku                     VARCHAR(100)  NOT NULL,  -- Stock Keeping Unit
    barcode                 VARCHAR(100)  NULL,  -- UPC/EAN barcode

    -- Pricing
    unit_type               VARCHAR(50)   NOT NULL,  -- kg, liter, piece, box, carton
    price_per_unit          DECIMAL(10,2) NOT NULL,
    currency                VARCHAR(3)    NOT NULL DEFAULT 'IQD',

    -- Bulk Pricing (Optional)
    bulk_discount_qty       DECIMAL(10,2) NULL,  -- Buy 10+ kg
    bulk_price_per_unit     DECIMAL(10,2) NULL,  -- Get 5% off

    -- Inventory
    stock_quantity          DECIMAL(10,2) NOT NULL DEFAULT 0,
    low_stock_threshold     DECIMAL(10,2) NOT NULL DEFAULT 10,
    is_available            BOOLEAN       NOT NULL DEFAULT TRUE,
    availability_status     VARCHAR(50)   NOT NULL DEFAULT 'in_stock',  -- in_stock, low_stock, out_of_stock

    -- Media
    image_urls              JSONB         NULL,  -- ["url1", "url2", "url3"]
    thumbnail_url           VARCHAR(500)  NULL,

    -- Specifications
    origin_country          VARCHAR(100)  NULL,  -- Iraq, Turkey, Jordan
    grade                   VARCHAR(10)   NULL,  -- A, B, C
    certifications          JSONB         NULL,  -- ["halal", "organic", "iso"]
    shelf_life_days         INTEGER       NULL,

    -- Metrics
    total_sold              DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_orders            INTEGER       NOT NULL DEFAULT 0,
    average_rating          DECIMAL(3,2)  NULL,
    total_reviews           INTEGER       NOT NULL DEFAULT 0,

    -- Seasonal
    is_seasonal             BOOLEAN       NOT NULL DEFAULT FALSE,
    available_from_month    INTEGER       NULL,  -- 1-12
    available_to_month      INTEGER       NULL,  -- 1-12

    -- Settings
    is_featured             BOOLEAN       NOT NULL DEFAULT FALSE,
    is_on_sale              BOOLEAN       NOT NULL DEFAULT FALSE,
    sale_price              DECIMAL(10,2) NULL,
    sale_ends_at            TIMESTAMP     NULL,

    -- Audit fields (inherited)
    created_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id           UUID          NULL REFERENCES users(id),
    updated_by_id           UUID          NULL REFERENCES users(id),
    is_deleted              BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at              TIMESTAMP     NULL,
    deleted_by_id           UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_products_supplier ON products(supplier_id) WHERE NOT is_deleted;
CREATE INDEX idx_products_category ON products(category_id) WHERE NOT is_deleted;
CREATE INDEX idx_products_sku ON products(sku) WHERE NOT is_deleted;
CREATE INDEX idx_products_available ON products(is_available) WHERE NOT is_deleted;
CREATE INDEX idx_products_featured ON products(is_featured) WHERE NOT is_deleted;
CREATE INDEX idx_products_rating ON products(average_rating DESC) WHERE NOT is_deleted;

-- Full-text search (PostgreSQL specific)
CREATE INDEX idx_products_search_ar ON products USING gin(to_tsvector('arabic', name_ar || ' ' || COALESCE(description_ar, '')));
CREATE INDEX idx_products_search_en ON products USING gin(to_tsvector('english', name_en || ' ' || COALESCE(description_en, '')));
```

**Storage:** ~1 KB per row
**Estimated Rows (Year 1):** 5,000-10,000

---

## 5. Order Management

### 5.1 `orders`

```sql
CREATE TABLE orders (
    -- Primary Key
    id                      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number            VARCHAR(50)   NOT NULL UNIQUE,  -- ORD-20250119-0001

    -- Relationships
    restaurant_id           UUID          NOT NULL REFERENCES restaurants(id),
    supplier_id             UUID          NOT NULL REFERENCES suppliers(id),

    -- Order Details
    status                  VARCHAR(50)   NOT NULL DEFAULT 'pending',
    -- pending, confirmed, preparing, out_for_delivery, delivered, cancelled, refunded
    order_date              TIMESTAMP     NOT NULL DEFAULT NOW(),

    -- Delivery
    delivery_address        TEXT          NOT NULL,
    delivery_latitude       DECIMAL(10,8) NULL,
    delivery_longitude      DECIMAL(11,8) NULL,
    preferred_delivery_date DATE          NULL,
    preferred_delivery_slot VARCHAR(50)   NULL,  -- "09:00-12:00"
    actual_delivery_date    TIMESTAMP     NULL,

    -- Pricing
    subtotal                DECIMAL(10,2) NOT NULL,  -- Sum of order items
    delivery_fee            DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_amount         DECIMAL(10,2) NOT NULL DEFAULT 0,
    tax_amount              DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_amount            DECIMAL(10,2) NOT NULL,  -- subtotal + delivery - discount + tax

    currency                VARCHAR(3)    NOT NULL DEFAULT 'IQD',

    -- Payment
    payment_method          VARCHAR(50)   NOT NULL,  -- cash, credit_card, bank_transfer, installment
    payment_status          VARCHAR(50)   NOT NULL DEFAULT 'pending',  -- pending, paid, failed, refunded
    paid_at                 TIMESTAMP     NULL,

    -- Notes
    customer_notes          TEXT          NULL,
    supplier_notes          TEXT          NULL,
    cancellation_reason     TEXT          NULL,
    cancelled_by_id         UUID          NULL REFERENCES users(id),
    cancelled_at            TIMESTAMP     NULL,

    -- Tracking
    driver_id               UUID          NULL REFERENCES users(id),
    invoice_url             VARCHAR(500)  NULL,  -- PDF invoice

    -- Status Timestamps (for analytics)
    confirmed_at            TIMESTAMP     NULL,
    preparing_at            TIMESTAMP     NULL,
    shipped_at              TIMESTAMP     NULL,
    delivered_at            TIMESTAMP     NULL,

    -- Audit fields (inherited)
    created_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id           UUID          NULL REFERENCES users(id),
    updated_by_id           UUID          NULL REFERENCES users(id),
    is_deleted              BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at              TIMESTAMP     NULL,
    deleted_by_id           UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_orders_restaurant ON orders(restaurant_id, status) WHERE NOT is_deleted;
CREATE INDEX idx_orders_supplier ON orders(supplier_id, status) WHERE NOT is_deleted;
CREATE INDEX idx_orders_number ON orders(order_number) WHERE NOT is_deleted;
CREATE INDEX idx_orders_status ON orders(status) WHERE NOT is_deleted;
CREATE INDEX idx_orders_date ON orders(order_date DESC) WHERE NOT is_deleted;
CREATE INDEX idx_orders_driver ON orders(driver_id) WHERE NOT is_deleted AND driver_id IS NOT NULL;
CREATE INDEX idx_orders_payment_status ON orders(payment_status) WHERE NOT is_deleted;
```

**Storage:** ~800 bytes per row
**Estimated Rows (Year 1):** 24,000 (2,000/month)

---

### 5.2 `order_items`

```sql
CREATE TABLE order_items (
    -- Primary Key
    id                  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    order_id            UUID          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id          UUID          NOT NULL REFERENCES products(id),

    -- Snapshot (product data at time of order)
    product_name_ar     VARCHAR(255)  NOT NULL,
    product_name_en     VARCHAR(255)  NOT NULL,
    product_sku         VARCHAR(100)  NOT NULL,
    product_image_url   VARCHAR(500)  NULL,

    -- Pricing (snapshot)
    unit_type           VARCHAR(50)   NOT NULL,
    quantity            DECIMAL(10,2) NOT NULL,
    price_per_unit      DECIMAL(10,2) NOT NULL,  -- Price at time of order
    subtotal            DECIMAL(10,2) NOT NULL,  -- quantity * price_per_unit

    -- Notes
    item_notes          TEXT          NULL,  -- Special requests

    -- Audit fields (inherited)
    created_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id       UUID          NULL REFERENCES users(id),
    updated_by_id       UUID          NULL REFERENCES users(id),
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMP     NULL,
    deleted_by_id       UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_order_items_order ON order_items(order_id) WHERE NOT is_deleted;
CREATE INDEX idx_order_items_product ON order_items(product_id) WHERE NOT is_deleted;
```

**Storage:** ~400 bytes per row
**Estimated Rows (Year 1):** 120,000 (avg 5 items/order × 24,000 orders)

---

## 6. Delivery Management

### 6.1 `deliveries`

```sql
CREATE TABLE deliveries (
    -- Primary Key
    id                  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    order_id            UUID          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    driver_id           UUID          NOT NULL REFERENCES users(id),

    -- Status
    status              VARCHAR(50)   NOT NULL DEFAULT 'assigned',
    -- assigned, picked_up, in_transit, delivered, failed

    -- Pickup
    pickup_address      TEXT          NOT NULL,
    pickup_latitude     DECIMAL(10,8) NOT NULL,
    pickup_longitude    DECIMAL(11,8) NOT NULL,

    -- Delivery
    delivery_address    TEXT          NOT NULL,
    delivery_latitude   DECIMAL(10,8) NOT NULL,
    delivery_longitude  DECIMAL(11,8) NOT NULL,

    -- Timestamps
    assigned_at         TIMESTAMP     NOT NULL DEFAULT NOW(),
    picked_up_at        TIMESTAMP     NULL,
    delivered_at        TIMESTAMP     NULL,
    failed_at           TIMESTAMP     NULL,

    -- Proof of Delivery
    signature_url       VARCHAR(500)  NULL,  -- Customer signature image
    photo_url           VARCHAR(500)  NULL,  -- Photo of delivered goods
    delivery_notes      TEXT          NULL,
    failure_reason      TEXT          NULL,

    -- Metrics
    distance_km         DECIMAL(6,2)  NULL,
    delivery_fee        DECIMAL(10,2) NOT NULL,
    driver_earnings     DECIMAL(10,2) NULL,  -- Driver commission

    -- Audit fields (inherited)
    created_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id       UUID          NULL REFERENCES users(id),
    updated_by_id       UUID          NULL REFERENCES users(id),
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMP     NULL,
    deleted_by_id       UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_deliveries_order ON deliveries(order_id) WHERE NOT is_deleted;
CREATE INDEX idx_deliveries_driver ON deliveries(driver_id, status) WHERE NOT is_deleted;
CREATE INDEX idx_deliveries_status ON deliveries(status) WHERE NOT is_deleted;
CREATE INDEX idx_deliveries_date ON deliveries(assigned_at DESC) WHERE NOT is_deleted;
```

**Storage:** ~500 bytes per row
**Estimated Rows (Year 1):** 24,000 (1 delivery per order)

---

## 7. Payment Management

### 7.1 `payments`

```sql
CREATE TABLE payments (
    -- Primary Key
    id                  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    order_id            UUID          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,

    -- Payment Info
    payment_method      VARCHAR(50)   NOT NULL,  -- cash, credit_card, bank_transfer, installment
    amount              DECIMAL(10,2) NOT NULL,
    currency            VARCHAR(3)    NOT NULL DEFAULT 'IQD',

    -- Status
    status              VARCHAR(50)   NOT NULL DEFAULT 'pending',
    -- pending, completed, failed, refunded, cancelled

    -- Timestamps
    initiated_at        TIMESTAMP     NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMP     NULL,
    failed_at           TIMESTAMP     NULL,
    refunded_at         TIMESTAMP     NULL,

    -- Transaction Details
    transaction_id      VARCHAR(255)  NULL,  -- External payment gateway transaction ID
    gateway_name        VARCHAR(50)   NULL,  -- qi_card, zaincash, fastpay
    receipt_url         VARCHAR(500)  NULL,  -- For bank transfers
    failure_reason      TEXT          NULL,
    refund_reason       TEXT          NULL,

    -- Notes
    notes               TEXT          NULL,

    -- Audit fields (inherited)
    created_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id       UUID          NULL REFERENCES users(id),
    updated_by_id       UUID          NULL REFERENCES users(id),
    is_deleted          BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMP     NULL,
    deleted_by_id       UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_payments_order ON payments(order_id) WHERE NOT is_deleted;
CREATE INDEX idx_payments_status ON payments(status) WHERE NOT is_deleted;
CREATE INDEX idx_payments_method ON payments(payment_method) WHERE NOT is_deleted;
CREATE INDEX idx_payments_transaction ON payments(transaction_id) WHERE NOT is_deleted AND transaction_id IS NOT NULL;
```

**Storage:** ~400 bytes per row
**Estimated Rows (Year 1):** 24,000 (1 payment per order)

---

## 8. Reviews & Ratings

### 8.1 `reviews`

```sql
CREATE TABLE reviews (
    -- Primary Key
    id                          UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    order_id                    UUID          NOT NULL REFERENCES orders(id),
    restaurant_id               UUID          NOT NULL REFERENCES restaurants(id),
    supplier_id                 UUID          NOT NULL REFERENCES suppliers(id),
    reviewer_id                 UUID          NOT NULL REFERENCES users(id),

    -- Ratings (1-5 stars)
    overall_rating              INTEGER       NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    product_quality_rating      INTEGER       NULL CHECK (product_quality_rating BETWEEN 1 AND 5),
    delivery_speed_rating       INTEGER       NULL CHECK (delivery_speed_rating BETWEEN 1 AND 5),
    customer_service_rating     INTEGER       NULL CHECK (customer_service_rating BETWEEN 1 AND 5),
    pricing_rating              INTEGER       NULL CHECK (pricing_rating BETWEEN 1 AND 5),

    -- Review Content
    review_text                 TEXT          NULL,
    photo_urls                  JSONB         NULL,  -- ["url1", "url2"]

    -- Status
    is_verified_purchase        BOOLEAN       NOT NULL DEFAULT TRUE,
    is_visible                  BOOLEAN       NOT NULL DEFAULT TRUE,
    is_flagged                  BOOLEAN       NOT NULL DEFAULT FALSE,
    flag_reason                 TEXT          NULL,

    -- Supplier Response
    supplier_response           TEXT          NULL,
    supplier_response_at        TIMESTAMP     NULL,
    supplier_response_by_id     UUID          NULL REFERENCES users(id),

    -- Helpful Votes
    helpful_count               INTEGER       NOT NULL DEFAULT 0,
    unhelpful_count             INTEGER       NOT NULL DEFAULT 0,

    -- Audit fields (inherited)
    created_at                  TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id               UUID          NULL REFERENCES users(id),
    updated_by_id               UUID          NULL REFERENCES users(id),
    is_deleted                  BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at                  TIMESTAMP     NULL,
    deleted_by_id               UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_reviews_order ON reviews(order_id) WHERE NOT is_deleted;
CREATE INDEX idx_reviews_restaurant ON reviews(restaurant_id) WHERE NOT is_deleted;
CREATE INDEX idx_reviews_supplier ON reviews(supplier_id, is_visible) WHERE NOT is_deleted;
CREATE INDEX idx_reviews_rating ON reviews(overall_rating) WHERE NOT is_deleted;
CREATE INDEX idx_reviews_date ON reviews(created_at DESC) WHERE NOT is_deleted;

-- Unique constraint: One review per order
CREATE UNIQUE INDEX idx_reviews_order_unique ON reviews(order_id) WHERE NOT is_deleted;
```

**Storage:** ~600 bytes per row
**Estimated Rows (Year 1):** 12,000 (50% of orders get reviewed)

---

## 9. Notifications

### 9.1 `notifications`

```sql
CREATE TABLE notifications (
    -- Primary Key
    id              UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    user_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Content
    title           VARCHAR(255)  NOT NULL,
    body            TEXT          NOT NULL,
    type            VARCHAR(50)   NOT NULL,
    -- order_update, payment, promotion, system, delivery

    -- Status
    is_read         BOOLEAN       NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMP     NULL,

    -- Metadata
    action_url      VARCHAR(500)  NULL,  -- Deep link: myapp://orders/123
    data            JSONB         NULL,  -- Additional structured data

    -- Delivery Channels
    sent_via_push   BOOLEAN       NOT NULL DEFAULT FALSE,
    sent_via_sms    BOOLEAN       NOT NULL DEFAULT FALSE,
    sent_via_email  BOOLEAN       NOT NULL DEFAULT FALSE,

    -- Timestamps
    sent_at         TIMESTAMP     NULL,
    expires_at      TIMESTAMP     NULL,

    -- Audit fields (inherited)
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id   UUID          NULL REFERENCES users(id),
    updated_by_id   UUID          NULL REFERENCES users(id),
    is_deleted      BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at      TIMESTAMP     NULL,
    deleted_by_id   UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read) WHERE NOT is_deleted;
CREATE INDEX idx_notifications_type ON notifications(type) WHERE NOT is_deleted;
CREATE INDEX idx_notifications_date ON notifications(created_at DESC) WHERE NOT is_deleted;

-- Auto-delete old read notifications (7 days)
CREATE INDEX idx_notifications_cleanup ON notifications(is_read, created_at) WHERE is_read = TRUE;
```

**Storage:** ~400 bytes per row
**Estimated Rows (Year 1):** 200,000+ (multiple notifications per order)

---

## 10. Supporting Tables

### 10.1 `addresses`

```sql
CREATE TABLE addresses (
    -- Primary Key
    id              UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    user_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Address Type
    type            VARCHAR(50)   NOT NULL,  -- delivery, billing, warehouse

    -- Address Details
    label           VARCHAR(100)  NULL,  -- "Main Restaurant", "Warehouse 2"
    address_line1   VARCHAR(255)  NOT NULL,
    address_line2   VARCHAR(255)  NULL,
    city            VARCHAR(100)  NOT NULL,
    district        VARCHAR(100)  NOT NULL,
    postal_code     VARCHAR(20)   NULL,
    latitude        DECIMAL(10,8) NULL,
    longitude       DECIMAL(11,8) NULL,

    -- Contact
    contact_name    VARCHAR(255)  NULL,
    contact_phone   VARCHAR(20)   NULL,

    -- Settings
    is_default      BOOLEAN       NOT NULL DEFAULT FALSE,

    -- Audit fields (inherited)
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id   UUID          NULL REFERENCES users(id),
    updated_by_id   UUID          NULL REFERENCES users(id),
    is_deleted      BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at      TIMESTAMP     NULL,
    deleted_by_id   UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_addresses_user ON addresses(user_id) WHERE NOT is_deleted;
CREATE INDEX idx_addresses_type ON addresses(type) WHERE NOT is_deleted;
```

---

### 10.2 `favorites`

```sql
CREATE TABLE favorites (
    -- Primary Key
    id              UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    user_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id      UUID          NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_id     UUID          NULL REFERENCES suppliers(id) ON DELETE CASCADE,

    -- Type
    type            VARCHAR(50)   NOT NULL,  -- product, supplier

    -- Audit fields (inherited)
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by_id   UUID          NULL REFERENCES users(id),
    updated_by_id   UUID          NULL REFERENCES users(id),
    is_deleted      BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at      TIMESTAMP     NULL,
    deleted_by_id   UUID          NULL REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_favorites_user ON favorites(user_id, type) WHERE NOT is_deleted;
CREATE UNIQUE INDEX idx_favorites_product_unique ON favorites(user_id, product_id) WHERE product_id IS NOT NULL AND NOT is_deleted;
CREATE UNIQUE INDEX idx_favorites_supplier_unique ON favorites(user_id, supplier_id) WHERE supplier_id IS NOT NULL AND NOT is_deleted;
```

---

### 10.3 `audit_logs` (Existing)

Already implemented - will track all supply chain actions.

---

## Database Indexes Summary

**Critical Indexes (High Query Frequency):**
1. `orders` by restaurant + status
2. `orders` by supplier + status
3. `products` by supplier + availability
4. `products` full-text search (Arabic/English)
5. `deliveries` by driver + status
6. `notifications` by user + read status

**Performance Considerations:**
- Partition `orders` table by month (if >1M rows)
- Partition `notifications` table by month
- Archive old `audit_logs` to separate table

---

## Storage Estimates (Year 1)

| Table | Rows | Size/Row | Total Size |
|-------|------|----------|------------|
| users | 1,000 | 600 B | 600 KB |
| restaurants | 500 | 500 B | 250 KB |
| suppliers | 50 | 800 B | 40 KB |
| categories | 100 | 400 B | 40 KB |
| products | 5,000 | 1 KB | 5 MB |
| orders | 24,000 | 800 B | 19 MB |
| order_items | 120,000 | 400 B | 48 MB |
| deliveries | 24,000 | 500 B | 12 MB |
| payments | 24,000 | 400 B | 10 MB |
| reviews | 12,000 | 600 B | 7 MB |
| notifications | 200,000 | 400 B | 80 MB |
| addresses | 2,000 | 400 B | 800 KB |
| favorites | 5,000 | 200 B | 1 MB |
| audit_logs | 500,000 | 600 B | 300 MB |
| **TOTAL** | | | **~480 MB** |

**With Indexes:** ~1 GB
**With 3 years data:** ~3-5 GB

---

## Migration Strategy

### Phase 1: Extend Existing Tables
```sql
-- Add columns to users table
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);
ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN language_preference VARCHAR(5) DEFAULT 'ar';
-- ... more columns
```

### Phase 2: Create New Tables
```sql
-- Create in order (respect foreign keys)
CREATE TABLE restaurants (...);
CREATE TABLE suppliers (...);
CREATE TABLE categories (...);
CREATE TABLE products (...);
-- ... more tables
```

### Phase 3: Seed Initial Data
```sql
INSERT INTO categories (name_ar, name_en, slug) VALUES
    ('منتجات طازجة', 'Fresh Produce', 'fresh-produce'),
    ('لحوم ودواجن', 'Meat & Poultry', 'meat-poultry'),
    ('ألبان', 'Dairy', 'dairy');
-- ... more seed data
```

---

## Backup & Recovery

**Backup Strategy:**
- Daily automated backups (PostgreSQL pg_dump)
- Weekly full backups to S3
- Transaction log streaming (for point-in-time recovery)

**Retention:**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 1 year

---

**End of Database Schema Document**

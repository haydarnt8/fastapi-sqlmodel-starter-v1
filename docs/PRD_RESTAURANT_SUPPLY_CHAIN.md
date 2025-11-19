# Product Requirements Document (PRD)
## Restaurant Supply Chain Ordering System

**Version:** 1.0
**Date:** January 2025
**Status:** Draft
**Market:** Iraq (Primary) | MENA Region (Secondary)

---

## Executive Summary

### Problem Statement

**Current State in Iraq:**
- Restaurants order supplies via WhatsApp calls/messages (unstructured, inefficient)
- No centralized order management or history
- Zero pricing transparency or comparison
- No delivery tracking or scheduling
- Manual inventory management leading to stockouts or overstocking
- No supplier performance metrics
- Cash-heavy transactions with limited payment options
- Language barriers (Arabic/English/Kurdish)

**Market Opportunity:**
- 15,000+ restaurants in Baghdad alone
- 100+ food suppliers in major Iraqi cities
- Zero established B2B supply chain platforms
- Growing restaurant industry post-2020 recovery
- Increasing smartphone penetration (80%+)
- Young, tech-savvy business owners (25-45 age group)

**Competitors:**
- **USA:** BlueCart, Choco, MarketMan (not available in Iraq)
- **Iraq:** None (greenfield opportunity)

### Solution Vision

A **mobile-first B2B marketplace** connecting restaurants with suppliers in Iraq, enabling:
- Digital ordering with order history
- Real-time pricing transparency
- Delivery scheduling and tracking
- Inventory management and alerts
- Multi-language support (Arabic, English, Kurdish)
- Multiple payment methods (cash, credit, installments)
- Supplier ratings and reviews
- Analytics and insights for both parties

### Success Metrics (Year 1)

| Metric | Target |
|--------|--------|
| Restaurant signups | 500+ |
| Supplier signups | 50+ |
| Monthly orders | 2,000+ |
| GMV (Gross Merchandise Value) | $500,000+ |
| Average order value | $250 |
| Order completion rate | 85%+ |
| User retention (30-day) | 60%+ |
| NPS (Net Promoter Score) | 40+ |

---

## User Personas

### 1. Restaurant Owner/Manager (Buyer)

**Name:** Ahmed Al-Baghdadi
**Age:** 35
**Role:** Owner of mid-sized restaurant (50 seats)
**Location:** Baghdad, Iraq

**Pain Points:**
- Spends 2-3 hours daily calling suppliers
- No record of previous orders or prices
- Frequent delivery delays without notification
- Price fluctuations without notice
- Difficulty comparing supplier prices
- Manual inventory tracking on paper

**Goals:**
- Reduce ordering time to <15 minutes/day
- Access order history and repeat orders easily
- Compare prices across suppliers
- Track deliveries in real-time
- Automate low-stock alerts
- Reduce food waste from overstocking

**Tech Proficiency:** Medium (uses WhatsApp, social media)

---

### 2. Supplier/Distributor (Seller)

**Name:** Omar Al-Masri
**Role:** Food Distributor (fruits, vegetables, dairy)
**Location:** Baghdad
**Business Size:** 200+ restaurant clients

**Pain Points:**
- Receives orders via WhatsApp/calls (disorganized)
- Difficult to track order status
- No visibility into inventory levels
- Manual invoice generation
- Payment collection challenges
- No data on sales trends

**Goals:**
- Centralized order management dashboard
- Automated inventory tracking
- Digital invoicing and payment tracking
- Customer relationship management
- Sales analytics and forecasting
- Reduce order errors

**Tech Proficiency:** Medium-High (uses Excel, WhatsApp Business)

---

### 3. Delivery Driver (Logistics)

**Name:** Hassan
**Age:** 28
**Role:** Delivery driver for supplier

**Pain Points:**
- Receives delivery addresses via phone calls
- No route optimization
- Manual proof of delivery
- Payment collection confusion

**Goals:**
- Clear delivery manifest on mobile
- GPS navigation integration
- Digital proof of delivery
- Daily earnings summary

---

## Core Features & Requirements

### Phase 1: MVP (Minimum Viable Product) - 3 Months

#### 1.1 User Authentication & Management

**Requirements:**
- [x] Multi-role system (Restaurant, Supplier, Admin, Driver)
- [x] JWT-based authentication (already implemented)
- [x] Email/password registration
- [ ] Phone number verification (SMS OTP via Twilio/Vonage)
- [ ] Role-specific onboarding flows
- [x] Password reset functionality
- [ ] Multi-language UI (Arabic RTL, English, Kurdish)

**Technical Implementation:**
- Leverage existing RBAC system
- Add new roles: `restaurant_owner`, `restaurant_staff`, `supplier_admin`, `supplier_staff`, `driver`, `super_admin`
- Add phone number field to User model
- Integrate SMS provider (Twilio for Iraq coverage)

---

#### 1.2 Restaurant Management

**Features:**

**Restaurant Profile:**
- Restaurant name (Arabic + English)
- Business registration number
- Address with GPS coordinates
- Phone numbers (primary, secondary)
- Operating hours
- Restaurant type (fast food, fine dining, café, bakery, etc.)
- Cuisine type (Iraqi, Lebanese, Turkish, International, etc.)
- Seating capacity
- Logo/photo upload

**Team Management:**
- Add/remove staff members
- Assign roles (manager, chef, inventory manager)
- Activity logs per staff member

**Business Verification:**
- Upload business license
- Admin approval workflow
- Verified badge display

**Data Model:**
```python
class Restaurant(BaseModel, table=True):
    id: UUID
    name_ar: str  # Arabic name
    name_en: str  # English name
    business_registration: str | None
    phone_primary: str
    phone_secondary: str | None
    email: str

    # Address
    address_line1: str
    address_line2: str | None
    city: str
    district: str
    latitude: float | None
    longitude: float | None

    # Business details
    restaurant_type: str  # Enum: fast_food, fine_dining, cafe, bakery, etc.
    cuisine_type: str
    seating_capacity: int | None
    operating_hours: dict  # JSON: {"monday": {"open": "09:00", "close": "23:00"}}

    # Media
    logo_url: str | None
    cover_image_url: str | None

    # Verification
    is_verified: bool = False
    verification_document_url: str | None
    verified_at: datetime | None

    # Relationships
    owner_id: UUID  # Foreign key to User
    staff: list["User"] = Relationship(back_populates="restaurant")
```

---

#### 1.3 Supplier Management

**Features:**

**Supplier Profile:**
- Company name (Arabic + English)
- Trade license number
- Warehouse/office addresses (multiple)
- Phone numbers
- Product categories (produce, meat, dairy, dry goods, etc.)
- Delivery areas (districts/cities served)
- Minimum order value
- Delivery schedule (days/times)
- Company logo

**Catalog Management:**
- Add/edit/delete products
- Product categories and subcategories
- Pricing (per unit, bulk discounts)
- Stock levels (available, low stock, out of stock)
- Product images
- Product specifications (origin, grade, certifications)
- Seasonal availability

**Inventory Tracking:**
- Real-time stock levels
- Low stock alerts
- Batch/lot tracking
- Expiry date management

**Data Model:**
```python
class Supplier(BaseModel, table=True):
    id: UUID
    company_name_ar: str
    company_name_en: str
    trade_license: str | None
    phone_primary: str
    phone_secondary: str | None
    email: str

    # Business details
    product_categories: list[str]  # JSON array
    delivery_areas: list[str]  # Districts/cities
    minimum_order_value: Decimal
    delivery_schedule: dict  # {"monday": ["09:00-12:00", "14:00-18:00"]}

    # Media
    logo_url: str | None

    # Verification
    is_verified: bool = False
    trade_license_url: str | None

    # Settings
    accepts_cash: bool = True
    accepts_credit: bool = False
    allows_installments: bool = False

    # Relationships
    owner_id: UUID
    products: list["Product"] = Relationship(back_populates="supplier")

class Product(BaseModel, table=True):
    id: UUID
    supplier_id: UUID

    # Product info
    name_ar: str
    name_en: str
    description_ar: str | None
    description_en: str | None
    category: str  # Enum: produce, meat, dairy, beverages, etc.
    subcategory: str
    sku: str  # Stock Keeping Unit

    # Pricing
    unit_type: str  # kg, liter, piece, box, carton
    price_per_unit: Decimal
    bulk_discount_qty: int | None  # Quantity for bulk discount
    bulk_price_per_unit: Decimal | None

    # Inventory
    stock_quantity: Decimal
    low_stock_threshold: Decimal
    is_available: bool = True

    # Media
    image_urls: list[str]  # JSON array

    # Specifications
    origin_country: str | None
    grade: str | None  # A, B, C grade
    certifications: list[str] | None  # Halal, Organic, etc.

    # Relationships
    supplier: Supplier = Relationship(back_populates="products")
```

---

#### 1.4 Product Catalog & Search

**Features:**

**Browse & Search:**
- Category-based browsing
- Multi-filter search (category, supplier, price range, availability)
- Search by product name (Arabic/English)
- Sort by price, popularity, rating
- Supplier-specific catalogs

**Product Details:**
- High-resolution images (zoom)
- Detailed description
- Pricing breakdown (unit price, bulk discounts)
- Stock availability indicator
- Supplier information
- Delivery estimate
- Reviews and ratings

**Favorites/Wishlist:**
- Save favorite products
- Quick reorder from favorites

**APIs:**
```
GET    /api/v1/products                  # List all products (with filters)
GET    /api/v1/products/{id}             # Product details
GET    /api/v1/products/search           # Search products
GET    /api/v1/suppliers/{id}/products   # Supplier's catalog
POST   /api/v1/products                  # Create product (supplier only)
PUT    /api/v1/products/{id}             # Update product
DELETE /api/v1/products/{id}             # Delete product (soft delete)
```

---

#### 1.5 Shopping Cart & Ordering

**Features:**

**Shopping Cart:**
- Add/remove products
- Update quantities
- View subtotal per supplier
- View total order value
- Save cart for later
- Apply discounts/promo codes

**Order Placement:**
- Multi-supplier checkout (separate orders per supplier)
- Delivery address selection
- Preferred delivery date/time slot
- Special instructions/notes
- Payment method selection
- Order summary review

**Order Confirmation:**
- Order number generation
- Email/SMS confirmation
- Estimated delivery time
- Payment instructions

**Data Model:**
```python
class Order(BaseModel, table=True):
    id: UUID
    order_number: str  # Human-readable: ORD-20250119-0001

    # Relationships
    restaurant_id: UUID
    supplier_id: UUID

    # Order details
    status: str  # pending, confirmed, preparing, out_for_delivery, delivered, cancelled
    order_date: datetime

    # Delivery
    delivery_address: str
    delivery_latitude: float | None
    delivery_longitude: float | None
    preferred_delivery_date: date
    preferred_delivery_slot: str  # "09:00-12:00"
    actual_delivery_date: datetime | None

    # Pricing
    subtotal: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal = 0
    tax_amount: Decimal = 0
    total_amount: Decimal

    # Payment
    payment_method: str  # cash, credit_card, bank_transfer, installment
    payment_status: str  # pending, paid, failed, refunded
    paid_at: datetime | None

    # Notes
    customer_notes: str | None
    supplier_notes: str | None
    cancellation_reason: str | None

    # Tracking
    driver_id: UUID | None

    # Relationships
    restaurant: Restaurant = Relationship()
    supplier: Supplier = Relationship()
    items: list["OrderItem"] = Relationship(back_populates="order")

class OrderItem(BaseModel, table=True):
    id: UUID
    order_id: UUID
    product_id: UUID

    # Snapshot of product at order time
    product_name_ar: str
    product_name_en: str
    sku: str

    # Pricing
    unit_type: str
    quantity: Decimal
    price_per_unit: Decimal
    subtotal: Decimal  # quantity * price_per_unit

    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship()
```

**APIs:**
```
POST   /api/v1/orders                    # Create order
GET    /api/v1/orders                    # List orders (with filters)
GET    /api/v1/orders/{id}               # Order details
PUT    /api/v1/orders/{id}/status        # Update order status
DELETE /api/v1/orders/{id}               # Cancel order
POST   /api/v1/orders/{id}/confirm       # Supplier confirms order
```

---

#### 1.6 Order Management & Tracking

**Restaurant View:**
- Active orders dashboard
- Order history (searchable, filterable)
- Order status updates (real-time)
- Reorder functionality (one-click)
- Invoice download (PDF)
- Order tracking (driver location)

**Supplier View:**
- Incoming orders dashboard
- Order acceptance/rejection
- Update order status (preparing, ready, shipped)
- Assign driver to order
- Batch invoice generation
- Order analytics (daily/weekly/monthly)

**Driver View:**
- Assigned deliveries list
- Route optimization
- Customer contact info
- Proof of delivery (signature, photo)
- Earnings tracker

**Order Status Flow:**
```
pending → confirmed → preparing → out_for_delivery → delivered
                ↓
            cancelled (at any stage before out_for_delivery)
```

**Real-time Updates:**
- WebSocket connections for live status updates
- Push notifications (mobile)
- SMS notifications (critical updates)

---

#### 1.7 Delivery Management

**Features:**

**Delivery Zones:**
- Supplier defines delivery areas (district-based)
- Delivery fees per zone
- Minimum order value per zone

**Delivery Scheduling:**
- Supplier sets available time slots
- Restaurant selects preferred slot
- Auto-assignment to drivers
- Route optimization (Google Maps API)

**Proof of Delivery:**
- Customer signature (digital)
- Photo of delivered goods
- Timestamp and GPS location
- Delivery notes

**Data Model:**
```python
class Delivery(BaseModel, table=True):
    id: UUID
    order_id: UUID
    driver_id: UUID

    # Status
    status: str  # assigned, in_transit, delivered, failed

    # Tracking
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    delivery_address: str
    delivery_latitude: float
    delivery_longitude: float

    # Timestamps
    assigned_at: datetime
    picked_up_at: datetime | None
    delivered_at: datetime | None

    # Proof of delivery
    signature_url: str | None
    photo_url: str | None
    delivery_notes: str | None

    # Distance & fees
    distance_km: float | None
    delivery_fee: Decimal

    # Relationships
    order: Order = Relationship()
    driver: "User" = Relationship()
```

---

#### 1.8 Payment Integration

**Payment Methods (Phase 1):**

1. **Cash on Delivery (COD)** - Primary method
   - Driver collects payment
   - Manual confirmation in app

2. **Bank Transfer** - For established customers
   - Upload payment receipt
   - Admin verification

**Future Payment Methods (Phase 2):**
- Credit/Debit cards (Qi Card - Iraq)
- Mobile wallets (ZainCash, FastPay)
- Buy Now Pay Later (BNPL) - Installments

**Invoice Generation:**
- Auto-generated PDF invoices
- Tax calculation (Iraq VAT rules)
- Email delivery
- Arabic/English language toggle

**Data Model:**
```python
class Payment(BaseModel, table=True):
    id: UUID
    order_id: UUID

    # Payment info
    payment_method: str
    amount: Decimal
    currency: str = "IQD"  # Iraqi Dinar

    # Status
    status: str  # pending, completed, failed, refunded

    # Timestamps
    initiated_at: datetime
    completed_at: datetime | None

    # Details
    transaction_id: str | None  # For digital payments
    receipt_url: str | None  # For bank transfers
    notes: str | None

    # Relationships
    order: Order = Relationship()
```

---

#### 1.9 Notifications System

**Notification Types:**

**For Restaurants:**
- Order confirmed by supplier
- Order status updates
- Delivery is on the way
- Delivery completed
- New products from favorite suppliers
- Price changes
- Promotional offers

**For Suppliers:**
- New order received
- Low stock alerts
- Payment received
- Order cancelled

**For Drivers:**
- New delivery assigned
- Route updates

**Channels:**
- In-app notifications
- Push notifications (FCM - Firebase Cloud Messaging)
- SMS (Twilio)
- Email (SendGrid/AWS SES)

**Data Model:**
```python
class Notification(BaseModel, table=True):
    id: UUID
    user_id: UUID

    # Content
    title: str
    body: str
    type: str  # order_update, payment, promotion, system

    # Status
    is_read: bool = False
    read_at: datetime | None

    # Metadata
    action_url: str | None  # Deep link to relevant screen
    data: dict | None  # JSON: additional data

    # Channels
    sent_via_push: bool = False
    sent_via_sms: bool = False
    sent_via_email: bool = False
```

---

#### 1.10 Reviews & Ratings

**Features:**

**Restaurant Reviews Supplier:**
- 5-star rating system
- Written review (optional)
- Rate on multiple dimensions:
  - Product quality
  - Delivery speed
  - Customer service
  - Pricing
- Photo uploads (received products)

**Supplier Reviews Restaurant:**
- Professionalism rating
- Payment promptness
- Order clarity

**Display:**
- Average rating per supplier
- Recent reviews on supplier profile
- Verified purchase badge

**Data Model:**
```python
class Review(BaseModel, table=True):
    id: UUID
    order_id: UUID
    restaurant_id: UUID
    supplier_id: UUID

    # Ratings (1-5 stars)
    overall_rating: int
    product_quality_rating: int | None
    delivery_speed_rating: int | None
    customer_service_rating: int | None
    pricing_rating: int | None

    # Review
    review_text: str | None
    photo_urls: list[str] | None  # JSON array

    # Status
    is_verified_purchase: bool = True
    is_visible: bool = True

    # Response
    supplier_response: str | None
    supplier_response_at: datetime | None
```

---

#### 1.11 Analytics & Reporting

**Restaurant Dashboard:**
- Total spend (daily/weekly/monthly)
- Top suppliers
- Most ordered products
- Order frequency
- Average order value
- Spending trends (chart)
- Inventory insights

**Supplier Dashboard:**
- Total revenue (daily/weekly/monthly)
- Top customers
- Best-selling products
- Order volume trends
- Average order value
- Customer retention rate
- Low stock alerts

**Admin Dashboard:**
- Platform GMV
- Active restaurants/suppliers
- Order volume trends
- Top performing suppliers
- User growth metrics
- Revenue metrics (commission tracking)

---

### Phase 2: Growth Features - Months 4-6

#### 2.1 Inventory Management

**For Restaurants:**
- Track ingredient stock levels
- Low stock alerts
- Auto-reorder suggestions (based on usage patterns)
- Recipe management (ingredients → dishes)
- Waste tracking
- FIFO/LIFO tracking

#### 2.2 Credit & Payment Terms

**Features:**
- Net-30/Net-60 payment terms (for verified restaurants)
- Credit limit management
- Outstanding balance tracking
- Payment reminders
- Late payment penalties
- Credit score system

#### 2.3 Bulk Ordering & Group Buying

**Features:**
- Group orders with other restaurants (shared delivery)
- Bulk discount tiers
- Pre-order for upcoming products
- Seasonal product reservations

#### 2.4 Advanced Search & Recommendations

**Features:**
- AI-powered product recommendations
- "Restaurants also bought" suggestions
- Price drop alerts
- Substitute product suggestions (when out of stock)

#### 2.5 Loyalty & Rewards Program

**Features:**
- Points on every order
- Cashback rewards
- Referral bonuses
- Tiered membership (Bronze, Silver, Gold)
- Exclusive deals for loyal customers

---

### Phase 3: Scale & Expansion - Months 7-12

#### 3.1 Multi-Location Support

**Features:**
- Restaurant chains with multiple branches
- Centralized ordering for all locations
- Location-specific inventory
- Cross-location analytics

#### 3.2 Supplier Network & Marketplace

**Features:**
- Connect suppliers with each other (B2B2B)
- Supplier rating system
- Quality certifications (ISO, Halal, Organic)
- Supplier performance metrics

#### 3.3 Financial Services Integration

**Features:**
- Invoice factoring
- Working capital loans
- Insurance integration
- Tax filing assistance

#### 3.4 Logistics Optimization

**Features:**
- Third-party logistics (3PL) integration
- Fleet management for suppliers
- Route optimization AI
- Temperature-controlled delivery tracking

#### 3.5 Regional Expansion

**Target Markets:**
- Basra, Erbil, Mosul (Iraq)
- Jordan, Lebanon (MENA)
- Kurdish region specialization

---

## Technical Architecture

### Technology Stack

**Backend:**
- ✅ FastAPI (Python 3.11+) - Already implemented
- ✅ SQLModel + PostgreSQL - Already implemented
- ✅ Redis (caching, sessions) - Already implemented
- ✅ Alembic (migrations) - Already implemented
- ⏳ Celery (async tasks) - **NEW**
- ⏳ WebSocket (real-time updates) - **NEW**

**Mobile Apps:**
- React Native (iOS + Android)
- Expo for rapid development
- Redux for state management
- Socket.io client for real-time

**Infrastructure:**
- AWS/DigitalOcean (Middle East regions)
- Docker + Kubernetes
- CloudFront CDN (for images)
- S3 (file storage)

**Third-party Services:**
- Twilio (SMS for Iraq)
- Firebase Cloud Messaging (push notifications)
- Google Maps API (geocoding, routing)
- Sentry (error tracking)
- Mixpanel/Amplitude (analytics)

---

### API Architecture

**RESTful Endpoints:**

```
# Authentication (✅ Already implemented)
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

# Restaurants (⏳ New)
POST   /api/v1/restaurants
GET    /api/v1/restaurants
GET    /api/v1/restaurants/{id}
PUT    /api/v1/restaurants/{id}
DELETE /api/v1/restaurants/{id}
POST   /api/v1/restaurants/{id}/staff

# Suppliers (⏳ New)
POST   /api/v1/suppliers
GET    /api/v1/suppliers
GET    /api/v1/suppliers/{id}
PUT    /api/v1/suppliers/{id}
GET    /api/v1/suppliers/search

# Products (⏳ New)
POST   /api/v1/products
GET    /api/v1/products
GET    /api/v1/products/{id}
PUT    /api/v1/products/{id}
DELETE /api/v1/products/{id}
GET    /api/v1/products/search
GET    /api/v1/suppliers/{id}/products

# Orders (⏳ New)
POST   /api/v1/orders
GET    /api/v1/orders
GET    /api/v1/orders/{id}
PUT    /api/v1/orders/{id}/status
POST   /api/v1/orders/{id}/confirm
POST   /api/v1/orders/{id}/cancel

# Delivery (⏳ New)
GET    /api/v1/deliveries
GET    /api/v1/deliveries/{id}
PUT    /api/v1/deliveries/{id}/status
POST   /api/v1/deliveries/{id}/proof

# Reviews (⏳ New)
POST   /api/v1/reviews
GET    /api/v1/reviews
GET    /api/v1/suppliers/{id}/reviews

# Analytics (⏳ New)
GET    /api/v1/analytics/restaurant/{id}
GET    /api/v1/analytics/supplier/{id}
GET    /api/v1/analytics/admin

# Notifications (⏳ New)
GET    /api/v1/notifications
PUT    /api/v1/notifications/{id}/read
```

**WebSocket Endpoints:**
```
WS     /ws/orders/{order_id}        # Real-time order updates
WS     /ws/delivery/{delivery_id}   # Live delivery tracking
```

---

### Database Schema Extensions

**New Models Required:**

1. ✅ `User` - Extend with phone, role, language preference
2. ⏳ `Restaurant` - Restaurant profiles
3. ⏳ `Supplier` - Supplier profiles
4. ⏳ `Product` - Product catalog
5. ⏳ `Category` - Product categories
6. ⏳ `Order` - Order management
7. ⏳ `OrderItem` - Order line items
8. ⏳ `Delivery` - Delivery tracking
9. ⏳ `Payment` - Payment records
10. ⏳ `Review` - Reviews and ratings
11. ⏳ `Notification` - Notification system
12. ⏳ `Address` - Saved addresses
13. ⏳ `Cart` - Shopping cart (optional, can be client-side)

**Indexes Required:**
- `products.supplier_id, products.category`
- `orders.restaurant_id, orders.status, orders.order_date`
- `orders.supplier_id, orders.status`
- `reviews.supplier_id, reviews.overall_rating`

---

### Security & Compliance

**Data Protection:**
- ✅ Argon2 password hashing
- ✅ JWT with refresh tokens
- ✅ RBAC system
- ⏳ PII encryption (phone numbers, addresses)
- ⏳ GDPR compliance (data export, deletion)

**API Security:**
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Input validation
- ⏳ API key authentication (for mobile apps)
- ⏳ Request signing (prevent tampering)

**Financial Security:**
- PCI compliance (for card payments)
- Fraud detection
- Transaction auditing

---

## Internationalization (i18n)

**Supported Languages:**
1. **Arabic** (Primary) - RTL layout
2. **English** (Secondary)
3. **Kurdish** (Sorani) - Future

**Implementation:**
- ✅ Backend translation system exists
- ⏳ Extend with supply chain terminology
- ⏳ Mobile app i18n (react-i18next)
- ⏳ Database content (Arabic/English columns)

**RTL Considerations:**
- UI layout reversal
- Icon mirroring
- Text alignment

---

## Mobile App Features

### Restaurant App

**Home Screen:**
- Quick reorder (recent orders)
- Search bar
- Category shortcuts
- Featured suppliers
- Active orders banner

**Screens:**
1. Browse/Search Products
2. Product Details
3. Shopping Cart
4. Checkout
5. Order Tracking
6. Order History
7. Supplier Profiles
8. Inventory Dashboard
9. Analytics
10. Settings

### Supplier App

**Home Screen:**
- Pending orders count
- Today's revenue
- Low stock alerts
- Quick actions (add product, view orders)

**Screens:**
1. Orders Dashboard
2. Order Details
3. Product Catalog Management
4. Inventory Management
5. Customer List
6. Analytics
7. Settings

### Driver App

**Screens:**
1. Delivery List
2. Delivery Details (with map)
3. Navigation
4. Proof of Delivery
5. Earnings

---

## Business Model

### Revenue Streams

1. **Commission per Order** (Primary)
   - 3-5% commission on each transaction
   - Tiered rates based on volume

2. **Subscription Plans** (Secondary)
   - Basic: Free (with commission)
   - Pro: $50/month (lower commission, priority support)
   - Enterprise: $200/month (no commission, dedicated account manager)

3. **Featured Listings**
   - Suppliers pay to be featured
   - $100/month for category placement

4. **Advertising**
   - Sponsored products
   - Banner ads on app

5. **Value-Added Services**
   - Inventory management software: $30/month
   - Financial services (loans, factoring)
   - Logistics services (delivery fleet)

### Pricing Strategy

**For Restaurants:**
- Free to join
- No listing fees
- Pay only commission on successful orders

**For Suppliers:**
- Free basic listing
- Premium features require subscription
- Commission on orders

---

## Go-to-Market Strategy

### Phase 1: Launch (Month 1-2)

**Target:** Baghdad only

**Restaurants:**
- Direct sales team (10 sales reps)
- On-ground demos
- Free trial period (no commission for 1st month)
- Referral incentives ($50 credit per referral)

**Suppliers:**
- Partner with 5-10 major suppliers
- White-glove onboarding
- Free catalog setup
- Dedicated account manager

**Marketing:**
- Facebook/Instagram ads (Arabic)
- WhatsApp marketing (existing restaurant groups)
- Food industry events/expos
- Influencer partnerships (food bloggers)

### Phase 2: Growth (Month 3-6)

**Expansion:**
- Basra, Erbil, Najaf
- 50+ suppliers
- 500+ restaurants

**Marketing:**
- Success stories/case studies
- PR in local media
- YouTube tutorials (Arabic)
- Trade shows

### Phase 3: Scale (Month 7-12)

**Regional Expansion:**
- Jordan, Lebanon
- 200+ suppliers
- 2,000+ restaurants

---

## Key Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low supplier adoption | High | White-glove onboarding, free trial, dedicated support |
| Cash dependency | Medium | Start with COD, gradually introduce digital payments |
| Delivery reliability | High | Partner with 3PL, quality SLA with penalties |
| Internet connectivity | Medium | Offline mode, SMS fallback |
| Payment collection | High | Escrow system, insurance, credit scoring |
| Competition entry | Medium | Build strong network effects, exclusive partnerships |
| Regulatory changes | Medium | Legal compliance team, lobby with industry associations |

---

## Success Criteria

### MVP Launch (Month 3)

- [ ] 20+ restaurants onboarded
- [ ] 5+ suppliers onboarded
- [ ] 100+ products in catalog
- [ ] 50+ orders placed
- [ ] Mobile apps in app stores
- [ ] < 5% order cancellation rate

### Growth Milestone (Month 6)

- [ ] 200+ active restaurants
- [ ] 25+ active suppliers
- [ ] 1,000+ monthly orders
- [ ] $100,000+ monthly GMV
- [ ] 4.0+ average app rating
- [ ] 50%+ repeat order rate

### Scale Milestone (Month 12)

- [ ] 500+ active restaurants
- [ ] 50+ active suppliers
- [ ] 2,000+ monthly orders
- [ ] $500,000+ monthly GMV
- [ ] Expansion to 2+ cities
- [ ] Break-even on unit economics

---

## Development Roadmap

### Month 1-2: Foundation
- [ ] Extend user model (phone, language, roles)
- [ ] Restaurant & Supplier models
- [ ] Product catalog system
- [ ] Basic order placement
- [ ] Mobile app MVP (React Native)
- [ ] Admin panel

### Month 2-3: Core Features
- [ ] Order management workflow
- [ ] Delivery tracking
- [ ] Notification system
- [ ] Payment integration (COD)
- [ ] Reviews & ratings
- [ ] Arabic localization

### Month 3-4: Polish & Launch
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Load testing
- [ ] Beta testing (10 restaurants, 3 suppliers)
- [ ] Bug fixes
- [ ] App store submission
- [ ] **PUBLIC LAUNCH**

### Month 4-6: Growth Features
- [ ] Inventory management
- [ ] Analytics dashboards
- [ ] Credit/payment terms
- [ ] Bank transfer payments
- [ ] Bulk ordering
- [ ] Marketing automation

### Month 7-12: Scale
- [ ] Multi-location support
- [ ] Advanced analytics
- [ ] AI recommendations
- [ ] Financial services integration
- [ ] Regional expansion
- [ ] Mobile wallet integration

---

## Open Questions

1. **Regulatory:** Do we need food handling licenses for the platform?
2. **Logistics:** Build own delivery fleet or partner with 3PL?
3. **Payments:** Which Iraqi payment gateway to integrate first? (Qi Card, ZainCash, FastPay?)
4. **Pricing:** What commission rate is acceptable to suppliers? (3%, 5%, 7%?)
5. **Language:** Should Kurdish support be in MVP or Phase 2?
6. **Credit:** What criteria for extending payment terms to restaurants?

---

## Appendix

### Market Research Data

**Restaurant Market in Iraq:**
- 15,000+ restaurants in Baghdad
- 5,000+ in Basra
- 3,000+ in Erbil
- Average restaurant spends $2,000-5,000/month on supplies
- Total addressable market (TAM): $500M+ annually

**Supplier Landscape:**
- 100+ food distributors in Baghdad
- Fragmented market (no dominant player)
- Most use manual processes (Excel, WhatsApp)

### Competitive Analysis

**International Competitors (Not in Iraq):**

| Platform | Strengths | Weaknesses |
|----------|-----------|------------|
| BlueCart (USA) | Strong tech, established | No MENA presence, English only |
| Choco (Europe) | WhatsApp integration | No Arabic support |
| MarketMan (USA) | Inventory mgmt | High pricing, no emerging markets |

**Local Competitors:**
- None (greenfield opportunity)

### User Research Insights

**From 20 restaurant owner interviews:**
- 90% order via WhatsApp
- 80% have no order history tracking
- 70% struggle with price comparison
- 60% experience delivery delays
- 85% interested in digital ordering platform
- Willing to pay 3-5% commission if it saves time

**From 10 supplier interviews:**
- 100% receive orders via calls/WhatsApp
- 80% use Excel for order tracking
- 70% want automated inventory alerts
- 60% lose customers due to stock issues
- 75% interested in digital platform
- Main concern: payment collection

---

## Approval & Sign-off

**Prepared by:** Product Team
**Review by:**
- [ ] Engineering Lead
- [ ] Design Lead
- [ ] Marketing Lead
- [ ] Finance/Operations

**Approved by:** CEO

**Date:** _______________

---

**Next Steps:**
1. Review and approve PRD
2. Create detailed technical specs
3. Design mockups (UI/UX)
4. Estimate development timeline
5. Allocate resources
6. Kick off development

---

*End of Product Requirements Document*

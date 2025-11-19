# Supplier Management Workflow Documentation

## Table of Contents

1. [Supplier Lifecycle Overview](#supplier-lifecycle-overview)
2. [Verification Workflow](#verification-workflow)
3. [API Endpoints](#api-endpoints)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

---

## Supplier Lifecycle Overview

The Supplier Management system handles supplier registration, verification, product catalog management, and order fulfillment:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Register   │ ──> │   Pending    │ ──> │   Verified   │ ──> │   Active     │
│  Supplier    │     │ Verification │     │   Approved   │     │  & Selling   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                     │                                          │
       │                     │                                          │
       │                     v                                          v
       │              ┌──────────────┐                          ┌──────────────┐
       │              │   Rejected   │                          │    Manage    │
       │              │   (Retry)    │                          │   Products   │
       │              └──────────────┘                          └──────────────┘
       │                                                                │
       │                                                                v
       │                                                         ┌──────────────┐
       │                                                         │   Process    │
       │                                                         │    Orders    │
       │                                                         └──────────────┘
       │                                                                │
       └────────────────────────────────────────────────────────────────┘
```

**Key Stages:**
1. **Register** - Supplier owner creates account with business information
2. **Pending Verification** - Admin reviews trade license and business documentation
3. **Verified/Approved** - Supplier can add products and receive orders
4. **Rejected** - Supplier must resubmit with corrections
5. **Active & Selling** - Supplier lists products, receives orders, manages deliveries
6. **Manage Products** - Add/update products, manage stock, set pricing
7. **Process Orders** - Receive, confirm, prepare, and deliver orders

---

## Verification Workflow

### Verification States

| Status | `is_verified` | `verification_status` | Can Add Products | Can Receive Orders |
|--------|---------------|----------------------|------------------|--------------------|
| Pending | `false` | `"pending"` | No | No |
| Approved | `true` | `"approved"` | Yes | Yes |
| Rejected | `false` | `"rejected"` | No | No |

### Status Transitions

```
        ┌─────────────┐
   ┌───>│   pending   │<───┐
   │    └──────┬──────┘    │
   │           │           │
   │           v           │
   │    ┌──────────────┐   │
   │    │Admin Reviews │   │
   │    └──────┬───────┘   │
   │           │           │
   │     ┌─────┴─────┐     │
   │     │           │     │
   │     v           v     │
   │  ┌────────┐ ┌────────┐
   │  │approved│ │rejected│─┘
   │  └────┬───┘ └────────┘
   │       │        (resubmit)
   │       v
   │  ┌────────┐
   └──│verified│
      └────────┘
```

---

## API Endpoints

### 1. Create Supplier (Register)

**Endpoint:** `POST /api/v1/suppliers`

**Authorization:** Requires authentication

**Request:**
```json
{
  "company_name_ar": "شركة بغداد للمواد الغذائية",
  "company_name_en": "Baghdad Food Supplies Company",
  "email": "contact@baghdadfood.iq",
  "phone_primary": "+964 771 234 5678",
  "phone_secondary": "+964 771 234 5679",
  "website": "https://baghdadfood.iq",
  "address_line1": "Industrial Zone, Street 40, Building 12",
  "address_line2": "Warehouse 5",
  "city": "Baghdad",
  "district": "Al-Doura",
  "postal_code": "10011",
  "latitude": 33.2500,
  "longitude": 44.4000,
  "trade_license": "BG-TRADE-2024-54321",
  "tax_id": "TAX-123456789",
  "description_ar": "نوفر أفضل المواد الغذائية الطازجة للمطاعم",
  "description_en": "We provide the freshest food supplies to restaurants",
  "product_categories": ["Vegetables", "Fruits", "Dairy", "Meat"],
  "delivery_areas": {
    "Baghdad": ["Al-Mansour", "Karrada", "Al-Doura", "Al-Adhamiya"],
    "Karbala": ["Downtown"]
  },
  "minimum_order_value": 50000,
  "delivery_fee": 10000,
  "free_delivery_threshold": 200000,
  "operating_hours": {
    "saturday": {"open": "07:00", "close": "18:00"},
    "sunday": {"open": "07:00", "close": "18:00"},
    "monday": {"open": "07:00", "close": "18:00"},
    "tuesday": {"open": "07:00", "close": "18:00"},
    "wednesday": {"open": "07:00", "close": "18:00"},
    "thursday": {"open": "07:00", "close": "18:00"},
    "friday": {"closed": true}
  },
  "accepts_cash": true,
  "accepts_credit": true,
  "allows_installments": false,
  "payment_terms_days": 7,
  "auto_accept_orders": false,
  "lead_time_hours": 24
}
```

**Response:** `201 Created`
```json
{
  "id": "c1d2e3f4-5678-90ab-cdef-1234567890cd",
  "company_name_en": "Baghdad Food Supplies Company",
  "email": "contact@baghdadfood.iq",
  "is_verified": false,
  "verification_status": "pending",
  "is_active": true,
  "average_rating": null,
  "total_reviews": 0,
  "total_orders_completed": 0,
  "owner_id": "user-uuid-here",
  "created_at": "2024-11-19T10:00:00Z"
}
```

---

### 2. Get My Suppliers

**Endpoint:** `GET /api/v1/suppliers/me`

**Authorization:** Requires authentication

**Response:** `200 OK`
```json
[
  {
    "id": "c1d2e3f4-5678-90ab-cdef-1234567890cd",
    "company_name_en": "Baghdad Food Supplies Company",
    "verification_status": "pending",
    "is_verified": false
  }
]
```

---

### 3. List Suppliers (with Filters)

**Endpoint:** `GET /api/v1/suppliers`

**Authorization:** Public access

**Query Parameters:**
```
skip=0&limit=20
query=baghdad
city=Baghdad
product_category=Vegetables
is_verified=true
is_active=true
min_rating=4.0
accepts_cash=true
accepts_credit=true
```

**Example:**
```
GET /api/v1/suppliers?city=Baghdad&is_verified=true&min_rating=4.0
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "c1d2e3f4-5678-90ab-cdef-1234567890cd",
      "company_name_ar": "شركة بغداد للمواد الغذائية",
      "company_name_en": "Baghdad Food Supplies Company",
      "city": "Baghdad",
      "district": "Al-Doura",
      "product_categories": ["Vegetables", "Fruits", "Dairy", "Meat"],
      "is_verified": true,
      "average_rating": 4.5,
      "total_reviews": 120,
      "is_active": true,
      "logo_url": null,
      "minimum_order_value": 50000.00,
      "delivery_fee": 10000.00
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

### 4. Get Suppliers by City

**Endpoint:** `GET /api/v1/suppliers/city/{city}`

**Example:** `GET /api/v1/suppliers/city/Baghdad`

---

### 5. Get Top-Rated Suppliers

**Endpoint:** `GET /api/v1/suppliers/top-rated`

**Query Parameters:** `city=Baghdad&limit=10`

**Response:** List of top-rated suppliers sorted by rating

---

### 6. Get Nearby Suppliers (GPS)

**Endpoint:** `GET /api/v1/suppliers/nearby`

**Query Parameters:** `latitude=33.3152&longitude=44.3661&radius_km=10`

**Response:** List of suppliers within radius

---

### 7. Get Suppliers by Delivery Area

**Endpoint:** `GET /api/v1/suppliers/delivery-area/{city}`

**Query Parameters:** `district=Karrada` (optional)

**Example:** `GET /api/v1/suppliers/delivery-area/Baghdad?district=Karrada`

**Response:** Suppliers that deliver to specified area

---

### 8. Update Supplier

**Endpoint:** `PATCH /api/v1/suppliers/{supplier_id}`

**Authorization:** Requires owner or `supplier:update` permission

**Request:**
```json
{
  "logo_url": "https://cdn.example.com/logos/baghdad-food.png",
  "delivery_fee": 8000,
  "free_delivery_threshold": 150000,
  "auto_accept_orders": true
}
```

---

### 9. Verify Supplier (Admin/Manager Only)

**Endpoint:** `POST /api/v1/suppliers/{supplier_id}/verify`

**Authorization:** Requires `supplier:verify` permission

**Request (Approve):**
```json
{
  "verification_status": "approved",
  "notes": "Trade license verified with Baghdad Chamber of Commerce. Valid until 2025-12-31."
}
```

**Response:**
```json
{
  "is_verified": true,
  "verification_status": "approved",
  "verified_at": "2024-11-19T14:30:00Z"
}
```

**Request (Reject):**
```json
{
  "verification_status": "rejected",
  "notes": "Trade license number format is incorrect. Please provide valid license from Chamber of Commerce."
}
```

---

### 10. Get Pending Verifications

**Endpoint:** `GET /api/v1/suppliers/pending/verification`

**Authorization:** Requires `supplier:verify` permission (Admin/Manager)

**Response:** List of suppliers pending verification

---

### 11. Toggle Active Status

**Endpoint:** `POST /api/v1/suppliers/{supplier_id}/toggle-active?is_active=false`

**Authorization:** Requires owner or `supplier:update` permission

**Use Cases:**
- Temporarily pause accepting orders (vacation, inventory issues)
- Deactivate supplier for maintenance

---

### 12. Get Supplier by ID

**Endpoint:** `GET /api/v1/suppliers/{supplier_id}`

**Authorization:** Public access

**Response:** Full supplier details

---

### 13. Delete Supplier

**Endpoint:** `DELETE /api/v1/suppliers/{supplier_id}`

**Authorization:** Requires `supplier:delete` permission (Admin) or owner

**Response:** `200 OK` with success message

---

## Complete Examples

### Example 1: Supplier Registration and Verification

**Step 1: Supplier Registers**
```bash
POST /api/v1/suppliers
Authorization: Bearer {token}

{
  "company_name_en": "Erbil Fresh Produce",
  "email": "contact@erbilfresh.iq",
  "phone_primary": "+964 750 123 4567",
  "city": "Erbil",
  "district": "Dream City",
  "product_categories": ["Vegetables", "Fruits"],
  "delivery_areas": {
    "Erbil": ["Dream City", "Downtown", "Ankawa"]
  }
}
```

**Step 2: Admin Reviews**
```bash
GET /api/v1/suppliers/pending/verification
Authorization: Bearer {admin_token}
```

**Step 3: Admin Approves**
```bash
POST /api/v1/suppliers/{supplier_id}/verify
Authorization: Bearer {admin_token}

{
  "verification_status": "approved",
  "notes": "Verified with Erbil Chamber of Commerce"
}
```

**Step 4: Supplier Adds Products**
```bash
POST /api/v1/products
Authorization: Bearer {supplier_token}

{
  "supplier_id": "{supplier_id}",
  "name_en": "Fresh Tomatoes",
  "sku": "VEG-TOM-001",
  "category": "Vegetables",
  "unit_price": 1500.00
}
```

---

### Example 2: Restaurant Finds Suppliers

**Step 1: Search by City and Category**
```bash
GET /api/v1/suppliers?city=Baghdad&product_category=Vegetables&is_verified=true
```

**Step 2: Check Delivery Area**
```bash
GET /api/v1/suppliers/delivery-area/Baghdad?district=Karrada
```

**Step 3: View Supplier Details**
```bash
GET /api/v1/suppliers/{supplier_id}
```

**Step 4: View Supplier's Products**
```bash
GET /api/v1/products/supplier/{supplier_id}
```

---

## Error Handling

### Common Errors

#### 1. Supplier Not Found
```json
{"detail": "Supplier not found"}
```
**HTTP Status:** `404 Not Found`

#### 2. Not Authorized
```json
{"detail": "Not authorized to update this supplier"}
```
**HTTP Status:** `403 Forbidden`

#### 3. Invalid Phone Format
```json
{"detail": "Phone number must be in E.164 format (e.g., +9647901234567)"}
```
**HTTP Status:** `422 Unprocessable Entity`

---

## Best Practices

### 1. Registration
- **Complete Profile**: Provide all business information during registration
- **GPS Coordinates**: Set accurate warehouse location for delivery routing
- **Delivery Areas**: Clearly define which cities/districts you serve
- **Operating Hours**: Set realistic business hours

### 2. Product Categories
```json
{
  "product_categories": [
    "Vegetables",
    "Fruits",
    "Dairy",
    "Meat",
    "Poultry",
    "Seafood",
    "Bakery",
    "Beverages",
    "Dry Goods",
    "Spices",
    "Frozen Foods"
  ]
}
```

### 3. Delivery Configuration
```json
{
  "minimum_order_value": 50000,        // 50,000 IQD (~$34 USD)
  "delivery_fee": 10000,               // 10,000 IQD (~$7 USD)
  "free_delivery_threshold": 200000,   // Free delivery on orders > 200,000 IQD
  "lead_time_hours": 24                // 24-hour lead time
}
```

### 4. Payment Settings
- **Cash**: Most common in Iraq, set `accepts_cash: true`
- **Credit**: For established restaurants, set `accepts_credit: true`
- **Payment Terms**: Common options: 0 (immediate), 7, 14, 30 days

### 5. Auto-Accept Orders
- `true` - Orders automatically confirmed (faster service, less control)
- `false` - Manual review of each order (recommended for quality control)

---

## Reference Tables

### Product Categories

```
Vegetables, Fruits, Meat, Poultry, Seafood, Dairy, Bakery,
Beverages, Dry Goods, Spices, Frozen Foods, Canned Goods,
Snacks, Oils, Cleaning Supplies, Disposables, Equipment
```

### Major Iraqi Cities

```
Baghdad, Basra, Erbil, Sulaymaniyah, Mosul, Kirkuk,
Najaf, Karbala, Dohuk, Diyala, Anbar, Babil
```

### Verification Statuses

```
- pending    - Awaiting admin review
- approved   - Verified and approved
- rejected   - Verification rejected (can resubmit)
```

### Payment Terms

```
- 0 days     - Immediate payment
- 7 days     - Net 7
- 14 days    - Net 14
- 30 days    - Net 30
```

---

## Additional Resources

- [Order Workflow Documentation](ORDER_WORKFLOW.md) - How restaurants place orders
- [Product Catalog Documentation](PRODUCT_CATALOG.md) - Managing products
- [Delivery Workflow Documentation](DELIVERY_WORKFLOW.md) - Delivery tracking
- [Restaurant Management Documentation](RESTAURANT_WORKFLOW.md) - Restaurant accounts

---

**Last Updated:** 2024-11-19
**API Version:** v1
**Base URL:** `https://api.example.com/api/v1`

# Restaurant Management Workflow Documentation

## Table of Contents

1. [Restaurant Lifecycle Overview](#restaurant-lifecycle-overview)
2. [Verification Workflow](#verification-workflow)
3. [API Endpoints](#api-endpoints)
   - [Registration](#1-create-restaurant-register)
   - [Profile Management](#2-get-my-restaurants)
   - [Search & Discovery](#4-list-restaurants)
   - [Verification](#9-verify-restaurant-adminmanager-only)
   - [Restaurant Details](#11-get-restaurant-by-id)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Additional Resources](#additional-resources)

---

## Restaurant Lifecycle Overview

The Restaurant Management system handles restaurant registration, verification, and profile management:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Register   │ ──> │   Pending    │ ──> │   Verified   │ ──> │    Active    │
│ Restaurant   │     │ Verification │     │   Approved   │     │   Ordering   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                     │                                          │
       │                     │                                          │
       │                     v                                          v
       │              ┌──────────────┐                          ┌──────────────┐
       │              │   Rejected   │                          │    Update    │
       │              │   (Retry)    │                          │   Profile    │
       │              └──────────────┘                          └──────────────┘
       │                                                                │
       │                                                                │
       └────────────────────────────────────────────────────────────────┘
```

**Key Stages:**
1. **Register** - Restaurant owner creates account and submits business information
2. **Pending Verification** - Admin reviews business registration and documentation
3. **Verified/Approved** - Restaurant can browse suppliers and place orders
4. **Rejected** - Restaurant must resubmit with corrections
5. **Active Ordering** - Fully operational, placing and managing orders
6. **Update Profile** - Ongoing profile and business information management

---

## Verification Workflow

### Verification States

```
┌─────────────────────────────────────────────────────────────┐
│               Restaurant Verification Flow                   │
└─────────────────────────────────────────────────────────────┘

                      ┌─────────────┐
           ┌─────────>│   pending   │<─────────┐
           │          └──────┬──────┘          │
           │                 │                 │
           │                 v                 │
           │          ┌──────────────┐         │
           │          │ Admin Review │         │
           │          └──────┬───────┘         │
           │                 │                 │
           │         ┌───────┴───────┐         │
           │         │               │         │
           │         v               v         │
           │  ┌──────────┐    ┌──────────┐    │
           │  │ approved │    │ rejected │────┘
           │  └────┬─────┘    └──────────┘
           │       │               (resubmit)
           │       v
           │  ┌──────────┐
           └──│ verified │
              └──────────┘
```

### Verification Status

| Status | Description | Can Place Orders | Admin Action Required |
|--------|-------------|------------------|-----------------------|
| `pending` | Awaiting admin review | No | Yes - Review required |
| `approved` | Verified and approved | Yes | No |
| `rejected` | Verification rejected | No | Owner must resubmit |

### Verification Fields

| Field | Status `pending` | Status `approved` | Status `rejected` |
|-------|------------------|-------------------|-------------------|
| `is_verified` | `false` | `true` | `false` |
| `verification_status` | `"pending"` | `"approved"` | `"rejected"` |
| `verified_at` | `null` | `timestamp` | `null` |
| `verified_by_id` | `null` | `admin_user_id` | `admin_user_id` |

---

## API Endpoints

### Registration

#### 1. Create Restaurant (Register)

**Endpoint:** `POST /api/v1/restaurants`

**Authorization:** Requires authentication (any logged-in user can create restaurant)

**Request:**
```json
{
  "name_ar": "مطعم بغداد للمأكولات العراقية",
  "name_en": "Baghdad Iraqi Restaurant",
  "email": "contact@baghdadrestaurant.iq",
  "phone_primary": "+964 771 234 5678",
  "phone_secondary": "+964 771 234 5679",
  "address_line1": "Al-Mansour Street, Building 45",
  "address_line2": "Near Al-Mansour Mall",
  "city": "Baghdad",
  "district": "Al-Mansour",
  "postal_code": "10001",
  "latitude": 33.3152,
  "longitude": 44.3661,
  "restaurant_type": "fine_dining",
  "cuisine_type": "iraqi",
  "seating_capacity": 120,
  "business_registration": "BG-REST-2024-12345",
  "operating_hours": {
    "sunday": {"open": "10:00", "close": "23:00"},
    "monday": {"open": "10:00", "close": "23:00"},
    "tuesday": {"open": "10:00", "close": "23:00"},
    "wednesday": {"open": "10:00", "close": "23:00"},
    "thursday": {"open": "10:00", "close": "23:00"},
    "friday": {"open": "10:00", "close": "23:00"},
    "saturday": {"open": "10:00", "close": "23:00"}
  },
  "preferred_payment_method": "cash"
}
```

**Response:** `201 Created`
```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "name_ar": "مطعم بغداد للمأكولات العراقية",
  "name_en": "Baghdad Iraqi Restaurant",
  "email": "contact@baghdadrestaurant.iq",
  "phone_primary": "+964 771 234 5678",
  "phone_secondary": "+964 771 234 5679",
  "address_line1": "Al-Mansour Street, Building 45",
  "address_line2": "Near Al-Mansour Mall",
  "city": "Baghdad",
  "district": "Al-Mansour",
  "postal_code": "10001",
  "latitude": 33.3152,
  "longitude": 44.3661,
  "restaurant_type": "fine_dining",
  "cuisine_type": "iraqi",
  "seating_capacity": 120,
  "business_registration": "BG-REST-2024-12345",
  "operating_hours": {
    "sunday": {"open": "10:00", "close": "23:00"},
    "monday": {"open": "10:00", "close": "23:00"},
    "tuesday": {"open": "10:00", "close": "23:00"},
    "wednesday": {"open": "10:00", "close": "23:00"},
    "thursday": {"open": "10:00", "close": "23:00"},
    "friday": {"open": "10:00", "close": "23:00"},
    "saturday": {"open": "10:00", "close": "23:00"}
  },
  "logo_url": null,
  "cover_image_url": null,
  "is_verified": false,
  "verification_status": "pending",
  "verified_at": null,
  "auto_accept_orders": true,
  "preferred_payment_method": "cash",
  "owner_id": "bbbbcc159-c15e-4dd7-82b1-7cf5c88d94da",
  "created_at": "2024-11-19T10:00:00Z",
  "updated_at": "2024-11-19T10:00:00Z"
}
```

**Business Rules:**
- Any authenticated user can register a restaurant
- User becomes the restaurant owner automatically
- Restaurant starts in `pending` verification status
- `is_verified` is initially `false`
- Owner cannot place orders until verified
- Business registration number should be unique

---

### Profile Management

#### 2. Get My Restaurants

**Endpoint:** `GET /api/v1/restaurants/me`

**Authorization:** Requires authentication

**Response:** `200 OK`
```json
[
  {
    "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "name_en": "Baghdad Iraqi Restaurant",
    "verification_status": "pending",
    "is_verified": false,
    "city": "Baghdad",
    "created_at": "2024-11-19T10:00:00Z"
  }
]
```

**Use Cases:**
- Check verification status
- View all owned restaurants
- Access restaurant IDs for updating

---

#### 3. Update Restaurant Profile

**Endpoint:** `PATCH /api/v1/restaurants/{restaurant_id}`

**Authorization:** Requires restaurant ownership or `restaurant:update` permission

**Request:**
```json
{
  "phone_primary": "+964 771 234 9999",
  "seating_capacity": 150,
  "logo_url": "https://cdn.example.com/restaurants/baghdad-logo.png",
  "cover_image_url": "https://cdn.example.com/restaurants/baghdad-cover.jpg",
  "operating_hours": {
    "sunday": {"open": "09:00", "close": "00:00"},
    "monday": {"open": "09:00", "close": "00:00"},
    "tuesday": {"open": "09:00", "close": "00:00"},
    "wednesday": {"open": "09:00", "close": "00:00"},
    "thursday": {"open": "09:00", "close": "00:00"},
    "friday": {"open": "09:00", "close": "02:00"},
    "saturday": {"open": "09:00", "close": "02:00"}
  }
}
```

**Response:** `200 OK` (updated restaurant details)

**Business Rules:**
- Only owner or users with `restaurant:update` can update
- All fields are optional (partial update)
- Cannot change `owner_id`
- Cannot change verification status (admin only via verification endpoint)

---

### Search & Discovery

#### 4. List Restaurants

**Endpoint:** `GET /api/v1/restaurants`

**Authorization:** Public access (no authentication required)

**Query Parameters:**
```
skip=0                          # Pagination offset
limit=20                        # Results per page (max 100)
query=baghdad                   # Search in name
city=Baghdad                    # Filter by city
restaurant_type=fine_dining     # Filter by type
is_verified=true                # Verified restaurants only
```

**Example Request:**
```
GET /api/v1/restaurants?city=Baghdad&is_verified=true&limit=10
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "name_ar": "مطعم بغداد للمأكولات العراقية",
      "name_en": "Baghdad Iraqi Restaurant",
      "city": "Baghdad",
      "district": "Al-Mansour",
      "restaurant_type": "fine_dining",
      "cuisine_type": "iraqi",
      "is_verified": true,
      "logo_url": "https://cdn.example.com/restaurants/baghdad-logo.png",
      "created_at": "2024-11-19T10:00:00Z"
    },
    {
      "id": "b2c3d4e5-6789-01bc-def0-234567890abc",
      "name_ar": "كافيه السعادة",
      "name_en": "Happiness Cafe",
      "city": "Baghdad",
      "district": "Karrada",
      "restaurant_type": "cafe",
      "cuisine_type": "international",
      "is_verified": true,
      "logo_url": "https://cdn.example.com/restaurants/happiness-logo.png",
      "created_at": "2024-11-18T15:30:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 10
}
```

---

#### 5. Get Restaurants by City

**Endpoint:** `GET /api/v1/restaurants/city/{city}`

**Authorization:** Public access

**Example:**
```
GET /api/v1/restaurants/city/Baghdad
```

**Response:** `200 OK` (list of restaurants in Baghdad)

**Use Case:** Browse restaurants in a specific city for supplier targeting

---

#### 6. Get Nearby Restaurants (GPS-based)

**Endpoint:** `GET /api/v1/restaurants/nearby`

**Authorization:** Public access

**Query Parameters:**
```
latitude=33.3152               # GPS latitude
longitude=44.3661              # GPS longitude
radius_km=10                   # Search radius (0.1-50 km)
```

**Example:**
```
GET /api/v1/restaurants/nearby?latitude=33.3152&longitude=44.3661&radius_km=5
```

**Response:** `200 OK`
```json
[
  {
    "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "name_en": "Baghdad Iraqi Restaurant",
    "city": "Baghdad",
    "district": "Al-Mansour",
    "latitude": 33.3152,
    "longitude": 44.3661,
    "is_verified": true
  },
  {
    "id": "c3d4e5f6-7890-12cd-ef01-34567890abcd",
    "name_en": "Karrada Grill House",
    "city": "Baghdad",
    "district": "Karrada",
    "latitude": 33.3200,
    "longitude": 44.3750,
    "is_verified": true
  }
]
```

**Use Cases:**
- Delivery zone planning for suppliers
- Find nearby restaurants for delivery optimization
- Location-based marketing

---

### Verification (Admin/Manager Only)

#### 7. Get Pending Verifications

**Endpoint:** `GET /api/v1/restaurants/pending/verification`

**Authorization:** Requires `restaurant:verify` permission (Admin/Manager only)

**Response:** `200 OK`
```json
[
  {
    "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "name_en": "Baghdad Iraqi Restaurant",
    "verification_status": "pending",
    "business_registration": "BG-REST-2024-12345",
    "email": "contact@baghdadrestaurant.iq",
    "city": "Baghdad",
    "created_at": "2024-11-19T10:00:00Z"
  },
  {
    "id": "d4e5f6g7-8901-23de-f012-4567890abcde",
    "name_en": "Basra Seafood Palace",
    "verification_status": "pending",
    "business_registration": "BS-REST-2024-67890",
    "email": "info@basraseafood.iq",
    "city": "Basra",
    "created_at": "2024-11-19T11:30:00Z"
  }
]
```

**Use Case:** Admin reviews pending restaurant registrations daily

---

#### 8. Verify Restaurant (Admin/Manager Only)

**Endpoint:** `POST /api/v1/restaurants/{restaurant_id}/verify`

**Authorization:** Requires `restaurant:verify` permission (Admin/Manager only)

**Request (Approve):**
```json
{
  "verification_status": "approved",
  "notes": "Business registration verified. Trade license is valid until 2025-12-31."
}
```

**Response:** `200 OK`
```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "name_en": "Baghdad Iraqi Restaurant",
  "is_verified": true,
  "verification_status": "approved",
  "verified_at": "2024-11-19T14:30:00Z",
  "verified_by_id": "admin-user-uuid-here"
}
```

---

**Request (Reject):**
```json
{
  "verification_status": "rejected",
  "notes": "Business registration number is invalid. Please provide a valid trade license from Baghdad Chamber of Commerce."
}
```

**Response:** `200 OK`
```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "name_en": "Baghdad Iraqi Restaurant",
  "is_verified": false,
  "verification_status": "rejected",
  "verified_at": null,
  "verified_by_id": "admin-user-uuid-here"
}
```

**Business Rules:**
- Only users with `restaurant:verify` permission can verify
- Approved restaurants: `is_verified=true`, `verification_status="approved"`
- Rejected restaurants: `is_verified=false`, `verification_status="rejected"`
- Notes are stored in audit log for reference
- Owner is notified (via future notification system)

---

### Restaurant Details

#### 9. Get Restaurant by ID

**Endpoint:** `GET /api/v1/restaurants/{restaurant_id}`

**Authorization:** Public access

**Example:**
```
GET /api/v1/restaurants/a1b2c3d4-5678-90ab-cdef-1234567890ab
```

**Response:** `200 OK` (full restaurant details - same as create response)

---

#### 10. Delete Restaurant

**Endpoint:** `DELETE /api/v1/restaurants/{restaurant_id}`

**Authorization:** Requires `restaurant:delete` permission (Admin) or restaurant owner

**Example:**
```
DELETE /api/v1/restaurants/a1b2c3d4-5678-90ab-cdef-1234567890ab
```

**Response:** `200 OK`
```json
{
  "message": "Restaurant deleted successfully"
}
```

**Business Rules:**
- **Soft delete**: Restaurant marked as deleted but data preserved
- Only owner or admin can delete
- Historical orders and data remain accessible
- Restaurant will not appear in public listings

---

## Complete Examples

### Example 1: Restaurant Registration and Verification

**Step 1: Restaurant Owner Registers**
```bash
POST /api/v1/restaurants
Authorization: Bearer {owner_token}

{
  "name_ar": "مطعم أربيل للكباب",
  "name_en": "Erbil Kebab House",
  "email": "contact@erbilkebab.iq",
  "phone_primary": "+964 750 123 4567",
  "address_line1": "100 Meter Street",
  "city": "Erbil",
  "district": "Dream City",
  "restaurant_type": "casual_dining",
  "cuisine_type": "kurdish",
  "seating_capacity": 80,
  "business_registration": "ER-REST-2024-99999",
  "operating_hours": {
    "sunday": {"open": "11:00", "close": "23:00"},
    "monday": {"open": "11:00", "close": "23:00"},
    "tuesday": {"open": "11:00", "close": "23:00"},
    "wednesday": {"open": "11:00", "close": "23:00"},
    "thursday": {"open": "11:00", "close": "23:00"},
    "friday": {"open": "11:00", "close": "23:00"},
    "saturday": {"open": "11:00", "close": "23:00"}
  }
}
```

**Response:**
```json
{
  "id": "e5f6g7h8-9012-34ef-0123-567890abcdef",
  "name_en": "Erbil Kebab House",
  "verification_status": "pending",
  "is_verified": false
}
```

---

**Step 2: Owner Checks Verification Status**
```bash
GET /api/v1/restaurants/me
Authorization: Bearer {owner_token}
```

**Response:**
```json
[
  {
    "id": "e5f6g7h8-9012-34ef-0123-567890abcdef",
    "name_en": "Erbil Kebab House",
    "verification_status": "pending",
    "is_verified": false
  }
]
```

---

**Step 3: Admin Views Pending Verifications**
```bash
GET /api/v1/restaurants/pending/verification
Authorization: Bearer {admin_token}
```

**Response:**
```json
[
  {
    "id": "e5f6g7h8-9012-34ef-0123-567890abcdef",
    "name_en": "Erbil Kebab House",
    "business_registration": "ER-REST-2024-99999",
    "verification_status": "pending",
    "created_at": "2024-11-19T09:00:00Z"
  }
]
```

---

**Step 4: Admin Approves Restaurant**
```bash
POST /api/v1/restaurants/e5f6g7h8-9012-34ef-0123-567890abcdef/verify
Authorization: Bearer {admin_token}

{
  "verification_status": "approved",
  "notes": "Verified with Erbil Chamber of Commerce. License valid."
}
```

**Response:**
```json
{
  "id": "e5f6g7h8-9012-34ef-0123-567890abcdef",
  "name_en": "Erbil Kebab House",
  "is_verified": true,
  "verification_status": "approved",
  "verified_at": "2024-11-19T10:30:00Z"
}
```

---

**Step 5: Restaurant Can Now Place Orders**
```bash
# Restaurant is now verified and can browse suppliers
GET /api/v1/suppliers
Authorization: Bearer {owner_token}

# Restaurant can create orders
POST /api/v1/orders
Authorization: Bearer {owner_token}
```

---

### Example 2: Rejected Verification - Resubmission

**Step 1: Admin Rejects Restaurant**
```bash
POST /api/v1/restaurants/f6g7h8i9-0123-45fg-1234-67890abcdef0/verify
Authorization: Bearer {admin_token}

{
  "verification_status": "rejected",
  "notes": "Business registration number format is incorrect. Should be format: BG-REST-YYYY-NNNNN"
}
```

**Response:**
```json
{
  "is_verified": false,
  "verification_status": "rejected"
}
```

---

**Step 2: Owner Updates Business Registration**
```bash
PATCH /api/v1/restaurants/f6g7h8i9-0123-45fg-1234-67890abcdef0
Authorization: Bearer {owner_token}

{
  "business_registration": "BG-REST-2024-54321"
}
```

---

**Step 3: Owner Contacts Support to Request Re-review**
_(Future: automated re-review request feature)_

---

**Step 4: Admin Re-verifies and Approves**
```bash
POST /api/v1/restaurants/f6g7h8i9-0123-45fg-1234-67890abcdef0/verify
Authorization: Bearer {admin_token}

{
  "verification_status": "approved",
  "notes": "Updated business registration is valid. Approved."
}
```

---

### Example 3: Update Restaurant Profile

**Step 1: Add Logo and Update Hours**
```bash
PATCH /api/v1/restaurants/a1b2c3d4-5678-90ab-cdef-1234567890ab
Authorization: Bearer {owner_token}

{
  "logo_url": "https://cdn.example.com/logos/baghdad-rest.png",
  "cover_image_url": "https://cdn.example.com/covers/baghdad-rest.jpg",
  "operating_hours": {
    "sunday": {"open": "09:00", "close": "01:00"},
    "monday": {"open": "09:00", "close": "01:00"},
    "tuesday": {"open": "09:00", "close": "01:00"},
    "wednesday": {"open": "09:00", "close": "01:00"},
    "thursday": {"open": "09:00", "close": "02:00"},
    "friday": {"open": "09:00", "close": "02:00"},
    "saturday": {"open": "09:00", "close": "02:00"}
  },
  "auto_accept_orders": false
}
```

**Response:**
```json
{
  "logo_url": "https://cdn.example.com/logos/baghdad-rest.png",
  "cover_image_url": "https://cdn.example.com/covers/baghdad-rest.jpg",
  "auto_accept_orders": false,
  "updated_at": "2024-11-19T15:00:00Z"
}
```

---

### Example 4: Supplier Finds Nearby Restaurants

**Step 1: Supplier in Baghdad Finds Nearby Restaurants for Delivery**
```bash
GET /api/v1/restaurants/nearby?latitude=33.3152&longitude=44.3661&radius_km=10
Authorization: Bearer {supplier_token}
```

**Response:**
```json
[
  {
    "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "name_en": "Baghdad Iraqi Restaurant",
    "city": "Baghdad",
    "district": "Al-Mansour",
    "latitude": 33.3152,
    "longitude": 44.3661,
    "is_verified": true
  },
  {
    "id": "b2c3d4e5-6789-01bc-def0-234567890abc",
    "name_en": "Karrada Grill House",
    "city": "Baghdad",
    "district": "Karrada",
    "latitude": 33.3200,
    "longitude": 44.3750,
    "is_verified": true
  }
]
```

---

## Error Handling

### Common Errors

#### 1. Restaurant Not Found
```json
{
  "detail": "Restaurant not found"
}
```
**HTTP Status:** `404 Not Found`

**Causes:**
- Invalid restaurant ID
- Restaurant has been deleted
- Restaurant doesn't exist

---

#### 2. Not Authorized to Update
```json
{
  "detail": "Not authorized to update this restaurant"
}
```
**HTTP Status:** `403 Forbidden`

**Causes:**
- User is not the restaurant owner
- User doesn't have `restaurant:update` permission
- Attempting to modify another user's restaurant

---

#### 3. Verification Permission Required
```json
{
  "detail": "Permission 'restaurant:verify' required"
}
```
**HTTP Status:** `403 Forbidden`

**Solution:** Only Admin/Manager roles can verify restaurants

---

#### 4. Invalid Restaurant Type
```json
{
  "detail": "Invalid restaurant_type"
}
```
**HTTP Status:** `422 Unprocessable Entity`

**Allowed Values:**
- `fast_food`
- `casual_dining`
- `fine_dining`
- `cafe`
- `bakery`
- `food_truck`
- `buffet`

---

#### 5. Invalid GPS Coordinates
```json
{
  "detail": "Latitude must be between -90 and 90"
}
```
**HTTP Status:** `422 Unprocessable Entity`

**Valid Ranges:**
- Latitude: -90 to 90
- Longitude: -180 to 180

---

## Best Practices

### 1. Registration
- **Complete Information**: Provide as much detail as possible during registration
- **Accurate GPS**: Set precise latitude/longitude for delivery accuracy
- **Valid Business Registration**: Ensure business registration number is valid and matches official documents
- **Operating Hours**: Set realistic operating hours (24-hour clock format: "HH:MM")

### 2. Verification
- **Submit Documentation**: Upload clear photos of trade license and business registration
- **Business Email**: Use official business email (not personal Gmail/Hotmail)
- **Phone Verification**: Provide working phone numbers for verification calls
- **Response Time**: Admins should review pending verifications within 24-48 hours

### 3. Profile Management
- **Professional Images**: Upload high-quality logo (500x500px) and cover image (1200x400px)
- **Bilingual Content**: Provide both Arabic and English names for better discoverability
- **Update Regularly**: Keep contact information, hours, and capacity up to date
- **GPS Accuracy**: Verify GPS coordinates on Google Maps before saving

### 4. Search Optimization
- **Descriptive Names**: Use clear, searchable restaurant names
- **Accurate Location**: Proper city, district, and address for location-based searches
- **Restaurant Type**: Choose the most appropriate type for your business
- **Cuisine Type**: Be specific (iraqi, kurdish, lebanese, etc.)

### 5. Ordering Settings
- **Auto-Accept Orders**:
  - `true` - Orders are automatically confirmed (faster for restaurants)
  - `false` - Manual review of each order (better control)
- **Preferred Payment**: Set realistic payment method expectations
- **Operating Hours**: Suppliers can filter restaurants by opening hours

---

## Reference Tables

### Restaurant Types

```
- fast_food          - Quick service restaurants
- casual_dining      - Family-style restaurants
- fine_dining        - Upscale restaurants
- cafe               - Coffee shops and cafes
- bakery             - Bakeries and patisseries
- food_truck         - Mobile food vendors
- buffet             - All-you-can-eat restaurants
```

### Cuisine Types

```
- iraqi              - Iraqi cuisine
- kurdish            - Kurdish cuisine
- lebanese           - Lebanese cuisine
- turkish            - Turkish cuisine
- syrian             - Syrian cuisine
- indian             - Indian cuisine
- chinese            - Chinese cuisine
- italian            - Italian cuisine
- international      - Mixed/international cuisine
```

### Verification Statuses

```
- pending            - Awaiting admin review
- approved           - Verified and approved
- rejected           - Verification rejected (can resubmit)
```

### Payment Methods

```
- cash               - Cash on delivery
- credit             - Credit card
- bank_transfer      - Bank transfer
- mobile_payment     - Mobile payment apps
```

---

## Additional Resources

- [Order Workflow Documentation](ORDER_WORKFLOW.md) - How restaurants place orders
- [Delivery Workflow Documentation](DELIVERY_WORKFLOW.md) - Delivery tracking
- [Product Catalog Documentation](PRODUCT_CATALOG.md) - Browse supplier products
- [Supplier Management Documentation](SUPPLIER_WORKFLOW.md) - Supplier information
- [Authentication Documentation](AUTHENTICATION.md) - User authentication

---

**Last Updated:** 2024-11-19
**API Version:** v1
**Base URL:** `https://api.example.com/api/v1`

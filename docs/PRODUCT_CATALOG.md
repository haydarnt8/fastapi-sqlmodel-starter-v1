# Product Catalog Workflow Documentation

## Table of Contents

1. [Product Lifecycle Overview](#product-lifecycle-overview)
2. [Product Status Workflow](#product-status-workflow)
3. [API Endpoints by Category](#api-endpoints-by-category)
   - [Product Creation](#1-create-product)
   - [Product Search & Browse](#2-list-products-with-filters)
   - [Product Details](#7-get-product-by-id)
   - [Product Management](#8-update-product)
   - [Stock Management](#9-update-product-stock)
   - [Bulk Operations](#12-bulk-update-discounts)
   - [Product Deletion](#13-delete-product)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Additional Resources](#additional-resources)

---

## Product Lifecycle Overview

The Product Catalog system manages products offered by suppliers in the supply chain marketplace:

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Create    │ ───> │    Active    │ ───> │   Featured   │ ───> │  Reorder    │
│   Product   │      │   & Listed   │      │  Promotion   │      │   Alert     │
└─────────────┘      └──────────────┘      └──────────────┘      └─────────────┘
                            │                                             │
                            │                                             │
                            v                                             v
                     ┌──────────────┐                              ┌─────────────┐
                     │  Deactivate  │                              │   Restock   │
                     │   (Paused)   │                              │  & Active   │
                     └──────────────┘                              └─────────────┘
                            │
                            v
                     ┌──────────────┐
                     │ Discontinued │
                     │  (Archived)  │
                     └──────────────┘
```

**Key Stages:**
1. **Create Product** - Supplier adds new product to catalog
2. **Active & Listed** - Product is available for restaurants to browse and order
3. **Featured Promotion** - Product can be marked as featured for visibility
4. **Stock Management** - Continuous monitoring and updates of inventory levels
5. **Reorder Alert** - System alerts when stock falls below reorder level
6. **Deactivate** - Temporarily pause product availability
7. **Discontinued** - Permanently archive product (soft delete)

---

## Product Status Workflow

### Availability States

```
┌─────────────────────────────────────────────────────────────┐
│                    Product Status Flow                       │
└─────────────────────────────────────────────────────────────┘

                      ┌─────────────┐
                      │  in_stock   │ ← Default state when created with stock > 0
                      └──────┬──────┘
                             │
                  ┌──────────┼──────────┐
                  │                     │
                  v                     v
          ┌──────────────┐      ┌──────────────┐
          │ out_of_stock │      │discontinued  │
          └──────┬───────┘      └──────────────┘
                 │                      │
                 │ (restock)            │ (permanent)
                 v                      v
          ┌──────────────┐       ┌──────────────┐
          │  in_stock    │       │   archived   │
          └──────────────┘       └──────────────┘
```

### Status Transitions

| Current Status | Can Transition To | Trigger Action | Business Rule |
|----------------|-------------------|----------------|---------------|
| `in_stock` | `out_of_stock` | Stock reaches 0 | Automatic or manual |
| `in_stock` | `discontinued` | Supplier discontinues | Manual only |
| `out_of_stock` | `in_stock` | Restock | Stock quantity > 0 |
| `out_of_stock` | `discontinued` | Supplier discontinues | Manual only |
| `discontinued` | - | - | No transitions allowed |

### Active Status

| Status | Description | Visible to Restaurants | Can Be Ordered |
|--------|-------------|----------------------|----------------|
| `is_active=true` | Product available | Yes | Yes (if in stock) |
| `is_active=false` | Product paused | No | No |
| `is_deleted=true` | Product archived | No | No |

---

## API Endpoints by Category

### Product Creation

#### 1. Create Product

**Endpoint:** `POST /api/v1/products`

**Authorization:** Requires `product:create` permission or supplier owner role

**Request:**
```json
{
  "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
  "sku": "VEG-TOM-001",
  "barcode": "6281012345678",
  "name_ar": "طماطم طازجة",
  "name_en": "Fresh Tomatoes",
  "description_ar": "طماطم طازجة من مزارع العراق",
  "description_en": "Fresh tomatoes from Iraqi farms",
  "category": "Vegetables",
  "subcategory": "Fresh Vegetables",
  "tags": ["organic", "fresh", "local"],
  "unit_price": 1500.00,
  "currency": "IQD",
  "tax_rate": 0.00,
  "discount_percentage": 0.00,
  "stock_quantity": 500.00,
  "reorder_level": 50.00,
  "unit_of_measure": "kg",
  "minimum_order_quantity": 5.00,
  "brand": "Iraqi Farms",
  "origin_country": "Iraq",
  "shelf_life_days": 7,
  "storage_instructions": "Keep refrigerated at 2-8°C",
  "primary_image_url": "https://example.com/images/tomatoes.jpg",
  "image_urls": [
    "https://example.com/images/tomatoes-1.jpg",
    "https://example.com/images/tomatoes-2.jpg"
  ],
  "search_keywords": ["tomato", "طماطم", "vegetables", "خضروات"]
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
  "sku": "VEG-TOM-001",
  "barcode": "6281012345678",
  "name_ar": "طماطم طازجة",
  "name_en": "Fresh Tomatoes",
  "description_ar": "طماطم طازجة من مزارع العراق",
  "description_en": "Fresh tomatoes from Iraqi farms",
  "category": "Vegetables",
  "subcategory": "Fresh Vegetables",
  "tags": ["organic", "fresh", "local"],
  "unit_price": 1500.00,
  "currency": "IQD",
  "tax_rate": 0.00,
  "discount_percentage": 0.00,
  "final_price": 1500.00,
  "price_with_tax": 1500.00,
  "stock_quantity": 500.00,
  "reorder_level": 50.00,
  "unit_of_measure": "kg",
  "minimum_order_quantity": 5.00,
  "brand": "Iraqi Farms",
  "manufacturer": null,
  "origin_country": "Iraq",
  "shelf_life_days": 7,
  "storage_instructions": "Keep refrigerated at 2-8°C",
  "primary_image_url": "https://example.com/images/tomatoes.jpg",
  "image_urls": [
    "https://example.com/images/tomatoes-1.jpg",
    "https://example.com/images/tomatoes-2.jpg"
  ],
  "is_active": true,
  "is_featured": false,
  "availability_status": "in_stock",
  "is_low_stock": false,
  "is_in_stock": true,
  "search_keywords": ["tomato", "طماطم", "vegetables", "خضروات"],
  "created_at": "2024-11-19T10:00:00Z",
  "updated_at": "2024-11-19T10:00:00Z"
}
```

**Business Rules:**
- SKU must be unique per supplier
- Category must be from allowed list (see [Categories](#allowed-categories))
- Unit of measure must be from allowed list (see [Units of Measure](#allowed-units))
- Currency must be IQD, USD, or EUR
- Stock quantity ≥ 0
- Unit price > 0
- Tax rate: 0-100%
- Discount percentage: 0-100%
- Supplier owner can create products for their supplier
- Users with `product:create` permission can create for any supplier

---

### Product Search & Browse

#### 2. List Products (with Filters)

**Endpoint:** `GET /api/v1/products`

**Authorization:** Public access (no authentication required)

**Query Parameters:**
```
skip=0                            # Pagination offset
limit=20                          # Results per page (max 100)
query=tomato                      # Search in name, SKU, description
supplier_id=b45a3c2e-...          # Filter by supplier
category=Vegetables               # Filter by category
subcategory=Fresh Vegetables      # Filter by subcategory
min_price=1000                    # Minimum price
max_price=5000                    # Maximum price
is_active=true                    # Active products only
is_featured=true                  # Featured products only
in_stock_only=true                # In stock products only (default)
sort_by=unit_price                # Sort field
sort_order=asc                    # Sort order (asc/desc)
```

**Example Request:**
```
GET /api/v1/products?category=Vegetables&in_stock_only=true&sort_by=unit_price&sort_order=asc&limit=10
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "sku": "VEG-TOM-001",
      "name_ar": "طماطم طازجة",
      "name_en": "Fresh Tomatoes",
      "category": "Vegetables",
      "subcategory": "Fresh Vegetables",
      "unit_price": 1500.00,
      "currency": "IQD",
      "discount_percentage": 0.00,
      "final_price": 1500.00,
      "stock_quantity": 500.00,
      "unit_of_measure": "kg",
      "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
      "primary_image_url": "https://example.com/images/tomatoes.jpg",
      "is_active": true,
      "is_featured": false,
      "availability_status": "in_stock",
      "is_in_stock": true
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "sku": "VEG-CUC-002",
      "name_ar": "خيار طازج",
      "name_en": "Fresh Cucumbers",
      "category": "Vegetables",
      "subcategory": "Fresh Vegetables",
      "unit_price": 1200.00,
      "currency": "IQD",
      "discount_percentage": 10.00,
      "final_price": 1080.00,
      "stock_quantity": 300.00,
      "unit_of_measure": "kg",
      "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
      "primary_image_url": "https://example.com/images/cucumbers.jpg",
      "is_active": true,
      "is_featured": true,
      "availability_status": "in_stock",
      "is_in_stock": true
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 10
}
```

**Advanced Filters:**
- **Text Search** (`query`): Searches in name_ar, name_en, SKU, and description
- **Supplier Filter** (`supplier_id`): Products from specific supplier
- **Category Filter** (`category`): Primary category
- **Subcategory Filter** (`subcategory`): Subcategory
- **Price Range** (`min_price`, `max_price`): Filter by price
- **Status Filters** (`is_active`, `is_featured`, `in_stock_only`): Filter by status
- **Sorting**: By name, price, stock, or creation date

---

#### 3. Get Products by Supplier

**Endpoint:** `GET /api/v1/products/supplier/{supplier_id}`

**Authorization:** Public access

**Example:**
```
GET /api/v1/products/supplier/b45a3c2e-1234-5678-9abc-def012345678?active_only=true&limit=20
```

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "sku": "VEG-TOM-001",
    "name_ar": "طماطم طازجة",
    "name_en": "Fresh Tomatoes",
    "category": "Vegetables",
    "unit_price": 1500.00,
    "final_price": 1500.00,
    "is_in_stock": true
  }
]
```

---

#### 4. Get Products by Category

**Endpoint:** `GET /api/v1/products/category/{category}`

**Authorization:** Public access

**Example:**
```
GET /api/v1/products/category/Vegetables?active_only=true&limit=20
```

**Response:** `200 OK` (same format as supplier list)

---

#### 5. Get Featured Products

**Endpoint:** `GET /api/v1/products/featured`

**Authorization:** Public access

**Example:**
```
GET /api/v1/products/featured?supplier_id=b45a3c2e-1234-5678-9abc-def012345678&limit=10
```

**Response:** `200 OK` (list of featured products)

**Use Case:** Display featured products on homepage or category pages for marketing

---

#### 6. Get Low Stock Products

**Endpoint:** `GET /api/v1/products/low-stock`

**Authorization:** Requires authentication (supplier owner or `product:read` permission)

**Example:**
```
GET /api/v1/products/low-stock?supplier_id=b45a3c2e-1234-5678-9abc-def012345678
```

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "sku": "VEG-TOM-001",
    "name_ar": "طماطم طازجة",
    "name_en": "Fresh Tomatoes",
    "stock_quantity": 45.00,
    "reorder_level": 50.00,
    "is_in_stock": true
  }
]
```

**Business Rules:**
- Returns products where `stock_quantity <= reorder_level`
- If no supplier_id provided, uses current user's supplier
- Supplier owners see only their products
- Admin can see all suppliers' low stock products

---

### Product Details

#### 7. Get Product by ID

**Endpoint:** `GET /api/v1/products/{product_id}`

**Authorization:** Public access

**Example:**
```
GET /api/v1/products/550e8400-e29b-41d4-a716-446655440001
```

**Response:** `200 OK` (full product details - same as create response)

---

#### 8. Get Product by SKU

**Endpoint:** `GET /api/v1/products/sku/{sku}`

**Authorization:** Public access

**Example:**
```
GET /api/v1/products/sku/VEG-TOM-001?supplier_id=b45a3c2e-1234-5678-9abc-def012345678
```

**Response:** `200 OK` (full product details)

**Note:** If multiple suppliers use same SKU, provide `supplier_id` parameter

---

### Product Management

#### 9. Update Product

**Endpoint:** `PATCH /api/v1/products/{product_id}`

**Authorization:** Requires `product:update` permission or supplier owner role

**Request:**
```json
{
  "name_en": "Fresh Organic Tomatoes",
  "description_en": "Premium organic tomatoes from certified Iraqi farms",
  "unit_price": 1800.00,
  "discount_percentage": 10.00,
  "is_featured": true,
  "tags": ["organic", "fresh", "local", "premium"]
}
```

**Response:** `200 OK` (updated product details)

**Business Rules:**
- Only supplier owner or users with `product:update` can update
- All fields are optional in update request
- Cannot change supplier_id
- SKU changes are allowed but must remain unique per supplier

---

### Stock Management

#### 10. Update Product Stock

**Endpoint:** `PATCH /api/v1/products/{product_id}/stock`

**Authorization:** Requires `product:update` permission or supplier owner role

**Request:**
```json
{
  "stock_quantity": 750.00,
  "notes": "Restocked from new shipment - 250kg added"
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "sku": "VEG-TOM-001",
  "name_en": "Fresh Tomatoes",
  "stock_quantity": 750.00,
  "reorder_level": 50.00,
  "is_low_stock": false,
  "is_in_stock": true,
  "availability_status": "in_stock"
}
```

**Business Rules:**
- Only supplier owner or users with permission can update stock
- Stock quantity must be ≥ 0
- Automatically updates `availability_status` to "in_stock" if quantity > 0
- Audit log created with notes

---

#### 11. Toggle Product Active Status

**Endpoint:** `POST /api/v1/products/{product_id}/toggle-active`

**Authorization:** Requires `product:update` permission or supplier owner role

**Example:**
```
POST /api/v1/products/550e8400-e29b-41d4-a716-446655440001/toggle-active?is_active=false
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name_en": "Fresh Tomatoes",
  "is_active": false,
  "is_in_stock": false
}
```

**Use Cases:**
- **Deactivate** (`is_active=false`): Temporarily hide product from catalog (seasonal products, supply issues)
- **Activate** (`is_active=true`): Make product available again

---

### Bulk Operations

#### 12. Bulk Update Discounts

**Endpoint:** `POST /api/v1/products/bulk/update-discount`

**Authorization:** Requires `product:update` permission or supplier owner role (for all products)

**Request:**
```json
{
  "product_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002",
    "770e8400-e29b-41d4-a716-446655440003"
  ],
  "discount_percentage": 15.00
}
```

**Response:** `200 OK`
```json
{
  "message": "Successfully updated discount for 3 products"
}
```

**Use Cases:**
- Seasonal promotions
- Category-wide discounts
- Flash sales
- Clearance events

**Business Rules:**
- Must own all products being updated OR have `product:update` permission
- Discount percentage: 0-100%
- Updates all products in single transaction

---

### Product Deletion

#### 13. Delete Product

**Endpoint:** `DELETE /api/v1/products/{product_id}`

**Authorization:** Requires `product:delete` permission or supplier owner role

**Example:**
```
DELETE /api/v1/products/550e8400-e29b-41d4-a716-446655440001
```

**Response:** `200 OK`
```json
{
  "message": "Product deleted successfully"
}
```

**Business Rules:**
- **Soft delete**: Product is marked as deleted but not removed from database
- `is_deleted=true` and `deleted_at` timestamp set
- Product will not appear in public listings
- Historical order data preserved
- Cannot be restored via API (requires database intervention)

---

## Complete Examples

### Example 1: Create and Manage Product Lifecycle

**Step 1: Create New Product**
```bash
POST /api/v1/products
Authorization: Bearer {token}

{
  "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
  "sku": "DAIRY-CHEESE-001",
  "name_ar": "جبن أبيض عراقي",
  "name_en": "Iraqi White Cheese",
  "category": "Dairy",
  "unit_price": 8500.00,
  "stock_quantity": 100.00,
  "reorder_level": 20.00,
  "unit_of_measure": "kg"
}
```

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440004",
  "sku": "DAIRY-CHEESE-001",
  "name_en": "Iraqi White Cheese",
  "is_active": true,
  "availability_status": "in_stock",
  "stock_quantity": 100.00
}
```

---

**Step 2: Mark as Featured**
```bash
PATCH /api/v1/products/880e8400-e29b-41d4-a716-446655440004
Authorization: Bearer {token}

{
  "is_featured": true
}
```

**Response:** Product marked as featured

---

**Step 3: Apply Discount**
```bash
PATCH /api/v1/products/880e8400-e29b-41d4-a716-446655440004
Authorization: Bearer {token}

{
  "discount_percentage": 20.00
}
```

**Response:**
```json
{
  "unit_price": 8500.00,
  "discount_percentage": 20.00,
  "final_price": 6800.00
}
```

---

**Step 4: Stock Runs Low (Below Reorder Level)**
```bash
PATCH /api/v1/products/880e8400-e29b-41d4-a716-446655440004/stock
Authorization: Bearer {token}

{
  "stock_quantity": 15.00,
  "notes": "Stock sold faster than expected"
}
```

**Response:**
```json
{
  "stock_quantity": 15.00,
  "reorder_level": 20.00,
  "is_low_stock": true
}
```

---

**Step 5: Check Low Stock Products**
```bash
GET /api/v1/products/low-stock
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440004",
    "name_en": "Iraqi White Cheese",
    "stock_quantity": 15.00,
    "reorder_level": 20.00,
    "is_low_stock": true
  }
]
```

---

**Step 6: Restock**
```bash
PATCH /api/v1/products/880e8400-e29b-41d4-a716-446655440004/stock
Authorization: Bearer {token}

{
  "stock_quantity": 150.00,
  "notes": "Restocked from new supplier shipment"
}
```

**Response:**
```json
{
  "stock_quantity": 150.00,
  "is_low_stock": false,
  "is_in_stock": true
}
```

---

### Example 2: Seasonal Product Management

**Step 1: Create Seasonal Product (Watermelon)**
```bash
POST /api/v1/products
Authorization: Bearer {token}

{
  "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
  "sku": "FRUIT-WM-SUMMER",
  "name_ar": "بطيخ أحمر",
  "name_en": "Red Watermelon",
  "category": "Fruits",
  "subcategory": "Summer Fruits",
  "unit_price": 800.00,
  "stock_quantity": 500.00,
  "unit_of_measure": "kg",
  "shelf_life_days": 14,
  "tags": ["summer", "seasonal", "fresh"]
}
```

---

**Step 2: Deactivate at End of Season**
```bash
POST /api/v1/products/990e8400-e29b-41d4-a716-446655440005/toggle-active?is_active=false
Authorization: Bearer {token}
```

**Response:**
```json
{
  "is_active": false,
  "is_in_stock": false
}
```

---

**Step 3: Reactivate Next Summer**
```bash
POST /api/v1/products/990e8400-e29b-41d4-a716-446655440005/toggle-active?is_active=true
Authorization: Bearer {token}
```

---

### Example 3: Bulk Discount Campaign

**Step 1: Find All Vegetables**
```bash
GET /api/v1/products/category/Vegetables?active_only=true
```

**Response:** (List of vegetable product IDs)

---

**Step 2: Apply 25% Discount to All**
```bash
POST /api/v1/products/bulk/update-discount
Authorization: Bearer {token}

{
  "product_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002",
    "770e8400-e29b-41d4-a716-446655440003"
  ],
  "discount_percentage": 25.00
}
```

**Response:**
```json
{
  "message": "Successfully updated discount for 3 products"
}
```

---

## Error Handling

### Common Errors

#### 1. Product Not Found
```json
{
  "detail": "Product not found"
}
```
**HTTP Status:** `404 Not Found`

**Causes:**
- Invalid product ID
- Product has been deleted
- Product doesn't exist

---

#### 2. SKU Already Exists
```json
{
  "detail": "Product with SKU 'VEG-TOM-001' already exists for this supplier"
}
```
**HTTP Status:** `400 Bad Request`

**Solution:** Use a different SKU or update the existing product

---

#### 3. Invalid Category
```json
{
  "detail": "Invalid category. Allowed values: Vegetables, Fruits, Meat, Poultry, Seafood, Dairy, Bakery, Beverages, Dry Goods, Spices, Frozen Foods, Canned Goods, Snacks, Oils, Cleaning Supplies, Disposables, Equipment, Other"
}
```
**HTTP Status:** `422 Unprocessable Entity`

**Solution:** Use one of the allowed categories

---

#### 4. Invalid Unit of Measure
```json
{
  "detail": "Invalid unit_of_measure. Allowed values: kg, g, liter, ml, piece, box, carton, dozen, pack, bag, can, bottle, jar, tray"
}
```
**HTTP Status:** `422 Unprocessable Entity`

**Solution:** Use one of the allowed units

---

#### 5. Not Authorized
```json
{
  "detail": "Not authorized to update this product"
}
```
**HTTP Status:** `403 Forbidden`

**Causes:**
- User is not the supplier owner
- User doesn't have `product:update` permission
- Attempting to modify another supplier's product

---

## Best Practices

### 1. Product Images
- **Primary Image**: Always set a high-quality primary image (500x500px minimum)
- **Multiple Images**: Provide 3-5 images showing different angles
- **Image URLs**: Use CDN URLs for fast loading
- **Alt Text**: Use descriptive names for accessibility

### 2. Stock Management
- **Reorder Levels**: Set realistic reorder levels based on sales velocity
- **Regular Updates**: Update stock after receiving shipments immediately
- **Low Stock Alerts**: Monitor `/low-stock` endpoint daily
- **Stock Notes**: Always include notes when updating stock for audit trail

### 3. Pricing Strategy
- **Competitive Pricing**: Research market prices before setting unit_price
- **Discount Timing**: Use bulk discount endpoint for campaign management
- **Tax Configuration**: Set appropriate tax_rate based on product category
- **Currency**: Stick to IQD for consistency in Iraqi market

### 4. Search Optimization
- **Bilingual Content**: Always provide both Arabic and English names/descriptions
- **Keywords**: Include relevant search_keywords for better discoverability
- **Tags**: Use descriptive tags (organic, halal, fresh, local, etc.)
- **Categories**: Choose the most specific category and subcategory

### 5. Product Status
- **Soft Deletes**: Use soft delete instead of hard delete to preserve order history
- **Deactivation**: Use `is_active=false` for temporary unavailability (don't delete)
- **Discontinuation**: Set `availability_status=discontinued` before deleting

---

## Reference Tables

### Allowed Categories

```
- Vegetables      - Fruits          - Meat            - Poultry
- Seafood         - Dairy           - Bakery          - Beverages
- Dry Goods       - Spices          - Frozen Foods    - Canned Goods
- Snacks          - Oils            - Cleaning Supplies
- Disposables     - Equipment       - Other
```

### Allowed Units of Measure

```
- kg              - g               - liter           - ml
- piece           - box             - carton          - dozen
- pack            - bag             - can             - bottle
- jar             - tray
```

### Allowed Currencies

```
- IQD (Iraqi Dinar) - Default
- USD (US Dollar)
- EUR (Euro)
```

---

## Additional Resources

- [Order Workflow Documentation](ORDER_WORKFLOW.md) - How products are ordered
- [Delivery Workflow Documentation](DELIVERY_WORKFLOW.md) - How products are delivered
- [Supplier Management](SUPPLIER_WORKFLOW.md) - Managing suppliers
- [Restaurant Management](RESTAURANT_WORKFLOW.md) - Restaurant accounts
- [Authentication](AUTHENTICATION.md) - User authentication and permissions

---

**Last Updated:** 2024-11-19
**API Version:** v1
**Base URL:** `https://api.example.com/api/v1`

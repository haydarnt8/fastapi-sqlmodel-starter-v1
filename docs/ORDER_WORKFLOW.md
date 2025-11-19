# Order Management Workflow Documentation

This document describes the complete order management workflow from creation to delivery, including all API endpoints, request/response examples, and business rules.

## Table of Contents

1. [Order Lifecycle Overview](#order-lifecycle-overview)
2. [Status Workflow](#status-workflow)
3. [API Endpoints by Workflow Stage](#api-endpoints-by-workflow-stage)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)

---

## Order Lifecycle Overview

The order management system supports the following workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORDER LIFECYCLE                             │
└─────────────────────────────────────────────────────────────────┘

RESTAURANT SIDE                    SUPPLIER SIDE
================                   ==============

1. CREATE (draft)      →→→→→→→→
2. SUBMIT (pending)    →→→→→→→→   3. REVIEW
                                   4. CONFIRM/REJECT
                       ←←←←←←←←
5. CONFIRMED           →→→→→→→→   6. PROCESS
                       ←←←←←←←←   7. READY_FOR_DELIVERY
8. IN_TRANSIT          →→→→→→→→
9. DELIVERED           →→→→→→→→   10. MARK_COMPLETE
10. PAYMENT            →→→→→→→→   11. CONFIRM_PAYMENT

Alternative Paths:
- CANCEL (restaurant)  - Any stage before in_transit
- REJECT (supplier)    - At pending stage
```

---

## Status Workflow

### Valid Status Transitions

```
draft ──────> pending ──────> confirmed ──────> processing
  │              │                │                  │
  │              │                │                  │
  ▼              ▼                ▼                  ▼
cancelled    cancelled/      cancelled      ready_for_delivery
             rejected                               │
                                                    │
                                                    ▼
                                              in_transit ──────> delivered
                                                    │
                                                    │
                                                    ▼
                                                cancelled

Note:
- Draft can be edited freely
- Once submitted (pending), requires supplier approval
- Cancelled/rejected/delivered are final statuses
```

### Status Descriptions

| Status | Description | Who Can Set | Next Valid Status |
|--------|-------------|-------------|-------------------|
| `draft` | Order being created (cart) | Restaurant | pending, cancelled |
| `pending` | Submitted, awaiting supplier approval | Restaurant (submit) | confirmed, rejected, cancelled |
| `confirmed` | Approved by supplier | Supplier | processing, cancelled |
| `processing` | Being prepared by supplier | Supplier | ready_for_delivery |
| `ready_for_delivery` | Ready to ship | Supplier | in_transit |
| `in_transit` | Out for delivery | System/Driver | delivered, cancelled |
| `delivered` | Successfully delivered | Driver/System | N/A (final) |
| `cancelled` | Cancelled by restaurant/supplier | Restaurant/Admin | N/A (final) |
| `rejected` | Rejected by supplier | Supplier | N/A (final) |

---

## API Endpoints by Workflow Stage

### 1. Create Order (Draft)

**Endpoint:** `POST /api/v1/orders`

**Permission Required:** `order:create`

**Use Case:** Restaurant creates a new order as draft (shopping cart).

**Request:**
```json
{
  "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
  "delivery_address": {
    "street": "Al-Mansour Street",
    "district": "Al-Mansour",
    "city": "Baghdad",
    "country": "Iraq"
  },
  "delivery_date": "2024-11-20",
  "notes": "Please deliver before 10 AM. Use back entrance.",
  "items": [
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440001",
      "quantity": 50,
      "notes": "Fresh tomatoes only"
    },
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440002",
      "quantity": 30,
      "notes": "Medium size onions"
    },
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440003",
      "quantity": 100
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "restaurant_id": "c1234567-89ab-cdef-0123-456789abcdef",
  "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
  "status": "draft",
  "delivery_date": "2024-11-20",
  "delivery_address": {
    "street": "Al-Mansour Street",
    "district": "Al-Mansour",
    "city": "Baghdad",
    "country": "Iraq"
  },
  "notes": "Please deliver before 10 AM. Use back entrance.",
  "subtotal": 175000.00,
  "tax_amount": 8750.00,
  "delivery_fee": 5000.00,
  "discount_amount": 0.00,
  "total_amount": 188750.00,
  "currency": "IQD",
  "payment_status": "unpaid",
  "paid_amount": 0.00,
  "items": [
    {
      "id": "item-001",
      "product_id": "550e8400-e29b-41d4-a716-446655440001",
      "product_name_ar": "طماطم طازجة",
      "product_name_en": "Fresh Tomatoes",
      "product_sku": "VEG-TOM-001",
      "unit_price": 1500.00,
      "unit_of_measure": "kg",
      "quantity": 50,
      "discount_percentage": 0,
      "tax_rate": 5,
      "line_subtotal": 75000.00,
      "discount_amount": 0.00,
      "line_total_before_tax": 75000.00,
      "tax_amount": 3750.00,
      "line_total": 78750.00,
      "notes": "Fresh tomatoes only"
    },
    {
      "id": "item-002",
      "product_id": "550e8400-e29b-41d4-a716-446655440002",
      "product_name_ar": "بصل",
      "product_name_en": "Onions",
      "product_sku": "VEG-ONI-001",
      "unit_price": 2000.00,
      "quantity": 30,
      "line_total": 63000.00,
      "notes": "Medium size onions"
    },
    {
      "id": "item-003",
      "product_id": "550e8400-e29b-41d4-a716-446655440003",
      "product_name_ar": "بطاطس",
      "product_name_en": "Potatoes",
      "unit_price": 1200.00,
      "quantity": 100,
      "line_total": 126000.00
    }
  ],
  "is_editable": true,
  "is_cancellable": true,
  "created_at": "2024-11-19T10:00:00Z"
}
```

**Key Features:**
- Status automatically set to `draft`
- Order number auto-generated (ORD-YYYY-NNNNN format)
- Product snapshots captured (name, SKU, price at order time)
- Totals auto-calculated from items
- Payment status set to `unpaid`

---

### 2. Update Draft Order

**Endpoint:** `PATCH /api/v1/orders/{order_id}`

**Permission Required:** `order:update`

**Use Case:** Restaurant modifies draft order before submission.

**Request:**
```json
{
  "delivery_date": "2024-11-21",
  "notes": "Changed delivery date. Please confirm availability.",
  "items": [
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440001",
      "quantity": 75
    },
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440002",
      "quantity": 30
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "status": "draft",
  "delivery_date": "2024-11-21",
  "total_amount": 220500.00,
  "items": [
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440001",
      "quantity": 75,
      "line_total": 118125.00
    },
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440002",
      "quantity": 30,
      "line_total": 63000.00
    }
  ],
  "updated_at": "2024-11-19T11:00:00Z"
}
```

**Business Rules:**
- Can only edit when status is `draft` or `pending`
- Totals are recalculated automatically
- Product snapshots are updated

---

### 3. Submit Order

**Endpoint:** `POST /api/v1/orders/{order_id}/submit`

**Permission Required:** `order:update`

**Use Case:** Restaurant submits order for supplier review.

**Request:**
```bash
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/submit
# No request body required
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "status": "pending",
  "submitted_at": "2024-11-19T11:30:00Z",
  "is_editable": true,
  "is_cancellable": true
}
```

**Business Rules:**
- Current status must be `draft`
- Status changes to `pending`
- `submitted_at` timestamp recorded
- Notification sent to supplier
- Order still editable while pending

---

### 4. List Pending Orders (Supplier View)

**Endpoint:** `GET /api/v1/orders/pending`

**Permission Required:** `order:read`

**Use Case:** Supplier views orders awaiting approval.

**Request:**
```bash
GET /api/v1/orders/pending?skip=0&limit=10
```

**Response:** `200 OK`
```json
[
  {
    "id": "9876dcba-5432-1098-fedc-ba9876543210",
    "order_number": "ORD-2024-00125",
    "restaurant_id": "c1234567-89ab-cdef-0123-456789abcdef",
    "status": "pending",
    "total_amount": 220500.00,
    "delivery_date": "2024-11-21",
    "submitted_at": "2024-11-19T11:30:00Z",
    "item_count": 2
  }
]
```

**Notes:**
- Automatically filtered by supplier_id for supplier users
- Sorted by submitted_at (oldest first - queue)

---

### 5. Confirm Order (Supplier)

**Endpoint:** `POST /api/v1/orders/{order_id}/confirm`

**Permission Required:** `order:approve`

**Use Case:** Supplier approves the order.

**Request:**
```json
{
  "estimated_preparation_time_hours": 4,
  "notes": "Order confirmed. Will be ready for pickup by 4 PM today."
}
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "status": "confirmed",
  "submitted_at": "2024-11-19T11:30:00Z",
  "confirmed_at": "2024-11-19T12:00:00Z",
  "confirmed_by_id": "supplier-user-123",
  "internal_notes": "Order confirmed. Will be ready for pickup by 4 PM today.",
  "is_editable": false,
  "is_cancellable": true
}
```

**Business Rules:**
- Current status must be `pending`
- Status changes to `confirmed`
- `confirmed_at` and `confirmed_by_id` recorded
- Notification sent to restaurant
- Order no longer editable

---

### 6. Reject Order (Supplier)

**Endpoint:** `POST /api/v1/orders/{order_id}/reject`

**Permission Required:** `order:approve`

**Use Case:** Supplier rejects the order (out of stock, capacity issues, etc.).

**Request:**
```json
{
  "rejection_reason": "Item VEG-TOM-001 out of stock. Cannot fulfill order. Please reorder next week."
}
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "status": "rejected",
  "rejected_at": "2024-11-19T12:00:00Z",
  "rejection_reason": "Item VEG-TOM-001 out of stock. Cannot fulfill order. Please reorder next week.",
  "is_editable": false,
  "is_cancellable": false
}
```

**Business Rules:**
- Current status must be `pending`
- Status changes to `rejected` (final)
- `rejection_reason` is mandatory
- Notification sent to restaurant
- Order cannot be edited or cancelled

---

### 7. Update Order Status (Processing)

**Endpoint:** `POST /api/v1/orders/{order_id}/status`

**Permission Required:** `order:update`

**Use Case:** Supplier updates order through preparation stages.

**Request:**
```json
{
  "status": "processing",
  "notes": "Started preparing order. Gathering items from warehouse."
}
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "status": "processing",
  "confirmed_at": "2024-11-19T12:00:00Z",
  "updated_at": "2024-11-19T13:00:00Z"
}
```

**Valid Status Transitions:**
- `confirmed` → `processing`
- `processing` → `ready_for_delivery`
- `ready_for_delivery` → `in_transit`
- `in_transit` → `delivered`

---

### 8. Record Payment

**Endpoint:** `POST /api/v1/orders/{order_id}/payment`

**Permission Required:** `payment:create`

**Use Case:** Record full or partial payment for the order.

**Request:**
```json
{
  "payment_amount": 100000.00,
  "payment_method": "cash",
  "notes": "Partial payment received. Remaining 120,500 IQD on delivery."
}
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "total_amount": 220500.00,
  "paid_amount": 100000.00,
  "payment_status": "partially_paid",
  "payment_method": "cash",
  "outstanding_amount": 120500.00,
  "updated_at": "2024-11-19T14:00:00Z"
}
```

**Business Rules:**
- Supports partial payments
- `payment_status` auto-updated:
  - `unpaid` if paid_amount = 0
  - `partially_paid` if 0 < paid_amount < total
  - `paid` if paid_amount >= total
- Payments are cumulative

---

### 9. Get Order Statistics

**Endpoint:** `GET /api/v1/orders/statistics`

**Permission Required:** `order:read`

**Use Case:** View order metrics and revenue analytics.

**Request:**
```bash
GET /api/v1/orders/statistics?start_date=2024-11-01&end_date=2024-11-30
```

**Response:** `200 OK`
```json
{
  "total_orders": 487,
  "total_revenue": 125450000.00,
  "average_order_value": 257618.48
}
```

**Filter Options:**
- `restaurant_id` - Restaurant-specific stats
- `supplier_id` - Supplier-specific stats
- `start_date` - Period start
- `end_date` - Period end

---

### 10. List Orders (Advanced Filtering)

**Endpoint:** `GET /api/v1/orders`

**Permission Required:** `order:read`

**Use Case:** Search and filter orders with multiple criteria.

**Request:**
```bash
GET /api/v1/orders?
  status=confirmed&
  payment_status=partially_paid&
  submitted_after=2024-11-01&
  min_amount=100000&
  sort_by=total_amount&
  sort_order=desc&
  skip=0&
  limit=20
```

**Response:** `200 OK`
```json
[
  {
    "id": "9876dcba-5432-1098-fedc-ba9876543210",
    "order_number": "ORD-2024-00125",
    "restaurant_id": "c1234567-89ab-cdef-0123-456789abcdef",
    "supplier_id": "b45a3c2e-1234-5678-9abc-def012345678",
    "status": "confirmed",
    "payment_status": "partially_paid",
    "total_amount": 220500.00,
    "paid_amount": 100000.00,
    "submitted_at": "2024-11-19T11:30:00Z",
    "delivery_date": "2024-11-21"
  }
]
```

**Available Filters:**
- `query` - Search by order number
- `restaurant_id` - Filter by restaurant
- `supplier_id` - Filter by supplier
- `status` - Filter by status
- `payment_status` - Filter by payment status
- `submitted_after` / `submitted_before` - Date range
- `delivery_after` / `delivery_before` - Delivery date range
- `min_amount` / `max_amount` - Amount range
- `has_outstanding_payment` - Boolean filter
- `sort_by` - Sort field
- `sort_order` - asc/desc

---

### 11. Cancel Order

**Endpoint:** `POST /api/v1/orders/{order_id}/cancel`

**Permission Required:** `order:cancel`

**Use Case:** Restaurant or admin cancels the order.

**Request:**
```json
{
  "cancellation_reason": "Restaurant closed due to emergency. Need to cancel order."
}
```

**Response:** `200 OK`
```json
{
  "id": "9876dcba-5432-1098-fedc-ba9876543210",
  "order_number": "ORD-2024-00125",
  "status": "cancelled",
  "cancelled_at": "2024-11-19T15:00:00Z",
  "cancellation_reason": "Restaurant closed due to emergency. Need to cancel order.",
  "is_cancellable": false
}
```

**Business Rules:**
- Cannot cancel if status is `delivered`, `cancelled`, or `rejected`
- Can cancel at any stage before `in_transit`
- Cancelling `in_transit` requires admin permission
- `cancellation_reason` is mandatory

---

## Complete Examples

### Example 1: Successful Order Flow

```bash
# RESTAURANT: Create draft order
POST /api/v1/orders
{
  "supplier_id": "...",
  "items": [...]
}
# Response: status = "draft"

# RESTAURANT: Review and modify
PATCH /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210
{
  "delivery_date": "2024-11-21"
}

# RESTAURANT: Submit for approval
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/submit
# Response: status = "pending"

# SUPPLIER: View pending orders
GET /api/v1/orders/pending

# SUPPLIER: Confirm order
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/confirm
{
  "notes": "Order confirmed"
}
# Response: status = "confirmed"

# SUPPLIER: Update to processing
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/status
{
  "status": "processing"
}

# SUPPLIER: Mark ready for delivery
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/status
{
  "status": "ready_for_delivery"
}

# SYSTEM/DRIVER: Update to in_transit
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/status
{
  "status": "in_transit"
}

# DRIVER: Mark as delivered
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/status
{
  "status": "delivered"
}
# Response: status = "delivered", payment_status = "paid" ✅

# RESTAURANT: Record payment
POST /api/v1/orders/9876dcba-5432-1098-fedc-ba9876543210/payment
{
  "payment_amount": 220500.00,
  "payment_method": "cash"
}
# Response: payment_status = "paid"
```

---

### Example 2: Rejected Order Flow

```bash
# RESTAURANT: Create and submit
POST /api/v1/orders
POST /api/v1/orders/{id}/submit
# Response: status = "pending"

# SUPPLIER: Reject order
POST /api/v1/orders/{id}/reject
{
  "rejection_reason": "Out of stock"
}
# Response: status = "rejected" ❌

# RESTAURANT: Create new order with different items
POST /api/v1/orders
...
```

---

### Example 3: Cancelled Order Flow

```bash
# RESTAURANT: Create, submit, supplier confirms
POST /api/v1/orders
POST /api/v1/orders/{id}/submit
# SUPPLIER confirms...
# Response: status = "confirmed"

# RESTAURANT: Emergency cancellation
POST /api/v1/orders/{id}/cancel
{
  "cancellation_reason": "Restaurant emergency"
}
# Response: status = "cancelled" ❌
```

---

## Integration with Delivery System

Once an order reaches `ready_for_delivery` status, create a delivery:

```bash
# Order is ready for delivery
POST /api/v1/orders/{order_id}/status
{
  "status": "ready_for_delivery"
}

# Create delivery for the order
POST /api/v1/deliveries
{
  "order_id": "{order_id}",
  "pickup_address": "...",
  "delivery_address": "...",
  ...
}

# Assign driver and proceed with delivery workflow
# See DELIVERY_WORKFLOW.md for details
```

---

## Error Handling

### Common Error Responses

#### 1. Invalid Status Transition
```json
{
  "detail": "Invalid status transition from delivered to processing"
}
```
**HTTP Status:** `400 Bad Request`

---

#### 2. Order Not Editable
```json
{
  "detail": "Order cannot be edited in current status: confirmed"
}
```
**HTTP Status:** `400 Bad Request`

---

#### 3. Order Not Found
```json
{
  "detail": "Order not found"
}
```
**HTTP Status:** `404 Not Found`

---

#### 4. Product Not Available
```json
{
  "detail": "Product Fresh Tomatoes is not available"
}
```
**HTTP Status:** `400 Bad Request`

---

#### 5. Insufficient Permissions
```json
{
  "detail": "You do not have permission to confirm orders"
}
```
**HTTP Status:** `403 Forbidden`

---

## Best Practices

1. **Order Creation**
   - Always save as draft first
   - Review totals before submission
   - Add detailed notes for supplier

2. **Product Snapshots**
   - Prices are captured at order time
   - Product changes don't affect existing orders
   - Historical accuracy maintained

3. **Payment Tracking**
   - Support partial payments
   - Record payment method
   - Track outstanding amounts

4. **Status Updates**
   - Follow workflow sequence
   - Validate transitions
   - Add notes for clarity

5. **Performance**
   - Use pagination for large datasets
   - Filter by status and dates
   - Cache statistics

---

## Additional Resources

- [Delivery Workflow](DELIVERY_WORKFLOW.md)
- [Product Catalog Guide](PRODUCT_CATALOG.md)
- [Payment Processing](PAYMENT_WORKFLOW.md)
- [API Authentication](AUTHENTICATION.md)

---

**Last Updated:** 2024-11-19
**Version:** 1.0
**API Version:** v1

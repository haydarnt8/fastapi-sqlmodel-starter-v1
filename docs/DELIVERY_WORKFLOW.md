# Delivery Workflow Documentation

This document describes the complete delivery workflow from creation to completion, including all API endpoints, request/response examples, and business rules.

## Table of Contents

1. [Delivery Lifecycle Overview](#delivery-lifecycle-overview)
2. [Status Workflow](#status-workflow)
3. [API Endpoints by Workflow Stage](#api-endpoints-by-workflow-stage)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)

---

## Delivery Lifecycle Overview

The delivery system supports the following workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                      DELIVERY LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

1. CREATE         → Order confirmed, delivery created (pending)
2. ASSIGN         → Driver assigned to delivery (assigned)
3. PICKUP         → Driver picks up from supplier (picked_up)
4. START          → Driver starts journey (in_transit)
5. ARRIVE         → Driver arrives at restaurant (arrived)
6. PROOF          → Submit proof of delivery (delivered)
7. COMPLETE       → Delivery completed successfully

Alternative Paths:
- CANCEL         → Cancel delivery (any stage before delivery)
- FAIL           → Mark delivery as failed (during active stages)
```

---

## Status Workflow

### Valid Status Transitions

```
pending ──────────> assigned ──────────> picked_up
   │                   │                      │
   │                   │                      │
   ▼                   ▼                      ▼
cancelled          cancelled          in_transit ──────> arrived ──────> delivered
                                           │                │
                                           │                │
                                           ▼                ▼
                                       cancelled         failed

Note:
- Any active status can transition to 'cancelled'
- Active statuses (picked_up, in_transit, arrived) can transition to 'failed'
- Final statuses: delivered, failed, cancelled, rejected
```

### Status Descriptions

| Status | Description | Who Can Set | Next Valid Status |
|--------|-------------|-------------|-------------------|
| `pending` | Waiting for driver assignment | System (auto) | assigned, cancelled |
| `assigned` | Driver assigned, not picked up yet | Dispatcher | picked_up, cancelled |
| `picked_up` | Driver picked up order from supplier | Driver | in_transit, failed, cancelled |
| `in_transit` | Driver en route to restaurant | Driver | arrived, failed, cancelled |
| `arrived` | Driver arrived at restaurant | Driver | delivered (via proof), failed, cancelled |
| `delivered` | Successfully delivered | System (via proof) | N/A (final) |
| `failed` | Delivery failed | Driver/Admin | N/A (final) |
| `cancelled` | Delivery cancelled | Admin | N/A (final) |

---

## API Endpoints by Workflow Stage

### 1. Create Delivery

**Endpoint:** `POST /api/v1/deliveries`

**Permission Required:** `delivery:create`

**Use Case:** When an order is confirmed and ready for delivery, create a delivery record.

**Request:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "priority": "normal",
  "pickup_address": "Baghdad Wholesale Market, Street 52, Baghdad",
  "pickup_city": "Baghdad",
  "pickup_district": "Karrada",
  "pickup_latitude": 33.3152,
  "pickup_longitude": 44.3661,
  "delivery_address": "Al-Mansour Restaurant, Al-Mansour St, Baghdad",
  "delivery_city": "Baghdad",
  "delivery_district": "Al-Mansour",
  "delivery_latitude": 33.3128,
  "delivery_longitude": 44.4009,
  "estimated_delivery_time": "2024-11-19T14:00:00Z",
  "special_instructions": "Use back entrance. Call upon arrival."
}
```

**Response:** `201 Created`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": null,
  "status": "pending",
  "priority": "normal",
  "pickup_address": "Baghdad Wholesale Market, Street 52, Baghdad",
  "pickup_city": "Baghdad",
  "pickup_latitude": 33.3152,
  "pickup_longitude": 44.3661,
  "delivery_address": "Al-Mansour Restaurant, Al-Mansour St, Baghdad",
  "delivery_city": "Baghdad",
  "delivery_latitude": 33.3128,
  "delivery_longitude": 44.4009,
  "estimated_distance_km": 3.87,
  "delivery_fee": 8870.00,
  "estimated_delivery_time": "2024-11-19T14:00:00Z",
  "special_instructions": "Use back entrance. Call upon arrival.",
  "is_assigned": false,
  "is_active": true,
  "is_completed": false,
  "created_at": "2024-11-19T10:00:00Z"
}
```

**Notes:**
- If GPS coordinates are provided, distance is auto-calculated using Haversine formula
- Delivery fee is auto-calculated: 5,000 IQD base + (distance_km × 1,000 IQD)
- Status automatically set to `pending`
- Driver not assigned yet

---

### 2. List Pending Assignments

**Endpoint:** `GET /api/v1/deliveries/pending`

**Permission Required:** `delivery:assign`

**Use Case:** Dispatchers view deliveries awaiting driver assignment.

**Request:**
```bash
GET /api/v1/deliveries/pending?city=Baghdad&skip=0&limit=10
```

**Response:** `200 OK`
```json
[
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "driver_id": null,
    "status": "pending",
    "priority": "normal",
    "delivery_address": "Al-Mansour Restaurant, Al-Mansour St, Baghdad",
    "delivery_city": "Baghdad",
    "estimated_delivery_time": "2024-11-19T14:00:00Z",
    "delivery_fee": 8870.00,
    "is_delayed": false,
    "created_at": "2024-11-19T10:00:00Z"
  }
]
```

---

### 3. Assign Driver

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/assign`

**Permission Required:** `delivery:assign`

**Use Case:** Dispatcher assigns a driver to the delivery.

**Request:**
```json
{
  "driver_id": "a8f5f167-68e1-41d4-b34d-123456789abc",
  "estimated_pickup_time": "2024-11-19T12:00:00Z",
  "notes": "Driver Ahmed assigned. Notify supplier of pickup time."
}
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": "a8f5f167-68e1-41d4-b34d-123456789abc",
  "status": "assigned",
  "priority": "normal",
  "assigned_at": "2024-11-19T10:30:00Z",
  "estimated_pickup_time": "2024-11-19T12:00:00Z",
  "estimated_delivery_time": "2024-11-19T14:00:00Z",
  "is_assigned": true,
  "is_active": true
}
```

**Business Rules:**
- Driver must exist and have 'driver' role
- Delivery must be in `pending` status
- Status automatically changes to `assigned`
- `assigned_at` timestamp is recorded

---

### 4. Mark as Picked Up

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/pickup`

**Permission Required:** None (driver endpoint)

**Use Case:** Driver marks the order as picked up from supplier.

**Request:**
```bash
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/pickup
# No request body required
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "picked_up",
  "assigned_at": "2024-11-19T10:30:00Z",
  "picked_up_at": "2024-11-19T12:05:00Z",
  "is_in_progress": true
}
```

**Business Rules:**
- Only the assigned driver can perform this action
- Current status must be `assigned`
- Status automatically changes to `picked_up`
- `picked_up_at` timestamp is recorded

---

### 5. Start Delivery (In Transit)

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/start`

**Permission Required:** None (driver endpoint)

**Use Case:** Driver starts journey to restaurant.

**Request:**
```bash
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/start
# No request body required
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "in_transit",
  "picked_up_at": "2024-11-19T12:05:00Z",
  "in_transit_at": "2024-11-19T12:10:00Z",
  "can_update_location": true,
  "is_in_progress": true
}
```

**Business Rules:**
- Only the assigned driver can perform this action
- Current status must be `picked_up`
- Status automatically changes to `in_transit`
- `in_transit_at` timestamp is recorded
- Driver can now update GPS location

---

### 6. Update GPS Location

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/location`

**Permission Required:** None (driver endpoint)

**Use Case:** Driver sends real-time location updates during delivery.

**Request:**
```json
{
  "latitude": 33.3140,
  "longitude": 44.3835
}
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "current_latitude": 33.3140,
  "current_longitude": 44.3835,
  "last_location_update": "2024-11-19T12:25:00Z",
  "location_history": {
    "points": [
      {
        "lat": 33.3152,
        "lng": 44.3661,
        "timestamp": "2024-11-19T12:10:00Z"
      },
      {
        "lat": 33.3145,
        "lng": 44.3750,
        "timestamp": "2024-11-19T12:17:00Z"
      },
      {
        "lat": 33.3140,
        "lng": 44.3835,
        "timestamp": "2024-11-19T12:25:00Z"
      }
    ]
  }
}
```

**Business Rules:**
- Only the assigned driver can update location
- Can only update during active delivery (`picked_up`, `in_transit`, `arrived`)
- Location points are appended to history
- `current_latitude` and `current_longitude` are updated
- `last_location_update` timestamp is recorded

**Recommended Update Frequency:**
- Every 30-60 seconds during active delivery
- Stop updates when arrived or delivered

---

### 7. Mark as Arrived

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/arrive`

**Permission Required:** None (driver endpoint)

**Use Case:** Driver arrives at restaurant delivery location.

**Request:**
```bash
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/arrive
# No request body required
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "arrived",
  "in_transit_at": "2024-11-19T12:10:00Z",
  "arrived_at": "2024-11-19T12:45:00Z",
  "requires_proof_of_delivery": true,
  "can_update_location": false
}
```

**Business Rules:**
- Only the assigned driver can perform this action
- Current status must be `in_transit`
- Status automatically changes to `arrived`
- `arrived_at` timestamp is recorded
- Driver must now submit proof of delivery to complete

---

### 8. Submit Proof of Delivery

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/proof`

**Permission Required:** None (driver endpoint)

**Use Case:** Driver submits signature, photos, and recipient information to complete delivery.

**Request:**
```json
{
  "signature_url": "https://cdn.example.com/signatures/abc123.png",
  "photo_urls": [
    "https://cdn.example.com/deliveries/photo1.jpg",
    "https://cdn.example.com/deliveries/photo2.jpg"
  ],
  "recipient_name": "محمد أحمد (Ahmed Mohammed)",
  "recipient_phone": "+964 771 234 5678",
  "recipient_notes": "Received in good condition. Restaurant manager signed."
}
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "delivered",
  "arrived_at": "2024-11-19T12:45:00Z",
  "delivered_at": "2024-11-19T12:50:00Z",
  "signature_url": "https://cdn.example.com/signatures/abc123.png",
  "photo_urls": {
    "photos": [
      "https://cdn.example.com/deliveries/photo1.jpg",
      "https://cdn.example.com/deliveries/photo2.jpg"
    ]
  },
  "recipient_name": "محمد أحمد (Ahmed Mohammed)",
  "recipient_phone": "+964 771 234 5678",
  "has_proof_of_delivery": true,
  "is_completed": true,
  "actual_duration_minutes": 45
}
```

**Business Rules:**
- Only the assigned driver can submit proof
- Current status must be `arrived`
- Status automatically changes to `delivered` upon successful submission
- `delivered_at` timestamp is recorded
- At least one proof type required (signature OR photos)
- Recipient name is mandatory

---

### 9. Get Delivery Details

**Endpoint:** `GET /api/v1/deliveries/{delivery_id}`

**Permission Required:** `delivery:read`

**Use Case:** View complete delivery details including order and driver information.

**Request:**
```bash
GET /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": "a8f5f167-68e1-41d4-b34d-123456789abc",
  "status": "delivered",
  "priority": "normal",
  "pickup_address": "Baghdad Wholesale Market, Street 52, Baghdad",
  "pickup_city": "Baghdad",
  "pickup_latitude": 33.3152,
  "pickup_longitude": 44.3661,
  "delivery_address": "Al-Mansour Restaurant, Al-Mansour St, Baghdad",
  "delivery_city": "Baghdad",
  "delivery_latitude": 33.3128,
  "delivery_longitude": 44.4009,
  "estimated_distance_km": 3.87,
  "actual_distance_km": 4.12,
  "delivery_fee": 8870.00,
  "assigned_at": "2024-11-19T10:30:00Z",
  "picked_up_at": "2024-11-19T12:05:00Z",
  "in_transit_at": "2024-11-19T12:10:00Z",
  "arrived_at": "2024-11-19T12:45:00Z",
  "delivered_at": "2024-11-19T12:50:00Z",
  "estimated_delivery_time": "2024-11-19T14:00:00Z",
  "signature_url": "https://cdn.example.com/signatures/abc123.png",
  "recipient_name": "محمد أحمد (Ahmed Mohammed)",
  "special_instructions": "Use back entrance. Call upon arrival.",
  "is_assigned": true,
  "is_active": false,
  "is_completed": true,
  "is_delayed": false,
  "estimated_duration_minutes": 120,
  "actual_duration_minutes": 45,
  "created_at": "2024-11-19T10:00:00Z",
  "updated_at": "2024-11-19T12:50:00Z"
}
```

---

### 10. List Active Deliveries

**Endpoint:** `GET /api/v1/deliveries/active`

**Permission Required:** `delivery:read`

**Use Case:** Monitor all deliveries currently in progress.

**Request:**
```bash
GET /api/v1/deliveries/active?city=Baghdad&skip=0&limit=10
```

**Response:** `200 OK`
```json
[
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "driver_id": "a8f5f167-68e1-41d4-b34d-123456789abc",
    "status": "in_transit",
    "priority": "high",
    "delivery_address": "Al-Mansour Restaurant, Baghdad",
    "delivery_city": "Baghdad",
    "estimated_delivery_time": "2024-11-19T14:00:00Z",
    "delivery_fee": 8870.00,
    "is_delayed": false,
    "created_at": "2024-11-19T10:00:00Z"
  }
]
```

---

### 11. Get Driver's Deliveries

**Endpoint:** `GET /api/v1/deliveries/driver/{driver_id}`

**Permission Required:** `delivery:read`

**Use Case:** View all deliveries assigned to a specific driver.

**Request:**
```bash
GET /api/v1/deliveries/driver/a8f5f167-68e1-41d4-b34d-123456789abc?status=in_transit
```

**Response:** `200 OK`
```json
[
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "driver_id": "a8f5f167-68e1-41d4-b34d-123456789abc",
    "status": "in_transit",
    "priority": "normal",
    "delivery_address": "Al-Mansour Restaurant, Baghdad",
    "estimated_delivery_time": "2024-11-19T14:00:00Z",
    "is_delayed": false
  }
]
```

**Notes:**
- Drivers can only access their own deliveries
- Admins can view any driver's deliveries

---

### 12. Get Delivery Statistics

**Endpoint:** `GET /api/v1/deliveries/statistics`

**Permission Required:** `delivery:read`

**Use Case:** View delivery metrics and performance analytics.

**Request:**
```bash
GET /api/v1/deliveries/statistics?driver_id=a8f5f167-68e1-41d4-b34d-123456789abc&start_date=2024-11-01&end_date=2024-11-30
```

**Response:** `200 OK`
```json
{
  "total_deliveries": 145,
  "pending_deliveries": 3,
  "in_progress_deliveries": 12,
  "completed_deliveries": 128,
  "failed_deliveries": 2,
  "cancelled_deliveries": 0,
  "total_distance_km": 5847.32,
  "total_delivery_fees": 10847320.00,
  "average_delivery_time_minutes": 42,
  "delayed_deliveries": 5
}
```

---

## Alternative Workflows

### Cancel Delivery

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/cancel`

**Permission Required:** `delivery:delete`

**Use Case:** Cancel delivery before completion (restaurant request, order cancelled, etc.).

**Request:**
```json
{
  "cancellation_reason": "Restaurant closed due to emergency. Order cancelled."
}
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "cancelled",
  "cancelled_at": "2024-11-19T13:00:00Z",
  "cancellation_reason": "Restaurant closed due to emergency. Order cancelled.",
  "is_completed": true,
  "can_be_cancelled": false
}
```

**Business Rules:**
- Cannot cancel if already `delivered`, `failed`, or `cancelled`
- Can cancel at any stage before delivery
- `cancellation_reason` is mandatory
- `cancelled_at` timestamp is recorded

---

### Mark as Failed

**Endpoint:** `POST /api/v1/deliveries/{delivery_id}/fail`

**Permission Required:** None (driver endpoint) or `delivery:update` (admin)

**Use Case:** Mark delivery as failed (restaurant closed, address wrong, refused delivery, etc.).

**Request:**
```json
{
  "failure_reason": "Restaurant address incorrect. Unable to locate. Customer not responding to calls.",
  "photo_urls": [
    "https://cdn.example.com/failures/location_proof.jpg"
  ]
}
```

**Response:** `200 OK`
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "failed",
  "failed_at": "2024-11-19T13:15:00Z",
  "failure_reason": "Restaurant address incorrect. Unable to locate. Customer not responding to calls.",
  "photo_urls": {
    "photos": [
      "https://cdn.example.com/failures/location_proof.jpg"
    ]
  },
  "is_completed": true
}
```

**Business Rules:**
- Driver can mark own delivery as failed
- Admin can mark any delivery as failed
- Cannot fail if already in final status
- `failure_reason` is mandatory
- Photos can be attached as evidence

---

## Complete Examples

### Example 1: Successful Delivery Flow

```bash
# 1. Create delivery
POST /api/v1/deliveries
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "pickup_address": "Baghdad Market",
  "delivery_address": "Al-Mansour Restaurant",
  ...
}
# Response: status = "pending"

# 2. Assign driver
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/assign
{
  "driver_id": "a8f5f167-68e1-41d4-b34d-123456789abc"
}
# Response: status = "assigned"

# 3. Driver picks up
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/pickup
# Response: status = "picked_up"

# 4. Driver starts delivery
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/start
# Response: status = "in_transit"

# 5. Update location (during transit, every 30-60 seconds)
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/location
{
  "latitude": 33.3140,
  "longitude": 44.3835
}
# Response: current location updated

# 6. Driver arrives
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/arrive
# Response: status = "arrived"

# 7. Submit proof of delivery
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/proof
{
  "signature_url": "https://...",
  "recipient_name": "Ahmed Mohammed",
  ...
}
# Response: status = "delivered" ✅
```

---

### Example 2: Failed Delivery Flow

```bash
# 1-4: Same as Example 1 (create, assign, pickup, start)

# 5: Driver arrives at location
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/arrive
# Response: status = "arrived"

# 6: Restaurant closed, mark as failed
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/fail
{
  "failure_reason": "Restaurant closed. No response to calls.",
  "photo_urls": ["https://cdn.example.com/proof.jpg"]
}
# Response: status = "failed" ❌
```

---

### Example 3: Cancelled Delivery Flow

```bash
# 1-2: Create and assign delivery

# 3: Order cancelled before pickup
POST /api/v1/deliveries/7c9e6679-7425-40de-944b-e07fc1f90ae7/cancel
{
  "cancellation_reason": "Customer cancelled order"
}
# Response: status = "cancelled" ❌
```

---

## Error Handling

### Common Error Responses

#### 1. Invalid Status Transition
```json
{
  "detail": "Invalid status transition from in_transit to assigned"
}
```
**HTTP Status:** `400 Bad Request`

---

#### 2. Unauthorized Driver Access
```json
{
  "detail": "You are not assigned to this delivery"
}
```
**HTTP Status:** `403 Forbidden`

---

#### 3. Delivery Not Found
```json
{
  "detail": "Delivery not found"
}
```
**HTTP Status:** `404 Not Found`

---

#### 4. Missing Proof Requirement
```json
{
  "detail": "Proof of delivery can only be submitted when status is 'arrived'"
}
```
**HTTP Status:** `400 Bad Request`

---

#### 5. Driver Not Found
```json
{
  "detail": "Driver a8f5f167-68e1-41d4-b34d-123456789abc not found"
}
```
**HTTP Status:** `400 Bad Request`

---

## Best Practices

1. **Location Updates**
   - Update every 30-60 seconds during active delivery
   - Stop updates when arrived or delivered
   - Include timestamp in location history

2. **Proof of Delivery**
   - Always include signature OR photos (minimum)
   - Recipient name is mandatory
   - Store photos/signatures securely (CDN/S3)

3. **Error Handling**
   - Always check status before transitions
   - Validate driver assignment before actions
   - Provide clear error messages

4. **Performance**
   - Use pagination for list endpoints
   - Filter by city/status for better performance
   - Cache delivery statistics

5. **Security**
   - Drivers can only access their own deliveries
   - Admin override for emergency situations
   - Audit all status changes

---

## Additional Resources

- [Order Management Workflow](ORDER_WORKFLOW.md)
- [Product Catalog Guide](PRODUCT_CATALOG.md)
- [API Authentication](AUTHENTICATION.md)
- [Role-Based Access Control](RBAC.md)

---

**Last Updated:** 2024-11-19
**Version:** 1.0
**API Version:** v1

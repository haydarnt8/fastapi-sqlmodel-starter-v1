# Roles and Permissions System

## Overview

This FastAPI application uses a **Role-Based Access Control (RBAC)** system to manage user permissions. Every user has one or more roles, and each role has a set of permissions that determine what actions they can perform.

---

## Default Role on Registration

### ✅ **"User" Role - Automatically Assigned**

When a new user registers via `POST /api/v1/auth/register`, they **automatically receive the "User" role**.

**Permissions granted to "User" role:**

| Permission | Description | What You Can Do |
|------------|-------------|-----------------|
| `user:read` | Read own profile | View your account information |
| `restaurant:create` | Create restaurant | Register as a restaurant owner |
| `supplier:create` | Create supplier | Register as a supplier owner |
| `product:read` | Browse products | View product catalog |
| `restaurant:read` | View restaurants | Browse restaurant listings |
| `supplier:read` | View suppliers | Browse supplier listings |

**What "User" role CANNOT do:**
- ❌ Create/modify products (need to be supplier owner)
- ❌ Place orders (need to create restaurant first)
- ❌ Manage deliveries (need to be driver or supplier)
- ❌ Admin functions (need Admin role)
- ❌ Verify restaurants/suppliers (need Manager role)

---

## Role Hierarchy

### System Administration Roles

#### 1. **Admin** (Superuser)
**Code:** `admin`
**Priority:** 1 (Highest)
**Permissions:** `*:*` (All permissions)

**Capabilities:**
- ✅ Full system access
- ✅ Manage all users, roles, and permissions
- ✅ Verify restaurants and suppliers
- ✅ Access audit logs
- ✅ Override any restriction

**How to Get:**
- Created by system initialization
- First superuser: `admin@example.com` / `admin123`
- Can be assigned by existing Admin

---

#### 2. **Manager**
**Code:** `manager`
**Priority:** 2
**Permissions:**
- `user:read`, `user:update`
- `role:read`, `role:assign`
- `restaurant:verify`, `supplier:verify`
- `audit:read`

**Capabilities:**
- ✅ View and update user accounts
- ✅ Assign roles to users
- ✅ Verify/approve restaurants and suppliers
- ✅ View audit logs
- ❌ Delete users or modify system configuration

**How to Get:**
- Assigned by Admin

---

### Restaurant Roles

#### 3. **Restaurant Owner**
**Code:** `restaurant_owner`
**Priority:** 5
**Permissions:**
- `restaurant:read`, `restaurant:update`
- `product:read`
- `order:create`, `order:read`, `order:update`, `order:cancel`
- `delivery:read`
- `payment:read`, `payment:create`
- `review:read`, `review:create`

**Capabilities:**
- ✅ Manage restaurant profile
- ✅ Browse supplier catalogs
- ✅ Create and manage orders
- ✅ Track deliveries
- ✅ Process payments
- ✅ Leave reviews for suppliers

**How to Get:**
- Automatically assigned when you create a restaurant
- `owner_id` field in Restaurant model is set to your user ID

---

#### 4. **Restaurant Manager**
**Code:** `restaurant_manager`
**Priority:** 6
**Permissions:**
- `restaurant:read`
- `product:read`
- `order:create`, `order:read`, `order:update`
- `delivery:read`
- `payment:read`
- `review:read`

**Capabilities:**
- ✅ View restaurant information
- ✅ Browse products and create orders
- ✅ Track deliveries
- ✅ View payment history
- ❌ Cannot modify restaurant profile
- ❌ Cannot cancel orders

**How to Get:**
- Assigned by Restaurant Owner or Admin

---

#### 5. **Restaurant Staff**
**Code:** `restaurant_staff`
**Priority:** 7
**Permissions:**
- `restaurant:read`
- `product:read`
- `order:read`
- `delivery:read`

**Capabilities:**
- ✅ View restaurant information (read-only)
- ✅ Browse products
- ✅ View order history
- ✅ Track deliveries
- ❌ Cannot create or modify orders
- ❌ Cannot make payments

**How to Get:**
- Assigned by Restaurant Owner/Manager or Admin

---

### Supplier Roles

#### 6. **Supplier Admin**
**Code:** `supplier_admin`
**Priority:** 5
**Permissions:**
- `supplier:read`, `supplier:update`
- `product:*` (All product permissions)
- `order:read`, `order:update`, `order:approve`
- `delivery:create`, `delivery:read`, `delivery:update`, `delivery:assign`
- `payment:read`, `payment:create`
- `review:read`

**Capabilities:**
- ✅ Manage supplier profile
- ✅ Full product catalog management (create, update, delete)
- ✅ Approve/reject orders
- ✅ Create and manage deliveries
- ✅ Assign deliveries to drivers
- ✅ Process payments
- ✅ View customer reviews

**How to Get:**
- Automatically assigned when you create a supplier
- `owner_id` field in Supplier model is set to your user ID

---

#### 7. **Supplier Manager**
**Code:** `supplier_manager`
**Priority:** 6
**Permissions:**
- `supplier:read`
- `product:create`, `product:read`, `product:update`
- `order:read`, `order:update`, `order:approve`
- `delivery:read`, `delivery:update`
- `payment:read`
- `review:read`

**Capabilities:**
- ✅ View supplier information
- ✅ Manage product catalog (cannot delete)
- ✅ Process orders
- ✅ Update delivery status
- ✅ View payment history
- ❌ Cannot modify supplier profile
- ❌ Cannot delete products

**How to Get:**
- Assigned by Supplier Admin or Admin

---

#### 8. **Supplier Staff**
**Code:** `supplier_staff`
**Priority:** 7
**Permissions:**
- `supplier:read`
- `product:read`
- `order:read`
- `delivery:read`

**Capabilities:**
- ✅ View supplier information (read-only)
- ✅ Browse product catalog
- ✅ View order history
- ✅ Track deliveries
- ❌ Cannot modify anything

**How to Get:**
- Assigned by Supplier Admin/Manager or Admin

---

### Specialized Roles

#### 9. **Driver**
**Code:** `driver`
**Priority:** 8
**Permissions:**
- `delivery:read`, `delivery:update`, `delivery:complete`
- `order:read`

**Capabilities:**
- ✅ View assigned deliveries
- ✅ Update GPS location
- ✅ Update delivery status
- ✅ Mark deliveries as complete
- ✅ Upload proof of delivery
- ✅ View order details for deliveries

**How to Get:**
- Assigned by Admin or Supplier Admin

---

#### 10. **Accountant**
**Code:** `accountant`
**Priority:** 6
**Permissions:**
- `order:read`
- `payment:*` (All payment permissions)
- `restaurant:read`
- `supplier:read`

**Capabilities:**
- ✅ View all orders
- ✅ Full payment management
- ✅ View restaurant and supplier information
- ✅ Generate financial reports

**How to Get:**
- Assigned by Admin

---

## Permission Format

Permissions follow the format: `resource:action`

### Resources
- `user` - User accounts
- `role` - Roles and role assignments
- `restaurant` - Restaurant profiles
- `supplier` - Supplier profiles
- `product` - Product catalog
- `order` - Orders
- `delivery` - Deliveries
- `payment` - Payments
- `review` - Reviews
- `audit` - Audit logs

### Actions
- `read` - View/list resources
- `create` - Create new resources
- `update` - Modify existing resources
- `delete` - Remove resources
- `*` - All actions on resource
- `verify` - Approve/verify (restaurants, suppliers)
- `assign` - Assign roles or deliveries
- `approve` - Approve orders
- `cancel` - Cancel orders
- `complete` - Complete deliveries

### Special Permissions
- `*:*` - All permissions on all resources (Admin only)
- `product:*` - All product actions (Supplier Admin)
- `payment:*` - All payment actions (Accountant, Supplier Admin)

---

## Common Workflows

### Scenario 1: Register as Restaurant Owner

```
1. Register → POST /api/v1/auth/register
   ↓ Auto-assigned "User" role

2. Login → POST /api/v1/auth/login
   ↓ Get access token

3. Create Restaurant → POST /api/v1/restaurants
   ↓ Auto-assigned "Restaurant Owner" role
   ↓ owner_id set to your user ID

4. Wait for Admin to verify restaurant
   ↓ Admin approves via POST /api/v1/restaurants/{id}/verify

5. Browse Products → GET /api/v1/products

6. Place Order → POST /api/v1/orders
```

**Roles After This Flow:**
- ✅ User
- ✅ Restaurant Owner

---

### Scenario 2: Register as Supplier

```
1. Register → POST /api/v1/auth/register
   ↓ Auto-assigned "User" role

2. Login → POST /api/v1/auth/login
   ↓ Get access token

3. Create Supplier → POST /api/v1/suppliers
   ↓ Auto-assigned "Supplier Admin" role
   ↓ owner_id set to your user ID

4. Wait for Admin to verify supplier
   ↓ Admin approves via POST /api/v1/suppliers/{id}/verify

5. Add Products → POST /api/v1/products

6. Receive Orders → GET /api/v1/orders (filtered by supplier)

7. Approve Orders → POST /api/v1/orders/{id}/approve
```

**Roles After This Flow:**
- ✅ User
- ✅ Supplier Admin

---

### Scenario 3: Be a Driver

```
1. Register → POST /api/v1/auth/register
   ↓ Auto-assigned "User" role

2. Wait for Admin to assign "Driver" role
   ↓ Admin uses POST /api/v1/users/{id}/roles

3. Login → POST /api/v1/auth/login

4. View Assigned Deliveries → GET /api/v1/deliveries/driver/assigned

5. Accept Delivery → POST /api/v1/deliveries/{id}/pickup

6. Update GPS → POST /api/v1/deliveries/{id}/location

7. Complete Delivery → POST /api/v1/deliveries/{id}/complete
```

**Roles After This Flow:**
- ✅ User
- ✅ Driver

---

## Checking Your Permissions

### Get Current User with Roles

```bash
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "roles": [
    {
      "id": "role-uuid-1",
      "code": "user",
      "name": "User"
    },
    {
      "id": "role-uuid-2",
      "code": "restaurant_owner",
      "name": "Restaurant Owner"
    }
  ]
}
```

---

## Role Assignment (Admin Only)

### Assign Role to User

```bash
POST /api/v1/users/{user_id}/roles
Authorization: Bearer {admin_token}

{
  "role_ids": ["role-uuid-1", "role-uuid-2"]
}
```

### Remove Role from User

```bash
DELETE /api/v1/users/{user_id}/roles/{role_id}
Authorization: Bearer {admin_token}
```

---

## Summary Table

| Role | Auto-Assigned | How to Get | Can Create Restaurant | Can Create Supplier | Can Manage Products | Can Place Orders | Can Deliver |
|------|---------------|------------|----------------------|--------------------|--------------------|-----------------|-------------|
| **User** | ✅ On Registration | Automatic | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Restaurant Owner** | ✅ On Restaurant Creation | Create restaurant | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Restaurant Manager** | ❌ | Assigned by owner | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Restaurant Staff** | ❌ | Assigned by owner | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Supplier Admin** | ✅ On Supplier Creation | Create supplier | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Supplier Manager** | ❌ | Assigned by supplier admin | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Supplier Staff** | ❌ | Assigned by supplier admin | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Driver** | ❌ | Assigned by admin | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Manager** | ❌ | Assigned by admin | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Admin** | ❌ | System/Assigned by admin | ✅ | ✅ | ✅ | ✅ | ✅ |

---

**Last Updated:** 2024-11-19
**API Version:** v1

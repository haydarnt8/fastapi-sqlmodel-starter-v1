# API Usage Guide

Complete guide with examples for all API endpoints in the FastAPI Starter Template.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication Flow](#authentication-flow)
- [Authentication Endpoints](#authentication-endpoints)
- [User Management](#user-management)
- [Role Management](#role-management)
- [Audit Logs](#audit-logs)
- [Internationalization](#internationalization)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Python Client Examples](#python-client-examples)

---

## Getting Started

### Base URL

```
Development: http://localhost:8000
Production: https://your-api-domain.com
```

### API Version

All endpoints are prefixed with `/api/v1`

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Authentication

Most endpoints require authentication. Include the access token in the Authorization header:

```bash
Authorization: Bearer <your-access-token>
```

---

## Authentication Flow

### Complete Authentication Flow

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure123",
    "full_name": "John Doe"
  }'

# 2. Login to get tokens
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure123"
  }'

# Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}

# 3. Use access token for authenticated requests
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGc..."

# 4. Refresh access token when it expires
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGc..."
  }'

# 5. Logout (revokes token)
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

## Authentication Endpoints

### Register User

Register a new user account.

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "secure123",
  "full_name": "Jane Smith"
}
```

**Response (200):**
```json
{
  "id": "uuid-here",
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-09T12:00:00Z",
  "roles": []
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Smith"
  }'
```

---

### Login

Authenticate and receive access and refresh tokens.

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "changeme123"
  }'
```

**Alternative (Form Data):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
```

---

### Get Current User

Get information about the currently authenticated user.

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response (200):**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-09T12:00:00Z",
  "roles": [
    {
      "id": "role-uuid",
      "name": "user",
      "description": "Standard User",
      "permissions": ["user:read", "user:update_own"]
    }
  ]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Refresh Token

Get a new access token using a refresh token.

**Endpoint:** `POST /api/v1/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGc..."
  }'
```

---

### Logout

Logout and revoke the current access token.

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer $TOKEN"
```

---

## User Management

All user management endpoints require admin privileges (`user:*` or `*:*` permission).

### List Users

Get a paginated list of users.

**Endpoint:** `GET /api/v1/users`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 20, max: 100)

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "email": "user1@example.com",
      "full_name": "User One",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-01-09T12:00:00Z",
      "roles": [...]
    },
    {
      "id": "uuid-2",
      "email": "user2@example.com",
      "full_name": "User Two",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-01-09T13:00:00Z",
      "roles": [...]
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 20
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

# Get first 10 users
curl -X GET "http://localhost:8000/api/v1/users?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get next 10 users (pagination)
curl -X GET "http://localhost:8000/api/v1/users?skip=10&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get User by ID

Get a specific user by ID.

**Endpoint:** `GET /api/v1/users/{user_id}`

**Response (200):**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-09T12:00:00Z",
  "updated_at": "2025-01-09T14:30:00Z",
  "roles": [...]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
USER_ID="uuid-here"

curl -X GET "http://localhost:8000/api/v1/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Create User

Create a new user (admin only).

**Endpoint:** `POST /api/v1/users`

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "secure123",
  "full_name": "New User",
  "is_active": true,
  "is_superuser": false
}
```

**Response (200):**
```json
{
  "id": "new-uuid",
  "email": "newuser@example.com",
  "full_name": "New User",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-09T15:00:00Z",
  "roles": []
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@example.com",
    "password": "SecurePass123!",
    "full_name": "Manager User",
    "is_active": true,
    "is_superuser": false
  }'
```

---

### Update User

Update an existing user.

**Endpoint:** `PUT /api/v1/users/{user_id}`

**Request Body:**
```json
{
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "is_active": true
}
```

**Response (200):**
```json
{
  "id": "uuid-here",
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "is_active": true,
  "is_superuser": false,
  "updated_at": "2025-01-09T16:00:00Z",
  "roles": [...]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
USER_ID="uuid-here"

curl -X PUT "http://localhost:8000/api/v1/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Full Name",
    "is_active": true
  }'
```

---

### Delete User

Delete a user (soft delete).

**Endpoint:** `DELETE /api/v1/users/{user_id}`

**Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
USER_ID="uuid-here"

curl -X DELETE "http://localhost:8000/api/v1/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Update User Roles

Assign roles to a user.

**Endpoint:** `PUT /api/v1/users/{user_id}/roles`

**Request Body:**
```json
{
  "role_ids": ["role-uuid-1", "role-uuid-2"]
}
```

**Response (200):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "User Name",
  "roles": [
    {
      "id": "role-uuid-1",
      "name": "manager",
      "description": "Manager Role"
    },
    {
      "id": "role-uuid-2",
      "name": "editor",
      "description": "Editor Role"
    }
  ]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
USER_ID="user-uuid"

curl -X PUT "http://localhost:8000/api/v1/users/$USER_ID/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_ids": ["role-uuid-1", "role-uuid-2"]
  }'
```

---

## Role Management

All role management endpoints require admin privileges (`role:*` or `*:*` permission).

### List Roles

Get all roles with their permissions.

**Endpoint:** `GET /api/v1/roles`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 20)

**Response (200):**
```json
{
  "items": [
    {
      "id": "role-uuid-1",
      "name": "admin",
      "description": "Administrator",
      "priority": 1000,
      "is_system_role": true,
      "created_at": "2025-01-09T12:00:00Z",
      "permissions": [
        {
          "id": "perm-uuid",
          "code": "*:*",
          "name": "Full Access",
          "resource": "*",
          "action": "*"
        }
      ]
    },
    {
      "id": "role-uuid-2",
      "name": "user",
      "description": "Standard User",
      "priority": 100,
      "is_system_role": true,
      "permissions": [...]
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 20
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

curl -X GET "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer $TOKEN"
```

**With Language (i18n):**
```bash
curl -X GET "http://localhost:8000/api/v1/roles?lang=ar" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Role by ID

Get a specific role with all its permissions.

**Endpoint:** `GET /api/v1/roles/{role_id}`

**Response (200):**
```json
{
  "id": "role-uuid",
  "name": "manager",
  "description": "Manager Role",
  "priority": 500,
  "is_system_role": false,
  "created_at": "2025-01-09T12:00:00Z",
  "permissions": [
    {
      "id": "perm-1",
      "code": "user:read",
      "name": "Read Users",
      "resource": "user",
      "action": "read"
    },
    {
      "id": "perm-2",
      "code": "user:create",
      "name": "Create Users",
      "resource": "user",
      "action": "create"
    }
  ]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
ROLE_ID="role-uuid"

curl -X GET "http://localhost:8000/api/v1/roles/$ROLE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Create Role

Create a new role.

**Endpoint:** `POST /api/v1/roles`

**Request Body:**
```json
{
  "name": "editor",
  "description": "Content Editor",
  "priority": 300
}
```

**Response (200):**
```json
{
  "id": "new-role-uuid",
  "name": "editor",
  "description": "Content Editor",
  "priority": 300,
  "is_system_role": false,
  "created_at": "2025-01-09T15:00:00Z",
  "permissions": []
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

curl -X POST "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "support",
    "description": "Customer Support",
    "priority": 200
  }'
```

---

### Update Role

Update an existing role.

**Endpoint:** `PUT /api/v1/roles/{role_id}`

**Request Body:**
```json
{
  "name": "senior_editor",
  "description": "Senior Content Editor",
  "priority": 400
}
```

**Response (200):**
```json
{
  "id": "role-uuid",
  "name": "senior_editor",
  "description": "Senior Content Editor",
  "priority": 400,
  "is_system_role": false,
  "updated_at": "2025-01-09T16:00:00Z",
  "permissions": [...]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
ROLE_ID="role-uuid"

curl -X PUT "http://localhost:8000/api/v1/roles/$ROLE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated Description",
    "priority": 450
  }'
```

---

### Delete Role

Delete a role (cannot delete system roles).

**Endpoint:** `DELETE /api/v1/roles/{role_id}`

**Response (200):**
```json
{
  "message": "Role deleted successfully"
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
ROLE_ID="role-uuid"

curl -X DELETE "http://localhost:8000/api/v1/roles/$ROLE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Update Role Permissions

Assign permissions to a role.

**Endpoint:** `PUT /api/v1/roles/{role_id}/permissions`

**Request Body:**
```json
{
  "permission_ids": ["perm-uuid-1", "perm-uuid-2", "perm-uuid-3"]
}
```

**Response (200):**
```json
{
  "id": "role-uuid",
  "name": "editor",
  "description": "Content Editor",
  "permissions": [
    {
      "id": "perm-uuid-1",
      "code": "post:create",
      "name": "Create Posts"
    },
    {
      "id": "perm-uuid-2",
      "code": "post:update",
      "name": "Update Posts"
    },
    {
      "id": "perm-uuid-3",
      "code": "post:read",
      "name": "Read Posts"
    }
  ]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
ROLE_ID="role-uuid"

curl -X PUT "http://localhost:8000/api/v1/roles/$ROLE_ID/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permission_ids": ["perm-1", "perm-2", "perm-3"]
  }'
```

---

## Audit Logs

Query and analyze audit logs (admin only).

### List Audit Logs

Get paginated audit logs with optional filters.

**Endpoint:** `GET /api/v1/audit/logs`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 50)
- `user_id` (optional): Filter by user ID
- `action` (optional): Filter by action (e.g., "USER_LOGIN", "USER_CREATED")
- `resource_type` (optional): Filter by resource type
- `start_date` (optional): Filter logs after this date (ISO format)
- `end_date` (optional): Filter logs before this date (ISO format)
- `success` (optional): Filter by success status (true/false)

**Response (200):**
```json
{
  "items": [
    {
      "id": "log-uuid-1",
      "user_id": "user-uuid",
      "action": "USER_LOGIN",
      "resource_type": "user",
      "resource_id": "user-uuid",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "error_message": null,
      "created_at": "2025-01-09T14:30:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

# Get all logs
curl -X GET "http://localhost:8000/api/v1/audit/logs" \
  -H "Authorization: Bearer $TOKEN"

# Filter by action
curl -X GET "http://localhost:8000/api/v1/audit/logs?action=USER_LOGIN" \
  -H "Authorization: Bearer $TOKEN"

# Filter by user and date range
curl -X GET "http://localhost:8000/api/v1/audit/logs?user_id=user-uuid&start_date=2025-01-01T00:00:00Z&end_date=2025-01-09T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"

# Filter failed actions only
curl -X GET "http://localhost:8000/api/v1/audit/logs?success=false" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Audit Log by ID

Get a specific audit log entry.

**Endpoint:** `GET /api/v1/audit/logs/{log_id}`

**Response (200):**
```json
{
  "id": "log-uuid",
  "user_id": "user-uuid",
  "action": "USER_UPDATED",
  "resource_type": "user",
  "resource_id": "target-user-uuid",
  "changes": {
    "before": {
      "full_name": "Old Name",
      "is_active": true
    },
    "after": {
      "full_name": "New Name",
      "is_active": true
    }
  },
  "ip_address": "192.168.1.1",
  "user_agent": "curl/7.64.1",
  "success": true,
  "error_message": null,
  "created_at": "2025-01-09T14:30:00Z"
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
LOG_ID="log-uuid"

curl -X GET "http://localhost:8000/api/v1/audit/logs/$LOG_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Audit Statistics

Get audit log statistics.

**Endpoint:** `GET /api/v1/audit/stats`

**Query Parameters:**
- `start_date` (optional): Start date for statistics
- `end_date` (optional): End date for statistics

**Response (200):**
```json
{
  "total_logs": 1523,
  "actions_breakdown": {
    "USER_LOGIN": 450,
    "USER_LOGOUT": 430,
    "USER_CREATED": 25,
    "USER_UPDATED": 80,
    "USER_DELETED": 5,
    "ROLE_CREATED": 10,
    "ROLE_UPDATED": 15
  },
  "success_rate": 98.5,
  "failed_attempts": 23,
  "unique_users": 45,
  "date_range": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-09T23:59:59Z"
  }
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

# Get all-time stats
curl -X GET "http://localhost:8000/api/v1/audit/stats" \
  -H "Authorization: Bearer $TOKEN"

# Get stats for specific period
curl -X GET "http://localhost:8000/api/v1/audit/stats?start_date=2025-01-01T00:00:00Z&end_date=2025-01-09T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get User Activity

Get activity history for a specific user.

**Endpoint:** `GET /api/v1/audit/user/{user_id}/activity`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 50)

**Response (200):**
```json
{
  "user_id": "user-uuid",
  "items": [
    {
      "id": "log-uuid-1",
      "action": "USER_LOGIN",
      "ip_address": "192.168.1.1",
      "success": true,
      "created_at": "2025-01-09T14:30:00Z"
    },
    {
      "id": "log-uuid-2",
      "action": "USER_UPDATED",
      "resource_id": "other-user-uuid",
      "success": true,
      "created_at": "2025-01-09T14:25:00Z"
    }
  ],
  "total": 87,
  "skip": 0,
  "limit": 50
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."
USER_ID="user-uuid"

curl -X GET "http://localhost:8000/api/v1/audit/user/$USER_ID/activity" \
  -H "Authorization: Bearer $TOKEN"
```

---

### List Audit Actions

Get list of all available audit action types.

**Endpoint:** `GET /api/v1/audit/actions`

**Response (200):**
```json
{
  "actions": [
    "USER_LOGIN",
    "USER_LOGOUT",
    "USER_CREATED",
    "USER_UPDATED",
    "USER_DELETED",
    "USER_ROLE_UPDATED",
    "ROLE_CREATED",
    "ROLE_UPDATED",
    "ROLE_DELETED",
    "ROLE_PERMISSION_UPDATED"
  ]
}
```

**Example:**
```bash
TOKEN="eyJhbGc..."

curl -X GET "http://localhost:8000/api/v1/audit/actions" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Internationalization

The API supports multiple languages via query parameters or headers.

### Language Detection Priority

1. **Query Parameter** `?lang=ar`
2. **Accept-Language Header** `Accept-Language: ar`
3. **Default**: English (`en`)

### Supported Languages

- `en` - English
- `ar` - Arabic

### Examples

**Using Query Parameter:**
```bash
TOKEN="eyJhbGc..."

# Get roles in Arabic
curl -X GET "http://localhost:8000/api/v1/roles?lang=ar" \
  -H "Authorization: Bearer $TOKEN"

# Get roles in English (default)
curl -X GET "http://localhost:8000/api/v1/roles?lang=en" \
  -H "Authorization: Bearer $TOKEN"
```

**Using Accept-Language Header:**
```bash
TOKEN="eyJhbGc..."

curl -X GET "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept-Language: ar"
```

**Response with Translation:**
```json
{
  "items": [
    {
      "id": "role-uuid",
      "name": "admin",
      "description": "مدير النظام",
      "permissions": [...]
    }
  ],
  "message": "تم جلب الأدوار بنجاح"
}
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Email already exists |
| 422 | Validation Error | Pydantic validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Examples

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Unauthorized (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Forbidden (403):**
```json
{
  "detail": "Not enough permissions"
}
```

**Rate Limit (429):**
```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1704801600
```

### Endpoint-Specific Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/auth/login` | 5 requests | 1 minute |
| `/api/v1/auth/register` | 3 requests | 1 minute |
| `/api/v1/auth/refresh` | 10 requests | 1 minute |
| General endpoints | 100 requests | 1 minute |

### Handling Rate Limits

```bash
# Check rate limit status
curl -i -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"wrong"}'

# Response headers:
# X-RateLimit-Limit: 5
# X-RateLimit-Remaining: 4
# X-RateLimit-Reset: 1704801660

# If exceeded:
# HTTP/1.1 429 Too Many Requests
# {"detail": "Rate limit exceeded: 5 per 1 minute"}
```

---

## Python Client Examples

### Using Requests Library

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "test@example.com",
        "password": "secure123",
        "full_name": "Test User"
    }
)
user = response.json()
print(f"Registered user: {user['email']}")

# 2. Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "test@example.com",
        "password": "secure123"
    }
)
tokens = response.json()
access_token = tokens["access_token"]

# 3. Get current user
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
current_user = response.json()
print(f"Current user: {current_user['email']}")

# 4. List users (admin only)
response = requests.get(
    f"{BASE_URL}/users",
    headers=headers,
    params={"skip": 0, "limit": 10}
)
users_page = response.json()
print(f"Total users: {users_page['total']}")

# 5. Create user (admin only)
response = requests.post(
    f"{BASE_URL}/users",
    headers=headers,
    json={
        "email": "newuser@example.com",
        "password": "pass123",
        "full_name": "New User"
    }
)
new_user = response.json()

# 6. Update user
user_id = new_user["id"]
response = requests.put(
    f"{BASE_URL}/users/{user_id}",
    headers=headers,
    json={"full_name": "Updated Name"}
)

# 7. Get audit logs
response = requests.get(
    f"{BASE_URL}/audit/logs",
    headers=headers,
    params={"action": "USER_LOGIN", "limit": 5}
)
logs = response.json()

# 8. Logout
response = requests.post(
    f"{BASE_URL}/auth/logout",
    headers=headers
)
print("Logged out successfully")
```

### Using HTTPX (Async)

```python
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "admin@example.com",
                "password": "changeme123"
            }
        )
        tokens = response.json()
        access_token = tokens["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Get users
        response = await client.get(
            f"{BASE_URL}/users",
            headers=headers
        )
        users = response.json()
        print(f"Found {users['total']} users")

asyncio.run(main())
```

---

## Complete Workflow Example

### Full User Management Workflow

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

# 1. Login as admin
echo "=== Logging in as admin ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "changeme123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Got token: ${TOKEN:0:20}..."

# 2. Create a new role
echo -e "\n=== Creating new role ==="
ROLE_RESPONSE=$(curl -s -X POST "$BASE_URL/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "content_manager",
    "description": "Content Manager",
    "priority": 400
  }')

ROLE_ID=$(echo $ROLE_RESPONSE | jq -r '.id')
echo "Created role: $ROLE_ID"

# 3. Create a new user
echo -e "\n=== Creating new user ==="
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@example.com",
    "password": "secure123",
    "full_name": "Content Manager"
  }')

USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
echo "Created user: $USER_ID"

# 4. Assign role to user
echo -e "\n=== Assigning role to user ==="
curl -s -X PUT "$BASE_URL/users/$USER_ID/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"role_ids\": [\"$ROLE_ID\"]
  }" | jq '.'

# 5. Get audit logs
echo -e "\n=== Recent audit logs ==="
curl -s -X GET "$BASE_URL/audit/logs?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[] | {action, created_at}'

# 6. Logout
echo -e "\n=== Logging out ==="
curl -s -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo -e "\n=== Workflow complete ==="
```

---

## Additional Resources

- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **I18N Guide**: See [I18N_GUIDE.md](../I18N_GUIDE.md)
- **Development Guide**: See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Need Help?** Check the [README.md](../README.md) or open an issue on GitHub.

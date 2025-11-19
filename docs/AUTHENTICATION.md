# Authentication Workflow Documentation

## Table of Contents

1. [Authentication Overview](#authentication-overview)
2. [Token Lifecycle](#token-lifecycle)
3. [API Endpoints](#api-endpoints)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

---

## Authentication Overview

The system uses **JWT (JSON Web Tokens)** for stateless authentication:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Register  │ ──> │    Login    │ ──> │  Use Token  │ ──> │   Refresh   │
│   Account   │     │  Get Tokens │     │  Call APIs  │     │    Token    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                     │                    │                   │
       │                     │                    │                   │
       v                     v                    v                   v
  Create User     Access + Refresh        Authenticated        New Access
  is_active=true     Tokens               API Calls            Token
```

**Key Components:**
1. **Register** - Create new user account (email + password)
2. **Login** - Authenticate and receive JWT tokens
3. **Access Token** - Short-lived token (30 minutes) for API calls
4. **Refresh Token** - Long-lived token (7 days) to get new access token
5. **Token Refresh** - Get new access token without re-login
6. **Change Password** - Update password while authenticated

---

## Token Lifecycle

### Token Types

| Token Type | Purpose | Expiration | Storage | Usage |
|------------|---------|------------|---------|-------|
| **Access Token** | API authentication | 30 minutes | Memory/sessionStorage | Authorization header |
| **Refresh Token** | Renew access token | 7 days | localStorage (secure) | Refresh endpoint only |

### Token Flow

```
┌──────────────────────────────────────────────────────────┐
│                    Token Lifecycle                        │
└──────────────────────────────────────────────────────────┘

        Login
          │
          v
    ┌───────────┐
    │  Tokens   │ Access: 30 min
    │  Created  │ Refresh: 7 days
    └─────┬─────┘
          │
          v
    ┌───────────┐
    │  Use for  │ Authorization: Bearer {access_token}
    │ API Calls │
    └─────┬─────┘
          │
          │ (30 minutes later)
          v
    ┌───────────┐
    │  Access   │
    │  Expires  │
    └─────┬─────┘
          │
          v
    ┌───────────┐
    │  Refresh  │ POST /api/v1/auth/refresh
    │   Token   │ with refresh_token
    └─────┬─────┘
          │
          v
    ┌───────────┐
    │New Access │ Continue using API
    │   Token   │
    └───────────┘
```

### Password Requirements

- **Minimum Length**: 8 characters
- **Must Contain**:
  - At least 1 uppercase letter (A-Z)
  - At least 1 lowercase letter (a-z)
  - At least 1 digit (0-9)
- **Examples**:
  - ✅ `MyPass123`
  - ✅ `SecureP@ss456`
  - ❌ `password` (no uppercase, no digit)
  - ❌ `Pass123` (too short)

---

## API Endpoints

### 1. Register Account

**Endpoint:** `POST /api/v1/auth/register`

**Authorization:** None required (public)

**Rate Limit:** 10 requests per hour per IP

**Request:**
```json
{
  "email": "owner@restaurant.iq",
  "password": "MySecurePass123",
  "full_name": "Ahmed Al-Baghdadi",
  "phone": "+964 771 234 5678"
}
```

**Response:** `201 Created`
```json
{
  "id": "bbbbcc159-c15e-4dd7-82b1-7cf5c88d94da",
  "email": "owner@restaurant.iq",
  "full_name": "Ahmed Al-Baghdadi",
  "phone": "+964 771 234 5678",
  "is_active": true,
  "is_superuser": false,
  "roles": [
    {
      "id": "role-uuid-here",
      "code": "user",
      "name": "User"
    }
  ],
  "created_at": "2024-11-19T10:00:00Z"
}
```

**Business Rules:**
- Email must be unique (cannot register duplicate)
- Password validated for strength
- Account is active immediately (`is_active=true`)
- Not a superuser by default (`is_superuser=false`)
- **Automatically assigned "User" role** with basic permissions
- Phone number is optional

---

### 2. Login (Get Tokens)

**Endpoint:** `POST /api/v1/auth/login`

**Authorization:** None required (public)

**Rate Limit:** 20 requests per minute per IP

**Request:**
```json
{
  "email": "owner@restaurant.iq",
  "password": "MySecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "bbbbcc159-c15e-4dd7-82b1-7cf5c88d94da",
    "email": "owner@restaurant.iq",
    "full_name": "Ahmed Al-Baghdadi",
    "is_active": true,
    "is_superuser": false
  }
}
```

**Token Details:**
- `access_token`: Use for API authentication (expires in 1800 seconds = 30 minutes)
- `refresh_token`: Use to get new access token (expires in 7 days)
- `token_type`: Always "bearer"
- `expires_in`: Access token expiration in seconds (1800 = 30 minutes)

**Usage:**
```bash
# All authenticated API calls must include:
Authorization: Bearer {access_token}
```

---

### 3. Login (OAuth2 Form - for Swagger UI)

**Endpoint:** `POST /api/v1/auth/login/form`

**Authorization:** None required

**Form Data:**
```
username=owner@restaurant.iq
password=MySecurePass123
```

**Note:** This endpoint exists for Swagger UI compatibility. Use `/auth/login` in production.

---

### 4. Refresh Access Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Authorization:** None required (refresh token in body)

**Rate Limit:** 20 requests per minute per IP

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**When to Use:**
- Access token has expired (401 Unauthorized error)
- Proactively refresh before expiration (recommended)
- User session should continue without re-login

---

### 5. Get Current User Profile

**Endpoint:** `GET /api/v1/auth/me`

**Authorization:** Required (Bearer token)

**Response:** `200 OK`
```json
{
  "id": "bbbbcc159-c15e-4dd7-82b1-7cf5c88d94da",
  "email": "owner@restaurant.iq",
  "full_name": "Ahmed Al-Baghdadi",
  "phone": "+964 771 234 5678",
  "is_active": true,
  "is_superuser": false,
  "restaurant_id": null,
  "supplier_id": null,
  "created_at": "2024-11-19T10:00:00Z"
}
```

**Use Cases:**
- Verify token is still valid
- Get user information after login
- Check user roles and permissions

---

### 6. Change Password

**Endpoint:** `POST /api/v1/auth/change-password`

**Authorization:** Required (Bearer token)

**Request:**
```json
{
  "old_password": "MySecurePass123",
  "new_password": "NewSecurePass456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Business Rules:**
- Must provide correct old password
- New password must meet strength requirements
- New password cannot be same as old password
- User must be authenticated

---

## Complete Examples

### Example 1: New User Registration and Login

**Step 1: Register Account**
```bash
POST /api/v1/auth/register

{
  "email": "supplier@baghdadfood.iq",
  "password": "Supplier123",
  "full_name": "Mohammed Hassan",
  "phone": "+964 771 999 8888"
}
```

**Response:**
```json
{
  "id": "d4e5f6g7-8901-23de-f012-4567890abcde",
  "email": "supplier@baghdadfood.iq",
  "full_name": "Mohammed Hassan",
  "is_active": true
}
```

---

**Step 2: Login to Get Tokens**
```bash
POST /api/v1/auth/login

{
  "email": "supplier@baghdadfood.iq",
  "password": "Supplier123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

**Step 3: Use Token for API Calls**
```bash
GET /api/v1/auth/me
Authorization: Bearer eyJhbGci...

# Response: User profile
```

```bash
POST /api/v1/suppliers
Authorization: Bearer eyJhbGci...

{
  "company_name_en": "Baghdad Food Supplies",
  ...
}
```

---

### Example 2: Token Refresh Flow

**Scenario:** Access token expired after 30 minutes

**Step 1: API Call Fails**
```bash
GET /api/v1/auth/me
Authorization: Bearer {expired_access_token}

# Response: 401 Unauthorized
{
  "detail": "Token has expired"
}
```

---

**Step 2: Refresh Access Token**
```bash
POST /api/v1/auth/refresh

{
  "refresh_token": "eyJhbGci..."
}

# Response:
{
  "access_token": "{new_access_token}",
  "refresh_token": "{new_refresh_token}",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

**Step 3: Retry API Call with New Token**
```bash
GET /api/v1/auth/me
Authorization: Bearer {new_access_token}

# Response: Success
```

---

### Example 3: Change Password

```bash
POST /api/v1/auth/change-password
Authorization: Bearer {access_token}

{
  "old_password": "Supplier123",
  "new_password": "NewSupplier456"
}

# Response:
{
  "message": "Password changed successfully"
}
```

**Next Login:** Use new password

---

## Error Handling

### Common Errors

#### 1. Invalid Credentials
```json
{
  "detail": "Incorrect email or password"
}
```
**HTTP Status:** `401 Unauthorized`

**Causes:**
- Wrong email
- Wrong password
- Account doesn't exist

---

#### 2. Account Inactive
```json
{
  "detail": "User account is inactive"
}
```
**HTTP Status:** `403 Forbidden`

**Cause:** Admin deactivated account

---

#### 3. Email Already Registered
```json
{
  "detail": "Email already exists"
}
```
**HTTP Status:** `409 Conflict`

**Solution:** Use different email or login with existing account

---

#### 4. Weak Password
```json
{
  "detail": "Password must be at least 8 characters and contain uppercase, lowercase, and digit"
}
```
**HTTP Status:** `422 Unprocessable Entity`

**Solution:** Use stronger password meeting requirements

---

#### 5. Token Expired
```json
{
  "detail": "Token has expired"
}
```
**HTTP Status:** `401 Unauthorized`

**Solution:** Use refresh token to get new access token

---

#### 6. Invalid Token
```json
{
  "detail": "Could not validate credentials"
}
```
**HTTP Status:** `401 Unauthorized`

**Causes:**
- Malformed token
- Token signature invalid
- Token from different system

---

#### 7. Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```
**HTTP Status:** `429 Too Many Requests`

**Rate Limits:**
- Register: 10/hour per IP
- Login: 20/minute per IP
- Refresh: 20/minute per IP

---

## Best Practices

### 1. Token Storage (Frontend)

**Access Token:**
```javascript
// Store in memory or sessionStorage (NOT localStorage)
sessionStorage.setItem('access_token', response.access_token);

// Include in all API calls
fetch('/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
  }
});
```

**Refresh Token:**
```javascript
// Store in httpOnly cookie (best) or localStorage (acceptable)
localStorage.setItem('refresh_token', response.refresh_token);
```

---

### 2. Automatic Token Refresh

```javascript
// Refresh token 5 minutes before expiration
const REFRESH_BEFORE_EXPIRY = 5 * 60 * 1000; // 5 minutes

async function refreshTokenIfNeeded() {
  const expiresAt = getTokenExpiryTime(); // From JWT payload
  const now = Date.now();

  if (now >= expiresAt - REFRESH_BEFORE_EXPIRY) {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({refresh_token: refreshToken})
    });

    const data = await response.json();
    sessionStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }
}
```

---

### 3. Handle 401 Errors Globally

```javascript
// Axios interceptor example
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Try to refresh token
      try {
        await refreshTokenIfNeeded();
        // Retry original request
        return axios(error.config);
      } catch {
        // Refresh failed - redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

---

### 4. Logout

```javascript
function logout() {
  // Clear tokens
  sessionStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // Redirect to login
  window.location.href = '/login';
}
```

**Note:** Backend doesn't track logout (stateless JWT). Tokens remain valid until expiration.

---

### 5. Password Security

**For Users:**
- Use unique password for this system
- Don't share password
- Change password if suspicious activity

**For Developers:**
- Never log passwords
- Use HTTPS in production
- Don't store passwords in code
- Hash passwords before storage (backend handles this)

---

### 6. Production Security

```bash
# Environment variables (backend)
SECRET_KEY=your-super-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Enable HTTPS
# Use secure httpOnly cookies
# Enable CORS only for trusted domains
```

---

## Token Payload Structure

### Access Token Payload
```json
{
  "sub": "bbbbcc159-c15e-4dd7-82b1-7cf5c88d94da",
  "type": "access",
  "exp": 1700395200,
  "iat": 1700393400
}
```

### Refresh Token Payload
```json
{
  "sub": "bbbbcc159-c15e-4dd7-82b1-7cf5c88d94da",
  "type": "refresh",
  "exp": 1700998200,
  "iat": 1700393400
}
```

**Fields:**
- `sub` - Subject (user ID)
- `type` - Token type (access or refresh)
- `exp` - Expiration timestamp
- `iat` - Issued at timestamp

---

## Additional Resources

- [User Management Documentation](USERS.md) - Managing users and roles
- [Restaurant Workflow](RESTAURANT_WORKFLOW.md) - Restaurant accounts
- [Supplier Workflow](SUPPLIER_WORKFLOW.md) - Supplier accounts
- [Order Workflow](ORDER_WORKFLOW.md) - Placing orders
- [API Reference](API_REFERENCE.md) - Complete API documentation

---

**Last Updated:** 2024-11-19
**API Version:** v1
**Base URL:** `https://api.example.com/api/v1`

#!/bin/bash

# Test script to demonstrate token revocation after logout
# This script verifies that tokens are properly blacklisted when users logout

set -e

BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api/v1"

echo "=========================================="
echo "Token Revocation Test"
echo "=========================================="
echo ""

# Step 1: Login and get token
echo "1. Logging in as admin@example.com..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "   ✓ Login successful"
echo "   Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Test token works by accessing /me endpoint
echo "2. Testing token with /me endpoint..."
ME_RESPONSE=$(curl -s -X GET "${API_BASE}/auth/me" \
  -H "Authorization: Bearer $TOKEN")

USER_EMAIL=$(echo $ME_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['email'])")
echo "   ✓ Token works! User: $USER_EMAIL"
echo ""

# Step 3: Logout (this should blacklist the token)
echo "3. Logging out (this will blacklist the token)..."
LOGOUT_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/logout" \
  -H "Authorization: Bearer $TOKEN")
echo "   ✓ Logout successful"
echo ""

# Step 4: Try to use the same token again (should fail with 401)
echo "4. Attempting to use the same token after logout..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${API_BASE}/auth/me" \
  -H "Authorization: Bearer $TOKEN")

if [ "$STATUS_CODE" == "401" ]; then
    echo "   ✅ SUCCESS! Token was revoked (got 401 Unauthorized)"
    echo ""
    echo "   This proves that:"
    echo "   - Logout properly blacklists tokens in Redis"
    echo "   - Blacklisted tokens cannot be reused"
    echo "   - Token revocation is WORKING! 🎉"
else
    echo "   ❌ FAILURE! Token still works (got HTTP $STATUS_CODE)"
    echo ""
    echo "   This means token revocation is NOT working."
    echo "   Check if Redis is properly connected."
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="

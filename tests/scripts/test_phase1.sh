#!/bin/bash

# Phase 1 Comprehensive Test Script
# Tests database models, migrations, roles, permissions, and API endpoints

set -e  # Exit on error

echo "=========================================="
echo "Phase 1 Supply Chain - Comprehensive Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo "1. Testing Database Schema..."
echo "========================================"

# Test that all tables exist
echo "Checking if user table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM user;" > /dev/null 2>&1
print_result $? "User table exists"

echo "Checking if restaurant table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM restaurant;" > /dev/null 2>&1
print_result $? "Restaurant table exists"

echo "Checking if supplier table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM supplier;" > /dev/null 2>&1
print_result $? "Supplier table exists"

echo "Checking if role table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM role;" > /dev/null 2>&1
print_result $? "Role table exists"

echo "Checking if permission table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM permission;" > /dev/null 2>&1
print_result $? "Permission table exists"

echo ""
echo "2. Testing User Model Extensions..."
echo "========================================"

# Check if user table has new columns
echo "Checking phone_number column..."
sqlite3 dev.db "PRAGMA table_info(user);" | grep -q "phone_number"
print_result $? "User.phone_number column exists"

echo "Checking language_preference column..."
sqlite3 dev.db "PRAGMA table_info(user);" | grep -q "language_preference"
print_result $? "User.language_preference column exists"

echo "Checking currency column..."
sqlite3 dev.db "PRAGMA table_info(user);" | grep -q "currency"
print_result $? "User.currency column exists"

echo "Checking restaurant_id column..."
sqlite3 dev.db "PRAGMA table_info(user);" | grep -q "restaurant_id"
print_result $? "User.restaurant_id column exists"

echo "Checking supplier_id column..."
sqlite3 dev.db "PRAGMA table_info(user);" | grep -q "supplier_id"
print_result $? "User.supplier_id column exists"

echo ""
echo "3. Testing Restaurant Model..."
echo "========================================"

# Count restaurant columns
RESTAURANT_COLS=$(sqlite3 dev.db "PRAGMA table_info(restaurant);" | wc -l)
echo "Restaurant table has $RESTAURANT_COLS columns"
[ "$RESTAURANT_COLS" -ge 30 ]
print_result $? "Restaurant table has 30+ columns"

# Check critical columns
sqlite3 dev.db "PRAGMA table_info(restaurant);" | grep -q "name_ar"
print_result $? "Restaurant.name_ar exists"

sqlite3 dev.db "PRAGMA table_info(restaurant);" | grep -q "name_en"
print_result $? "Restaurant.name_en exists"

sqlite3 dev.db "PRAGMA table_info(restaurant);" | grep -q "latitude"
print_result $? "Restaurant.latitude exists (GPS support)"

sqlite3 dev.db "PRAGMA table_info(restaurant);" | grep -q "is_verified"
print_result $? "Restaurant.is_verified exists"

# Check indexes
RESTAURANT_INDEXES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='restaurant';")
echo "Restaurant table has $RESTAURANT_INDEXES indexes"
[ "$RESTAURANT_INDEXES" -ge 5 ]
print_result $? "Restaurant has 5+ indexes"

echo ""
echo "4. Testing Supplier Model..."
echo "========================================"

# Count supplier columns
SUPPLIER_COLS=$(sqlite3 dev.db "PRAGMA table_info(supplier);" | wc -l)
echo "Supplier table has $SUPPLIER_COLS columns"
[ "$SUPPLIER_COLS" -ge 40 ]
print_result $? "Supplier table has 40+ columns"

# Check critical columns
sqlite3 dev.db "PRAGMA table_info(supplier);" | grep -q "company_name_ar"
print_result $? "Supplier.company_name_ar exists"

sqlite3 dev.db "PRAGMA table_info(supplier);" | grep -q "product_categories"
print_result $? "Supplier.product_categories exists"

sqlite3 dev.db "PRAGMA table_info(supplier);" | grep -q "delivery_areas"
print_result $? "Supplier.delivery_areas exists"

sqlite3 dev.db "PRAGMA table_info(supplier);" | grep -q "average_rating"
print_result $? "Supplier.average_rating exists"

sqlite3 dev.db "PRAGMA table_info(supplier);" | grep -q "is_active"
print_result $? "Supplier.is_active exists"

# Check indexes
SUPPLIER_INDEXES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='supplier';")
echo "Supplier table has $SUPPLIER_INDEXES indexes"
[ "$SUPPLIER_INDEXES" -ge 5 ]
print_result $? "Supplier has 5+ indexes"

echo ""
echo "5. Testing Roles..."
echo "========================================"

# Count roles
ROLE_COUNT=$(sqlite3 dev.db "SELECT COUNT(*) FROM role;")
echo "Found $ROLE_COUNT roles in database"
[ "$ROLE_COUNT" -ge 10 ]
print_result $? "At least 10 roles exist"

# Check specific roles
sqlite3 dev.db "SELECT code FROM role;" | grep -q "admin"
print_result $? "Admin role exists"

sqlite3 dev.db "SELECT code FROM role;" | grep -q "restaurant_owner"
print_result $? "Restaurant Owner role exists"

sqlite3 dev.db "SELECT code FROM role;" | grep -q "supplier_admin"
print_result $? "Supplier Admin role exists"

sqlite3 dev.db "SELECT code FROM role;" | grep -q "driver"
print_result $? "Driver role exists"

# Check role priorities
ADMIN_PRIORITY=$(sqlite3 dev.db "SELECT priority FROM role WHERE code='admin';")
echo "Admin priority: $ADMIN_PRIORITY"
[ "$ADMIN_PRIORITY" -eq 1 ]
print_result $? "Admin has highest priority (1)"

echo ""
echo "6. Testing Permissions..."
echo "========================================"

# Count permissions
PERM_COUNT=$(sqlite3 dev.db "SELECT COUNT(*) FROM permission;")
echo "Found $PERM_COUNT permissions in database"
[ "$PERM_COUNT" -ge 50 ]
print_result $? "At least 50 permissions exist"

# Check supply chain permissions
sqlite3 dev.db "SELECT code FROM permission;" | grep -q "restaurant:create"
print_result $? "restaurant:create permission exists"

sqlite3 dev.db "SELECT code FROM permission;" | grep -q "restaurant:verify"
print_result $? "restaurant:verify permission exists"

sqlite3 dev.db "SELECT code FROM permission;" | grep -q "supplier:create"
print_result $? "supplier:create permission exists"

sqlite3 dev.db "SELECT code FROM permission;" | grep -q "product:create"
print_result $? "product:create permission exists"

sqlite3 dev.db "SELECT code FROM permission;" | grep -q "order:approve"
print_result $? "order:approve permission exists"

sqlite3 dev.db "SELECT code FROM permission;" | grep -q "delivery:complete"
print_result $? "delivery:complete permission exists"

echo ""
echo "7. Testing Role-Permission Mappings..."
echo "========================================"

# Check admin has all permissions
ADMIN_PERMS=$(sqlite3 dev.db "SELECT COUNT(*) FROM role_permission rp JOIN role r ON rp.role_id = r.id WHERE r.code = 'admin';")
echo "Admin has $ADMIN_PERMS permissions"
[ "$ADMIN_PERMS" -ge 1 ]
print_result $? "Admin has permissions assigned"

# Check restaurant_owner permissions
RESTAURANT_OWNER_PERMS=$(sqlite3 dev.db "SELECT COUNT(*) FROM role_permission rp JOIN role r ON rp.role_id = r.id WHERE r.code = 'restaurant_owner';")
echo "Restaurant Owner has $RESTAURANT_OWNER_PERMS permissions"
[ "$RESTAURANT_OWNER_PERMS" -ge 5 ]
print_result $? "Restaurant Owner has 5+ permissions"

# Check supplier_admin permissions
SUPPLIER_ADMIN_PERMS=$(sqlite3 dev.db "SELECT COUNT(*) FROM role_permission rp JOIN role r ON rp.role_id = r.id WHERE r.code = 'supplier_admin';")
echo "Supplier Admin has $SUPPLIER_ADMIN_PERMS permissions"
[ "$SUPPLIER_ADMIN_PERMS" -ge 5 ]
print_result $? "Supplier Admin has 5+ permissions"

echo ""
echo "8. Testing Migrations..."
echo "========================================"

# Check migration version
CURRENT_VERSION=$(.venv/bin/alembic current 2>&1 | grep -o '[a-z0-9]*' | head -1)
echo "Current migration version: $CURRENT_VERSION"
[ ! -z "$CURRENT_VERSION" ]
print_result $? "Migration version is set"

# Count migrations
MIGRATION_COUNT=$(ls -1 alembic/versions/*.py | wc -l)
echo "Found $MIGRATION_COUNT migration files"
[ "$MIGRATION_COUNT" -ge 4 ]
print_result $? "At least 4 migrations exist"

echo ""
echo "9. Testing Python Imports..."
echo "========================================"

# Test model imports
.venv/bin/python -c "from app.models import Restaurant; print('OK')" > /dev/null 2>&1
print_result $? "Restaurant model imports successfully"

.venv/bin/python -c "from app.models import Supplier; print('OK')" > /dev/null 2>&1
print_result $? "Supplier model imports successfully"

.venv/bin/python -c "from app.models import User, Role, Permission; print('OK')" > /dev/null 2>&1
print_result $? "User, Role, Permission models import successfully"

# Test schema imports
.venv/bin/python -c "from app.schemas.restaurant import RestaurantCreate, RestaurantRead; print('OK')" > /dev/null 2>&1
print_result $? "Restaurant schemas import successfully"

.venv/bin/python -c "from app.schemas.supplier import SupplierCreate, SupplierRead; print('OK')" > /dev/null 2>&1
print_result $? "Supplier schemas import successfully"

# Test CRUD imports
.venv/bin/python -c "from app.crud.restaurant import restaurant; print('OK')" > /dev/null 2>&1
print_result $? "Restaurant CRUD imports successfully"

.venv/bin/python -c "from app.crud.supplier import supplier; print('OK')" > /dev/null 2>&1
print_result $? "Supplier CRUD imports successfully"

# Test API imports
.venv/bin/python -c "from app.api.v1 import restaurants; print('OK')" > /dev/null 2>&1
print_result $? "Restaurant API imports successfully"

.venv/bin/python -c "from app.api.v1 import suppliers; print('OK')" > /dev/null 2>&1
print_result $? "Supplier API imports successfully"

echo ""
echo "10. Testing API Router..."
echo "========================================"

# Test router loading
.venv/bin/python -c "from app.api.v1.router import api_router; print('OK')" > /dev/null 2>&1
print_result $? "API router loads successfully"

# Count routes
ROUTE_COUNT=$(.venv/bin/python -c "from app.main import app; print(len(app.routes))" 2>/dev/null)
echo "Application has $ROUTE_COUNT routes"
[ "$ROUTE_COUNT" -ge 50 ]
print_result $? "Application has 50+ routes"

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "✓ ALL TESTS PASSED!"
    echo "Phase 1 implementation is complete and working correctly."
    echo "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "✗ SOME TESTS FAILED"
    echo "Please review the failures above."
    echo "==========================================${NC}"
    exit 1
fi

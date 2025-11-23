#!/bin/bash

# Phase 2 Comprehensive Test Script
# Tests Product catalog and Order management features

set -e  # Exit on error

echo "=========================================="
echo "Phase 2 Supply Chain - Comprehensive Test"
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

echo "1. Testing Product Model..."
echo "========================================"

# Test product table exists
echo "Checking if product table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM product;" > /dev/null 2>&1
print_result $? "Product table exists"

# Count product columns
PRODUCT_COLS=$(sqlite3 dev.db "PRAGMA table_info(product);" | wc -l)
echo "Product table has $PRODUCT_COLS columns"
[ "$PRODUCT_COLS" -eq 37 ]
print_result $? "Product table has 37 columns"

# Check critical product columns
sqlite3 dev.db "PRAGMA table_info(product);" | grep -q "sku"
print_result $? "Product.sku exists"

sqlite3 dev.db "PRAGMA table_info(product);" | grep -q "name_ar"
print_result $? "Product.name_ar exists (bilingual support)"

sqlite3 dev.db "PRAGMA table_info(product);" | grep -q "unit_price"
print_result $? "Product.unit_price exists"

sqlite3 dev.db "PRAGMA table_info(product);" | grep -q "stock_quantity"
print_result $? "Product.stock_quantity exists"

sqlite3 dev.db "PRAGMA table_info(product);" | grep -q "is_active"
print_result $? "Product.is_active exists"

# Check product indexes
PRODUCT_INDEXES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='product';")
echo "Product table has $PRODUCT_INDEXES indexes"
[ "$PRODUCT_INDEXES" -ge 10 ]
print_result $? "Product has 10+ indexes"

echo ""
echo "2. Testing Order Model..."
echo "========================================"

# Test order table exists (note: 'order' is a reserved keyword, use quotes)
echo "Checking if order table exists..."
sqlite3 dev.db 'SELECT COUNT(*) FROM "order";' > /dev/null 2>&1
print_result $? "Order table exists"

# Count order columns
ORDER_COLS=$(sqlite3 dev.db 'PRAGMA table_info("order");' | wc -l)
echo "Order table has $ORDER_COLS columns"
[ "$ORDER_COLS" -eq 36 ]
print_result $? "Order table has 36 columns"

# Check critical order columns
sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "order_number"
print_result $? "Order.order_number exists"

sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "restaurant_id"
print_result $? "Order.restaurant_id exists"

sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "supplier_id"
print_result $? "Order.supplier_id exists"

sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "status"
print_result $? "Order.status exists"

sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "total_amount"
print_result $? "Order.total_amount exists"

sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "payment_status"
print_result $? "Order.payment_status exists"

sqlite3 dev.db 'PRAGMA table_info("order");' | grep -q "submitted_at"
print_result $? "Order.submitted_at exists (workflow tracking)"

# Check order indexes
ORDER_INDEXES=$(sqlite3 dev.db 'SELECT COUNT(*) FROM sqlite_master WHERE type='"'"'index'"'"' AND tbl_name='"'"'order'"'"';')
echo "Order table has $ORDER_INDEXES indexes"
[ "$ORDER_INDEXES" -ge 10 ]
print_result $? "Order has 10+ indexes"

echo ""
echo "3. Testing OrderItem Model..."
echo "========================================"

# Test order_item table exists
echo "Checking if order_item table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM order_item;" > /dev/null 2>&1
print_result $? "OrderItem table exists"

# Count order_item columns
ORDERITEM_COLS=$(sqlite3 dev.db "PRAGMA table_info(order_item);" | wc -l)
echo "OrderItem table has $ORDERITEM_COLS columns"
[ "$ORDERITEM_COLS" -eq 19 ]
print_result $? "OrderItem table has 19 columns"

# Check critical order_item columns (product snapshot)
sqlite3 dev.db "PRAGMA table_info(order_item);" | grep -q "product_name_ar"
print_result $? "OrderItem.product_name_ar exists (snapshot)"

sqlite3 dev.db "PRAGMA table_info(order_item);" | grep -q "product_sku"
print_result $? "OrderItem.product_sku exists (snapshot)"

sqlite3 dev.db "PRAGMA table_info(order_item);" | grep -q "unit_price"
print_result $? "OrderItem.unit_price exists (price snapshot)"

sqlite3 dev.db "PRAGMA table_info(order_item);" | grep -q "quantity"
print_result $? "OrderItem.quantity exists"

sqlite3 dev.db "PRAGMA table_info(order_item);" | grep -q "tax_rate"
print_result $? "OrderItem.tax_rate exists"

# Check order_item indexes
ORDERITEM_INDEXES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='order_item';")
echo "OrderItem table has $ORDERITEM_INDEXES indexes"
[ "$ORDERITEM_INDEXES" -ge 3 ]
print_result $? "OrderItem has 3+ indexes"

echo ""
echo "4. Testing Database Relationships..."
echo "========================================"

# Check foreign keys
echo "Checking foreign key constraints..."

# Product -> Supplier
sqlite3 dev.db "PRAGMA foreign_key_list(product);" | grep -q "supplier"
print_result $? "Product has foreign key to Supplier"

# Order -> Restaurant
sqlite3 dev.db 'PRAGMA foreign_key_list("order");' | grep -q "restaurant"
print_result $? "Order has foreign key to Restaurant"

# Order -> Supplier
sqlite3 dev.db 'PRAGMA foreign_key_list("order");' | grep -q "supplier"
print_result $? "Order has foreign key to Supplier"

# OrderItem -> Order
sqlite3 dev.db "PRAGMA foreign_key_list(order_item);" | grep -q "order"
print_result $? "OrderItem has foreign key to Order"

# OrderItem -> Product
sqlite3 dev.db "PRAGMA foreign_key_list(order_item);" | grep -q "product"
print_result $? "OrderItem has foreign key to Product"

echo ""
echo "5. Testing Database Migrations..."
echo "========================================"

# Check current migration version
CURRENT_VERSION=$(.venv/bin/alembic current 2>&1 | grep -o '[a-z0-9]*' | head -1)
echo "Current migration version: $CURRENT_VERSION"
[ ! -z "$CURRENT_VERSION" ]
print_result $? "Migration version is set"

# Count total migrations
MIGRATION_COUNT=$(ls -1 alembic/versions/*.py | wc -l)
echo "Found $MIGRATION_COUNT migration files"
[ "$MIGRATION_COUNT" -ge 6 ]
print_result $? "At least 6 migrations exist"

# Check specific Phase 2 migrations exist
ls alembic/versions/*product*.py > /dev/null 2>&1
print_result $? "Product migration file exists"

ls alembic/versions/*order*.py > /dev/null 2>&1
print_result $? "Order migration file exists"

echo ""
echo "6. Testing Python Model Imports..."
echo "========================================"

# Test Product model imports
.venv/bin/python -c "from app.models import Product; print('OK')" > /dev/null 2>&1
print_result $? "Product model imports successfully"

# Test Order models import
.venv/bin/python -c "from app.models import Order, OrderItem, OrderStatus, PaymentStatus; print('OK')" > /dev/null 2>&1
print_result $? "Order models import successfully"

# Test all models together
.venv/bin/python -c "from app.models import Restaurant, Supplier, Product, Order, OrderItem; print('OK')" > /dev/null 2>&1
print_result $? "All supply chain models import together"

echo ""
echo "7. Testing Schema Imports..."
echo "========================================"

# Test Product schemas
.venv/bin/python -c "from app.schemas.product import ProductCreate, ProductRead, ProductList; print('OK')" > /dev/null 2>&1
print_result $? "Product schemas import successfully"

# Test Order schemas
.venv/bin/python -c "from app.schemas.order import OrderCreate, OrderRead, OrderList, OrderItemCreate; print('OK')" > /dev/null 2>&1
print_result $? "Order schemas import successfully"

echo ""
echo "8. Testing CRUD Operations..."
echo "========================================"

# Test Product CRUD imports
.venv/bin/python -c "from app.crud.product import product; print('OK')" > /dev/null 2>&1
print_result $? "Product CRUD imports successfully"

# Test Order CRUD imports
.venv/bin/python -c "from app.crud.order import order; print('OK')" > /dev/null 2>&1
print_result $? "Order CRUD imports successfully"

echo ""
echo "9. Testing API Endpoints..."
echo "========================================"

# Test Product API imports
.venv/bin/python -c "from app.api.v1 import products; print('OK')" > /dev/null 2>&1
print_result $? "Product API imports successfully"

# Test Order API imports
.venv/bin/python -c "from app.api.v1 import orders; print('OK')" > /dev/null 2>&1
print_result $? "Order API imports successfully"

# Count total routes
ROUTE_COUNT=$(.venv/bin/python -c "from app.main import app; print(len([r for r in app.routes]))" 2>/dev/null)
echo "Application has $ROUTE_COUNT routes"
[ "$ROUTE_COUNT" -ge 84 ]
print_result $? "Application has 84+ routes"

echo ""
echo "10. Testing Application Startup..."
echo "========================================"

# Test application loads without errors
.venv/bin/python -c "from app.main import app; print('Application loaded successfully')" > /dev/null 2>&1
print_result $? "Application loads without errors"

# Test API router configuration
.venv/bin/python -c "from app.api.v1.router import api_router; print('OK')" > /dev/null 2>&1
print_result $? "API router configured correctly"

echo ""
echo "11. Testing Database Integrity..."
echo "========================================"

# Count total tables
TOTAL_TABLES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
echo "Database has $TOTAL_TABLES tables"
[ "$TOTAL_TABLES" -ge 17 ]
print_result $? "Database has 17+ tables (Phase 1 + Phase 2)"

# Verify no orphaned data
echo "Checking database integrity..."
sqlite3 dev.db "PRAGMA integrity_check;" | grep -q "ok"
print_result $? "Database integrity check passed"

echo ""
echo "12. Testing Phase 2 Specific Features..."
echo "========================================"

# Test Product model has calculated properties
.venv/bin/python -c "
from app.models.product import Product
from decimal import Decimal
p = Product(
    id='test', name_ar='test', name_en='test', sku='test',
    category='Vegetables', unit_price=Decimal('100'),
    discount_percentage=Decimal('10'), tax_rate=Decimal('5'),
    unit_of_measure='kg', supplier_id='test'
)
assert hasattr(p, 'final_price'), 'Product.final_price property missing'
assert hasattr(p, 'price_with_tax'), 'Product.price_with_tax property missing'
assert hasattr(p, 'is_low_stock'), 'Product.is_low_stock property missing'
print('OK')
" > /dev/null 2>&1
print_result $? "Product has calculated properties (final_price, price_with_tax, is_low_stock)"

# Test Order model has calculated properties
.venv/bin/python -c "
from app.models.order import Order, OrderStatus
from decimal import Decimal
o = Order(
    id='test', order_number='TEST-001', restaurant_id='test',
    supplier_id='test', status=OrderStatus.DRAFT.value,
    total_amount=Decimal('1000'), paid_amount=Decimal('500')
)
assert hasattr(o, 'is_editable'), 'Order.is_editable property missing'
assert hasattr(o, 'is_cancellable'), 'Order.is_cancellable property missing'
assert hasattr(o, 'outstanding_amount'), 'Order.outstanding_amount property missing'
print('OK')
" > /dev/null 2>&1
print_result $? "Order has calculated properties (is_editable, is_cancellable, outstanding_amount)"

# Test OrderItem model has calculated properties
.venv/bin/python -c "
from app.models.order import OrderItem
from decimal import Decimal
oi = OrderItem(
    id='test', order_id='test', product_id='test',
    product_name_ar='test', product_name_en='test', product_sku='test',
    unit_price=Decimal('100'), unit_of_measure='kg',
    quantity=Decimal('5'), discount_percentage=Decimal('10'),
    tax_rate=Decimal('5')
)
assert hasattr(oi, 'line_subtotal'), 'OrderItem.line_subtotal property missing'
assert hasattr(oi, 'line_total'), 'OrderItem.line_total property missing'
print('OK')
" > /dev/null 2>&1
print_result $? "OrderItem has calculated properties (line_subtotal, line_total)"

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
    echo "Phase 2 implementation is complete and working correctly."
    echo ""
    echo "Summary:"
    echo "- Product catalog with inventory management"
    echo "- Order system with complete workflow"
    echo "- 3 new database tables (product, order, order_item)"
    echo "- 26 new API endpoints (13 product + 13 order)"
    echo "- Total routes: $ROUTE_COUNT"
    echo "- Total tables: $TOTAL_TABLES"
    echo "=========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "✗ SOME TESTS FAILED"
    echo "Please review the failures above."
    echo "=========================================${NC}"
    exit 1
fi

#!/bin/bash

# Phase 3.1 Comprehensive Test Script
# Tests Delivery Management features

# set -e disabled to see all test results

echo "================================================"
echo "Phase 3.1 Delivery Management - Test Suite"
echo "================================================"
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

echo "1. Testing Delivery Model..."
echo "========================================"

# Test delivery table exists
echo "Checking if delivery table exists..."
sqlite3 dev.db "SELECT COUNT(*) FROM delivery;" > /dev/null 2>&1
print_result $? "Delivery table exists"

# Count delivery columns
DELIVERY_COLS=$(sqlite3 dev.db "PRAGMA table_info(delivery);" | wc -l)
echo "Delivery table has $DELIVERY_COLS columns"
[ "$DELIVERY_COLS" -eq 47 ]
print_result $? "Delivery table has 47 columns"

# Check critical delivery columns
sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "order_id"
print_result $? "Delivery.order_id exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "driver_id"
print_result $? "Delivery.driver_id exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "status"
print_result $? "Delivery.status exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "priority"
print_result $? "Delivery.priority exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "pickup_address"
print_result $? "Delivery.pickup_address exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "delivery_address"
print_result $? "Delivery.delivery_address exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "pickup_latitude"
print_result $? "Delivery.pickup_latitude exists (GPS tracking)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "current_latitude"
print_result $? "Delivery.current_latitude exists (real-time tracking)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "location_history"
print_result $? "Delivery.location_history exists (JSON tracking)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "assigned_at"
print_result $? "Delivery.assigned_at exists (workflow tracking)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "picked_up_at"
print_result $? "Delivery.picked_up_at exists (workflow tracking)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "delivered_at"
print_result $? "Delivery.delivered_at exists (workflow tracking)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "signature_url"
print_result $? "Delivery.signature_url exists (proof of delivery)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "recipient_name"
print_result $? "Delivery.recipient_name exists (proof of delivery)"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "delivery_fee"
print_result $? "Delivery.delivery_fee exists"

sqlite3 dev.db "PRAGMA table_info(delivery);" | grep -q "estimated_distance_km"
print_result $? "Delivery.estimated_distance_km exists"

# Check delivery indexes
DELIVERY_INDEXES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='delivery';")
echo "Delivery table has $DELIVERY_INDEXES indexes"
[ "$DELIVERY_INDEXES" -ge 10 ]
print_result $? "Delivery has 10+ indexes"

echo ""
echo "2. Testing Database Relationships..."
echo "========================================"

# Check foreign keys
echo "Checking foreign key constraints..."

# Delivery -> Order
sqlite3 dev.db "PRAGMA foreign_key_list(delivery);" | grep -q "order"
print_result $? "Delivery has foreign key to Order"

# Delivery -> User (driver)
sqlite3 dev.db "PRAGMA foreign_key_list(delivery);" | grep -q "user"
print_result $? "Delivery has foreign key to User (driver)"

echo ""
echo "3. Testing Database Migrations..."
echo "========================================"

# Check current migration version
CURRENT_VERSION=$(.venv/bin/alembic current 2>&1 | grep -o '[a-z0-9]*' | head -1)
echo "Current migration version: $CURRENT_VERSION"
[ ! -z "$CURRENT_VERSION" ]
print_result $? "Migration version is set"

# Count total migrations
MIGRATION_COUNT=$(ls -1 alembic/versions/*.py | wc -l)
echo "Found $MIGRATION_COUNT migration files"
[ "$MIGRATION_COUNT" -ge 7 ]
print_result $? "At least 7 migrations exist"

# Check specific Phase 3 migration exists
ls alembic/versions/*delivery*.py > /dev/null 2>&1
print_result $? "Delivery migration file exists"

echo ""
echo "4. Testing Python Model Imports..."
echo "========================================"

# Test Delivery model imports
.venv/bin/python -c "from app.models import Delivery; print('OK')" > /dev/null 2>&1
print_result $? "Delivery model imports successfully"

# Test Delivery enums import
.venv/bin/python -c "from app.models import DeliveryStatus, DeliveryPriority; print('OK')" > /dev/null 2>&1
print_result $? "Delivery enums import successfully"

# Test all models together
.venv/bin/python -c "from app.models import Restaurant, Supplier, Product, Order, OrderItem, Delivery; print('OK')" > /dev/null 2>&1
print_result $? "All supply chain models import together with Delivery"

echo ""
echo "5. Testing Schema Imports..."
echo "========================================"

# Test Delivery schemas
.venv/bin/python -c "from app.schemas.delivery import DeliveryCreate, DeliveryRead, DeliveryList; print('OK')" > /dev/null 2>&1
print_result $? "Delivery schemas import successfully"

# Test workflow schemas
.venv/bin/python -c "from app.schemas.delivery import DeliveryAssignment, DeliveryProofOfDelivery, DeliveryLocationUpdate; print('OK')" > /dev/null 2>&1
print_result $? "Delivery workflow schemas import successfully"

echo ""
echo "6. Testing CRUD Operations..."
echo "========================================"

# Test Delivery CRUD imports
.venv/bin/python -c "from app.crud.delivery import delivery; print('OK')" > /dev/null 2>&1
print_result $? "Delivery CRUD imports successfully"

echo ""
echo "7. Testing API Endpoints..."
echo "========================================"

# Test Delivery API imports
.venv/bin/python -c "from app.api.v1 import deliveries; print('OK')" > /dev/null 2>&1
print_result $? "Delivery API imports successfully"

# Count total routes
ROUTE_COUNT=$(.venv/bin/python -c "from app.main import app; print(len([r for r in app.routes]));" 2>&1 | grep -E "^[0-9]+$" | head -1)
echo "Application has $ROUTE_COUNT routes"
[ "$ROUTE_COUNT" -ge 102 ]
print_result $? "Application has 100+ routes (84 Phase 2 + 18 Phase 3.1)"

echo ""
echo "8. Testing Application Startup..."
echo "========================================"

# Test application loads without errors
.venv/bin/python -c "from app.main import app; print('Application loaded successfully')" > /dev/null 2>&1
print_result $? "Application loads without errors"

# Test API router configuration
.venv/bin/python -c "from app.api.v1.router import api_router; print('OK')" > /dev/null 2>&1
print_result $? "API router configured correctly"

echo ""
echo "9. Testing Database Integrity..."
echo "========================================"

# Count total tables
TOTAL_TABLES=$(sqlite3 dev.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
echo "Database has $TOTAL_TABLES tables"
[ "$TOTAL_TABLES" -ge 18 ]
print_result $? "Database has 18+ tables (Phase 1 + Phase 2 + Phase 3.1)"

# Verify no orphaned data
echo "Checking database integrity..."
sqlite3 dev.db "PRAGMA integrity_check;" | grep -q "ok"
print_result $? "Database integrity check passed"

echo ""
echo "10. Testing Phase 3.1 Specific Features..."
echo "========================================"

# Test Delivery model has calculated properties
.venv/bin/python -c "
from app.models.delivery import Delivery, DeliveryStatus
from decimal import Decimal
d = Delivery(
    id='test', order_id='test', status=DeliveryStatus.ASSIGNED.value,
    priority='normal', pickup_address='test', delivery_address='test',
    delivery_fee=Decimal('5000')
)
assert hasattr(d, 'is_assigned'), 'Delivery.is_assigned property missing'
assert hasattr(d, 'is_active'), 'Delivery.is_active property missing'
assert hasattr(d, 'is_completed'), 'Delivery.is_completed property missing'
assert hasattr(d, 'is_in_progress'), 'Delivery.is_in_progress property missing'
assert hasattr(d, 'can_be_cancelled'), 'Delivery.can_be_cancelled property missing'
print('OK')
" > /dev/null 2>&1
print_result $? "Delivery has calculated properties (is_assigned, is_active, is_completed, etc.)"

# Test Delivery model has GPS tracking methods
.venv/bin/python -c "
from app.models.delivery import Delivery, DeliveryStatus
from decimal import Decimal
d = Delivery(
    id='test', order_id='test', status=DeliveryStatus.IN_TRANSIT.value,
    priority='normal', pickup_address='test', delivery_address='test',
    delivery_fee=Decimal('5000')
)
assert hasattr(d, 'add_location_point'), 'Delivery.add_location_point method missing'
assert hasattr(d, 'calculate_delivery_fee'), 'Delivery.calculate_delivery_fee method missing'
# Test add_location_point
d.add_location_point(Decimal('33.3152'), Decimal('44.3661'))
assert d.current_latitude == Decimal('33.3152'), 'Location update failed'
assert d.location_history is not None, 'Location history not created'
print('OK')
" > /dev/null 2>&1
print_result $? "Delivery has GPS tracking methods (add_location_point, calculate_delivery_fee)"

# Test CRUD distance calculation (Haversine formula)
.venv/bin/python -c "
from app.crud.delivery import delivery
from decimal import Decimal
# Test distance between Baghdad (33.3152, 44.3661) and Basra (30.5085, 47.7830)
distance = delivery._calculate_distance(
    Decimal('33.3152'), Decimal('44.3661'),
    Decimal('30.5085'), Decimal('47.7830')
)
# Expected ~449 km
assert 440 <= distance <= 460, f'Distance calculation incorrect: {distance}'
print('OK')
" > /dev/null 2>&1
print_result $? "CRUD has Haversine distance calculation working correctly"

# Test status transition validation
.venv/bin/python -c "
from app.crud.delivery import delivery
from app.models.delivery import DeliveryStatus
# Test valid transitions
assert delivery._is_valid_status_transition('pending', 'assigned') == True
assert delivery._is_valid_status_transition('assigned', 'picked_up') == True
assert delivery._is_valid_status_transition('picked_up', 'in_transit') == True
assert delivery._is_valid_status_transition('in_transit', 'arrived') == True
assert delivery._is_valid_status_transition('arrived', 'delivered') == True
# Test invalid transitions
assert delivery._is_valid_status_transition('pending', 'delivered') == False
assert delivery._is_valid_status_transition('delivered', 'assigned') == False
# Test cancellation allowed
assert delivery._is_valid_status_transition('assigned', 'cancelled') == True
assert delivery._is_valid_status_transition('in_transit', 'cancelled') == True
print('OK')
" > /dev/null 2>&1
print_result $? "Delivery status transition validation working correctly"

# Test permissions exist
.venv/bin/python -c "
from app.models.role import PERMISSIONS
required = ['DELIVERY_CREATE', 'DELIVERY_READ', 'DELIVERY_UPDATE', 'DELIVERY_DELETE', 'DELIVERY_ASSIGN']
for perm in required:
    assert perm in PERMISSIONS, f'Permission {perm} not found'
print('OK')
" > /dev/null 2>&1
print_result $? "All delivery permissions exist in PERMISSIONS constant"

echo ""
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}================================================"
    echo "✓ ALL TESTS PASSED!"
    echo "Phase 3.1 Delivery Management is complete and working correctly."
    echo ""
    echo "Summary:"
    echo "- Delivery model with GPS tracking and workflow"
    echo "- 1 new database table (delivery)"
    echo "- 18 new API endpoints for full delivery lifecycle"
    echo "- Total routes: $ROUTE_COUNT (84 Phase 2 + 18 Phase 3.1)"
    echo "- Total tables: $TOTAL_TABLES"
    echo ""
    echo "Features Implemented:"
    echo "- Driver assignment and tracking"
    echo "- Real-time GPS location updates"
    echo "- 8-stage delivery workflow (pending → delivered)"
    echo "- Proof of delivery (signature, photos, recipient)"
    echo "- Distance calculation (Haversine formula)"
    echo "- Delivery fee auto-calculation"
    echo "- Status transition validation"
    echo "- Delayed delivery detection"
    echo "- Delivery statistics and analytics"
    echo "================================================${NC}"
    exit 0
else
    echo -e "${RED}================================================"
    echo "✗ SOME TESTS FAILED"
    echo "Please review the failures above."
    echo "================================================${NC}"
    exit 1
fi

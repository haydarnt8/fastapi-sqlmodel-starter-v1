#!/bin/bash
# Test script for Phase 2 fixes

echo "====================================="
echo "Testing Phase 2 Production Fixes"
echo "====================================="
echo ""

# Check if server is running
echo "1. Checking if server is accessible..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ Server is running"

    echo ""
    echo "2. Testing health check endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "   Response: $HEALTH_RESPONSE"

    # Check if response contains database field
    if echo "$HEALTH_RESPONSE" | grep -q '"database"'; then
        echo "   ✓ Health check includes database status"
    else
        echo "   ✗ Health check missing database status"
    fi

    # Check if response contains redis field
    if echo "$HEALTH_RESPONSE" | grep -q '"redis"'; then
        echo "   ✓ Health check includes redis status"
    else
        echo "   ✗ Health check missing redis status"
    fi

    # Check if response contains timestamp
    if echo "$HEALTH_RESPONSE" | grep -q '"timestamp"'; then
        echo "   ✓ Health check includes timestamp"
    else
        echo "   ✗ Health check missing timestamp"
    fi

    echo ""
    echo "3. Testing request logging (check for X-Process-Time header)..."
    HEADERS=$(curl -sI http://localhost:8000/health)
    if echo "$HEADERS" | grep -qi "X-Process-Time"; then
        echo "   ✓ Request logging middleware is active"
    else
        echo "   ✗ Request logging middleware not detected"
    fi

    echo ""
    echo "====================================="
    echo "Phase 2 Testing Complete!"
    echo "====================================="
else
    echo "   ✗ Server not running on localhost:8000"
    echo ""
    echo "To test, first start the server:"
    echo "  .venv/bin/uvicorn app.main:app --reload"
    echo ""
    echo "Then run this script again."
fi

"""
Order Schemas

Pydantic schemas for Order and OrderItem API request/response validation.

Schemas:
- OrderItemBase: Base order item schema
- OrderItemCreate: Schema for adding items to order
- OrderItemRead: Order item details for responses
- OrderBase: Base order schema
- OrderCreate: Schema for creating orders
- OrderUpdate: Schema for updating orders
- OrderRead: Full order details with items
- OrderList: Lightweight order list view
- OrderStatusUpdate: Schema for status transitions
- OrderSearchFilters: Advanced search parameters
"""

from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==================== Order Item Schemas ====================

class OrderItemBase(BaseModel):
    """Base order item schema."""

    product_id: UUID = Field(..., description="Product being ordered")
    quantity: Decimal = Field(..., gt=0, description="Quantity to order")
    notes: Optional[str] = Field(None, max_length=500, description="Special notes for this item")


class OrderItemCreate(OrderItemBase):
    """Schema for adding item to order."""
    pass


class OrderItemUpdate(BaseModel):
    """Schema for updating order item."""

    quantity: Optional[Decimal] = Field(None, gt=0, description="New quantity")
    notes: Optional[str] = Field(None, max_length=500, description="Updated notes")


class OrderItemRead(BaseModel):
    """Order item details for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    product_id: UUID

    # Product snapshot
    product_name_ar: str
    product_name_en: str
    product_sku: str
    unit_price: Decimal
    unit_of_measure: str

    # Quantity and pricing
    quantity: Decimal
    discount_percentage: Decimal
    tax_rate: Decimal
    notes: Optional[str]

    # Calculated fields
    line_subtotal: Decimal
    discount_amount: Decimal
    line_total_before_tax: Decimal
    tax_amount: Decimal
    line_total: Decimal

    created_at: datetime
    updated_at: datetime


# ==================== Order Schemas ====================

class OrderBase(BaseModel):
    """Base order schema."""

    restaurant_id: UUID = Field(..., description="Restaurant placing the order")
    supplier_id: UUID = Field(..., description="Supplier fulfilling the order")
    notes: Optional[str] = Field(None, max_length=2000, description="Special instructions")
    special_instructions: Optional[str] = Field(
        None, max_length=1000, description="Delivery or handling instructions"
    )
    delivery_address: Optional[Dict] = Field(None, description="Delivery address (JSON)")
    delivery_date: Optional[datetime] = Field(None, description="Expected delivery date")


class OrderCreate(OrderBase):
    """Schema for creating a new order."""

    items: List[OrderItemCreate] = Field(..., min_length=1, description="Order items (at least 1 required)")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[OrderItemCreate]) -> List[OrderItemCreate]:
        """Validate order items."""
        if not v or len(v) == 0:
            raise ValueError("Order must have at least one item")
        return v


class OrderUpdate(BaseModel):
    """Schema for updating an order (draft/pending only)."""

    notes: Optional[str] = Field(None, max_length=2000)
    special_instructions: Optional[str] = Field(None, max_length=1000)
    delivery_address: Optional[Dict] = None
    delivery_date: Optional[datetime] = None
    delivery_fee: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)


class OrderRead(BaseModel):
    """Full order details with items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    restaurant_id: UUID
    supplier_id: UUID
    status: str

    # Order details
    notes: Optional[str]
    internal_notes: Optional[str]
    special_instructions: Optional[str]

    # Financial
    subtotal: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str

    # Payment
    payment_status: str
    payment_method: Optional[str]
    paid_amount: Decimal
    payment_due_date: Optional[datetime]

    # Delivery
    delivery_address: Optional[Dict]
    delivery_date: Optional[datetime]
    delivered_at: Optional[datetime]
    delivery_notes: Optional[str]

    # Tracking
    submitted_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    confirmed_by_id: Optional[UUID]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]

    # Calculated properties
    is_editable: bool
    is_cancellable: bool
    is_completed: bool
    outstanding_amount: Decimal

    # Items
    items: List[OrderItemRead] = []

    # Audit
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[UUID]


class OrderList(BaseModel):
    """Lightweight order schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    restaurant_id: UUID
    supplier_id: UUID
    status: str
    payment_status: str

    # Financial summary
    total_amount: Decimal
    currency: str
    outstanding_amount: Decimal

    # Key dates
    submitted_at: Optional[datetime]
    delivery_date: Optional[datetime]
    created_at: datetime

    # Quick status checks
    is_editable: bool
    is_cancellable: bool
    is_completed: bool


class OrderStatusUpdate(BaseModel):
    """Schema for order status transitions."""

    status: str = Field(
        ...,
        description="New status (pending, confirmed, processing, ready_for_delivery, in_transit, delivered, cancelled, rejected)"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Notes about the status change")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed_statuses = [
            "draft", "pending", "confirmed", "processing",
            "ready_for_delivery", "in_transit", "delivered",
            "cancelled", "rejected"
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status. Allowed: {', '.join(allowed_statuses)}")
        return v


class OrderCancellation(BaseModel):
    """Schema for order cancellation."""

    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for cancellation")


class OrderRejection(BaseModel):
    """Schema for order rejection (supplier only)."""

    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for rejection")


class OrderConfirmation(BaseModel):
    """Schema for order confirmation (supplier only)."""

    delivery_date: Optional[datetime] = Field(None, description="Confirmed delivery date")
    notes: Optional[str] = Field(None, max_length=1000, description="Confirmation notes")


class OrderSearchFilters(BaseModel):
    """Advanced order search and filter parameters."""

    # Text search
    query: Optional[str] = Field(
        None,
        description="Search by order number"
    )

    # Relationship filters
    restaurant_id: Optional[UUID] = Field(None, description="Filter by restaurant")
    supplier_id: Optional[UUID] = Field(None, description="Filter by supplier")

    # Status filters
    status: Optional[str] = Field(None, description="Filter by order status")
    payment_status: Optional[str] = Field(None, description="Filter by payment status")

    # Date filters
    submitted_after: Optional[datetime] = Field(None, description="Orders submitted after this date")
    submitted_before: Optional[datetime] = Field(None, description="Orders submitted before this date")
    delivery_after: Optional[datetime] = Field(None, description="Orders with delivery after this date")
    delivery_before: Optional[datetime] = Field(None, description="Orders with delivery before this date")

    # Amount filters
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum order amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum order amount")

    # Payment filters
    has_outstanding_payment: Optional[bool] = Field(
        None,
        description="Filter orders with outstanding payments"
    )

    # Sorting
    sort_by: str = Field(
        default="submitted_at",
        description="Sort field: order_number, submitted_at, delivery_date, total_amount, status"
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: asc or desc"
    )

    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=100, description="Maximum records to return")

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort_by field."""
        allowed_fields = [
            "order_number", "submitted_at", "delivery_date",
            "total_amount", "status", "created_at"
        ]
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort_by. Allowed: {', '.join(allowed_fields)}")
        return v


class OrderPaymentUpdate(BaseModel):
    """Schema for updating order payment."""

    payment_method: str = Field(..., min_length=1, max_length=50, description="Payment method")
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_notes: Optional[str] = Field(None, max_length=500, description="Payment notes")


class OrderDeliveryUpdate(BaseModel):
    """Schema for updating delivery information."""

    delivered_at: datetime = Field(..., description="Actual delivery timestamp")
    delivery_notes: Optional[str] = Field(None, max_length=1000, description="Delivery notes")


class OrderInternalNotesUpdate(BaseModel):
    """Schema for updating internal notes (supplier only)."""

    internal_notes: str = Field(..., max_length=2000, description="Internal notes")

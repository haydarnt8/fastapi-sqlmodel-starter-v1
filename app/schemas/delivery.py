"""
Delivery Schemas

Pydantic schemas for Delivery model validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.delivery import DeliveryStatus, DeliveryPriority


# ==================== Base Schemas ====================


class DeliveryBase(BaseModel):
    """Base schema for delivery with common fields."""

    priority: str = Field(default=DeliveryPriority.NORMAL.value)
    pickup_address: str = Field(max_length=500)
    pickup_city: Optional[str] = Field(default=None, max_length=100)
    pickup_district: Optional[str] = Field(default=None, max_length=100)
    pickup_latitude: Optional[Decimal] = None
    pickup_longitude: Optional[Decimal] = None
    delivery_address: str = Field(max_length=500)
    delivery_city: Optional[str] = Field(default=None, max_length=100)
    delivery_district: Optional[str] = Field(default=None, max_length=100)
    delivery_latitude: Optional[Decimal] = None
    delivery_longitude: Optional[Decimal] = None
    estimated_distance_km: Optional[Decimal] = None
    delivery_fee: Decimal = Field(default=Decimal("0.00"))
    estimated_pickup_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None
    special_instructions: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is a valid enum value."""
        valid_priorities = [p.value for p in DeliveryPriority]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v


# ==================== Create Schemas ====================


class DeliveryCreate(DeliveryBase):
    """Schema for creating a new delivery."""

    order_id: UUID
    driver_id: Optional[UUID] = None  # Can be assigned later


# ==================== Update Schemas ====================


class DeliveryUpdate(BaseModel):
    """Schema for updating a delivery (partial updates)."""

    driver_id: Optional[UUID] = None
    priority: Optional[str] = None
    pickup_address: Optional[str] = Field(default=None, max_length=500)
    pickup_city: Optional[str] = Field(default=None, max_length=100)
    pickup_district: Optional[str] = Field(default=None, max_length=100)
    pickup_latitude: Optional[Decimal] = None
    pickup_longitude: Optional[Decimal] = None
    delivery_address: Optional[str] = Field(default=None, max_length=500)
    delivery_city: Optional[str] = Field(default=None, max_length=100)
    delivery_district: Optional[str] = Field(default=None, max_length=100)
    delivery_latitude: Optional[Decimal] = None
    delivery_longitude: Optional[Decimal] = None
    estimated_distance_km: Optional[Decimal] = None
    delivery_fee: Optional[Decimal] = None
    estimated_pickup_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None
    special_instructions: Optional[str] = Field(default=None, max_length=1000)
    driver_notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority is a valid enum value."""
        if v is not None:
            valid_priorities = [p.value for p in DeliveryPriority]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")
        return v


# ==================== Status Update Schemas ====================


class DeliveryStatusUpdate(BaseModel):
    """Schema for updating delivery status."""

    status: str
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is a valid enum value."""
        valid_statuses = [s.value for s in DeliveryStatus]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class DeliveryAssignment(BaseModel):
    """Schema for assigning driver to delivery."""

    driver_id: UUID
    estimated_pickup_time: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class DeliveryLocationUpdate(BaseModel):
    """Schema for updating driver's current location."""

    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)


class DeliveryProofOfDelivery(BaseModel):
    """Schema for submitting proof of delivery."""

    signature_url: Optional[str] = Field(default=None, max_length=500)
    photo_urls: Optional[List[str]] = None
    recipient_name: str = Field(max_length=255)
    recipient_phone: Optional[str] = Field(default=None, max_length=20)
    recipient_notes: Optional[str] = Field(default=None, max_length=1000)


class DeliveryCancellation(BaseModel):
    """Schema for cancelling delivery."""

    cancellation_reason: str = Field(max_length=500)


class DeliveryFailure(BaseModel):
    """Schema for marking delivery as failed."""

    failure_reason: str = Field(max_length=500)
    photo_urls: Optional[List[str]] = None  # Evidence of failure


# ==================== Response Schemas ====================


class DeliveryRead(DeliveryBase):
    """Schema for reading delivery data."""

    id: UUID
    order_id: UUID
    driver_id: Optional[UUID]
    status: str

    # Tracking
    current_latitude: Optional[Decimal]
    current_longitude: Optional[Decimal]
    last_location_update: Optional[datetime]
    actual_distance_km: Optional[Decimal]

    # Timestamps
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    in_transit_at: Optional[datetime]
    arrived_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    # Proof of Delivery
    signature_url: Optional[str]
    recipient_name: Optional[str]
    recipient_phone: Optional[str]
    recipient_notes: Optional[str]

    # Failure/Cancellation
    failure_reason: Optional[str]
    cancellation_reason: Optional[str]

    # Notes
    driver_notes: Optional[str]

    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[UUID]
    updated_by_id: Optional[UUID]

    # Calculated properties
    is_assigned: bool
    is_active: bool
    is_completed: bool
    is_in_progress: bool
    can_be_cancelled: bool
    is_delayed: bool

    class Config:
        from_attributes = True


class DeliveryList(BaseModel):
    """Schema for delivery list response."""

    id: UUID
    order_id: UUID
    driver_id: Optional[UUID]
    status: str
    priority: str
    delivery_address: str
    delivery_city: Optional[str]
    estimated_delivery_time: Optional[datetime]
    delivered_at: Optional[datetime]
    delivery_fee: Decimal
    is_delayed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DeliverySearchFilters(BaseModel):
    """Schema for delivery search filters."""

    driver_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    city: Optional[str] = None
    assigned_after: Optional[datetime] = None
    assigned_before: Optional[datetime] = None
    delivery_after: Optional[datetime] = None
    delivery_before: Optional[datetime] = None
    is_delayed: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class DeliveryStatistics(BaseModel):
    """Schema for delivery statistics."""

    total_deliveries: int
    pending_deliveries: int
    in_progress_deliveries: int
    completed_deliveries: int
    failed_deliveries: int
    cancelled_deliveries: int
    total_distance_km: Decimal
    total_delivery_fees: Decimal
    average_delivery_time_minutes: Optional[int]
    delayed_deliveries: int


class DriverStatistics(BaseModel):
    """Schema for driver performance statistics."""

    driver_id: UUID
    total_deliveries: int
    completed_deliveries: int
    failed_deliveries: int
    total_distance_km: Decimal
    total_delivery_fees: Decimal
    average_delivery_time_minutes: Optional[int]
    on_time_percentage: Decimal
    current_active_deliveries: int

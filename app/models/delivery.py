"""
Delivery Model

Handles delivery tracking for orders including:
- Driver assignment
- GPS location tracking
- Delivery status workflow
- Proof of delivery (signature, photos)
- Distance and delivery fee calculation
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, JSON
from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class DeliveryStatus(str, Enum):
    """Delivery status workflow."""
    PENDING = "pending"  # Waiting for driver assignment
    ASSIGNED = "assigned"  # Driver assigned but not picked up
    PICKED_UP = "picked_up"  # Driver picked up from supplier
    IN_TRANSIT = "in_transit"  # On the way to restaurant
    ARRIVED = "arrived"  # Arrived at restaurant
    DELIVERED = "delivered"  # Successfully delivered
    FAILED = "failed"  # Delivery failed
    CANCELLED = "cancelled"  # Delivery cancelled


class DeliveryPriority(str, Enum):
    """Delivery priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Delivery(BaseModel, table=True):
    """
    Delivery model for tracking order deliveries.

    Attributes:
        order_id: Link to order being delivered
        driver_id: Assigned driver (User with driver role)
        status: Current delivery status
        priority: Delivery priority level

        # Addresses and GPS
        pickup_address: Full pickup address (supplier)
        pickup_latitude: Pickup GPS latitude
        pickup_longitude: Pickup GPS longitude
        delivery_address: Full delivery address (restaurant)
        delivery_latitude: Delivery GPS latitude
        delivery_longitude: Delivery GPS longitude

        # Distance and Fees
        estimated_distance_km: Estimated distance
        actual_distance_km: Actual distance traveled
        delivery_fee: Delivery fee charged

        # Tracking
        current_latitude: Current driver location latitude
        current_longitude: Current driver location longitude
        last_location_update: Last GPS update timestamp
        location_history: Array of GPS points with timestamps

        # Workflow Timestamps
        assigned_at: When driver was assigned
        picked_up_at: When order was picked up
        in_transit_at: When delivery started
        arrived_at: When driver arrived at restaurant
        delivered_at: When delivery was completed
        failed_at: When delivery failed
        cancelled_at: When delivery was cancelled

        # Time Estimates
        estimated_pickup_time: Expected pickup time
        estimated_delivery_time: Expected delivery time

        # Proof of Delivery
        signature_url: URL to delivery signature image
        photo_urls: URLs to delivery photos
        recipient_name: Name of person who received
        recipient_notes: Notes from recipient

        # Failure/Cancellation
        failure_reason: Reason for failed delivery
        cancellation_reason: Reason for cancellation

        # Notes
        driver_notes: Notes from driver
        special_instructions: Special delivery instructions
    """

    __tablename__ = "delivery"

    # ==================== Primary Key ====================
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique delivery identifier"
    )

    # ==================== Relationships ====================

    order_id: UUID = Field(foreign_key="order.id", nullable=False, index=True)
    driver_id: Optional[UUID] = Field(foreign_key="user.id", nullable=True, index=True)

    # Relationships
    order: "Order" = Relationship(back_populates="deliveries")  # type: ignore
    driver: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Delivery.driver_id]",
            "lazy": "selectin",
        }
    )  # type: ignore

    # ==================== Status and Priority ====================

    status: str = Field(
        default=DeliveryStatus.PENDING.value,
        max_length=50,
        nullable=False,
        index=True
    )
    priority: str = Field(
        default=DeliveryPriority.NORMAL.value,
        max_length=20,
        nullable=False,
        index=True
    )

    # ==================== Pickup Location ====================

    pickup_address: str = Field(max_length=500, nullable=False)
    pickup_city: Optional[str] = Field(default=None, max_length=100)
    pickup_district: Optional[str] = Field(default=None, max_length=100)
    pickup_latitude: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=8
    )
    pickup_longitude: Optional[Decimal] = Field(
        default=None,
        max_digits=11,
        decimal_places=8
    )

    # ==================== Delivery Location ====================

    delivery_address: str = Field(max_length=500, nullable=False)
    delivery_city: Optional[str] = Field(default=None, max_length=100, index=True)
    delivery_district: Optional[str] = Field(default=None, max_length=100)
    delivery_latitude: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=8
    )
    delivery_longitude: Optional[Decimal] = Field(
        default=None,
        max_digits=11,
        decimal_places=8
    )

    # ==================== Distance and Fees ====================

    estimated_distance_km: Optional[Decimal] = Field(
        default=None,
        max_digits=8,
        decimal_places=2
    )
    actual_distance_km: Optional[Decimal] = Field(
        default=None,
        max_digits=8,
        decimal_places=2
    )
    delivery_fee: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False
    )

    # ==================== Real-time Tracking ====================

    current_latitude: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=8
    )
    current_longitude: Optional[Decimal] = Field(
        default=None,
        max_digits=11,
        decimal_places=8
    )
    last_location_update: Optional[datetime] = Field(default=None, nullable=True)

    # GPS tracking history - JSON array of {lat, lng, timestamp}
    location_history: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # ==================== Workflow Timestamps ====================

    assigned_at: Optional[datetime] = Field(default=None, nullable=True, index=True)
    picked_up_at: Optional[datetime] = Field(default=None, nullable=True)
    in_transit_at: Optional[datetime] = Field(default=None, nullable=True)
    arrived_at: Optional[datetime] = Field(default=None, nullable=True)
    delivered_at: Optional[datetime] = Field(default=None, nullable=True, index=True)
    failed_at: Optional[datetime] = Field(default=None, nullable=True)
    cancelled_at: Optional[datetime] = Field(default=None, nullable=True)

    # ==================== Time Estimates ====================

    estimated_pickup_time: Optional[datetime] = Field(default=None, nullable=True)
    estimated_delivery_time: Optional[datetime] = Field(default=None, nullable=True)

    # ==================== Proof of Delivery ====================

    signature_url: Optional[str] = Field(default=None, max_length=500)
    photo_urls: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON)
    )  # {"photos": ["url1", "url2"]}
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    recipient_phone: Optional[str] = Field(default=None, max_length=20)
    recipient_notes: Optional[str] = Field(default=None, max_length=1000)

    # ==================== Failure/Cancellation ====================

    failure_reason: Optional[str] = Field(default=None, max_length=500)
    cancellation_reason: Optional[str] = Field(default=None, max_length=500)

    # ==================== Notes and Instructions ====================

    driver_notes: Optional[str] = Field(default=None, max_length=1000)
    special_instructions: Optional[str] = Field(default=None, max_length=1000)

    # ==================== Calculated Properties ====================

    @property
    def is_assigned(self) -> bool:
        """Check if delivery has a driver assigned."""
        return self.driver_id is not None

    @property
    def is_active(self) -> bool:
        """Check if delivery is in active state."""
        return self.status not in [
            DeliveryStatus.DELIVERED.value,
            DeliveryStatus.FAILED.value,
            DeliveryStatus.CANCELLED.value,
        ]

    @property
    def is_completed(self) -> bool:
        """Check if delivery is in final state."""
        return self.status in [
            DeliveryStatus.DELIVERED.value,
            DeliveryStatus.FAILED.value,
            DeliveryStatus.CANCELLED.value,
        ]

    @property
    def is_in_progress(self) -> bool:
        """Check if delivery is currently in progress."""
        return self.status in [
            DeliveryStatus.PICKED_UP.value,
            DeliveryStatus.IN_TRANSIT.value,
            DeliveryStatus.ARRIVED.value,
        ]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if delivery can be cancelled."""
        return self.status not in [
            DeliveryStatus.DELIVERED.value,
            DeliveryStatus.FAILED.value,
            DeliveryStatus.CANCELLED.value,
        ]

    @property
    def can_update_location(self) -> bool:
        """Check if driver can update location."""
        return self.is_in_progress

    @property
    def requires_proof_of_delivery(self) -> bool:
        """Check if proof of delivery is required."""
        return self.status == DeliveryStatus.ARRIVED.value

    @property
    def has_proof_of_delivery(self) -> bool:
        """Check if proof of delivery has been submitted."""
        return (
            self.signature_url is not None or
            (self.photo_urls is not None and len(self.photo_urls.get("photos", [])) > 0)
        )

    @property
    def estimated_duration_minutes(self) -> Optional[int]:
        """Calculate estimated delivery duration in minutes."""
        if self.estimated_pickup_time and self.estimated_delivery_time:
            delta = self.estimated_delivery_time - self.estimated_pickup_time
            return int(delta.total_seconds() / 60)
        return None

    @property
    def actual_duration_minutes(self) -> Optional[int]:
        """Calculate actual delivery duration in minutes."""
        if self.picked_up_at and self.delivered_at:
            delta = self.delivered_at - self.picked_up_at
            return int(delta.total_seconds() / 60)
        return None

    @property
    def is_delayed(self) -> bool:
        """Check if delivery is delayed based on estimated time."""
        if self.estimated_delivery_time and self.status not in [
            DeliveryStatus.DELIVERED.value,
            DeliveryStatus.FAILED.value,
            DeliveryStatus.CANCELLED.value,
        ]:
            return datetime.utcnow() > self.estimated_delivery_time
        return False

    # ==================== Methods ====================

    def add_location_point(self, latitude: Decimal, longitude: Decimal) -> None:
        """
        Add a GPS point to location history.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
        """
        if self.location_history is None:
            self.location_history = {"points": []}

        point = {
            "lat": float(latitude),
            "lng": float(longitude),
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.location_history["points"].append(point)
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = datetime.utcnow()

    def calculate_delivery_fee(self, base_fee: Decimal = Decimal("5000"), per_km_fee: Decimal = Decimal("1000")) -> Decimal:
        """
        Calculate delivery fee based on distance.

        Default fees for Iraq (IQD):
        - Base fee: 5,000 IQD (~$3.40)
        - Per km: 1,000 IQD (~$0.68)

        Args:
            base_fee: Base delivery fee
            per_km_fee: Fee per kilometer

        Returns:
            Calculated delivery fee
        """
        if self.estimated_distance_km:
            return base_fee + (self.estimated_distance_km * per_km_fee)
        return base_fee


# ==================== Database Indexes ====================

# Composite indexes for common queries
Index(
    "ix_delivery_status_priority",
    Delivery.status,
    Delivery.priority,
)

Index(
    "ix_delivery_driver_status",
    Delivery.driver_id,
    Delivery.status,
)

Index(
    "ix_delivery_city_status",
    Delivery.delivery_city,
    Delivery.status,
)

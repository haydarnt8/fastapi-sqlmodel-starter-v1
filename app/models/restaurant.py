"""
Restaurant Model

Represents a restaurant in the supply chain system.

A restaurant can:
- Have multiple staff members (users)
- Place orders with suppliers
- Manage their profile and business information
- Be verified by admins before ordering
"""

from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, Relationship, Column
from sqlalchemy import JSON

from app.models.base import BaseModel

# Avoid circular imports
if TYPE_CHECKING:
    from app.models.user import User


class Restaurant(BaseModel, table=True):
    """
    Restaurant model for the supply chain system.

    Represents a restaurant business that orders supplies from suppliers.

    Fields:
    - Basic info: name (Arabic + English), business registration
    - Contact: email, phone numbers
    - Address: full address with GPS coordinates
    - Business details: type, cuisine, capacity, operating hours
    - Verification: admin approval status
    - Media: logo and cover images

    Relationships:
    - owner: User who owns/manages the restaurant
    - staff: List of users who work at this restaurant
    """

    __tablename__ = "restaurant"

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Basic Information
    name_ar: str = Field(
        max_length=255,
        nullable=False,
        description="Restaurant name in Arabic",
    )
    name_en: str = Field(
        max_length=255,
        nullable=False,
        description="Restaurant name in English",
    )
    business_registration: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="Business registration number / Trade license",
    )

    # Contact Information
    email: str = Field(
        max_length=255,
        nullable=False,
        index=True,
        description="Restaurant email address",
    )
    phone_primary: str = Field(
        max_length=20,
        nullable=False,
        description="Primary phone number",
    )
    phone_secondary: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        description="Secondary phone number",
    )

    # Address
    address_line1: str = Field(
        max_length=255,
        nullable=False,
        description="Address line 1",
    )
    address_line2: Optional[str] = Field(
        default=None,
        max_length=255,
        nullable=True,
        description="Address line 2 (optional)",
    )
    city: str = Field(
        max_length=100,
        nullable=False,
        index=True,
        description="City (e.g., Baghdad, Basra)",
    )
    district: str = Field(
        max_length=100,
        nullable=False,
        description="District/Neighborhood",
    )
    postal_code: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        description="Postal code (if applicable)",
    )
    latitude: Optional[Decimal] = Field(
        default=None,
        nullable=True,
        max_digits=10,
        decimal_places=8,
        description="GPS latitude for delivery routing",
    )
    longitude: Optional[Decimal] = Field(
        default=None,
        nullable=True,
        max_digits=11,
        decimal_places=8,
        description="GPS longitude for delivery routing",
    )

    # Business Details
    restaurant_type: str = Field(
        max_length=50,
        nullable=False,
        index=True,
        description="Type: fast_food, fine_dining, cafe, bakery, etc.",
    )
    cuisine_type: str = Field(
        max_length=100,
        nullable=False,
        description="Cuisine: iraqi, lebanese, turkish, international, etc.",
    )
    seating_capacity: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Number of seats",
    )
    operating_hours: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description='Operating hours JSON: {"monday": {"open": "09:00", "close": "23:00"}}',
    )

    # Media
    logo_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="URL to restaurant logo",
    )
    cover_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="URL to restaurant cover image",
    )

    # Verification
    is_verified: bool = Field(
        default=False,
        nullable=False,
        index=True,
        description="Whether restaurant is verified by admin",
    )
    verification_status: str = Field(
        default="pending",
        max_length=50,
        nullable=False,
        description="Status: pending, approved, rejected",
    )
    verification_document_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="URL to uploaded trade license/verification document",
    )
    verified_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Timestamp when restaurant was verified",
    )
    verified_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="Admin user who verified the restaurant",
    )

    # Settings
    auto_accept_orders: bool = Field(
        default=True,
        nullable=False,
        description="Auto-accept orders or require manual confirmation",
    )
    preferred_payment_method: str = Field(
        default="cash",
        max_length=50,
        nullable=False,
        description="Preferred payment method: cash, credit, bank_transfer",
    )

    # Relationships
    owner_id: UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        description="User ID of the restaurant owner",
    )

    # Relationship objects (populated by SQLModel)
    owner: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Restaurant.owner_id]",
            "lazy": "selectin",
        },
    )

    staff: List["User"] = Relationship(
        back_populates="restaurant",
        sa_relationship_kwargs={
            "foreign_keys": "[User.restaurant_id]",
            "lazy": "selectin",
        },
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Restaurant {self.name_en}>"

    @property
    def display_name(self) -> str:
        """Get display name based on language preference."""
        return self.name_ar or self.name_en

    @property
    def full_address(self) -> str:
        """Get full address as a single string."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.district,
            self.city,
        ]
        return ", ".join(filter(None, parts))

    def is_open_now(self) -> bool:
        """
        Check if restaurant is currently open based on operating hours.

        Returns:
            bool: True if restaurant is open now
        """
        if not self.operating_hours:
            return True  # Assume open if no hours specified

        from datetime import datetime

        now = datetime.now()
        day_name = now.strftime("%A").lower()  # monday, tuesday, etc.

        if day_name not in self.operating_hours:
            return False

        hours = self.operating_hours[day_name]
        if not hours or "open" not in hours or "close" not in hours:
            return False

        try:
            open_time = datetime.strptime(hours["open"], "%H:%M").time()
            close_time = datetime.strptime(hours["close"], "%H:%M").time()
            current_time = now.time()

            return open_time <= current_time <= close_time
        except (ValueError, KeyError):
            return True  # Default to open if parsing fails

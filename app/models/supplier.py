"""
Supplier Model

This module defines the Supplier model for supply chain management.
Suppliers provide products to restaurants through the platform.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


class Supplier(BaseModel, table=True):
    """
    Supplier model representing a business that supplies products to restaurants.

    This model stores comprehensive supplier information including business details,
    contact information, product categories, delivery capabilities, payment options,
    verification status, and ratings.
    """

    __tablename__ = "supplier"

    # Primary Key
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique identifier for the supplier",
    )

    # =========================================================================
    # Basic Information (Bilingual)
    # =========================================================================
    company_name_ar: str = Field(
        max_length=255,
        nullable=False,
        description="Company name in Arabic",
    )
    company_name_en: str = Field(
        max_length=255,
        nullable=False,
        description="Company name in English",
    )
    trade_license: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="Trade license number issued by government",
    )
    tax_id: Optional[str] = Field(
        default=None,
        max_length=50,
        nullable=True,
        description="Tax identification number",
    )
    description_ar: Optional[str] = Field(
        default=None,
        max_length=1000,
        nullable=True,
        description="Company description in Arabic",
    )
    description_en: Optional[str] = Field(
        default=None,
        max_length=1000,
        nullable=True,
        description="Company description in English",
    )

    # =========================================================================
    # Contact Information
    # =========================================================================
    email: str = Field(
        max_length=255,
        nullable=False,
        index=True,
        description="Primary business email",
    )
    phone_primary: str = Field(
        max_length=20,
        nullable=False,
        description="Primary contact phone number in E.164 format",
    )
    phone_secondary: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        description="Secondary contact phone number",
    )
    website: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="Company website URL",
    )

    # =========================================================================
    # Address with GPS Coordinates
    # =========================================================================
    address_line1: str = Field(
        max_length=255,
        nullable=False,
        description="Primary address line",
    )
    address_line2: Optional[str] = Field(
        default=None,
        max_length=255,
        nullable=True,
        description="Secondary address line (building, floor, etc.)",
    )
    city: str = Field(
        max_length=100,
        nullable=False,
        index=True,
        description="City name (e.g., Baghdad, Erbil, Basra)",
    )
    district: str = Field(
        max_length=100,
        nullable=False,
        description="District/neighborhood within city",
    )
    postal_code: Optional[str] = Field(
        default=None,
        max_length=20,
        nullable=True,
        description="Postal/ZIP code if applicable",
    )
    latitude: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=8,
        nullable=True,
        description="Warehouse/office latitude for delivery routing",
    )
    longitude: Optional[Decimal] = Field(
        default=None,
        max_digits=11,
        decimal_places=8,
        nullable=True,
        description="Warehouse/office longitude for delivery routing",
    )

    # =========================================================================
    # Business Details
    # =========================================================================
    product_categories: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="List of product categories supplied (e.g., ['dairy', 'meat', 'vegetables'])",
    )
    delivery_areas: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="List of cities/districts where supplier delivers",
    )
    minimum_order_value: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        nullable=True,
        description="Minimum order value in IQD for delivery",
    )
    delivery_fee: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        nullable=True,
        description="Standard delivery fee in IQD",
    )
    free_delivery_threshold: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        nullable=True,
        description="Order value for free delivery in IQD",
    )
    operating_hours: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Operating hours per day (e.g., {'saturday': {'open': '08:00', 'close': '18:00'}})",
    )

    # =========================================================================
    # Media
    # =========================================================================
    logo_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="URL to company logo image",
    )
    cover_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="URL to company cover/banner image",
    )

    # =========================================================================
    # Verification Status
    # =========================================================================
    is_verified: bool = Field(
        default=False,
        nullable=False,
        index=True,
        description="Whether supplier has been verified by admin",
    )
    verification_status: str = Field(
        default="pending",
        max_length=50,
        nullable=False,
        description="Verification status: pending, approved, rejected",
    )
    verification_document_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="URL to uploaded verification documents (trade license, etc.)",
    )
    verified_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Timestamp when supplier was verified",
    )
    verified_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="Admin user who verified the supplier",
    )

    # =========================================================================
    # Payment Settings
    # =========================================================================
    accepts_cash: bool = Field(
        default=True,
        nullable=False,
        description="Whether supplier accepts cash on delivery",
    )
    accepts_credit: bool = Field(
        default=False,
        nullable=False,
        description="Whether supplier accepts credit card payments",
    )
    allows_installments: bool = Field(
        default=False,
        nullable=False,
        description="Whether supplier allows installment payments",
    )
    payment_terms_days: int = Field(
        default=0,
        nullable=False,
        description="Payment terms in days (0=immediate, 30=net 30, etc.)",
    )

    # =========================================================================
    # Ratings and Reviews
    # =========================================================================
    average_rating: Optional[Decimal] = Field(
        default=None,
        max_digits=3,
        decimal_places=2,
        nullable=True,
        description="Average rating from 0.00 to 5.00",
    )
    total_reviews: int = Field(
        default=0,
        nullable=False,
        description="Total number of reviews received",
    )
    total_orders_completed: int = Field(
        default=0,
        nullable=False,
        description="Total number of successfully completed orders",
    )

    # =========================================================================
    # Settings
    # =========================================================================
    auto_accept_orders: bool = Field(
        default=False,
        nullable=False,
        description="Whether to automatically accept incoming orders",
    )
    lead_time_hours: int = Field(
        default=24,
        nullable=False,
        description="Default lead time for order fulfillment in hours",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        index=True,
        description="Whether supplier is currently active and accepting orders",
    )

    # =========================================================================
    # Relationships
    # =========================================================================
    owner_id: UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        description="Owner/creator of the supplier account",
    )

    # Define relationships (will be populated by SQLModel)
    owner: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Supplier.owner_id]",
            "lazy": "joined",
        }
    )

    staff: List["User"] = Relationship(
        back_populates="supplier",
        sa_relationship_kwargs={
            "foreign_keys": "[User.supplier_id]",
            "lazy": "selectin",
        },
    )

    verified_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Supplier.verified_by_id]",
            "lazy": "joined",
        }
    )

    products: List["Product"] = Relationship(
        back_populates="supplier",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )

    # =========================================================================
    # Helper Properties and Methods
    # =========================================================================
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.district,
            self.city,
            self.postal_code,
        ]
        return ", ".join(filter(None, parts))

    @property
    def display_name(self) -> str:
        """Get display name (Arabic preferred, fallback to English)."""
        return self.company_name_ar or self.company_name_en

    def is_open_now(self) -> bool:
        """
        Check if supplier is currently open based on operating hours.

        Returns:
            bool: True if open now, False otherwise
        """
        if not self.operating_hours:
            return True  # Assume 24/7 if no hours specified

        from datetime import datetime
        import calendar

        now = datetime.now()
        day_name = calendar.day_name[now.weekday()].lower()

        if day_name not in self.operating_hours:
            return False

        hours = self.operating_hours[day_name]
        if not hours or hours.get("closed"):
            return False

        try:
            open_time = datetime.strptime(hours["open"], "%H:%M").time()
            close_time = datetime.strptime(hours["close"], "%H:%M").time()
            current_time = now.time()

            return open_time <= current_time <= close_time
        except (KeyError, ValueError):
            return True  # If parsing fails, assume open

    def can_deliver_to(self, city: str, district: Optional[str] = None) -> bool:
        """
        Check if supplier delivers to specified location.

        Args:
            city: City name
            district: Optional district name

        Returns:
            bool: True if delivery available, False otherwise
        """
        if not self.delivery_areas:
            return False

        # Check if city is in delivery areas
        if city not in self.delivery_areas:
            return False

        # If no district specified, city match is enough
        if not district:
            return True

        # Check if specific district is covered
        city_data = self.delivery_areas.get(city, {})
        if isinstance(city_data, list):
            return district in city_data

        return True  # If no district list, assume all districts in city

    def __repr__(self) -> str:
        """String representation of Supplier."""
        return f"<Supplier(id={self.id}, company={self.display_name}, verified={self.is_verified})>"

"""
Restaurant Schemas

Request/response schemas for Restaurant operations.
"""

from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import base_config


# ============= Base Schemas =============

class RestaurantBase(BaseModel):
    """Base restaurant fields (common to all operations)."""

    model_config = base_config

    name_ar: str = Field(
        min_length=2,
        max_length=255,
        description="Restaurant name in Arabic",
        examples=["مطعم بغداد"],
    )
    name_en: str = Field(
        min_length=2,
        max_length=255,
        description="Restaurant name in English",
        examples=["Baghdad Restaurant"],
    )
    email: EmailStr = Field(
        description="Restaurant email address",
        examples=["restaurant@example.com"],
    )
    phone_primary: str = Field(
        max_length=20,
        description="Primary phone number",
        examples=["+9647901234567"],
    )
    phone_secondary: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Secondary phone number",
        examples=["+9647901234568"],
    )
    address_line1: str = Field(
        min_length=5,
        max_length=255,
        description="Address line 1",
        examples=["123 Main Street"],
    )
    address_line2: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Address line 2",
    )
    city: str = Field(
        max_length=100,
        description="City",
        examples=["Baghdad"],
    )
    district: str = Field(
        max_length=100,
        description="District/Neighborhood",
        examples=["Karada"],
    )
    postal_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Postal code",
    )
    latitude: Optional[Decimal] = Field(
        default=None,
        description="GPS latitude",
        examples=[33.3152],
    )
    longitude: Optional[Decimal] = Field(
        default=None,
        description="GPS longitude",
        examples=[44.3661],
    )
    restaurant_type: str = Field(
        max_length=50,
        description="Restaurant type",
        examples=["fast_food", "fine_dining", "cafe", "bakery"],
    )
    cuisine_type: str = Field(
        max_length=100,
        description="Cuisine type",
        examples=["iraqi", "lebanese", "turkish", "international"],
    )
    seating_capacity: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of seats",
        examples=[50],
    )


# ============= Create Schemas =============

class RestaurantCreate(RestaurantBase):
    """
    Schema for creating a new restaurant.

    Used when restaurant owner registers their business.
    """

    model_config = base_config

    business_registration: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Business registration number",
    )
    operating_hours: Optional[Dict[str, Dict[str, str]]] = Field(
        default=None,
        description='Operating hours: {"monday": {"open": "09:00", "close": "23:00"}}',
        examples=[{
            "monday": {"open": "09:00", "close": "23:00"},
            "tuesday": {"open": "09:00", "close": "23:00"},
        }],
    )
    preferred_payment_method: str = Field(
        default="cash",
        max_length=50,
        description="Preferred payment method",
        examples=["cash"],
    )


# ============= Update Schemas =============

class RestaurantUpdate(BaseModel):
    """
    Schema for updating restaurant information.

    All fields are optional (partial update).
    """

    model_config = base_config

    name_ar: Optional[str] = Field(default=None, min_length=2, max_length=255)
    name_en: Optional[str] = Field(default=None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(default=None, max_length=20)
    phone_secondary: Optional[str] = Field(default=None, max_length=20)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    restaurant_type: Optional[str] = Field(default=None, max_length=50)
    cuisine_type: Optional[str] = Field(default=None, max_length=100)
    seating_capacity: Optional[int] = Field(default=None, ge=1)
    business_registration: Optional[str] = Field(default=None, max_length=100)
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    preferred_payment_method: Optional[str] = Field(default=None, max_length=50)
    auto_accept_orders: Optional[bool] = None


# ============= Read Schemas =============

class RestaurantRead(RestaurantBase):
    """
    Schema for reading restaurant data.

    Includes all fields plus metadata.
    """

    model_config = base_config

    id: UUID
    business_registration: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None

    # Verification
    is_verified: bool
    verification_status: str
    verified_at: Optional[datetime] = None

    # Settings
    auto_accept_orders: bool
    preferred_payment_method: str

    # Metadata
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class RestaurantList(BaseModel):
    """
    Simplified restaurant info for list endpoints.

    Less detail than RestaurantRead for better performance.
    """

    model_config = base_config

    id: UUID
    name_ar: str
    name_en: str
    city: str
    district: str
    restaurant_type: str
    cuisine_type: str
    is_verified: bool
    logo_url: Optional[str] = None
    created_at: datetime


class RestaurantProfile(RestaurantRead):
    """
    Extended restaurant profile with additional information.

    Includes staff count and other metrics.
    """

    model_config = base_config

    # Can add additional computed fields here
    # staff_count: int = 0
    # total_orders: int = 0
    pass


# ============= Verification Schemas =============

class RestaurantVerification(BaseModel):
    """
    Schema for admin to verify/reject restaurant.
    """

    model_config = base_config

    verification_status: str = Field(
        description="Status: approved or rejected",
        examples=["approved"],
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Admin notes about verification",
    )


# ============= Staff Management Schemas =============

class RestaurantStaffAdd(BaseModel):
    """
    Schema for adding staff member to restaurant.
    """

    model_config = base_config

    user_id: UUID = Field(
        description="User ID to add as staff",
    )
    role: str = Field(
        default="staff",
        description="Role: manager or staff",
        examples=["staff"],
    )


class RestaurantStaffRemove(BaseModel):
    """
    Schema for removing staff member from restaurant.
    """

    model_config = base_config

    user_id: UUID = Field(
        description="User ID to remove from staff",
    )

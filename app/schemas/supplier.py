"""
Supplier Schemas

This module defines Pydantic schemas for Supplier API requests and responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class SupplierBase(BaseModel):
    """Base schema with common supplier fields."""

    company_name_ar: str = Field(..., max_length=255, description="Company name in Arabic")
    company_name_en: str = Field(..., max_length=255, description="Company name in English")
    email: EmailStr = Field(..., description="Primary business email")
    phone_primary: str = Field(..., max_length=20, description="Primary contact phone")
    phone_secondary: Optional[str] = Field(None, max_length=20, description="Secondary contact phone")
    website: Optional[str] = Field(None, max_length=500, description="Company website")

    # Address
    address_line1: str = Field(..., max_length=255, description="Primary address")
    address_line2: Optional[str] = Field(None, max_length=255, description="Secondary address")
    city: str = Field(..., max_length=100, description="City name")
    district: str = Field(..., max_length=100, description="District/neighborhood")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Warehouse latitude")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Warehouse longitude")

    # Business details
    product_categories: Optional[List[str]] = Field(None, description="Product categories supplied")
    minimum_order_value: Optional[Decimal] = Field(None, ge=0, description="Minimum order value in IQD")
    delivery_fee: Optional[Decimal] = Field(None, ge=0, description="Standard delivery fee in IQD")
    free_delivery_threshold: Optional[Decimal] = Field(None, ge=0, description="Free delivery threshold in IQD")

    @field_validator("phone_primary", "phone_secondary")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (E.164)."""
        if v is None:
            return v
        # Basic validation - should start with + and contain only digits
        if not v.startswith("+"):
            raise ValueError("Phone number must be in E.164 format (e.g., +9647901234567)")
        if not v[1:].isdigit():
            raise ValueError("Phone number must contain only digits after +")
        if len(v) < 10 or len(v) > 20:
            raise ValueError("Phone number must be between 10 and 20 characters")
        return v


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier."""

    trade_license: Optional[str] = Field(None, max_length=100, description="Trade license number")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax ID number")
    description_ar: Optional[str] = Field(None, max_length=1000, description="Description in Arabic")
    description_en: Optional[str] = Field(None, max_length=1000, description="Description in English")

    # Business configuration
    delivery_areas: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Delivery areas as dict of city -> list of districts",
        examples=[{"Baghdad": ["Karrada", "Mansour"], "Erbil": ["Downtown"]}],
    )
    operating_hours: Optional[Dict[str, Dict[str, str]]] = Field(
        None,
        description="Operating hours per day",
        examples=[{
            "saturday": {"open": "08:00", "close": "18:00"},
            "sunday": {"open": "08:00", "close": "18:00"},
            "friday": {"closed": True}
        }],
    )

    # Payment settings
    accepts_cash: bool = Field(True, description="Accept cash payments")
    accepts_credit: bool = Field(False, description="Accept credit card payments")
    allows_installments: bool = Field(False, description="Allow installment payments")
    payment_terms_days: int = Field(0, ge=0, description="Payment terms in days")

    # Settings
    auto_accept_orders: bool = Field(False, description="Auto-accept incoming orders")
    lead_time_hours: int = Field(24, ge=1, description="Default lead time in hours")


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier (all fields optional)."""

    company_name_ar: Optional[str] = Field(None, max_length=255)
    company_name_en: Optional[str] = Field(None, max_length=255)
    trade_license: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    description_ar: Optional[str] = Field(None, max_length=1000)
    description_en: Optional[str] = Field(None, max_length=1000)

    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)

    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)

    product_categories: Optional[List[str]] = None
    delivery_areas: Optional[Dict[str, List[str]]] = None
    minimum_order_value: Optional[Decimal] = Field(None, ge=0)
    delivery_fee: Optional[Decimal] = Field(None, ge=0)
    free_delivery_threshold: Optional[Decimal] = Field(None, ge=0)
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None

    logo_url: Optional[str] = Field(None, max_length=500)
    cover_image_url: Optional[str] = Field(None, max_length=500)

    accepts_cash: Optional[bool] = None
    accepts_credit: Optional[bool] = None
    allows_installments: Optional[bool] = None
    payment_terms_days: Optional[int] = Field(None, ge=0)

    auto_accept_orders: Optional[bool] = None
    lead_time_hours: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None

    @field_validator("phone_primary", "phone_secondary")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (E.164)."""
        if v is None:
            return v
        if not v.startswith("+"):
            raise ValueError("Phone number must be in E.164 format (e.g., +9647901234567)")
        if not v[1:].isdigit():
            raise ValueError("Phone number must contain only digits after +")
        if len(v) < 10 or len(v) > 20:
            raise ValueError("Phone number must be between 10 and 20 characters")
        return v


class SupplierRead(SupplierBase):
    """Schema for reading supplier data."""

    id: UUID
    trade_license: Optional[str] = None
    tax_id: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None

    delivery_areas: Optional[Dict[str, List[str]]] = None
    operating_hours: Optional[Dict[str, Dict[str, str]]] = None

    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None

    is_verified: bool
    verification_status: str
    verified_at: Optional[datetime] = None

    accepts_cash: bool
    accepts_credit: bool
    allows_installments: bool
    payment_terms_days: int

    average_rating: Optional[Decimal] = None
    total_reviews: int
    total_orders_completed: int

    auto_accept_orders: bool
    lead_time_hours: int
    is_active: bool

    owner_id: UUID

    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[UUID] = None
    updated_by_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class SupplierList(BaseModel):
    """Schema for supplier list items (lightweight)."""

    id: UUID
    company_name_ar: str
    company_name_en: str
    city: str
    district: str
    product_categories: Optional[List[str]] = None
    is_verified: bool
    average_rating: Optional[Decimal] = None
    total_reviews: int
    is_active: bool
    logo_url: Optional[str] = None
    minimum_order_value: Optional[Decimal] = None
    delivery_fee: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class SupplierVerification(BaseModel):
    """Schema for supplier verification by admin."""

    verification_status: str = Field(
        ...,
        pattern="^(approved|rejected)$",
        description="Verification decision: approved or rejected",
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Admin notes about verification decision",
    )


class SupplierStaffAdd(BaseModel):
    """Schema for adding staff member to supplier."""

    user_id: UUID = Field(..., description="User ID to add as staff")
    role: str = Field(
        "staff",
        max_length=50,
        description="Role within supplier organization",
    )


class SupplierStaffRemove(BaseModel):
    """Schema for removing staff member from supplier."""

    user_id: UUID = Field(..., description="User ID to remove from staff")


class SupplierSearchFilters(BaseModel):
    """Schema for supplier search filters."""

    query: Optional[str] = Field(None, max_length=255, description="Search by company name")
    city: Optional[str] = Field(None, max_length=100, description="Filter by city")
    product_category: Optional[str] = Field(None, max_length=100, description="Filter by product category")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    min_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Minimum average rating")
    accepts_cash: Optional[bool] = Field(None, description="Filter by cash payment acceptance")
    accepts_credit: Optional[bool] = Field(None, description="Filter by credit payment acceptance")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=100, description="Maximum number of records to return")


class SupplierStats(BaseModel):
    """Schema for supplier statistics."""

    total_orders: int
    completed_orders: int
    pending_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    average_rating: Optional[Decimal] = None
    total_reviews: int
    active_products: int
    total_products: int

    model_config = {"from_attributes": True}

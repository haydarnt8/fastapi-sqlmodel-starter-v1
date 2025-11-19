"""
Product Schemas

Pydantic schemas for Product API request/response validation.

Schemas:
- ProductBase: Base schema with common fields
- ProductCreate: Schema for creating new products
- ProductUpdate: Schema for updating products (all fields optional)
- ProductRead: Full product details for API responses
- ProductList: Lightweight schema for list views
- ProductSearchFilters: Advanced search/filter parameters
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ProductBase(BaseModel):
    """Base product schema with common fields."""

    # Basic Info
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=50, description="Product barcode")

    # Bilingual Information
    name_ar: str = Field(..., min_length=1, max_length=255, description="Product name in Arabic")
    name_en: str = Field(..., min_length=1, max_length=255, description="Product name in English")
    description_ar: Optional[str] = Field(None, max_length=2000, description="Description in Arabic")
    description_en: Optional[str] = Field(None, max_length=2000, description="Description in English")

    # Categorization
    category: str = Field(..., min_length=1, max_length=100, description="Primary category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategory")
    tags: Optional[List[str]] = Field(None, description="Product tags for search")

    # Pricing
    unit_price: Decimal = Field(..., gt=0, description="Price per unit")
    currency: str = Field(default="IQD", max_length=3, description="Currency code")
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Tax rate percentage")
    discount_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Discount percentage")

    # Inventory
    stock_quantity: Decimal = Field(default=Decimal("0.00"), ge=0, description="Current stock")
    reorder_level: Decimal = Field(default=Decimal("10.00"), ge=0, description="Reorder level")
    unit_of_measure: str = Field(..., min_length=1, max_length=20, description="Unit of measure")
    minimum_order_quantity: Decimal = Field(default=Decimal("1.00"), gt=0, description="Minimum order quantity")

    # Product Details
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    manufacturer: Optional[str] = Field(None, max_length=200, description="Manufacturer")
    origin_country: Optional[str] = Field(None, max_length=100, description="Country of origin")
    shelf_life_days: Optional[int] = Field(None, ge=0, description="Shelf life in days")
    storage_instructions: Optional[str] = Field(None, max_length=500, description="Storage instructions")

    # Media
    image_urls: Optional[List[str]] = Field(None, description="Product image URLs")
    primary_image_url: Optional[str] = Field(None, max_length=500, description="Primary image URL")

    # SEO
    search_keywords: Optional[List[str]] = Field(None, description="Search keywords")

    @field_validator("unit_of_measure")
    @classmethod
    def validate_unit_of_measure(cls, v: str) -> str:
        """Validate unit of measure against allowed values."""
        allowed_units = [
            "kg", "g", "liter", "ml", "piece", "box", "carton",
            "dozen", "pack", "bag", "can", "bottle", "jar", "tray"
        ]
        if v.lower() not in allowed_units:
            raise ValueError(
                f"Invalid unit_of_measure. Allowed values: {', '.join(allowed_units)}"
            )
        return v.lower()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        allowed_currencies = ["IQD", "USD", "EUR"]
        if v.upper() not in allowed_currencies:
            raise ValueError(f"Invalid currency. Allowed values: {', '.join(allowed_currencies)}")
        return v.upper()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category against predefined list."""
        allowed_categories = [
            "Vegetables", "Fruits", "Meat", "Poultry", "Seafood",
            "Dairy", "Bakery", "Beverages", "Dry Goods", "Spices",
            "Frozen Foods", "Canned Goods", "Snacks", "Oils",
            "Cleaning Supplies", "Disposables", "Equipment", "Other"
        ]
        if v not in allowed_categories:
            raise ValueError(f"Invalid category. Allowed values: {', '.join(allowed_categories)}")
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    supplier_id: UUID = Field(..., description="Supplier ID who offers this product")


class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields are optional."""

    # Basic Info
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)

    # Bilingual Information
    name_ar: Optional[str] = Field(None, min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, min_length=1, max_length=255)
    description_ar: Optional[str] = Field(None, max_length=2000)
    description_en: Optional[str] = Field(None, max_length=2000)

    # Categorization
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None

    # Pricing
    unit_price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    # Inventory
    stock_quantity: Optional[Decimal] = Field(None, ge=0)
    reorder_level: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, min_length=1, max_length=20)
    minimum_order_quantity: Optional[Decimal] = Field(None, gt=0)

    # Product Details
    brand: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    origin_country: Optional[str] = Field(None, max_length=100)
    shelf_life_days: Optional[int] = Field(None, ge=0)
    storage_instructions: Optional[str] = Field(None, max_length=500)

    # Media
    image_urls: Optional[List[str]] = None
    primary_image_url: Optional[str] = Field(None, max_length=500)

    # Status
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    availability_status: Optional[str] = Field(
        None,
        pattern="^(in_stock|out_of_stock|discontinued)$",
        description="Availability status"
    )

    # SEO
    search_keywords: Optional[List[str]] = None


class ProductRead(ProductBase):
    """Full product details for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    supplier_id: UUID
    is_active: bool
    is_featured: bool
    availability_status: str

    # Calculated fields
    final_price: Decimal = Field(..., description="Price after discount")
    price_with_tax: Decimal = Field(..., description="Price including tax")
    is_low_stock: bool = Field(..., description="Stock is below reorder level")
    is_in_stock: bool = Field(..., description="Product is available")

    # Audit fields
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    """Lightweight product schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name_ar: str
    name_en: str
    category: str
    subcategory: Optional[str]
    unit_price: Decimal
    currency: str
    discount_percentage: Decimal
    final_price: Decimal
    stock_quantity: Decimal
    unit_of_measure: str
    supplier_id: UUID
    primary_image_url: Optional[str]
    is_active: bool
    is_featured: bool
    availability_status: str
    is_in_stock: bool


class ProductSearchFilters(BaseModel):
    """Advanced search and filter parameters."""

    # Text search
    query: Optional[str] = Field(
        None,
        description="Search in product name (Arabic/English), SKU, or description"
    )

    # Filters
    supplier_id: Optional[UUID] = Field(None, description="Filter by supplier")
    category: Optional[str] = Field(None, description="Filter by category")
    subcategory: Optional[str] = Field(None, description="Filter by subcategory")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (AND logic)")

    # Price range
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")

    # Status filters
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_featured: Optional[bool] = Field(None, description="Filter featured products")
    availability_status: Optional[str] = Field(
        None,
        pattern="^(in_stock|out_of_stock|discontinued)$",
        description="Filter by availability"
    )
    in_stock_only: bool = Field(
        default=True,
        description="Show only products in stock (default: true)"
    )

    # Inventory filters
    low_stock_only: Optional[bool] = Field(
        None,
        description="Show only products with low stock (below reorder level)"
    )

    # Sorting
    sort_by: str = Field(
        default="created_at",
        description="Sort field: name_ar, name_en, unit_price, stock_quantity, created_at"
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
            "name_ar", "name_en", "unit_price", "stock_quantity",
            "created_at", "updated_at", "category"
        ]
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort_by. Allowed values: {', '.join(allowed_fields)}")
        return v


class ProductStockUpdate(BaseModel):
    """Schema for updating product stock."""

    stock_quantity: Decimal = Field(..., ge=0, description="New stock quantity")
    notes: Optional[str] = Field(None, max_length=500, description="Stock update notes")


class ProductBulkPriceUpdate(BaseModel):
    """Schema for bulk price updates."""

    product_ids: List[UUID] = Field(..., min_length=1, description="List of product IDs")
    discount_percentage: Decimal = Field(..., ge=0, le=100, description="New discount percentage")

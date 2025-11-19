"""
Product Model

Represents products offered by suppliers in the supply chain system.

Business Rules:
- Each product belongs to one supplier
- Products have bilingual information (Arabic/English)
- Inventory tracking with reorder levels
- Support for multiple units of measure (kg, liter, piece, box, etc.)
- Product images stored as JSON array of URLs
- Categories stored as JSON array
- Pricing in Iraqi Dinar (IQD) by default
- Support for tax calculations
- Products can be active/inactive
- Soft delete support via BaseModel

Relationships:
- supplier: Many-to-One with Supplier (each product belongs to one supplier)
- order_items: One-to-Many with OrderItem (future implementation)
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal

from sqlmodel import Field, Relationship, Column, JSON
from sqlalchemy import Index

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.supplier import Supplier


class Product(BaseModel, table=True):
    """
    Product model for supply chain marketplace.

    Attributes:
        Basic Info:
            id: Unique product identifier (UUID)
            sku: Stock Keeping Unit (supplier's product code)
            barcode: Product barcode (EAN-13, UPC, etc.)

        Bilingual Information:
            name_ar: Product name in Arabic
            name_en: Product name in English
            description_ar: Detailed description in Arabic
            description_en: Detailed description in English

        Supplier Relationship:
            supplier_id: Foreign key to supplier
            supplier: Relationship to Supplier model

        Categorization:
            category: Primary category (e.g., "Vegetables", "Dairy", "Meat")
            subcategory: Subcategory (e.g., "Fresh Vegetables", "Cheese")
            tags: Additional tags for search (JSON array)

        Pricing:
            unit_price: Price per unit
            currency: Currency code (default: IQD)
            tax_rate: Tax percentage (default: 0)
            discount_percentage: Current discount (0-100)
            final_price: Calculated price after discount

        Inventory:
            stock_quantity: Current stock available
            reorder_level: Minimum stock before reorder alert
            unit_of_measure: Unit type (kg, liter, piece, box, etc.)
            minimum_order_quantity: Minimum quantity per order

        Product Details:
            brand: Brand name
            manufacturer: Manufacturer name
            origin_country: Country of origin
            shelf_life_days: Product shelf life in days
            storage_instructions: How to store the product

        Media:
            image_urls: Array of product image URLs (JSON)
            primary_image_url: Main product image

        Status:
            is_active: Product available for ordering
            is_featured: Featured/promoted product
            availability_status: "in_stock", "out_of_stock", "discontinued"

        SEO & Search:
            search_keywords: Additional keywords for search (JSON array)

        Audit Fields (from BaseModel):
            created_at, updated_at, deleted_at
            created_by_id, updated_by_id, deleted_by_id
            is_deleted
    """

    __tablename__ = "product"

    # ==================== Primary Key ====================
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique product identifier"
    )

    # ==================== Basic Information ====================
    sku: str = Field(
        max_length=100,
        nullable=False,
        index=True,
        description="Stock Keeping Unit - Supplier's product code"
    )

    barcode: Optional[str] = Field(
        default=None,
        max_length=50,
        nullable=True,
        index=True,
        description="Product barcode (EAN-13, UPC, etc.)"
    )

    # ==================== Bilingual Information ====================
    name_ar: str = Field(
        max_length=255,
        nullable=False,
        index=True,
        description="Product name in Arabic"
    )

    name_en: str = Field(
        max_length=255,
        nullable=False,
        index=True,
        description="Product name in English"
    )

    description_ar: Optional[str] = Field(
        default=None,
        max_length=2000,
        nullable=True,
        description="Detailed product description in Arabic"
    )

    description_en: Optional[str] = Field(
        default=None,
        max_length=2000,
        nullable=True,
        description="Detailed product description in English"
    )

    # ==================== Supplier Relationship ====================
    supplier_id: UUID = Field(
        foreign_key="supplier.id",
        nullable=False,
        index=True,
        description="Supplier who offers this product"
    )

    # ==================== Categorization ====================
    category: str = Field(
        max_length=100,
        nullable=False,
        index=True,
        description="Primary category (e.g., Vegetables, Dairy, Meat)"
    )

    subcategory: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        index=True,
        description="Subcategory for finer classification"
    )

    tags: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional tags for search (JSON array: ['organic', 'halal', 'fresh'])"
    )

    # ==================== Pricing ====================
    unit_price: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Price per unit in specified currency"
    )

    currency: str = Field(
        default="IQD",
        max_length=3,
        nullable=False,
        description="Currency code (ISO 4217) - default: IQD"
    )

    tax_rate: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=5,
        decimal_places=2,
        nullable=False,
        description="Tax rate percentage (e.g., 15.00 for 15%)"
    )

    discount_percentage: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=5,
        decimal_places=2,
        nullable=False,
        description="Current discount percentage (0-100)"
    )

    # ==================== Inventory ====================
    stock_quantity: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Current stock available"
    )

    reorder_level: Decimal = Field(
        default=Decimal("10.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Minimum stock level before reorder alert"
    )

    unit_of_measure: str = Field(
        max_length=20,
        nullable=False,
        description="Unit of measure (kg, liter, piece, box, carton, dozen)"
    )

    minimum_order_quantity: Decimal = Field(
        default=Decimal("1.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Minimum quantity that can be ordered"
    )

    # ==================== Product Details ====================
    brand: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="Brand name"
    )

    manufacturer: Optional[str] = Field(
        default=None,
        max_length=200,
        nullable=True,
        description="Manufacturer or producer name"
    )

    origin_country: Optional[str] = Field(
        default=None,
        max_length=100,
        nullable=True,
        description="Country of origin"
    )

    shelf_life_days: Optional[int] = Field(
        default=None,
        nullable=True,
        description="Product shelf life in days"
    )

    storage_instructions: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="Storage instructions (e.g., 'Keep refrigerated at 2-8°C')"
    )

    # ==================== Media ====================
    image_urls: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Array of image URLs (JSON: ['url1', 'url2', 'url3'])"
    )

    primary_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="Primary product image URL"
    )

    # ==================== Status ====================
    is_active: bool = Field(
        default=True,
        nullable=False,
        index=True,
        description="Product is active and available for ordering"
    )

    is_featured: bool = Field(
        default=False,
        nullable=False,
        description="Product is featured/promoted"
    )

    availability_status: str = Field(
        default="in_stock",
        max_length=50,
        nullable=False,
        index=True,
        description="Availability status: in_stock, out_of_stock, discontinued"
    )

    # ==================== SEO & Search ====================
    search_keywords: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional keywords for search optimization (JSON array)"
    )

    # ==================== Relationships ====================
    supplier: Optional["Supplier"] = Relationship(
        back_populates="products",
        sa_relationship_kwargs={
            "lazy": "selectin"
        }
    )

    # ==================== Calculated Properties ====================
    @property
    def final_price(self) -> Decimal:
        """Calculate final price after discount."""
        if self.discount_percentage > 0:
            discount_amount = self.unit_price * (self.discount_percentage / Decimal("100"))
            return self.unit_price - discount_amount
        return self.unit_price

    @property
    def price_with_tax(self) -> Decimal:
        """Calculate price including tax."""
        tax_amount = self.final_price * (self.tax_rate / Decimal("100"))
        return self.final_price + tax_amount

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below reorder level."""
        return self.stock_quantity <= self.reorder_level

    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock and available."""
        return (
            self.is_active
            and not self.is_deleted
            and self.availability_status == "in_stock"
            and self.stock_quantity > 0
        )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name_en={self.name_en}, sku={self.sku}, price={self.unit_price})>"


# ==================== Table Indexes ====================
# Additional composite indexes for common queries
Index("ix_product_supplier_category", Product.supplier_id, Product.category)
Index("ix_product_active_stock", Product.is_active, Product.availability_status)

"""
Order and OrderItem Models

Represents orders placed by restaurants to suppliers in the supply chain system.

Order Workflow:
1. draft → pending (submitted by restaurant)
2. pending → confirmed (approved by supplier)
3. confirmed → processing (being prepared)
4. processing → ready_for_delivery (ready to ship)
5. ready_for_delivery → in_transit (out for delivery)
6. in_transit → delivered (completed successfully)

Alternative flows:
- Any state → cancelled (cancelled by restaurant or supplier)
- confirmed/processing → rejected (rejected by supplier after approval)

Business Rules:
- Each order belongs to one restaurant and one supplier
- Orders contain multiple order items (products with quantity and price snapshot)
- Order totals are calculated from order items
- Price snapshots prevent price changes from affecting historical orders
- Orders track delivery information and timestamps
- Payment tracking (paid/unpaid status)
- Audit trail for all status changes
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, Relationship, Column, JSON
from sqlalchemy import Index

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.restaurant import Restaurant
    from app.models.supplier import Supplier
    from app.models.product import Product
    from app.models.delivery import Delivery


class OrderStatus(str, Enum):
    """Order status enumeration."""
    DRAFT = "draft"  # Order being created (cart)
    PENDING = "pending"  # Submitted, awaiting supplier approval
    CONFIRMED = "confirmed"  # Approved by supplier
    PROCESSING = "processing"  # Being prepared
    READY_FOR_DELIVERY = "ready_for_delivery"  # Ready to ship
    IN_TRANSIT = "in_transit"  # Out for delivery
    DELIVERED = "delivered"  # Successfully delivered
    CANCELLED = "cancelled"  # Cancelled by restaurant or supplier
    REJECTED = "rejected"  # Rejected by supplier


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"


class Order(BaseModel, table=True):
    """
    Order model representing a purchase order from restaurant to supplier.

    Attributes:
        Basic Info:
            id: Unique order identifier (UUID)
            order_number: Human-readable order number (auto-generated)
            restaurant_id: Foreign key to restaurant
            supplier_id: Foreign key to supplier
            status: Current order status (enum)

        Order Details:
            notes: Special instructions from restaurant
            internal_notes: Internal notes (supplier only)
            special_instructions: Delivery or handling instructions

        Financial:
            subtotal: Sum of all items before tax/delivery
            tax_amount: Total tax amount
            delivery_fee: Delivery charge
            discount_amount: Discount applied
            total_amount: Final total (subtotal + tax + delivery - discount)
            currency: Currency code (default: IQD)

        Payment:
            payment_status: Payment status (enum)
            payment_method: Payment method used
            paid_amount: Amount already paid
            payment_due_date: When payment is due

        Delivery:
            delivery_address: Full delivery address (JSON)
            delivery_date: Expected delivery date
            delivered_at: Actual delivery timestamp
            delivery_notes: Notes about delivery

        Tracking:
            submitted_at: When order was submitted
            confirmed_at: When supplier confirmed
            rejected_at: When/if order was rejected
            cancelled_at: When/if order was cancelled
            rejection_reason: Why order was rejected
            cancellation_reason: Why order was cancelled

        Relationships:
            restaurant: Restaurant placing the order
            supplier: Supplier fulfilling the order
            items: Order items (products with quantities)
            created_by: User who created the order
            confirmed_by: User who confirmed the order

        Audit Fields (from BaseModel):
            created_at, updated_at, deleted_at
            created_by_id, updated_by_id, deleted_by_id
            is_deleted
    """

    __tablename__ = "order"

    # ==================== Primary Key ====================
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique order identifier"
    )

    # ==================== Order Identification ====================
    order_number: str = Field(
        max_length=50,
        nullable=False,
        unique=True,
        index=True,
        description="Human-readable order number (e.g., ORD-2024-00001)"
    )

    # ==================== Relationships (Foreign Keys) ====================
    restaurant_id: UUID = Field(
        foreign_key="restaurant.id",
        nullable=False,
        index=True,
        description="Restaurant placing the order"
    )

    supplier_id: UUID = Field(
        foreign_key="supplier.id",
        nullable=False,
        index=True,
        description="Supplier fulfilling the order"
    )

    # ==================== Order Status ====================
    status: str = Field(
        default=OrderStatus.DRAFT.value,
        max_length=50,
        nullable=False,
        index=True,
        description="Current order status"
    )

    # ==================== Order Details ====================
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        nullable=True,
        description="Special instructions or notes from restaurant"
    )

    internal_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        nullable=True,
        description="Internal notes (visible to supplier only)"
    )

    special_instructions: Optional[str] = Field(
        default=None,
        max_length=1000,
        nullable=True,
        description="Special delivery or handling instructions"
    )

    # ==================== Financial Information ====================
    subtotal: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Sum of all items before tax and delivery"
    )

    tax_amount: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Total tax amount"
    )

    delivery_fee: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Delivery charge"
    )

    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Discount applied to order"
    )

    total_amount: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Final total amount"
    )

    currency: str = Field(
        default="IQD",
        max_length=3,
        nullable=False,
        description="Currency code (ISO 4217)"
    )

    # ==================== Payment Information ====================
    payment_status: str = Field(
        default=PaymentStatus.UNPAID.value,
        max_length=50,
        nullable=False,
        index=True,
        description="Payment status"
    )

    payment_method: Optional[str] = Field(
        default=None,
        max_length=50,
        nullable=True,
        description="Payment method (cash, credit, bank_transfer, etc.)"
    )

    paid_amount: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Amount already paid"
    )

    payment_due_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="When payment is due"
    )

    # ==================== Delivery Information ====================
    delivery_address: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Full delivery address (JSON object)"
    )

    delivery_date: Optional[datetime] = Field(
        default=None,
        nullable=True,
        index=True,
        description="Expected delivery date"
    )

    delivered_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Actual delivery timestamp"
    )

    delivery_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        nullable=True,
        description="Notes about the delivery"
    )

    # ==================== Order Tracking Timestamps ====================
    submitted_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        index=True,
        description="When order was submitted (moved from draft to pending)"
    )

    confirmed_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="When supplier confirmed the order"
    )

    confirmed_by_id: Optional[UUID] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        description="User who confirmed the order"
    )

    rejected_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="When order was rejected"
    )

    rejection_reason: Optional[str] = Field(
        default=None,
        max_length=1000,
        nullable=True,
        description="Reason for rejection"
    )

    cancelled_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="When order was cancelled"
    )

    cancellation_reason: Optional[str] = Field(
        default=None,
        max_length=1000,
        nullable=True,
        description="Reason for cancellation"
    )

    # ==================== Relationships ====================
    restaurant: Optional["Restaurant"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Order.restaurant_id]",
            "lazy": "selectin",
        }
    )

    supplier: Optional["Supplier"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Order.supplier_id]",
            "lazy": "selectin",
        }
    )

    items: List["OrderItem"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        }
    )

    confirmed_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Order.confirmed_by_id]",
            "lazy": "joined",
        }
    )

    deliveries: List["Delivery"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={
            "lazy": "selectin",
        }
    )

    # ==================== Helper Properties ====================
    @property
    def is_editable(self) -> bool:
        """Check if order can be edited."""
        return self.status in [OrderStatus.DRAFT.value, OrderStatus.PENDING.value]

    @property
    def is_cancellable(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in [
            OrderStatus.PENDING.value,
            OrderStatus.CONFIRMED.value,
            OrderStatus.PROCESSING.value,
        ]

    @property
    def is_completed(self) -> bool:
        """Check if order is in final state."""
        return self.status in [
            OrderStatus.DELIVERED.value,
            OrderStatus.CANCELLED.value,
            OrderStatus.REJECTED.value,
        ]

    @property
    def outstanding_amount(self) -> Decimal:
        """Calculate outstanding payment amount."""
        return self.total_amount - self.paid_amount

    def calculate_totals(self, items: List["OrderItem"]) -> None:
        """
        Calculate order totals from items.

        Args:
            items: List of order items
        """
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.total_amount = (
            self.subtotal + self.tax_amount + self.delivery_fee - self.discount_amount
        )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status}, total={self.total_amount})>"


class OrderItem(BaseModel, table=True):
    """
    Order item representing a product in an order with quantity and price snapshot.

    Attributes:
        id: Unique order item identifier
        order_id: Foreign key to order
        product_id: Foreign key to product

        Product Snapshot (at time of order):
            product_name_ar: Product name in Arabic (snapshot)
            product_name_en: Product name in English (snapshot)
            product_sku: Product SKU (snapshot)
            unit_price: Price per unit at time of order
            unit_of_measure: Unit of measure

        Quantity and Pricing:
            quantity: Quantity ordered
            discount_percentage: Discount applied to this item
            tax_rate: Tax rate applied to this item

        Calculated Fields:
            line_subtotal: quantity × unit_price
            discount_amount: line_subtotal × (discount_percentage / 100)
            line_total_before_tax: line_subtotal - discount_amount
            tax_amount: line_total_before_tax × (tax_rate / 100)
            line_total: line_total_before_tax + tax_amount

        Item Details:
            notes: Special notes for this item

        Relationships:
            order: Parent order
            product: Product reference
    """

    __tablename__ = "order_item"

    # ==================== Primary Key ====================
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique order item identifier"
    )

    # ==================== Foreign Keys ====================
    order_id: UUID = Field(
        foreign_key="order.id",
        nullable=False,
        index=True,
        description="Parent order"
    )

    product_id: UUID = Field(
        foreign_key="product.id",
        nullable=False,
        index=True,
        description="Product being ordered"
    )

    # ==================== Product Snapshot (Price Protection) ====================
    product_name_ar: str = Field(
        max_length=255,
        nullable=False,
        description="Product name in Arabic (at time of order)"
    )

    product_name_en: str = Field(
        max_length=255,
        nullable=False,
        description="Product name in English (at time of order)"
    )

    product_sku: str = Field(
        max_length=100,
        nullable=False,
        description="Product SKU (at time of order)"
    )

    unit_price: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Price per unit at time of order"
    )

    unit_of_measure: str = Field(
        max_length=20,
        nullable=False,
        description="Unit of measure (kg, liter, piece, etc.)"
    )

    # ==================== Quantity and Pricing ====================
    quantity: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
        description="Quantity ordered"
    )

    discount_percentage: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=5,
        decimal_places=2,
        nullable=False,
        description="Discount percentage applied to this item"
    )

    tax_rate: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=5,
        decimal_places=2,
        nullable=False,
        description="Tax rate percentage applied to this item"
    )

    # ==================== Item Details ====================
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        nullable=True,
        description="Special notes for this item"
    )

    # ==================== Relationships ====================
    order: Optional["Order"] = Relationship(
        back_populates="items",
        sa_relationship_kwargs={
            "lazy": "joined",
        }
    )

    product: Optional["Product"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[OrderItem.product_id]",
            "lazy": "selectin",
        }
    )

    # ==================== Calculated Properties ====================
    @property
    def line_subtotal(self) -> Decimal:
        """Calculate line subtotal (quantity × unit_price)."""
        return self.quantity * self.unit_price

    @property
    def discount_amount(self) -> Decimal:
        """Calculate discount amount."""
        if self.discount_percentage > 0:
            return self.line_subtotal * (self.discount_percentage / Decimal("100"))
        return Decimal("0.00")

    @property
    def line_total_before_tax(self) -> Decimal:
        """Calculate line total before tax."""
        return self.line_subtotal - self.discount_amount

    @property
    def tax_amount(self) -> Decimal:
        """Calculate tax amount."""
        if self.tax_rate > 0:
            return self.line_total_before_tax * (self.tax_rate / Decimal("100"))
        return Decimal("0.00")

    @property
    def line_total(self) -> Decimal:
        """Calculate final line total (including tax)."""
        return self.line_total_before_tax + self.tax_amount

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, product={self.product_sku}, qty={self.quantity}, total={self.line_total})>"


# ==================== Table Indexes ====================
# Additional composite indexes for common queries
Index("ix_order_restaurant_status", Order.restaurant_id, Order.status)
Index("ix_order_supplier_status", Order.supplier_id, Order.status)
Index("ix_order_status_submitted", Order.status, Order.submitted_at)
Index("ix_order_payment_status_v2", Order.payment_status, Order.payment_due_date)  # v2 to avoid Alembic conflicts
Index("ix_orderitem_order_product", OrderItem.order_id, OrderItem.product_id)

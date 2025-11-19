"""
Order CRUD Operations

Handles all database operations for Order and OrderItem models including:
- Order creation with items
- Order updates and status management
- Advanced search and filtering
- Status transition workflows
- Payment tracking
- Order statistics and reporting
"""

from typing import List, Optional, Sequence, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.crud.product import product as product_crud
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    """CRUD operations for Order model."""

    async def create_with_items(
        self,
        session: AsyncSession,
        *,
        obj_in: OrderCreate,
        created_by_id: UUID,
    ) -> Order:
        """
        Create a new order with items.

        Args:
            session: Database session
            obj_in: Order creation schema with items
            created_by_id: ID of user creating the order

        Returns:
            Created order instance with items
        """
        # Generate order number
        order_number = await self._generate_order_number(session)

        # Create order (without items first)
        order_data = obj_in.model_dump(exclude={"items"})
        order_data["order_number"] = order_number
        order_data["status"] = OrderStatus.DRAFT.value
        order_data["created_by_id"] = created_by_id
        order_data["updated_by_id"] = created_by_id

        db_order = Order(**order_data)
        session.add(db_order)
        await session.flush()  # Get order ID

        # Create order items with product snapshots
        items = []
        for item_in in obj_in.items:
            # Get product details for snapshot
            product = await product_crud.get(session, id=item_in.product_id)
            if not product:
                raise ValueError(f"Product {item_in.product_id} not found")

            if not product.is_in_stock:
                raise ValueError(f"Product {product.name_en} is not available")

            # Create order item with product snapshot
            item_data = {
                "order_id": db_order.id,
                "product_id": product.id,
                "product_name_ar": product.name_ar,
                "product_name_en": product.name_en,
                "product_sku": product.sku,
                "unit_price": product.final_price,  # Use final_price (after discount)
                "unit_of_measure": product.unit_of_measure,
                "quantity": item_in.quantity,
                "discount_percentage": product.discount_percentage,
                "tax_rate": product.tax_rate,
                "notes": item_in.notes,
                "created_by_id": created_by_id,
                "updated_by_id": created_by_id,
            }
            db_item = OrderItem(**item_data)
            session.add(db_item)
            items.append(db_item)

        await session.flush()

        # Calculate order totals
        db_order.calculate_totals(items)
        session.add(db_order)

        await session.commit()
        await session.refresh(db_order)

        # Load items relationship
        await session.refresh(db_order, ["items"])

        return db_order

    async def get_with_items(
        self,
        session: AsyncSession,
        *,
        order_id: UUID,
    ) -> Optional[Order]:
        """
        Get order with items loaded.

        Args:
            session: Database session
            order_id: Order ID

        Returns:
            Order with items if found
        """
        statement = (
            select(Order)
            .where(
                and_(
                    Order.id == order_id,
                    Order.is_deleted == False,
                )
            )
            .options(selectinload(Order.items))
        )

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_order_number(
        self,
        session: AsyncSession,
        *,
        order_number: str,
    ) -> Optional[Order]:
        """
        Get order by order number.

        Args:
            session: Database session
            order_number: Order number

        Returns:
            Order if found
        """
        statement = (
            select(Order)
            .where(
                and_(
                    Order.order_number == order_number,
                    Order.is_deleted == False,
                )
            )
            .options(selectinload(Order.items))
        )

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_restaurant(
        self,
        session: AsyncSession,
        *,
        restaurant_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Order]:
        """
        Get orders for a restaurant.

        Args:
            session: Database session
            restaurant_id: Restaurant ID
            status: Optional status filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of orders
        """
        statement = select(Order).where(
            and_(
                Order.restaurant_id == restaurant_id,
                Order.is_deleted == False,
            )
        )

        if status:
            statement = statement.where(Order.status == status)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Order.submitted_at.desc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_by_supplier(
        self,
        session: AsyncSession,
        *,
        supplier_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Order]:
        """
        Get orders for a supplier.

        Args:
            session: Database session
            supplier_id: Supplier ID
            status: Optional status filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of orders
        """
        statement = select(Order).where(
            and_(
                Order.supplier_id == supplier_id,
                Order.is_deleted == False,
            )
        )

        if status:
            statement = statement.where(Order.status == status)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Order.submitted_at.desc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def search(
        self,
        session: AsyncSession,
        *,
        query: Optional[str] = None,
        restaurant_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        submitted_after: Optional[datetime] = None,
        submitted_before: Optional[datetime] = None,
        delivery_after: Optional[datetime] = None,
        delivery_before: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        has_outstanding_payment: Optional[bool] = None,
        sort_by: str = "submitted_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Order]:
        """
        Advanced order search with filters.

        Args:
            session: Database session
            query: Search by order number
            restaurant_id: Filter by restaurant
            supplier_id: Filter by supplier
            status: Filter by status
            payment_status: Filter by payment status
            submitted_after: Orders submitted after date
            submitted_before: Orders submitted before date
            delivery_after: Delivery after date
            delivery_before: Delivery before date
            min_amount: Minimum order amount
            max_amount: Maximum order amount
            has_outstanding_payment: Filter orders with outstanding payments
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of orders matching filters
        """
        statement = select(Order).where(Order.is_deleted == False)

        # Text search
        if query:
            statement = statement.where(Order.order_number.ilike(f"%{query}%"))

        # Relationship filters
        if restaurant_id:
            statement = statement.where(Order.restaurant_id == restaurant_id)

        if supplier_id:
            statement = statement.where(Order.supplier_id == supplier_id)

        # Status filters
        if status:
            statement = statement.where(Order.status == status)

        if payment_status:
            statement = statement.where(Order.payment_status == payment_status)

        # Date filters
        if submitted_after:
            statement = statement.where(Order.submitted_at >= submitted_after)

        if submitted_before:
            statement = statement.where(Order.submitted_at <= submitted_before)

        if delivery_after:
            statement = statement.where(Order.delivery_date >= delivery_after)

        if delivery_before:
            statement = statement.where(Order.delivery_date <= delivery_before)

        # Amount filters
        if min_amount is not None:
            statement = statement.where(Order.total_amount >= min_amount)

        if max_amount is not None:
            statement = statement.where(Order.total_amount <= max_amount)

        # Outstanding payment filter
        if has_outstanding_payment is not None:
            if has_outstanding_payment:
                statement = statement.where(Order.total_amount > Order.paid_amount)
            else:
                statement = statement.where(Order.total_amount <= Order.paid_amount)

        # Sorting
        sort_column = getattr(Order, sort_by, Order.submitted_at)
        if sort_order == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        # Pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return result.scalars().all()

    async def update_status(
        self,
        session: AsyncSession,
        *,
        order_id: UUID,
        new_status: str,
        updated_by_id: UUID,
        notes: Optional[str] = None,
    ) -> Optional[Order]:
        """
        Update order status with validation and tracking.

        Args:
            session: Database session
            order_id: Order ID
            new_status: New status value
            updated_by_id: User making the change
            notes: Optional notes about the change

        Returns:
            Updated order if successful
        """
        order = await self.get_with_items(session, order_id=order_id)
        if not order:
            return None

        # Validate status transition
        if not self._is_valid_status_transition(order.status, new_status):
            raise ValueError(f"Invalid status transition from {order.status} to {new_status}")

        # Update status and tracking fields
        order.status = new_status
        order.updated_by_id = updated_by_id

        # Update tracking timestamps
        if new_status == OrderStatus.PENDING.value:
            order.submitted_at = datetime.utcnow()
        elif new_status == OrderStatus.CONFIRMED.value:
            order.confirmed_at = datetime.utcnow()
            order.confirmed_by_id = updated_by_id
        elif new_status == OrderStatus.REJECTED.value:
            order.rejected_at = datetime.utcnow()
            if notes:
                order.rejection_reason = notes
        elif new_status == OrderStatus.CANCELLED.value:
            order.cancelled_at = datetime.utcnow()
            if notes:
                order.cancellation_reason = notes
        elif new_status == OrderStatus.DELIVERED.value:
            order.delivered_at = datetime.utcnow()
            order.payment_status = PaymentStatus.PAID.value  # Mark as paid on delivery

        session.add(order)
        await session.commit()
        await session.refresh(order)

        return order

    async def add_payment(
        self,
        session: AsyncSession,
        *,
        order_id: UUID,
        payment_amount: Decimal,
        payment_method: str,
        updated_by_id: UUID,
    ) -> Optional[Order]:
        """
        Record a payment for an order.

        Args:
            session: Database session
            order_id: Order ID
            payment_amount: Payment amount
            payment_method: Payment method
            updated_by_id: User recording the payment

        Returns:
            Updated order
        """
        order = await self.get(session, id=order_id)
        if not order:
            return None

        order.paid_amount += payment_amount
        order.payment_method = payment_method
        order.updated_by_id = updated_by_id

        # Update payment status
        if order.paid_amount >= order.total_amount:
            order.payment_status = PaymentStatus.PAID.value
        elif order.paid_amount > 0:
            order.payment_status = PaymentStatus.PARTIALLY_PAID.value

        session.add(order)
        await session.commit()
        await session.refresh(order)

        return order

    async def get_pending_orders(
        self,
        session: AsyncSession,
        *,
        supplier_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Order]:
        """
        Get pending orders awaiting supplier confirmation.

        Args:
            session: Database session
            supplier_id: Optional supplier filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of pending orders
        """
        statement = select(Order).where(
            and_(
                Order.status == OrderStatus.PENDING.value,
                Order.is_deleted == False,
            )
        )

        if supplier_id:
            statement = statement.where(Order.supplier_id == supplier_id)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Order.submitted_at.asc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_statistics(
        self,
        session: AsyncSession,
        *,
        restaurant_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get order statistics.

        Args:
            session: Database session
            restaurant_id: Optional restaurant filter
            supplier_id: Optional supplier filter
            start_date: Start date for period
            end_date: End date for period

        Returns:
            Dictionary with statistics
        """
        statement = select(
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_amount).label("total_revenue"),
            func.avg(Order.total_amount).label("average_order_value"),
        ).where(Order.is_deleted == False)

        if restaurant_id:
            statement = statement.where(Order.restaurant_id == restaurant_id)

        if supplier_id:
            statement = statement.where(Order.supplier_id == supplier_id)

        if start_date:
            statement = statement.where(Order.submitted_at >= start_date)

        if end_date:
            statement = statement.where(Order.submitted_at <= end_date)

        result = await session.execute(statement)
        row = result.one()

        return {
            "total_orders": row.total_orders or 0,
            "total_revenue": float(row.total_revenue or 0),
            "average_order_value": float(row.average_order_value or 0),
        }

    # ==================== Helper Methods ====================

    async def _generate_order_number(self, session: AsyncSession) -> str:
        """
        Generate unique order number.

        Format: ORD-YYYY-NNNNN (e.g., ORD-2024-00001)
        """
        current_year = datetime.utcnow().year

        # Get count of orders this year
        statement = select(func.count(Order.id)).where(
            and_(
                Order.order_number.like(f"ORD-{current_year}-%"),
                Order.is_deleted == False,
            )
        )
        result = await session.execute(statement)
        count = result.scalar_one() or 0

        # Generate order number
        order_number = f"ORD-{current_year}-{(count + 1):05d}"

        # Check if exists (collision detection)
        existing = await self.get_by_order_number(session, order_number=order_number)
        if existing:
            # Rare collision, add timestamp
            timestamp = int(datetime.utcnow().timestamp())
            order_number = f"ORD-{current_year}-{(count + 1):05d}-{timestamp}"

        return order_number

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed.

        Valid transitions:
        - draft → pending, cancelled
        - pending → confirmed, rejected, cancelled
        - confirmed → processing, cancelled
        - processing → ready_for_delivery, cancelled
        - ready_for_delivery → in_transit, cancelled
        - in_transit → delivered, cancelled
        - Any → cancelled (can always cancel)
        """
        # Can always cancel (except if already in final state)
        if new_status == OrderStatus.CANCELLED.value:
            return current_status not in [
                OrderStatus.DELIVERED.value,
                OrderStatus.CANCELLED.value,
                OrderStatus.REJECTED.value,
            ]

        # Define valid transitions
        valid_transitions = {
            OrderStatus.DRAFT.value: [OrderStatus.PENDING.value],
            OrderStatus.PENDING.value: [OrderStatus.CONFIRMED.value, OrderStatus.REJECTED.value],
            OrderStatus.CONFIRMED.value: [OrderStatus.PROCESSING.value],
            OrderStatus.PROCESSING.value: [OrderStatus.READY_FOR_DELIVERY.value],
            OrderStatus.READY_FOR_DELIVERY.value: [OrderStatus.IN_TRANSIT.value],
            OrderStatus.IN_TRANSIT.value: [OrderStatus.DELIVERED.value],
        }

        return new_status in valid_transitions.get(current_status, [])


# Create singleton instance
order = CRUDOrder(Order)

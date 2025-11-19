"""
Delivery CRUD Operations

Handles all database operations for Delivery model including:
- Delivery creation and assignment
- GPS location tracking
- Status workflow management
- Proof of delivery submission
- Driver statistics and analytics
"""

from typing import List, Optional, Sequence
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.delivery import Delivery, DeliveryStatus, DeliveryPriority
from app.models.user import User
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate


class CRUDDelivery(CRUDBase[Delivery, DeliveryCreate, DeliveryUpdate]):
    """CRUD operations for Delivery model."""

    async def create_with_calculation(
        self,
        session: AsyncSession,
        *,
        obj_in: DeliveryCreate,
        created_by_id: UUID,
    ) -> Delivery:
        """
        Create a new delivery with automatic distance and fee calculation.

        Args:
            session: Database session
            obj_in: Delivery creation schema
            created_by_id: ID of user creating the delivery

        Returns:
            Created delivery instance
        """
        # Calculate distance if coordinates provided
        if (
            obj_in.pickup_latitude and obj_in.pickup_longitude and
            obj_in.delivery_latitude and obj_in.delivery_longitude
        ):
            distance = self._calculate_distance(
                obj_in.pickup_latitude,
                obj_in.pickup_longitude,
                obj_in.delivery_latitude,
                obj_in.delivery_longitude,
            )
            obj_in.estimated_distance_km = distance

        # Calculate delivery fee if not provided
        if obj_in.delivery_fee == Decimal("0.00") and obj_in.estimated_distance_km:
            # Default fee structure for Iraq (IQD)
            base_fee = Decimal("5000")  # 5,000 IQD base fee
            per_km_fee = Decimal("1000")  # 1,000 IQD per km
            obj_in.delivery_fee = base_fee + (obj_in.estimated_distance_km * per_km_fee)

        # Create delivery
        delivery_data = obj_in.model_dump()
        delivery_data["status"] = DeliveryStatus.PENDING.value
        delivery_data["created_by_id"] = created_by_id
        delivery_data["updated_by_id"] = created_by_id

        # If driver assigned immediately, set assigned_at
        if obj_in.driver_id:
            delivery_data["assigned_at"] = datetime.utcnow()
            delivery_data["status"] = DeliveryStatus.ASSIGNED.value

        db_delivery = Delivery(**delivery_data)
        session.add(db_delivery)
        await session.commit()
        await session.refresh(db_delivery)

        return db_delivery

    async def get_with_details(
        self,
        session: AsyncSession,
        *,
        delivery_id: UUID,
    ) -> Optional[Delivery]:
        """
        Get delivery with order and driver details loaded.

        Args:
            session: Database session
            delivery_id: Delivery ID

        Returns:
            Delivery with relationships if found
        """
        statement = (
            select(Delivery)
            .where(
                and_(
                    Delivery.id == delivery_id,
                    Delivery.is_deleted == False,
                )
            )
            .options(
                selectinload(Delivery.order),
                selectinload(Delivery.driver),
            )
        )

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_order(
        self,
        session: AsyncSession,
        *,
        order_id: UUID,
    ) -> Sequence[Delivery]:
        """
        Get all deliveries for an order.

        Args:
            session: Database session
            order_id: Order ID

        Returns:
            List of deliveries for the order
        """
        statement = (
            select(Delivery)
            .where(
                and_(
                    Delivery.order_id == order_id,
                    Delivery.is_deleted == False,
                )
            )
            .order_by(Delivery.created_at.desc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_by_driver(
        self,
        session: AsyncSession,
        *,
        driver_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Delivery]:
        """
        Get deliveries assigned to a driver.

        Args:
            session: Database session
            driver_id: Driver (User) ID
            status: Optional status filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of deliveries
        """
        statement = select(Delivery).where(
            and_(
                Delivery.driver_id == driver_id,
                Delivery.is_deleted == False,
            )
        )

        if status:
            statement = statement.where(Delivery.status == status)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Delivery.estimated_delivery_time.asc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_active_deliveries(
        self,
        session: AsyncSession,
        *,
        driver_id: Optional[UUID] = None,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Delivery]:
        """
        Get active deliveries (not completed/failed/cancelled).

        Args:
            session: Database session
            driver_id: Optional driver filter
            city: Optional city filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of active deliveries
        """
        active_statuses = [
            DeliveryStatus.PENDING.value,
            DeliveryStatus.ASSIGNED.value,
            DeliveryStatus.PICKED_UP.value,
            DeliveryStatus.IN_TRANSIT.value,
            DeliveryStatus.ARRIVED.value,
        ]

        statement = select(Delivery).where(
            and_(
                Delivery.status.in_(active_statuses),
                Delivery.is_deleted == False,
            )
        )

        if driver_id:
            statement = statement.where(Delivery.driver_id == driver_id)

        if city:
            statement = statement.where(Delivery.delivery_city == city)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Delivery.priority.desc(), Delivery.estimated_delivery_time.asc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_pending_assignments(
        self,
        session: AsyncSession,
        *,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Delivery]:
        """
        Get deliveries pending driver assignment.

        Args:
            session: Database session
            city: Optional city filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of unassigned deliveries
        """
        statement = select(Delivery).where(
            and_(
                Delivery.status == DeliveryStatus.PENDING.value,
                Delivery.driver_id == None,
                Delivery.is_deleted == False,
            )
        )

        if city:
            statement = statement.where(Delivery.delivery_city == city)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Delivery.priority.desc(), Delivery.created_at.asc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def search(
        self,
        session: AsyncSession,
        *,
        driver_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        city: Optional[str] = None,
        assigned_after: Optional[datetime] = None,
        assigned_before: Optional[datetime] = None,
        delivery_after: Optional[datetime] = None,
        delivery_before: Optional[datetime] = None,
        is_delayed: Optional[bool] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Delivery]:
        """
        Advanced delivery search with filters.

        Args:
            session: Database session
            driver_id: Filter by driver
            order_id: Filter by order
            status: Filter by status
            priority: Filter by priority
            city: Filter by city
            assigned_after: Assigned after date
            assigned_before: Assigned before date
            delivery_after: Delivery after date
            delivery_before: Delivery before date
            is_delayed: Filter delayed deliveries
            is_active: Filter active deliveries
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of deliveries matching filters
        """
        statement = select(Delivery).where(Delivery.is_deleted == False)

        # Relationship filters
        if driver_id:
            statement = statement.where(Delivery.driver_id == driver_id)

        if order_id:
            statement = statement.where(Delivery.order_id == order_id)

        # Status filters
        if status:
            statement = statement.where(Delivery.status == status)

        if priority:
            statement = statement.where(Delivery.priority == priority)

        # Location filter
        if city:
            statement = statement.where(Delivery.delivery_city == city)

        # Date filters
        if assigned_after:
            statement = statement.where(Delivery.assigned_at >= assigned_after)

        if assigned_before:
            statement = statement.where(Delivery.assigned_at <= assigned_before)

        if delivery_after:
            statement = statement.where(Delivery.estimated_delivery_time >= delivery_after)

        if delivery_before:
            statement = statement.where(Delivery.estimated_delivery_time <= delivery_before)

        # Delayed filter
        if is_delayed is not None:
            if is_delayed:
                statement = statement.where(
                    and_(
                        Delivery.estimated_delivery_time < datetime.utcnow(),
                        Delivery.status.not_in([
                            DeliveryStatus.DELIVERED.value,
                            DeliveryStatus.FAILED.value,
                            DeliveryStatus.CANCELLED.value,
                        ])
                    )
                )

        # Active filter
        if is_active is not None:
            if is_active:
                statement = statement.where(
                    Delivery.status.not_in([
                        DeliveryStatus.DELIVERED.value,
                        DeliveryStatus.FAILED.value,
                        DeliveryStatus.CANCELLED.value,
                    ])
                )
            else:
                statement = statement.where(
                    Delivery.status.in_([
                        DeliveryStatus.DELIVERED.value,
                        DeliveryStatus.FAILED.value,
                        DeliveryStatus.CANCELLED.value,
                    ])
                )

        # Sorting
        sort_column = getattr(Delivery, sort_by, Delivery.created_at)
        if sort_order == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        # Pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return result.scalars().all()

    async def assign_driver(
        self,
        session: AsyncSession,
        *,
        delivery_id: UUID,
        driver_id: UUID,
        updated_by_id: UUID,
        estimated_pickup_time: Optional[datetime] = None,
    ) -> Optional[Delivery]:
        """
        Assign a driver to a delivery.

        Args:
            session: Database session
            delivery_id: Delivery ID
            driver_id: Driver (User) ID
            updated_by_id: User making the assignment
            estimated_pickup_time: Optional estimated pickup time

        Returns:
            Updated delivery
        """
        delivery = await self.get(session, id=delivery_id)
        if not delivery:
            return None

        # Verify driver exists and has driver role
        driver = await session.get(User, driver_id)
        if not driver:
            raise ValueError(f"Driver {driver_id} not found")

        delivery.driver_id = driver_id
        delivery.status = DeliveryStatus.ASSIGNED.value
        delivery.assigned_at = datetime.utcnow()
        delivery.updated_by_id = updated_by_id

        if estimated_pickup_time:
            delivery.estimated_pickup_time = estimated_pickup_time

        session.add(delivery)
        await session.commit()
        await session.refresh(delivery)

        return delivery

    async def update_status(
        self,
        session: AsyncSession,
        *,
        delivery_id: UUID,
        new_status: str,
        updated_by_id: UUID,
        notes: Optional[str] = None,
    ) -> Optional[Delivery]:
        """
        Update delivery status with validation and tracking.

        Args:
            session: Database session
            delivery_id: Delivery ID
            new_status: New status value
            updated_by_id: User making the change
            notes: Optional notes about the change

        Returns:
            Updated delivery if successful
        """
        delivery = await self.get(session, id=delivery_id)
        if not delivery:
            return None

        # Validate status transition
        if not self._is_valid_status_transition(delivery.status, new_status):
            raise ValueError(f"Invalid status transition from {delivery.status} to {new_status}")

        # Update status and tracking fields
        delivery.status = new_status
        delivery.updated_by_id = updated_by_id

        # Update tracking timestamps
        now = datetime.utcnow()
        if new_status == DeliveryStatus.PICKED_UP.value:
            delivery.picked_up_at = now
        elif new_status == DeliveryStatus.IN_TRANSIT.value:
            delivery.in_transit_at = now
        elif new_status == DeliveryStatus.ARRIVED.value:
            delivery.arrived_at = now
        elif new_status == DeliveryStatus.DELIVERED.value:
            delivery.delivered_at = now
        elif new_status == DeliveryStatus.FAILED.value:
            delivery.failed_at = now
            if notes:
                delivery.failure_reason = notes
        elif new_status == DeliveryStatus.CANCELLED.value:
            delivery.cancelled_at = now
            if notes:
                delivery.cancellation_reason = notes

        session.add(delivery)
        await session.commit()
        await session.refresh(delivery)

        return delivery

    async def update_location(
        self,
        session: AsyncSession,
        *,
        delivery_id: UUID,
        latitude: Decimal,
        longitude: Decimal,
        updated_by_id: UUID,
    ) -> Optional[Delivery]:
        """
        Update driver's current GPS location.

        Args:
            session: Database session
            delivery_id: Delivery ID
            latitude: Current latitude
            longitude: Current longitude
            updated_by_id: Driver user ID

        Returns:
            Updated delivery
        """
        delivery = await self.get(session, id=delivery_id)
        if not delivery:
            return None

        if not delivery.can_update_location:
            raise ValueError("Cannot update location for delivery in current status")

        # Add location point to history
        delivery.add_location_point(latitude, longitude)
        delivery.updated_by_id = updated_by_id

        session.add(delivery)
        await session.commit()
        await session.refresh(delivery)

        return delivery

    async def submit_proof_of_delivery(
        self,
        session: AsyncSession,
        *,
        delivery_id: UUID,
        signature_url: Optional[str] = None,
        photo_urls: Optional[List[str]] = None,
        recipient_name: str,
        recipient_phone: Optional[str] = None,
        recipient_notes: Optional[str] = None,
        updated_by_id: UUID,
    ) -> Optional[Delivery]:
        """
        Submit proof of delivery.

        Args:
            session: Database session
            delivery_id: Delivery ID
            signature_url: URL to signature image
            photo_urls: List of photo URLs
            recipient_name: Name of person who received
            recipient_phone: Phone of recipient
            recipient_notes: Notes from recipient
            updated_by_id: Driver user ID

        Returns:
            Updated delivery
        """
        delivery = await self.get(session, id=delivery_id)
        if not delivery:
            return None

        if delivery.status != DeliveryStatus.ARRIVED.value:
            raise ValueError("Proof of delivery can only be submitted when status is 'arrived'")

        delivery.signature_url = signature_url
        if photo_urls:
            delivery.photo_urls = {"photos": photo_urls}
        delivery.recipient_name = recipient_name
        delivery.recipient_phone = recipient_phone
        delivery.recipient_notes = recipient_notes
        delivery.updated_by_id = updated_by_id

        # Automatically mark as delivered after proof submission
        delivery.status = DeliveryStatus.DELIVERED.value
        delivery.delivered_at = datetime.utcnow()

        session.add(delivery)
        await session.commit()
        await session.refresh(delivery)

        return delivery

    async def get_statistics(
        self,
        session: AsyncSession,
        *,
        driver_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get delivery statistics.

        Args:
            session: Database session
            driver_id: Optional driver filter
            start_date: Start date for period
            end_date: End date for period

        Returns:
            Dictionary with statistics
        """
        # Base query
        base_statement = select(Delivery).where(Delivery.is_deleted == False)

        if driver_id:
            base_statement = base_statement.where(Delivery.driver_id == driver_id)

        if start_date:
            base_statement = base_statement.where(Delivery.created_at >= start_date)

        if end_date:
            base_statement = base_statement.where(Delivery.created_at <= end_date)

        # Total deliveries
        total_statement = select(func.count(Delivery.id)).select_from(base_statement.subquery())
        total_result = await session.execute(total_statement)
        total_deliveries = total_result.scalar_one() or 0

        # Status counts
        status_counts = {}
        for status in DeliveryStatus:
            status_statement = base_statement.where(Delivery.status == status.value)
            count_statement = select(func.count(Delivery.id)).select_from(status_statement.subquery())
            count_result = await session.execute(count_statement)
            status_counts[status.value] = count_result.scalar_one() or 0

        # Distance and fees
        metrics_statement = select(
            func.sum(Delivery.actual_distance_km).label("total_distance"),
            func.sum(Delivery.delivery_fee).label("total_fees"),
        ).select_from(base_statement.subquery())

        metrics_result = await session.execute(metrics_statement)
        metrics = metrics_result.one()

        # Average delivery time (completed deliveries only)
        completed_statement = base_statement.where(
            and_(
                Delivery.status == DeliveryStatus.DELIVERED.value,
                Delivery.picked_up_at.is_not(None),
                Delivery.delivered_at.is_not(None),
            )
        )

        completed_result = await session.execute(completed_statement)
        completed_deliveries = completed_result.scalars().all()

        avg_delivery_time = None
        if completed_deliveries:
            total_minutes = sum([d.actual_duration_minutes or 0 for d in completed_deliveries])
            avg_delivery_time = total_minutes // len(completed_deliveries) if total_minutes > 0 else 0

        # Delayed deliveries
        delayed_statement = base_statement.where(
            and_(
                Delivery.estimated_delivery_time < datetime.utcnow(),
                Delivery.status.not_in([
                    DeliveryStatus.DELIVERED.value,
                    DeliveryStatus.FAILED.value,
                    DeliveryStatus.CANCELLED.value,
                ])
            )
        )
        delayed_count_statement = select(func.count(Delivery.id)).select_from(delayed_statement.subquery())
        delayed_result = await session.execute(delayed_count_statement)
        delayed_deliveries = delayed_result.scalar_one() or 0

        return {
            "total_deliveries": total_deliveries,
            "pending_deliveries": status_counts.get(DeliveryStatus.PENDING.value, 0),
            "in_progress_deliveries": (
                status_counts.get(DeliveryStatus.PICKED_UP.value, 0) +
                status_counts.get(DeliveryStatus.IN_TRANSIT.value, 0) +
                status_counts.get(DeliveryStatus.ARRIVED.value, 0)
            ),
            "completed_deliveries": status_counts.get(DeliveryStatus.DELIVERED.value, 0),
            "failed_deliveries": status_counts.get(DeliveryStatus.FAILED.value, 0),
            "cancelled_deliveries": status_counts.get(DeliveryStatus.CANCELLED.value, 0),
            "total_distance_km": float(metrics.total_distance or 0),
            "total_delivery_fees": float(metrics.total_fees or 0),
            "average_delivery_time_minutes": avg_delivery_time,
            "delayed_deliveries": delayed_deliveries,
        }

    # ==================== Helper Methods ====================

    def _calculate_distance(
        self,
        lat1: Decimal,
        lon1: Decimal,
        lat2: Decimal,
        lon2: Decimal,
    ) -> Decimal:
        """
        Calculate distance between two GPS coordinates using Haversine formula.

        Args:
            lat1: First point latitude
            lon1: First point longitude
            lat2: Second point latitude
            lon2: Second point longitude

        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = radians(float(lat1))
        lon1_rad = radians(float(lon1))
        lat2_rad = radians(float(lat2))
        lon2_rad = radians(float(lon2))

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return Decimal(str(round(distance, 2)))

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed.

        Valid transitions:
        - pending → assigned, cancelled
        - assigned → picked_up, cancelled
        - picked_up → in_transit, failed, cancelled
        - in_transit → arrived, failed, cancelled
        - arrived → delivered, failed, cancelled
        - Any → cancelled (can always cancel before delivery)
        """
        # Can always cancel (except if already in final state)
        if new_status == DeliveryStatus.CANCELLED.value:
            return current_status not in [
                DeliveryStatus.DELIVERED.value,
                DeliveryStatus.FAILED.value,
                DeliveryStatus.CANCELLED.value,
            ]

        # Can always mark as failed (except if already in final state)
        if new_status == DeliveryStatus.FAILED.value:
            return current_status not in [
                DeliveryStatus.DELIVERED.value,
                DeliveryStatus.FAILED.value,
                DeliveryStatus.CANCELLED.value,
            ]

        # Define valid transitions
        valid_transitions = {
            DeliveryStatus.PENDING.value: [DeliveryStatus.ASSIGNED.value],
            DeliveryStatus.ASSIGNED.value: [DeliveryStatus.PICKED_UP.value],
            DeliveryStatus.PICKED_UP.value: [DeliveryStatus.IN_TRANSIT.value],
            DeliveryStatus.IN_TRANSIT.value: [DeliveryStatus.ARRIVED.value],
            DeliveryStatus.ARRIVED.value: [DeliveryStatus.DELIVERED.value],
        }

        return new_status in valid_transitions.get(current_status, [])


# Create singleton instance
delivery = CRUDDelivery(Delivery)

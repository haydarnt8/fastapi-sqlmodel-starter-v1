"""
Supplier CRUD Operations

This module provides CRUD operations for the Supplier model with specialized
methods for supply chain management.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.base import CRUDBase
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


class CRUDSupplier(CRUDBase[Supplier, SupplierCreate, SupplierUpdate]):
    """
    CRUD operations for Supplier model with supply chain-specific methods.
    """

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: SupplierCreate,
        created_by_id: Optional[UUID] = None,
        owner_id: UUID,
    ) -> Supplier:
        """
        Create a new supplier with specified owner.

        Args:
            session: Database session
            obj_in: Supplier creation data
            created_by_id: ID of user creating the record
            owner_id: ID of supplier owner

        Returns:
            Created supplier instance
        """
        # Convert to dict and add owner_id
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        obj_in_data["owner_id"] = owner_id

        # Add audit fields
        if created_by_id:
            obj_in_data["created_by_id"] = created_by_id
            obj_in_data["updated_by_id"] = created_by_id

        # Create supplier instance
        db_obj = Supplier(**obj_in_data)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        return db_obj

    async def get_by_owner(
        self,
        session: AsyncSession,
        owner_id: UUID,
    ) -> List[Supplier]:
        """
        Get all suppliers owned by a specific user.

        Args:
            session: Database session
            owner_id: Owner's user ID

        Returns:
            List of suppliers owned by the user
        """
        statement = (
            select(Supplier)
            .where(Supplier.owner_id == owner_id)
            .where(Supplier.is_deleted == False)
            .order_by(Supplier.created_at.desc())
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def search(
        self,
        session: AsyncSession,
        query: Optional[str] = None,
        city: Optional[str] = None,
        product_category: Optional[str] = None,
        is_verified: Optional[bool] = None,
        is_active: Optional[bool] = None,
        min_rating: Optional[Decimal] = None,
        accepts_cash: Optional[bool] = None,
        accepts_credit: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Supplier]:
        """
        Search suppliers with multiple filters.

        Args:
            session: Database session
            query: Search query for company name (Arabic or English)
            city: Filter by city
            product_category: Filter by product category
            is_verified: Filter by verification status
            is_active: Filter by active status
            min_rating: Minimum average rating
            accepts_cash: Filter by cash payment acceptance
            accepts_credit: Filter by credit payment acceptance
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of matching suppliers
        """
        statement = select(Supplier).where(Supplier.is_deleted == False)

        # Text search on company name (Arabic or English)
        if query:
            statement = statement.where(
                or_(
                    Supplier.company_name_ar.ilike(f"%{query}%"),
                    Supplier.company_name_en.ilike(f"%{query}%"),
                )
            )

        # Filter by city
        if city:
            statement = statement.where(Supplier.city == city)

        # Filter by product category (JSON column)
        if product_category:
            # Note: This requires JSON contains support
            # For SQLite, we'll use a simpler LIKE approach
            statement = statement.where(
                Supplier.product_categories.ilike(f"%{product_category}%")
            )

        # Filter by verification status
        if is_verified is not None:
            statement = statement.where(Supplier.is_verified == is_verified)

        # Filter by active status
        if is_active is not None:
            statement = statement.where(Supplier.is_active == is_active)

        # Filter by minimum rating
        if min_rating is not None:
            statement = statement.where(Supplier.average_rating >= min_rating)

        # Filter by payment methods
        if accepts_cash is not None:
            statement = statement.where(Supplier.accepts_cash == accepts_cash)

        if accepts_credit is not None:
            statement = statement.where(Supplier.accepts_credit == accepts_credit)

        # Order by rating and total reviews (popular first)
        statement = statement.order_by(
            Supplier.is_verified.desc(),
            Supplier.average_rating.desc(),
            Supplier.total_reviews.desc(),
        )

        # Pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def filter_by_delivery_area(
        self,
        session: AsyncSession,
        city: str,
        district: Optional[str] = None,
    ) -> List[Supplier]:
        """
        Get suppliers that deliver to a specific area.

        Args:
            session: Database session
            city: City name
            district: Optional district name

        Returns:
            List of suppliers that deliver to the specified area
        """
        # Get all active, verified suppliers
        statement = (
            select(Supplier)
            .where(Supplier.is_deleted == False)
            .where(Supplier.is_active == True)
            .where(Supplier.is_verified == True)
        )

        result = await session.execute(statement)
        suppliers = list(result.scalars().all())

        # Filter by delivery area in Python (since JSON querying is complex)
        filtered_suppliers = [
            s for s in suppliers if s.can_deliver_to(city, district)
        ]

        return filtered_suppliers

    async def get_top_rated(
        self,
        session: AsyncSession,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[Supplier]:
        """
        Get top-rated suppliers.

        Args:
            session: Database session
            city: Optional city filter
            limit: Maximum number of suppliers to return

        Returns:
            List of top-rated suppliers
        """
        statement = (
            select(Supplier)
            .where(Supplier.is_deleted == False)
            .where(Supplier.is_active == True)
            .where(Supplier.is_verified == True)
        )

        if city:
            statement = statement.where(Supplier.city == city)

        statement = statement.order_by(
            Supplier.average_rating.desc(),
            Supplier.total_reviews.desc(),
        ).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_by_city(
        self,
        session: AsyncSession,
        city: str,
    ) -> List[Supplier]:
        """
        Get all active suppliers in a specific city.

        Args:
            session: Database session
            city: City name

        Returns:
            List of suppliers in the city
        """
        statement = (
            select(Supplier)
            .where(Supplier.city == city)
            .where(Supplier.is_deleted == False)
            .where(Supplier.is_active == True)
            .order_by(Supplier.average_rating.desc())
        )

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_pending_verification(
        self,
        session: AsyncSession,
    ) -> List[Supplier]:
        """
        Get all suppliers pending verification.

        Args:
            session: Database session

        Returns:
            List of suppliers pending verification
        """
        statement = (
            select(Supplier)
            .where(Supplier.verification_status == "pending")
            .where(Supplier.is_deleted == False)
            .order_by(Supplier.created_at.asc())
        )

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def verify(
        self,
        session: AsyncSession,
        supplier_id: UUID,
        verified_by_id: UUID,
        approved: bool,
    ) -> Optional[Supplier]:
        """
        Verify or reject a supplier.

        Args:
            session: Database session
            supplier_id: Supplier ID to verify
            verified_by_id: Admin user ID performing verification
            approved: True to approve, False to reject

        Returns:
            Updated supplier or None if not found
        """
        supplier = await self.get(session=session, id=supplier_id)
        if not supplier:
            return None

        supplier.verification_status = "approved" if approved else "rejected"
        supplier.is_verified = approved
        supplier.verified_at = datetime.utcnow() if approved else None
        supplier.verified_by_id = verified_by_id
        supplier.updated_at = datetime.utcnow()
        supplier.updated_by_id = verified_by_id

        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)

        return supplier

    async def update_rating(
        self,
        session: AsyncSession,
        supplier_id: UUID,
        new_rating: Decimal,
    ) -> Optional[Supplier]:
        """
        Update supplier's average rating and review count.

        This is typically called after a new review is added.

        Args:
            session: Database session
            supplier_id: Supplier ID
            new_rating: New rating to incorporate (0-5)

        Returns:
            Updated supplier or None if not found
        """
        supplier = await self.get(session=session, id=supplier_id)
        if not supplier:
            return None

        # Calculate new average rating
        total_reviews = supplier.total_reviews
        current_avg = supplier.average_rating or Decimal("0")

        # New average = (old_avg * old_count + new_rating) / (old_count + 1)
        new_avg = (current_avg * total_reviews + new_rating) / (total_reviews + 1)

        supplier.average_rating = new_avg
        supplier.total_reviews = total_reviews + 1
        supplier.updated_at = datetime.utcnow()

        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)

        return supplier

    async def increment_order_count(
        self,
        session: AsyncSession,
        supplier_id: UUID,
    ) -> Optional[Supplier]:
        """
        Increment the total completed orders count.

        Args:
            session: Database session
            supplier_id: Supplier ID

        Returns:
            Updated supplier or None if not found
        """
        supplier = await self.get(session=session, id=supplier_id)
        if not supplier:
            return None

        supplier.total_orders_completed += 1
        supplier.updated_at = datetime.utcnow()

        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)

        return supplier

    async def toggle_active_status(
        self,
        session: AsyncSession,
        supplier_id: UUID,
        is_active: bool,
    ) -> Optional[Supplier]:
        """
        Toggle supplier's active status.

        Args:
            session: Database session
            supplier_id: Supplier ID
            is_active: New active status

        Returns:
            Updated supplier or None if not found
        """
        supplier = await self.get(session=session, id=supplier_id)
        if not supplier:
            return None

        supplier.is_active = is_active
        supplier.updated_at = datetime.utcnow()

        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)

        return supplier

    async def get_nearby(
        self,
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
    ) -> List[Supplier]:
        """
        Get suppliers within a certain radius of coordinates.

        Uses Haversine formula for distance calculation.

        Args:
            session: Database session
            latitude: Center point latitude
            longitude: Center point longitude
            radius_km: Search radius in kilometers

        Returns:
            List of nearby suppliers
        """
        # Get all active suppliers with coordinates
        statement = (
            select(Supplier)
            .where(Supplier.is_deleted == False)
            .where(Supplier.is_active == True)
            .where(Supplier.is_verified == True)
            .where(Supplier.latitude.isnot(None))
            .where(Supplier.longitude.isnot(None))
        )

        result = await session.execute(statement)
        suppliers = list(result.scalars().all())

        # Filter by distance in Python (Haversine formula)
        from math import radians, sin, cos, sqrt, atan2

        def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate distance between two points using Haversine formula."""
            R = 6371  # Earth's radius in kilometers

            lat1_rad = radians(lat1)
            lat2_rad = radians(lat2)
            delta_lat = radians(lat2 - lat1)
            delta_lon = radians(lon2 - lon1)

            a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            return R * c

        nearby_suppliers = []
        for supplier in suppliers:
            if supplier.latitude and supplier.longitude:
                distance = calculate_distance(
                    latitude,
                    longitude,
                    float(supplier.latitude),
                    float(supplier.longitude),
                )
                if distance <= radius_km:
                    nearby_suppliers.append(supplier)

        # Sort by distance (closest first)
        nearby_suppliers.sort(
            key=lambda s: calculate_distance(
                latitude, longitude, float(s.latitude), float(s.longitude)
            )
        )

        return nearby_suppliers


# Create singleton instance
supplier = CRUDSupplier(Supplier)

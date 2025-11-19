"""
Restaurant CRUD Operations

CRUD operations for Restaurant model.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlmodel import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


class CRUDRestaurant(CRUDBase[Restaurant, RestaurantCreate, RestaurantUpdate]):
    """
    CRUD operations for Restaurant model.

    Inherits standard CRUD operations from CRUDBase and adds
    restaurant-specific methods.
    """

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: RestaurantCreate,
        created_by_id: Optional[UUID] = None,
        owner_id: UUID,
    ) -> Restaurant:
        """
        Create a new restaurant with specified owner.

        Args:
            session: Database session
            obj_in: Restaurant creation data
            created_by_id: ID of user creating the record
            owner_id: ID of restaurant owner

        Returns:
            Created restaurant instance
        """
        # Convert to dict and add owner_id
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        obj_in_data["owner_id"] = owner_id

        # Add audit fields
        if created_by_id:
            obj_in_data["created_by_id"] = created_by_id
            obj_in_data["updated_by_id"] = created_by_id

        # Create restaurant instance
        db_obj = Restaurant(**obj_in_data)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        return db_obj

    async def get_by_owner(
        self,
        session: AsyncSession,
        owner_id: UUID,
    ) -> List[Restaurant]:
        """
        Get all restaurants owned by a specific user.

        Args:
            session: Database session
            owner_id: Owner user ID

        Returns:
            List of restaurants owned by the user
        """
        statement = select(Restaurant).where(
            Restaurant.owner_id == owner_id,
            Restaurant.is_deleted == False,
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def search(
        self,
        session: AsyncSession,
        query: str,
        city: Optional[str] = None,
        restaurant_type: Optional[str] = None,
        is_verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Restaurant]:
        """
        Search restaurants by name or location.

        Args:
            session: Database session
            query: Search query (matches name_ar or name_en)
            city: Filter by city
            restaurant_type: Filter by restaurant type
            is_verified: Filter by verification status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching restaurants
        """
        statement = select(Restaurant).where(Restaurant.is_deleted == False)

        # Search by name
        if query:
            statement = statement.where(
                or_(
                    Restaurant.name_ar.ilike(f"%{query}%"),
                    Restaurant.name_en.ilike(f"%{query}%"),
                )
            )

        # Filter by city
        if city:
            statement = statement.where(Restaurant.city == city)

        # Filter by restaurant type
        if restaurant_type:
            statement = statement.where(Restaurant.restaurant_type == restaurant_type)

        # Filter by verification status
        if is_verified is not None:
            statement = statement.where(Restaurant.is_verified == is_verified)

        # Pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_nearby(
        self,
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Restaurant]:
        """
        Get restaurants near a specific location.

        Uses Haversine formula to calculate distance.
        Note: For production, consider using PostGIS for better performance.

        Args:
            session: Database session
            latitude: Center point latitude
            longitude: Center point longitude
            radius_km: Search radius in kilometers
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of nearby restaurants
        """
        # For now, just return all restaurants with coordinates
        # TODO: Implement proper geospatial search with PostGIS or similar
        statement = (
            select(Restaurant)
            .where(
                Restaurant.is_deleted == False,
                Restaurant.latitude.isnot(None),
                Restaurant.longitude.isnot(None),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(statement)
        restaurants = list(result.scalars().all())

        # Simple distance filter (not optimized for production)
        # In production, use PostGIS or database-level geospatial queries
        from math import radians, sin, cos, sqrt, atan2

        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate distance between two points using Haversine formula."""
            R = 6371  # Earth's radius in kilometers

            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            return R * c

        # Filter by distance
        nearby = []
        for restaurant in restaurants:
            if restaurant.latitude and restaurant.longitude:
                distance = haversine_distance(
                    latitude,
                    longitude,
                    float(restaurant.latitude),
                    float(restaurant.longitude),
                )
                if distance <= radius_km:
                    nearby.append(restaurant)

        return nearby

    async def get_by_city(
        self,
        session: AsyncSession,
        city: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Restaurant]:
        """
        Get all restaurants in a specific city.

        Args:
            session: Database session
            city: City name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of restaurants in the city
        """
        statement = (
            select(Restaurant)
            .where(
                Restaurant.city == city,
                Restaurant.is_deleted == False,
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_pending_verification(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Restaurant]:
        """
        Get restaurants pending verification (admin use).

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of restaurants pending verification
        """
        statement = (
            select(Restaurant)
            .where(
                Restaurant.verification_status == "pending",
                Restaurant.is_deleted == False,
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(statement)
        return list(result.scalars().all())

    async def verify(
        self,
        session: AsyncSession,
        restaurant_id: UUID,
        verified_by_id: UUID,
        approved: bool = True,
    ) -> Optional[Restaurant]:
        """
        Verify or reject a restaurant.

        Args:
            session: Database session
            restaurant_id: Restaurant ID
            verified_by_id: Admin user ID who is verifying
            approved: True to approve, False to reject

        Returns:
            Updated restaurant or None if not found
        """
        from datetime import datetime

        restaurant = await self.get(session, restaurant_id)
        if not restaurant:
            return None

        restaurant.is_verified = approved
        restaurant.verification_status = "approved" if approved else "rejected"
        restaurant.verified_at = datetime.utcnow() if approved else None
        restaurant.verified_by_id = verified_by_id if approved else None
        restaurant.updated_by_id = verified_by_id

        session.add(restaurant)
        await session.commit()
        await session.refresh(restaurant)

        return restaurant


# Create a singleton instance
restaurant = CRUDRestaurant(Restaurant)

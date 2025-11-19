"""
Restaurant Management Endpoints

Endpoints for managing restaurants in the supply chain system.

Permission Requirements:
- List/Read: "restaurant:read" or "restaurant:*"
- Create: "restaurant:create" or "restaurant:*"
- Update: "restaurant:update" or "restaurant:*"
- Delete: "restaurant:delete" or "restaurant:*"
- Verify: "restaurant:verify" (Admin/Manager only)

Roles with access:
- Admin: Full access (has "*:*")
- Manager: Can verify restaurants
- Restaurant Owner: Can read and update own restaurant
- Restaurant Manager/Staff: Can read own restaurant
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    PermissionChecker,
    get_current_active_user,
    get_pagination_params,
)
from app.crud.restaurant import restaurant
from app.db.session import get_session
from app.models import User, Restaurant
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_user_action
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantRead,
    RestaurantList,
    RestaurantVerification,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    MessageResponse,
)

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.post(
    "",
    response_model=RestaurantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new restaurant",
    description="Register a new restaurant. Requires 'restaurant:create' permission or user must be creating their own restaurant.",
)
async def create_restaurant(
    request: Request,
    restaurant_data: RestaurantCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> RestaurantRead:
    """
    Create a new restaurant.

    Any authenticated user can create a restaurant and become the owner.
    The creator is automatically assigned as the owner.

    Request Body:
    - name_ar: Restaurant name in Arabic (required)
    - name_en: Restaurant name in English (required)
    - email: Business email (required)
    - phone_primary: Primary contact phone (required)
    - address_line1, city, district: Address fields (required)
    - restaurant_type: Type of restaurant (required)
    - cuisine_type: Cuisine type (required)
    - ... (other optional fields)

    Returns:
    - Created restaurant record
    """
    # Create restaurant with current user as owner
    new_restaurant = await restaurant.create(
        session,
        obj_in=restaurant_data,
        created_by_id=current_user.id,
        owner_id=current_user.id,  # Set owner to current user
    )

    # Audit: Restaurant creation
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Created restaurant: {new_restaurant.name_en} (ID: {new_restaurant.id})",
        changes={
            "name_ar": new_restaurant.name_ar,
            "name_en": new_restaurant.name_en,
            "city": new_restaurant.city,
            "restaurant_type": new_restaurant.restaurant_type,
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return RestaurantRead.model_validate(new_restaurant)


@router.get(
    "",
    response_model=PaginatedResponse[RestaurantList],
    summary="List restaurants",
    description="List all restaurants with filtering and pagination. Public access for browsing.",
)
async def list_restaurants(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    query: Optional[str] = Query(None, description="Search by restaurant name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    restaurant_type: Optional[str] = Query(None, description="Filter by restaurant type"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
) -> PaginatedResponse[RestaurantList]:
    """
    List restaurants with optional filters.

    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum records to return (max 100)
    - query: Search text (matches name in Arabic or English)
    - city: Filter by city name
    - restaurant_type: Filter by restaurant type
    - is_verified: Filter by verification status

    Returns:
    - Paginated list of restaurants (lightweight format)
    """
    restaurants = await restaurant.search(
        session,
        query=query,
        city=city,
        restaurant_type=restaurant_type,
        is_verified=is_verified,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Convert to list schema
    restaurant_list = [RestaurantList.model_validate(r) for r in restaurants]

    return PaginatedResponse(
        items=restaurant_list,
        total=len(restaurant_list),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/me",
    response_model=List[RestaurantRead],
    summary="Get my restaurants",
    description="Get all restaurants owned by the current user.",
)
async def get_my_restaurants(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> List[RestaurantRead]:
    """
    Get all restaurants owned by the current user.

    Returns:
    - List of restaurants where current user is the owner
    """
    restaurants = await restaurant.get_by_owner(session, owner_id=current_user.id)
    return [RestaurantRead.model_validate(r) for r in restaurants]


@router.get(
    "/city/{city}",
    response_model=List[RestaurantList],
    summary="Get restaurants by city",
    description="Get all active restaurants in a specific city.",
)
async def get_restaurants_by_city(
    city: str,
    session: AsyncSession = Depends(get_session),
) -> List[RestaurantList]:
    """
    Get all active restaurants in a specific city.

    Path Parameters:
    - city: City name (e.g., "Baghdad", "Erbil", "Basra")

    Returns:
    - List of active restaurants in the city
    """
    restaurants = await restaurant.get_by_city(session, city=city)
    return [RestaurantList.model_validate(r) for r in restaurants]


@router.get(
    "/nearby",
    response_model=List[RestaurantList],
    summary="Get nearby restaurants",
    description="Get restaurants near specified GPS coordinates.",
)
async def get_nearby_restaurants(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(10.0, ge=0.1, le=50, description="Search radius in kilometers"),
    session: AsyncSession = Depends(get_session),
) -> List[RestaurantList]:
    """
    Get restaurants within specified radius of GPS coordinates.

    Query Parameters:
    - latitude: Center point latitude (-90 to 90)
    - longitude: Center point longitude (-180 to 180)
    - radius_km: Search radius in kilometers (0.1 to 50)

    Returns:
    - List of nearby restaurants, sorted by distance
    """
    restaurants = await restaurant.get_nearby(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )
    return [RestaurantList.model_validate(r) for r in restaurants]


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantRead,
    summary="Get restaurant by ID",
    description="Get detailed information about a specific restaurant.",
)
async def get_restaurant(
    restaurant_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> RestaurantRead:
    """
    Get restaurant details by ID.

    Path Parameters:
    - restaurant_id: UUID of the restaurant

    Returns:
    - Detailed restaurant information

    Raises:
    - 404: Restaurant not found
    """
    db_restaurant = await restaurant.get(session, id=restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    return RestaurantRead.model_validate(db_restaurant)


@router.patch(
    "/{restaurant_id}",
    response_model=RestaurantRead,
    summary="Update restaurant",
    description="Update restaurant information. Only owner or admin can update.",
)
async def update_restaurant(
    request: Request,
    restaurant_id: UUID,
    restaurant_data: RestaurantUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> RestaurantRead:
    """
    Update restaurant information.

    Only the restaurant owner or users with "restaurant:update" permission can update.

    Path Parameters:
    - restaurant_id: UUID of the restaurant

    Request Body:
    - Any restaurant fields to update (all optional)

    Returns:
    - Updated restaurant record

    Raises:
    - 404: Restaurant not found
    - 403: Not authorized (not owner and no permission)
    """
    db_restaurant = await restaurant.get(session, id=restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    # Check if user is owner or has permission
    is_owner = db_restaurant.owner_id == current_user.id
    has_permission = current_user.has_permission("restaurant:update")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this restaurant",
        )

    # Update restaurant
    updated_restaurant = await restaurant.update(
        session,
        db_obj=db_restaurant,
        obj_in=restaurant_data,
        updated_by_id=current_user.id,
    )

    # Audit: Restaurant update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Updated restaurant: {updated_restaurant.name_en} (ID: {restaurant_id})",
        changes=restaurant_data.model_dump(exclude_unset=True),
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return RestaurantRead.model_validate(updated_restaurant)


@router.delete(
    "/{restaurant_id}",
    response_model=MessageResponse,
    summary="Delete restaurant",
    description="Soft delete a restaurant. Only owner or admin can delete.",
)
async def delete_restaurant(
    request: Request,
    restaurant_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("restaurant:delete")),
) -> MessageResponse:
    """
    Soft delete a restaurant.

    Permission required: restaurant:delete (Admin only) OR restaurant owner

    Path Parameters:
    - restaurant_id: UUID of the restaurant

    Returns:
    - Success message

    Raises:
    - 404: Restaurant not found
    - 403: Not authorized
    """
    db_restaurant = await restaurant.get(session, id=restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    # Check if user is owner or has permission
    is_owner = db_restaurant.owner_id == current_user.id
    if not is_owner:
        # If not owner, permission is already checked by PermissionChecker
        pass

    # Soft delete
    await restaurant.remove(session, id=restaurant_id, deleted_by_id=current_user.id)

    # Audit: Restaurant deletion
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Deleted restaurant: {db_restaurant.name_en} (ID: {restaurant_id})",
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message="Restaurant deleted successfully")


@router.post(
    "/{restaurant_id}/verify",
    response_model=RestaurantRead,
    summary="Verify restaurant",
    description="Approve or reject restaurant verification. Admin/Manager only.",
)
async def verify_restaurant(
    request: Request,
    restaurant_id: UUID,
    verification: RestaurantVerification,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("restaurant:verify")),
) -> RestaurantRead:
    """
    Verify (approve or reject) a restaurant.

    Permission required: restaurant:verify (Admin/Manager only)

    Path Parameters:
    - restaurant_id: UUID of the restaurant

    Request Body:
    - verification_status: "approved" or "rejected"
    - notes: Optional notes about the decision

    Returns:
    - Updated restaurant with verification status

    Raises:
    - 404: Restaurant not found
    """
    approved = verification.verification_status == "approved"

    verified_restaurant = await restaurant.verify(
        session,
        restaurant_id=restaurant_id,
        verified_by_id=current_user.id,
        approved=approved,
    )

    if not verified_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    # Audit: Restaurant verification
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"{'Approved' if approved else 'Rejected'} restaurant: {verified_restaurant.name_en} (ID: {restaurant_id})",
        changes={"verification_status": verification.verification_status, "notes": verification.notes},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return RestaurantRead.model_validate(verified_restaurant)


@router.get(
    "/pending/verification",
    response_model=List[RestaurantRead],
    summary="Get pending verifications",
    description="Get all restaurants pending verification. Admin/Manager only.",
)
async def get_pending_verifications(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("restaurant:verify")),
) -> List[RestaurantRead]:
    """
    Get all restaurants pending verification.

    Permission required: restaurant:verify (Admin/Manager only)

    Returns:
    - List of restaurants with pending verification status
    """
    restaurants = await restaurant.get_pending_verification(session)
    return [RestaurantRead.model_validate(r) for r in restaurants]

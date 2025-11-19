"""
Delivery API Endpoints

Provides RESTful API for delivery management including:
- Delivery creation and assignment
- GPS tracking and location updates
- Status workflow management
- Proof of delivery submission
- Driver performance analytics
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import (
    PermissionChecker,
    get_current_active_user,
    get_pagination_params,
)
from app.db.session import get_session
from app.models.user import User
from app.models.delivery import DeliveryStatus
from app.crud import delivery as delivery_crud
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryUpdate,
    DeliveryRead,
    DeliveryList,
    DeliverySearchFilters,
    DeliveryStatusUpdate,
    DeliveryAssignment,
    DeliveryLocationUpdate,
    DeliveryProofOfDelivery,
    DeliveryCancellation,
    DeliveryFailure,
    DeliveryStatistics,
    DriverStatistics,
)

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


# ==================== Create ====================


@router.post(
    "",
    response_model=DeliveryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("delivery:create"))],
)
async def create_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    delivery_in: DeliveryCreate,
    current_user: User = Depends(get_current_active_user),
) -> DeliveryRead:
    """
    Create a new delivery.

    Requires: delivery:create permission

    - Automatically calculates distance if GPS coordinates provided
    - Automatically calculates delivery fee based on distance
    - Can optionally assign driver immediately
    """
    delivery_obj = await delivery_crud.delivery.create_with_calculation(
        session,
        obj_in=delivery_in,
        created_by_id=current_user.id,
    )
    return DeliveryRead.model_validate(delivery_obj)


# ==================== Read ====================


@router.get(
    "",
    response_model=List[DeliveryList],
    dependencies=[Depends(PermissionChecker("delivery:read"))],
)
async def list_deliveries(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[UUID] = None,
    order_id: Optional[UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    city: Optional[str] = None,
    is_delayed: Optional[bool] = None,
    is_active: Optional[bool] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> List[DeliveryList]:
    """
    List deliveries with advanced filtering.

    Requires: delivery:read permission

    Filters:
    - driver_id: Filter by driver
    - order_id: Filter by order
    - status: Filter by status
    - priority: Filter by priority
    - city: Filter by delivery city
    - is_delayed: Show only delayed deliveries
    - is_active: Show only active deliveries
    """
    # Role-based filtering
    # Drivers can only see their own deliveries
    if "driver" in [role.name for role in current_user.roles]:
        driver_id = current_user.id

    deliveries = await delivery_crud.delivery.search(
        session,
        driver_id=driver_id,
        order_id=order_id,
        status=status,
        priority=priority,
        city=city,
        is_delayed=is_delayed,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )

    return [DeliveryList.model_validate(d) for d in deliveries]


@router.get(
    "/pending",
    response_model=List[DeliveryList],
    dependencies=[Depends(PermissionChecker("delivery:assign"))],
)
async def list_pending_assignments(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = None,
) -> List[DeliveryList]:
    """
    List deliveries pending driver assignment.

    Requires: delivery:assign permission

    Useful for dispatchers to see available deliveries to assign.
    """
    deliveries = await delivery_crud.delivery.get_pending_assignments(
        session,
        city=city,
        skip=skip,
        limit=limit,
    )

    return [DeliveryList.model_validate(d) for d in deliveries]


@router.get(
    "/active",
    response_model=List[DeliveryList],
    dependencies=[Depends(PermissionChecker("delivery:read"))],
)
async def list_active_deliveries(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[UUID] = None,
    city: Optional[str] = None,
) -> List[DeliveryList]:
    """
    List active deliveries (in progress, not completed).

    Requires: delivery:read permission

    Shows deliveries that are pending, assigned, picked up, in transit, or arrived.
    """
    # Drivers can only see their own deliveries
    if "driver" in [role.name for role in current_user.roles]:
        driver_id = current_user.id

    deliveries = await delivery_crud.delivery.get_active_deliveries(
        session,
        driver_id=driver_id,
        city=city,
        skip=skip,
        limit=limit,
    )

    return [DeliveryList.model_validate(d) for d in deliveries]


@router.get(
    "/driver/{driver_id}",
    response_model=List[DeliveryList],
    dependencies=[Depends(PermissionChecker("delivery:read"))],
)
async def list_driver_deliveries(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    driver_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
) -> List[DeliveryList]:
    """
    List all deliveries for a specific driver.

    Requires: delivery:read permission

    Drivers can only access their own deliveries.
    """
    # Drivers can only see their own deliveries
    if "driver" in [role.name for role in current_user.roles]:
        if driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own deliveries",
            )

    deliveries = await delivery_crud.delivery.get_by_driver(
        session,
        driver_id=driver_id,
        status=status,
        skip=skip,
        limit=limit,
    )

    return [DeliveryList.model_validate(d) for d in deliveries]


@router.get(
    "/order/{order_id}",
    response_model=List[DeliveryRead],
    dependencies=[Depends(PermissionChecker("delivery:read"))],
)
async def list_order_deliveries(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    order_id: UUID,
) -> List[DeliveryRead]:
    """
    List all deliveries for a specific order.

    Requires: delivery:read permission

    An order may have multiple delivery attempts if previous ones failed.
    """
    deliveries = await delivery_crud.delivery.get_by_order(
        session,
        order_id=order_id,
    )

    return [DeliveryRead.model_validate(d) for d in deliveries]


@router.get(
    "/statistics",
    response_model=DeliveryStatistics,
    dependencies=[Depends(PermissionChecker("delivery:read"))],
)
async def get_delivery_statistics(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    driver_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> DeliveryStatistics:
    """
    Get delivery statistics and metrics.

    Requires: delivery:read permission

    Provides:
    - Total deliveries by status
    - Total distance and fees
    - Average delivery time
    - Delayed deliveries count
    """
    # Drivers can only see their own statistics
    if "driver" in [role.name for role in current_user.roles]:
        driver_id = current_user.id

    stats = await delivery_crud.delivery.get_statistics(
        session,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
    )

    return DeliveryStatistics(**stats)


@router.get(
    "/{delivery_id}",
    response_model=DeliveryRead,
    dependencies=[Depends(PermissionChecker("delivery:read"))],
)
async def get_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
) -> DeliveryRead:
    """
    Get delivery details by ID.

    Requires: delivery:read permission

    Includes order and driver details.
    """
    delivery_obj = await delivery_crud.delivery.get_with_details(
        session,
        delivery_id=delivery_id,
    )

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Drivers can only see their own deliveries
    if "driver" in [role.name for role in current_user.roles]:
        if delivery_obj.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own deliveries",
            )

    return DeliveryRead.model_validate(delivery_obj)


# ==================== Update ====================


@router.patch(
    "/{delivery_id}",
    response_model=DeliveryRead,
    dependencies=[Depends(PermissionChecker("delivery:update"))],
)
async def update_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    delivery_in: DeliveryUpdate,
) -> DeliveryRead:
    """
    Update delivery details.

    Requires: delivery:update permission

    Can update addresses, fees, estimated times, and other details.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    updated_delivery = await delivery_crud.delivery.update(
        session,
        db_obj=delivery_obj,
        obj_in=delivery_in,
        updated_by_id=current_user.id,
    )

    return DeliveryRead.model_validate(updated_delivery)


# ==================== Driver Assignment ====================


@router.post(
    "/{delivery_id}/assign",
    response_model=DeliveryRead,
    dependencies=[Depends(PermissionChecker("delivery:assign"))],
)
async def assign_driver(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    assignment: DeliveryAssignment,
) -> DeliveryRead:
    """
    Assign a driver to a delivery.

    Requires: delivery:assign permission

    - Verifies driver exists and has driver role
    - Updates status to 'assigned'
    - Records assignment timestamp
    """
    try:
        delivery_obj = await delivery_crud.delivery.assign_driver(
            session,
            delivery_id=delivery_id,
            driver_id=assignment.driver_id,
            updated_by_id=current_user.id,
            estimated_pickup_time=assignment.estimated_pickup_time,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    return DeliveryRead.model_validate(delivery_obj)


# ==================== Status Management ====================


@router.post(
    "/{delivery_id}/status",
    response_model=DeliveryRead,
    dependencies=[Depends(PermissionChecker("delivery:update"))],
)
async def update_delivery_status(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    status_update: DeliveryStatusUpdate,
) -> DeliveryRead:
    """
    Update delivery status.

    Requires: delivery:update permission

    Validates status transitions and updates tracking timestamps.
    Drivers can update their own delivery status.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Drivers can only update their own deliveries
    if "driver" in [role.name for role in current_user.roles]:
        if delivery_obj.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own deliveries",
            )

    try:
        updated_delivery = await delivery_crud.delivery.update_status(
            session,
            delivery_id=delivery_id,
            new_status=status_update.status,
            updated_by_id=current_user.id,
            notes=status_update.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


@router.post(
    "/{delivery_id}/pickup",
    response_model=DeliveryRead,
)
async def mark_as_picked_up(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
) -> DeliveryRead:
    """
    Mark delivery as picked up.

    Driver endpoint - marks the delivery as picked up from supplier.
    Updates status to 'picked_up' and records timestamp.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Verify driver is assigned to this delivery
    if delivery_obj.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this delivery",
        )

    try:
        updated_delivery = await delivery_crud.delivery.update_status(
            session,
            delivery_id=delivery_id,
            new_status=DeliveryStatus.PICKED_UP.value,
            updated_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


@router.post(
    "/{delivery_id}/start",
    response_model=DeliveryRead,
)
async def start_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
) -> DeliveryRead:
    """
    Start delivery (in transit).

    Driver endpoint - marks the delivery as in transit to restaurant.
    Updates status to 'in_transit' and records timestamp.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Verify driver is assigned to this delivery
    if delivery_obj.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this delivery",
        )

    try:
        updated_delivery = await delivery_crud.delivery.update_status(
            session,
            delivery_id=delivery_id,
            new_status=DeliveryStatus.IN_TRANSIT.value,
            updated_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


@router.post(
    "/{delivery_id}/arrive",
    response_model=DeliveryRead,
)
async def mark_as_arrived(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
) -> DeliveryRead:
    """
    Mark delivery as arrived at restaurant.

    Driver endpoint - marks the driver as arrived at delivery location.
    Updates status to 'arrived' and records timestamp.
    Ready for proof of delivery submission.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Verify driver is assigned to this delivery
    if delivery_obj.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this delivery",
        )

    try:
        updated_delivery = await delivery_crud.delivery.update_status(
            session,
            delivery_id=delivery_id,
            new_status=DeliveryStatus.ARRIVED.value,
            updated_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


# ==================== GPS Tracking ====================


@router.post(
    "/{delivery_id}/location",
    response_model=DeliveryRead,
)
async def update_location(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    location: DeliveryLocationUpdate,
) -> DeliveryRead:
    """
    Update driver's current GPS location.

    Driver endpoint - updates current location during active delivery.
    Adds location point to tracking history.
    Only available when delivery is in progress.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Verify driver is assigned to this delivery
    if delivery_obj.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this delivery",
        )

    try:
        updated_delivery = await delivery_crud.delivery.update_location(
            session,
            delivery_id=delivery_id,
            latitude=location.latitude,
            longitude=location.longitude,
            updated_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


# ==================== Proof of Delivery ====================


@router.post(
    "/{delivery_id}/proof",
    response_model=DeliveryRead,
)
async def submit_proof_of_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    proof: DeliveryProofOfDelivery,
) -> DeliveryRead:
    """
    Submit proof of delivery.

    Driver endpoint - submits delivery proof (signature, photos, recipient info).
    Automatically marks delivery as 'delivered'.
    Must be called when status is 'arrived'.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Verify driver is assigned to this delivery
    if delivery_obj.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this delivery",
        )

    try:
        updated_delivery = await delivery_crud.delivery.submit_proof_of_delivery(
            session,
            delivery_id=delivery_id,
            signature_url=proof.signature_url,
            photo_urls=proof.photo_urls,
            recipient_name=proof.recipient_name,
            recipient_phone=proof.recipient_phone,
            recipient_notes=proof.recipient_notes,
            updated_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


# ==================== Failure and Cancellation ====================


@router.post(
    "/{delivery_id}/fail",
    response_model=DeliveryRead,
)
async def mark_as_failed(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    failure: DeliveryFailure,
) -> DeliveryRead:
    """
    Mark delivery as failed.

    Driver/Admin endpoint - marks delivery as failed with reason.
    Can include photos as evidence.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # Drivers can only mark their own deliveries as failed
    if "driver" in [role.name for role in current_user.roles]:
        if delivery_obj.driver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only mark your own deliveries as failed",
            )

    # Update status and store failure info
    try:
        updated_delivery = await delivery_crud.delivery.update_status(
            session,
            delivery_id=delivery_id,
            new_status=DeliveryStatus.FAILED.value,
            updated_by_id=current_user.id,
            notes=failure.failure_reason,
        )

        # Add photos if provided
        if failure.photo_urls:
            updated_delivery.photo_urls = {"photos": failure.photo_urls}
            session.add(updated_delivery)
            await session.commit()
            await session.refresh(updated_delivery)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return DeliveryRead.model_validate(updated_delivery)


@router.post(
    "/{delivery_id}/cancel",
    response_model=DeliveryRead,
    dependencies=[Depends(PermissionChecker("delivery:delete"))],
)
async def cancel_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
    cancellation: DeliveryCancellation,
) -> DeliveryRead:
    """
    Cancel a delivery.

    Requires: delivery:delete permission

    Can only cancel deliveries that haven't been delivered yet.
    Records cancellation reason and timestamp.
    """
    try:
        updated_delivery = await delivery_crud.delivery.update_status(
            session,
            delivery_id=delivery_id,
            new_status=DeliveryStatus.CANCELLED.value,
            updated_by_id=current_user.id,
            notes=cancellation.cancellation_reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not updated_delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    return DeliveryRead.model_validate(updated_delivery)


# ==================== Delete ====================


@router.delete(
    "/{delivery_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionChecker("delivery:delete"))],
)
async def delete_delivery(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    delivery_id: UUID,
) -> None:
    """
    Soft delete a delivery.

    Requires: delivery:delete permission

    Only for admin use. Sets is_deleted flag.
    """
    delivery_obj = await delivery_crud.delivery.get(session, id=delivery_id)

    if not delivery_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    await delivery_crud.delivery.remove(
        session,
        id=delivery_id,
        deleted_by_id=current_user.id,
    )

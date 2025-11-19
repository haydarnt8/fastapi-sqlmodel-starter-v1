"""
Order Management Endpoints

Comprehensive order management API with full workflow support.

Permission Requirements:
- List/Read: "order:read" or order owner (restaurant/supplier)
- Create: "order:create" (restaurant users)
- Update: "order:update" or order owner (draft/pending only)
- Delete: "order:delete" (admin only)
- Confirm/Reject: "order:approve" (supplier users)
- Cancel: Order owner or "order:cancel"
- Status Updates: Based on role (restaurant vs supplier)

Roles with access:
- Admin: Full access
- Restaurant Owner/Manager/Staff: Create and view own orders
- Supplier Admin/Manager: Confirm/reject orders, update status
- Accountant: View orders, update payment status
"""

from uuid import UUID
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    PermissionChecker,
    get_current_active_user,
    get_pagination_params,
)
from app.crud.order import order
from app.crud.restaurant import restaurant as restaurant_crud
from app.crud.supplier import supplier as supplier_crud
from app.db.session import get_session
from app.models import User, Order, OrderStatus
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_user_action
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderRead,
    OrderList,
    OrderStatusUpdate,
    OrderCancellation,
    OrderRejection,
    OrderConfirmation,
    OrderPaymentUpdate,
    OrderDeliveryUpdate,
    OrderInternalNotesUpdate,
    OrderSearchFilters,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    MessageResponse,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ==================== Order CRUD Endpoints ====================

@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order with items. Restaurant users only.",
)
async def create_order(
    request: Request,
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Create a new order.

    Restaurant users can create orders to suppliers.
    The order is created in 'draft' status and can be edited before submission.

    Request Body:
    - restaurant_id: Restaurant placing the order
    - supplier_id: Supplier fulfilling the order
    - items: List of products with quantities (at least 1 required)
    - notes: Optional special instructions
    - delivery_address: Optional delivery address
    - delivery_date: Optional expected delivery date

    Returns:
    - Created order with auto-calculated totals
    """
    # Verify restaurant exists
    db_restaurant = await restaurant_crud.get(session, id=order_data.restaurant_id)
    if not db_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    # Verify supplier exists
    db_supplier = await supplier_crud.get(session, id=order_data.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is authorized (restaurant owner/staff or has permission)
    is_restaurant_owner = db_restaurant.owner_id == current_user.id
    is_restaurant_staff = current_user.restaurant_id == order_data.restaurant_id
    has_permission = current_user.has_permission("order:create")

    if not (is_restaurant_owner or is_restaurant_staff or has_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create orders for this restaurant",
        )

    # Verify supplier is active
    if not db_supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier is not currently accepting orders",
        )

    try:
        # Create order with items
        new_order = await order.create_with_items(
            session,
            obj_in=order_data,
            created_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit: Order creation
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Created order: {new_order.order_number} ({len(new_order.items)} items, {new_order.total_amount} {new_order.currency})",
        changes={
            "order_number": new_order.order_number,
            "restaurant_id": str(order_data.restaurant_id),
            "supplier_id": str(order_data.supplier_id),
            "item_count": len(new_order.items),
            "total_amount": str(new_order.total_amount),
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(new_order)


@router.get(
    "",
    response_model=PaginatedResponse[OrderList],
    summary="List orders",
    description="List orders with advanced filtering. Access based on user role.",
)
async def list_orders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    pagination: PaginationParams = Depends(get_pagination_params),
    query: Optional[str] = Query(None, description="Search by order number"),
    restaurant_id: Optional[UUID] = Query(None, description="Filter by restaurant"),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    submitted_after: Optional[datetime] = Query(None, description="Submitted after date"),
    submitted_before: Optional[datetime] = Query(None, description="Submitted before date"),
) -> PaginatedResponse[OrderList]:
    """
    List orders with filters.

    Access control:
    - Admin: See all orders
    - Restaurant users: See orders for their restaurant
    - Supplier users: See orders for their supplier

    Query Parameters:
    - skip, limit: Pagination
    - query: Search by order number
    - restaurant_id: Filter by restaurant (admin only)
    - supplier_id: Filter by supplier (admin only)
    - status: Filter by order status
    - payment_status: Filter by payment status
    - submitted_after, submitted_before: Date range filter

    Returns:
    - Paginated list of orders
    """
    # Determine user's access level
    has_admin_permission = current_user.has_permission("order:*") or current_user.has_permission("*:*")

    # Apply access restrictions
    if not has_admin_permission:
        # Restaurant users: filter by their restaurant
        if current_user.restaurant_id:
            restaurant_id = current_user.restaurant_id
        # Supplier users: filter by their supplier
        elif current_user.supplier_id:
            supplier_id = current_user.supplier_id
        else:
            # User has no restaurant or supplier association
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view orders",
            )

    orders = await order.search(
        session,
        query=query,
        restaurant_id=restaurant_id,
        supplier_id=supplier_id,
        status=status_filter,
        payment_status=payment_status,
        submitted_after=submitted_after,
        submitted_before=submitted_before,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    order_list = [OrderList.model_validate(o) for o in orders]

    return PaginatedResponse(
        items=order_list,
        total=len(order_list),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/pending",
    response_model=List[OrderList],
    summary="Get pending orders",
    description="Get orders awaiting supplier confirmation. Supplier users only.",
)
async def get_pending_orders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> List[OrderList]:
    """
    Get pending orders awaiting confirmation.

    Only accessible to:
    - Supplier users (sees their supplier's pending orders)
    - Admin (sees all pending orders)

    Returns:
    - List of pending orders
    """
    supplier_id = None

    # Check if user is supplier staff
    if current_user.supplier_id:
        supplier_id = current_user.supplier_id
    elif not current_user.has_permission("order:approve"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view pending orders",
        )

    orders = await order.get_pending_orders(
        session,
        supplier_id=supplier_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    return [OrderList.model_validate(o) for o in orders]


@router.get(
    "/statistics",
    response_model=dict,
    summary="Get order statistics",
    description="Get order statistics and metrics.",
)
async def get_order_statistics(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    restaurant_id: Optional[UUID] = Query(None, description="Filter by restaurant"),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
    start_date: Optional[datetime] = Query(None, description="Start date for period"),
    end_date: Optional[datetime] = Query(None, description="End date for period"),
) -> dict:
    """
    Get order statistics.

    Access control:
    - Restaurant users: See stats for their restaurant
    - Supplier users: See stats for their supplier
    - Admin: See stats for any restaurant/supplier

    Returns:
    - total_orders: Number of orders
    - total_revenue: Total order value
    - average_order_value: Average order amount
    """
    # Apply access restrictions
    has_admin_permission = current_user.has_permission("order:*") or current_user.has_permission("*:*")

    if not has_admin_permission:
        if current_user.restaurant_id:
            restaurant_id = current_user.restaurant_id
        elif current_user.supplier_id:
            supplier_id = current_user.supplier_id
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view statistics",
            )

    stats = await order.get_statistics(
        session,
        restaurant_id=restaurant_id,
        supplier_id=supplier_id,
        start_date=start_date,
        end_date=end_date,
    )

    return stats


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get order by ID",
    description="Get detailed order information with items.",
)
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Get order details by ID.

    Access control:
    - Order must belong to user's restaurant or supplier
    - Admin can access any order

    Path Parameters:
    - order_id: UUID of the order

    Returns:
    - Detailed order information with items

    Raises:
    - 404: Order not found
    - 403: Not authorized to view this order
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check authorization
    is_restaurant_order = db_order.restaurant_id == current_user.restaurant_id
    is_supplier_order = db_order.supplier_id == current_user.supplier_id
    has_permission = current_user.has_permission("order:read") or current_user.has_permission("order:*")

    if not (is_restaurant_order or is_supplier_order or has_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order",
        )

    return OrderRead.model_validate(db_order)


@router.patch(
    "/{order_id}",
    response_model=OrderRead,
    summary="Update order",
    description="Update order details. Only for draft/pending orders.",
)
async def update_order(
    request: Request,
    order_id: UUID,
    order_data: OrderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Update order information.

    Only draft and pending orders can be updated.
    Only restaurant owner/staff can update their orders.

    Path Parameters:
    - order_id: UUID of the order

    Request Body:
    - Any order fields to update (all optional)

    Returns:
    - Updated order record

    Raises:
    - 404: Order not found
    - 403: Not authorized or order not editable
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check if order is editable
    if not db_order.is_editable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order in '{db_order.status}' status cannot be edited",
        )

    # Check authorization
    is_restaurant_order = db_order.restaurant_id == current_user.restaurant_id
    has_permission = current_user.has_permission("order:update")

    if not (is_restaurant_order or has_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this order",
        )

    # Update order
    updated_order = await order.update(
        session,
        db_obj=db_order,
        obj_in=order_data,
        updated_by_id=current_user.id,
    )

    # Recalculate if delivery fee or discount changed
    if order_data.delivery_fee is not None or order_data.discount_amount is not None:
        await session.refresh(updated_order, ["items"])
        updated_order.calculate_totals(updated_order.items)
        session.add(updated_order)
        await session.commit()
        await session.refresh(updated_order)

    # Audit: Order update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Updated order: {updated_order.order_number}",
        changes=order_data.model_dump(exclude_unset=True),
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


# ==================== Order Workflow Endpoints ====================

@router.post(
    "/{order_id}/submit",
    response_model=OrderRead,
    summary="Submit order",
    description="Submit draft order to supplier for approval.",
)
async def submit_order(
    request: Request,
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Submit draft order for supplier approval.

    Changes status from 'draft' to 'pending'.

    Path Parameters:
    - order_id: UUID of the order

    Returns:
    - Updated order with 'pending' status

    Raises:
    - 404: Order not found
    - 400: Order not in draft status
    - 403: Not authorized
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check authorization
    is_restaurant_order = db_order.restaurant_id == current_user.restaurant_id
    if not is_restaurant_order and not current_user.has_permission("order:update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this order",
        )

    # Verify order is in draft status
    if db_order.status != OrderStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only draft orders can be submitted. Current status: {db_order.status}",
        )

    # Submit order
    try:
        updated_order = await order.update_status(
            session,
            order_id=order_id,
            new_status=OrderStatus.PENDING.value,
            updated_by_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit: Order submission
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Submitted order: {updated_order.order_number} for supplier approval",
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


@router.post(
    "/{order_id}/confirm",
    response_model=OrderRead,
    summary="Confirm order",
    description="Supplier confirms order. Changes status to 'confirmed'.",
)
async def confirm_order(
    request: Request,
    order_id: UUID,
    confirmation: OrderConfirmation,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("order:approve")),
) -> OrderRead:
    """
    Confirm order (supplier only).

    Changes status from 'pending' to 'confirmed'.

    Path Parameters:
    - order_id: UUID of the order

    Request Body:
    - delivery_date: Optional confirmed delivery date
    - notes: Optional confirmation notes

    Returns:
    - Updated order with 'confirmed' status

    Raises:
    - 404: Order not found
    - 400: Order not in pending status
    - 403: Not authorized (must be supplier staff)
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check if user is from the supplier
    is_supplier_order = db_order.supplier_id == current_user.supplier_id
    if not is_supplier_order and not current_user.has_permission("order:*"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to confirm this order",
        )

    # Verify order is in pending status
    if db_order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only pending orders can be confirmed. Current status: {db_order.status}",
        )

    # Update delivery date if provided
    if confirmation.delivery_date:
        db_order.delivery_date = confirmation.delivery_date

    # Confirm order
    try:
        updated_order = await order.update_status(
            session,
            order_id=order_id,
            new_status=OrderStatus.CONFIRMED.value,
            updated_by_id=current_user.id,
            notes=confirmation.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit: Order confirmation
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Confirmed order: {updated_order.order_number}",
        changes={"delivery_date": str(confirmation.delivery_date) if confirmation.delivery_date else None},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


@router.post(
    "/{order_id}/reject",
    response_model=OrderRead,
    summary="Reject order",
    description="Supplier rejects order. Changes status to 'rejected'.",
)
async def reject_order(
    request: Request,
    order_id: UUID,
    rejection: OrderRejection,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("order:approve")),
) -> OrderRead:
    """
    Reject order (supplier only).

    Changes status from 'pending' to 'rejected'.

    Path Parameters:
    - order_id: UUID of the order

    Request Body:
    - reason: Reason for rejection (required)

    Returns:
    - Updated order with 'rejected' status

    Raises:
    - 404: Order not found
    - 400: Order not in pending status
    - 403: Not authorized (must be supplier staff)
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check if user is from the supplier
    is_supplier_order = db_order.supplier_id == current_user.supplier_id
    if not is_supplier_order and not current_user.has_permission("order:*"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reject this order",
        )

    # Verify order is in pending status
    if db_order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only pending orders can be rejected. Current status: {db_order.status}",
        )

    # Reject order
    try:
        updated_order = await order.update_status(
            session,
            order_id=order_id,
            new_status=OrderStatus.REJECTED.value,
            updated_by_id=current_user.id,
            notes=rejection.reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit: Order rejection
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Rejected order: {updated_order.order_number} - Reason: {rejection.reason}",
        changes={"rejection_reason": rejection.reason},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Cancel order",
    description="Cancel order. Can be done by restaurant or supplier (before delivery).",
)
async def cancel_order(
    request: Request,
    order_id: UUID,
    cancellation: OrderCancellation,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Cancel order.

    Can be cancelled by:
    - Restaurant (if pending or confirmed)
    - Supplier (if confirmed or processing)
    - Admin (any time before delivery)

    Path Parameters:
    - order_id: UUID of the order

    Request Body:
    - reason: Reason for cancellation (required)

    Returns:
    - Updated order with 'cancelled' status

    Raises:
    - 404: Order not found
    - 400: Order cannot be cancelled (already delivered/cancelled/rejected)
    - 403: Not authorized
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check if order can be cancelled
    if not db_order.is_cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order in '{db_order.status}' status cannot be cancelled",
        )

    # Check authorization
    is_restaurant_order = db_order.restaurant_id == current_user.restaurant_id
    is_supplier_order = db_order.supplier_id == current_user.supplier_id
    has_permission = current_user.has_permission("order:cancel") or current_user.has_permission("order:*")

    if not (is_restaurant_order or is_supplier_order or has_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order",
        )

    # Cancel order
    try:
        updated_order = await order.update_status(
            session,
            order_id=order_id,
            new_status=OrderStatus.CANCELLED.value,
            updated_by_id=current_user.id,
            notes=cancellation.reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit: Order cancellation
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Cancelled order: {updated_order.order_number} - Reason: {cancellation.reason}",
        changes={"cancellation_reason": cancellation.reason},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


@router.post(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Update order status",
    description="Update order status through workflow. Supplier only.",
)
async def update_order_status(
    request: Request,
    order_id: UUID,
    status_update: OrderStatusUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Update order status.

    Supplier can move order through workflow:
    - confirmed → processing → ready_for_delivery → in_transit → delivered

    Path Parameters:
    - order_id: UUID of the order

    Request Body:
    - status: New status
    - notes: Optional notes

    Returns:
    - Updated order

    Raises:
    - 404: Order not found
    - 400: Invalid status transition
    - 403: Not authorized (must be supplier staff)
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check if user is from the supplier or has permission
    is_supplier_order = db_order.supplier_id == current_user.supplier_id
    has_permission = current_user.has_permission("order:update") or current_user.has_permission("order:*")

    if not (is_supplier_order or has_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update order status",
        )

    # Update status
    try:
        updated_order = await order.update_status(
            session,
            order_id=order_id,
            new_status=status_update.status,
            updated_by_id=current_user.id,
            notes=status_update.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit: Status update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Updated order {updated_order.order_number} status: {db_order.status} → {status_update.status}",
        changes={"old_status": db_order.status, "new_status": status_update.status},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


# ==================== Payment & Delivery Endpoints ====================

@router.post(
    "/{order_id}/payment",
    response_model=OrderRead,
    summary="Add payment",
    description="Record a payment for an order.",
)
async def add_payment(
    request: Request,
    order_id: UUID,
    payment: OrderPaymentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> OrderRead:
    """
    Record a payment for an order.

    Can be done by:
    - Supplier staff (recording payment received)
    - Accountant
    - Admin

    Path Parameters:
    - order_id: UUID of the order

    Request Body:
    - payment_method: Payment method
    - payment_amount: Amount paid
    - payment_notes: Optional notes

    Returns:
    - Updated order with payment recorded

    Raises:
    - 404: Order not found
    - 403: Not authorized
    """
    db_order = await order.get_with_items(session, order_id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Check authorization
    is_supplier_order = db_order.supplier_id == current_user.supplier_id
    has_permission = current_user.has_permission("payment:create") or current_user.has_permission("order:*")

    if not (is_supplier_order or has_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to record payments for this order",
        )

    # Add payment
    updated_order = await order.add_payment(
        session,
        order_id=order_id,
        payment_amount=payment.payment_amount,
        payment_method=payment.payment_method,
        updated_by_id=current_user.id,
    )

    # Audit: Payment recorded
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Recorded payment for order {updated_order.order_number}: {payment.payment_amount} {updated_order.currency}",
        changes={
            "payment_method": payment.payment_method,
            "payment_amount": str(payment.payment_amount),
            "outstanding": str(updated_order.outstanding_amount),
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return OrderRead.model_validate(updated_order)


@router.delete(
    "/{order_id}",
    response_model=MessageResponse,
    summary="Delete order",
    description="Soft delete an order. Admin only.",
)
async def delete_order(
    request: Request,
    order_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("order:delete")),
) -> MessageResponse:
    """
    Soft delete an order.

    Permission required: order:delete (Admin only)

    Path Parameters:
    - order_id: UUID of the order

    Returns:
    - Success message

    Raises:
    - 404: Order not found
    """
    db_order = await order.get(session, id=order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Soft delete
    await order.remove(session, id=order_id, deleted_by_id=current_user.id)

    # Audit: Order deletion
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Deleted order: {db_order.order_number}",
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message="Order deleted successfully")

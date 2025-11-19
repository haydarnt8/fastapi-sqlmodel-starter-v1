"""
Supplier Management Endpoints

Endpoints for managing suppliers in the supply chain system.

Permission Requirements:
- List/Read: "supplier:read" or "supplier:*"
- Create: "supplier:create" or "supplier:*"
- Update: "supplier:update" or "supplier:*"
- Delete: "supplier:delete" or "supplier:*"
- Verify: "supplier:verify" (Admin/Manager only)

Roles with access:
- Admin: Full access (has "*:*")
- Manager: Can verify suppliers
- Supplier Admin: Can read and update own supplier
- Supplier Manager/Staff: Can read own supplier
"""

from uuid import UUID
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    PermissionChecker,
    get_current_active_user,
    get_pagination_params,
)
from app.crud.supplier import supplier
from app.db.session import get_session
from app.models import User, Supplier
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_user_action
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierRead,
    SupplierList,
    SupplierVerification,
    SupplierSearchFilters,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    MessageResponse,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post(
    "",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supplier",
    description="Register a new supplier. Any authenticated user can create and become the owner.",
)
async def create_supplier(
    request: Request,
    supplier_data: SupplierCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SupplierRead:
    """
    Create a new supplier.

    Any authenticated user can create a supplier and become the owner.
    The creator is automatically assigned as the owner.

    Request Body:
    - company_name_ar: Company name in Arabic (required)
    - company_name_en: Company name in English (required)
    - email: Business email (required)
    - phone_primary: Primary contact phone (required)
    - address_line1, city, district: Address fields (required)
    - product_categories: List of product categories (optional)
    - ... (other optional fields)

    Returns:
    - Created supplier record
    """
    # Create supplier with current user as owner
    new_supplier = await supplier.create(
        session,
        obj_in=supplier_data,
        created_by_id=current_user.id,
        owner_id=current_user.id,  # Set owner to current user
    )

    # Audit: Supplier creation
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Created supplier: {new_supplier.company_name_en} (ID: {new_supplier.id})",
        changes={
            "company_name_ar": new_supplier.company_name_ar,
            "company_name_en": new_supplier.company_name_en,
            "city": new_supplier.city,
            "product_categories": new_supplier.product_categories,
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return SupplierRead.model_validate(new_supplier)


@router.get(
    "",
    response_model=PaginatedResponse[SupplierList],
    summary="List suppliers",
    description="List all suppliers with filtering and pagination. Public access for browsing.",
)
async def list_suppliers(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    query: Optional[str] = Query(None, description="Search by company name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    product_category: Optional[str] = Query(None, description="Filter by product category"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_rating: Optional[Decimal] = Query(None, ge=0, le=5, description="Minimum average rating"),
    accepts_cash: Optional[bool] = Query(None, description="Filter by cash payment acceptance"),
    accepts_credit: Optional[bool] = Query(None, description="Filter by credit payment acceptance"),
) -> PaginatedResponse[SupplierList]:
    """
    List suppliers with optional filters.

    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum records to return (max 100)
    - query: Search text (matches company name in Arabic or English)
    - city: Filter by city name
    - product_category: Filter by product category
    - is_verified: Filter by verification status
    - is_active: Filter by active status
    - min_rating: Minimum average rating (0-5)
    - accepts_cash: Filter by cash payment acceptance
    - accepts_credit: Filter by credit payment acceptance

    Returns:
    - Paginated list of suppliers (lightweight format)
    """
    suppliers = await supplier.search(
        session,
        query=query,
        city=city,
        product_category=product_category,
        is_verified=is_verified,
        is_active=is_active,
        min_rating=min_rating,
        accepts_cash=accepts_cash,
        accepts_credit=accepts_credit,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Convert to list schema
    supplier_list = [SupplierList.model_validate(s) for s in suppliers]

    return PaginatedResponse(
        items=supplier_list,
        total=len(supplier_list),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/me",
    response_model=List[SupplierRead],
    summary="Get my suppliers",
    description="Get all suppliers owned by the current user.",
)
async def get_my_suppliers(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> List[SupplierRead]:
    """
    Get all suppliers owned by the current user.

    Returns:
    - List of suppliers where current user is the owner
    """
    suppliers = await supplier.get_by_owner(session, owner_id=current_user.id)
    return [SupplierRead.model_validate(s) for s in suppliers]


@router.get(
    "/city/{city}",
    response_model=List[SupplierList],
    summary="Get suppliers by city",
    description="Get all active suppliers in a specific city.",
)
async def get_suppliers_by_city(
    city: str,
    session: AsyncSession = Depends(get_session),
) -> List[SupplierList]:
    """
    Get all active suppliers in a specific city.

    Path Parameters:
    - city: City name (e.g., "Baghdad", "Erbil", "Basra")

    Returns:
    - List of active suppliers in the city
    """
    suppliers = await supplier.get_by_city(session, city=city)
    return [SupplierList.model_validate(s) for s in suppliers]


@router.get(
    "/top-rated",
    response_model=List[SupplierList],
    summary="Get top-rated suppliers",
    description="Get top-rated suppliers, optionally filtered by city.",
)
async def get_top_rated_suppliers(
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(10, ge=1, le=50, description="Number of suppliers to return"),
    session: AsyncSession = Depends(get_session),
) -> List[SupplierList]:
    """
    Get top-rated suppliers.

    Query Parameters:
    - city: Optional city filter
    - limit: Maximum number of suppliers (1-50, default 10)

    Returns:
    - List of top-rated suppliers, sorted by rating
    """
    suppliers = await supplier.get_top_rated(session, city=city, limit=limit)
    return [SupplierList.model_validate(s) for s in suppliers]


@router.get(
    "/nearby",
    response_model=List[SupplierList],
    summary="Get nearby suppliers",
    description="Get suppliers near specified GPS coordinates.",
)
async def get_nearby_suppliers(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(10.0, ge=0.1, le=50, description="Search radius in kilometers"),
    session: AsyncSession = Depends(get_session),
) -> List[SupplierList]:
    """
    Get suppliers within specified radius of GPS coordinates.

    Query Parameters:
    - latitude: Center point latitude (-90 to 90)
    - longitude: Center point longitude (-180 to 180)
    - radius_km: Search radius in kilometers (0.1 to 50)

    Returns:
    - List of nearby suppliers, sorted by distance
    """
    suppliers = await supplier.get_nearby(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )
    return [SupplierList.model_validate(s) for s in suppliers]


@router.get(
    "/delivery-area/{city}",
    response_model=List[SupplierList],
    summary="Get suppliers by delivery area",
    description="Get suppliers that deliver to a specific area.",
)
async def get_suppliers_by_delivery_area(
    city: str,
    district: Optional[str] = Query(None, description="Optional district name"),
    session: AsyncSession = Depends(get_session),
) -> List[SupplierList]:
    """
    Get suppliers that deliver to a specific area.

    Path Parameters:
    - city: City name

    Query Parameters:
    - district: Optional district/neighborhood name

    Returns:
    - List of suppliers that deliver to the specified area
    """
    suppliers = await supplier.filter_by_delivery_area(
        session,
        city=city,
        district=district,
    )
    return [SupplierList.model_validate(s) for s in suppliers]


@router.get(
    "/{supplier_id}",
    response_model=SupplierRead,
    summary="Get supplier by ID",
    description="Get detailed information about a specific supplier.",
)
async def get_supplier(
    supplier_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SupplierRead:
    """
    Get supplier details by ID.

    Path Parameters:
    - supplier_id: UUID of the supplier

    Returns:
    - Detailed supplier information

    Raises:
    - 404: Supplier not found
    """
    db_supplier = await supplier.get(session, id=supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return SupplierRead.model_validate(db_supplier)


@router.patch(
    "/{supplier_id}",
    response_model=SupplierRead,
    summary="Update supplier",
    description="Update supplier information. Only owner or admin can update.",
)
async def update_supplier(
    request: Request,
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SupplierRead:
    """
    Update supplier information.

    Only the supplier owner or users with "supplier:update" permission can update.

    Path Parameters:
    - supplier_id: UUID of the supplier

    Request Body:
    - Any supplier fields to update (all optional)

    Returns:
    - Updated supplier record

    Raises:
    - 404: Supplier not found
    - 403: Not authorized (not owner and no permission)
    """
    db_supplier = await supplier.get(session, id=supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is owner or has permission
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("supplier:update")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this supplier",
        )

    # Update supplier
    updated_supplier = await supplier.update(
        session,
        db_obj=db_supplier,
        obj_in=supplier_data,
        updated_by_id=current_user.id,
    )

    # Audit: Supplier update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Updated supplier: {updated_supplier.company_name_en} (ID: {supplier_id})",
        changes=supplier_data.model_dump(exclude_unset=True),
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return SupplierRead.model_validate(updated_supplier)


@router.delete(
    "/{supplier_id}",
    response_model=MessageResponse,
    summary="Delete supplier",
    description="Soft delete a supplier. Only owner or admin can delete.",
)
async def delete_supplier(
    request: Request,
    supplier_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("supplier:delete")),
) -> MessageResponse:
    """
    Soft delete a supplier.

    Permission required: supplier:delete (Admin only) OR supplier owner

    Path Parameters:
    - supplier_id: UUID of the supplier

    Returns:
    - Success message

    Raises:
    - 404: Supplier not found
    - 403: Not authorized
    """
    db_supplier = await supplier.get(session, id=supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is owner or has permission
    is_owner = db_supplier.owner_id == current_user.id
    if not is_owner:
        # If not owner, permission is already checked by PermissionChecker
        pass

    # Soft delete
    await supplier.remove(session, id=supplier_id, deleted_by_id=current_user.id)

    # Audit: Supplier deletion
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Deleted supplier: {db_supplier.company_name_en} (ID: {supplier_id})",
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message="Supplier deleted successfully")


@router.post(
    "/{supplier_id}/verify",
    response_model=SupplierRead,
    summary="Verify supplier",
    description="Approve or reject supplier verification. Admin/Manager only.",
)
async def verify_supplier(
    request: Request,
    supplier_id: UUID,
    verification: SupplierVerification,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("supplier:verify")),
) -> SupplierRead:
    """
    Verify (approve or reject) a supplier.

    Permission required: supplier:verify (Admin/Manager only)

    Path Parameters:
    - supplier_id: UUID of the supplier

    Request Body:
    - verification_status: "approved" or "rejected"
    - notes: Optional notes about the decision

    Returns:
    - Updated supplier with verification status

    Raises:
    - 404: Supplier not found
    """
    approved = verification.verification_status == "approved"

    verified_supplier = await supplier.verify(
        session,
        supplier_id=supplier_id,
        verified_by_id=current_user.id,
        approved=approved,
    )

    if not verified_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Audit: Supplier verification
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"{'Approved' if approved else 'Rejected'} supplier: {verified_supplier.company_name_en} (ID: {supplier_id})",
        changes={"verification_status": verification.verification_status, "notes": verification.notes},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return SupplierRead.model_validate(verified_supplier)


@router.get(
    "/pending/verification",
    response_model=List[SupplierRead],
    summary="Get pending verifications",
    description="Get all suppliers pending verification. Admin/Manager only.",
)
async def get_pending_verifications(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(PermissionChecker("supplier:verify")),
) -> List[SupplierRead]:
    """
    Get all suppliers pending verification.

    Permission required: supplier:verify (Admin/Manager only)

    Returns:
    - List of suppliers with pending verification status
    """
    suppliers = await supplier.get_pending_verification(session)
    return [SupplierRead.model_validate(s) for s in suppliers]


@router.post(
    "/{supplier_id}/toggle-active",
    response_model=SupplierRead,
    summary="Toggle supplier active status",
    description="Activate or deactivate a supplier. Owner or admin only.",
)
async def toggle_supplier_active(
    request: Request,
    supplier_id: UUID,
    is_active: bool = Query(..., description="New active status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SupplierRead:
    """
    Toggle supplier's active status.

    Only owner or users with supplier:update permission can toggle.

    Path Parameters:
    - supplier_id: UUID of the supplier

    Query Parameters:
    - is_active: True to activate, False to deactivate

    Returns:
    - Updated supplier record

    Raises:
    - 404: Supplier not found
    - 403: Not authorized
    """
    db_supplier = await supplier.get(session, id=supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is owner or has permission
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("supplier:update")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this supplier",
        )

    # Toggle active status
    updated_supplier = await supplier.toggle_active_status(
        session,
        supplier_id=supplier_id,
        is_active=is_active,
    )

    # Audit: Status change
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"{'Activated' if is_active else 'Deactivated'} supplier: {db_supplier.company_name_en} (ID: {supplier_id})",
        changes={"is_active": is_active},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return SupplierRead.model_validate(updated_supplier)

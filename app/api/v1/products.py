"""
Product Management Endpoints

Endpoints for managing products in the supply chain marketplace.

Permission Requirements:
- List/Read: Public access (no permission required)
- Create: "product:create" or "product:*"
- Update: "product:update" or "product:*" (or supplier owner)
- Delete: "product:delete" or "product:*" (or supplier owner)

Roles with access:
- Admin: Full access (has "*:*")
- Supplier Admin/Manager: Can manage their supplier's products
- Restaurant users: Can browse products (read-only)
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
from app.crud.product import product
from app.crud.supplier import supplier as supplier_crud
from app.db.session import get_session
from app.models import User, Product
from app.models.audit_log import AuditAction, AuditStatus
from app.core.audit import log_user_action
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductRead,
    ProductList,
    ProductSearchFilters,
    ProductStockUpdate,
    ProductBulkPriceUpdate,
)
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    MessageResponse,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product. Requires 'product:create' permission or user must be supplier owner/manager.",
)
async def create_product(
    request: Request,
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ProductRead:
    """
    Create a new product.

    Supplier owners/managers can create products for their supplier.
    Users with product:create permission can create products for any supplier.

    Request Body:
    - supplier_id: Supplier who offers this product (required)
    - sku: Stock Keeping Unit (required)
    - name_ar, name_en: Product names in Arabic and English (required)
    - category: Product category (required)
    - unit_price: Price per unit (required)
    - unit_of_measure: Unit type (required)
    - ... (other optional fields)

    Returns:
    - Created product record
    """
    # Get the supplier
    db_supplier = await supplier_crud.get(session, id=product_data.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is supplier owner or has permission
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("product:create")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create products for this supplier",
        )

    # Check if SKU already exists for this supplier
    existing_product = await product.get_by_sku(
        session, sku=product_data.sku, supplier_id=product_data.supplier_id
    )
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product_data.sku}' already exists for this supplier",
        )

    # Create product
    new_product = await product.create(
        session,
        obj_in=product_data,
        created_by_id=current_user.id,
    )

    # Audit: Product creation
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Created product: {new_product.name_en} (SKU: {new_product.sku})",
        changes={
            "name_ar": new_product.name_ar,
            "name_en": new_product.name_en,
            "sku": new_product.sku,
            "category": new_product.category,
            "unit_price": str(new_product.unit_price),
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return ProductRead.model_validate(new_product)


@router.get(
    "",
    response_model=PaginatedResponse[ProductList],
    summary="List products",
    description="List all products with advanced filtering and pagination. Public access.",
)
async def list_products(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    query: Optional[str] = Query(None, description="Search by product name, SKU, or description"),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter featured products"),
    in_stock_only: bool = Query(True, description="Show only in-stock products"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
) -> PaginatedResponse[ProductList]:
    """
    List products with advanced filters.

    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum records to return (max 100)
    - query: Search text (matches name, SKU, description)
    - supplier_id: Filter by supplier
    - category: Filter by category
    - subcategory: Filter by subcategory
    - min_price, max_price: Price range filter
    - is_active: Filter by active status
    - is_featured: Filter featured products
    - in_stock_only: Show only available products (default: true)
    - sort_by: Field to sort by
    - sort_order: asc or desc

    Returns:
    - Paginated list of products (lightweight format)
    """
    products = await product.search(
        session,
        query=query,
        supplier_id=supplier_id,
        category=category,
        subcategory=subcategory,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        is_featured=is_featured,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=pagination.skip,
        limit=pagination.limit,
    )

    # Convert to list schema
    product_list = [ProductList.model_validate(p) for p in products]

    return PaginatedResponse(
        items=product_list,
        total=len(product_list),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/supplier/{supplier_id}",
    response_model=List[ProductList],
    summary="Get products by supplier",
    description="Get all products offered by a specific supplier.",
)
async def get_products_by_supplier(
    supplier_id: UUID,
    session: AsyncSession = Depends(get_session),
    active_only: bool = Query(True, description="Return only active products"),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> List[ProductList]:
    """
    Get all products for a specific supplier.

    Path Parameters:
    - supplier_id: UUID of the supplier

    Query Parameters:
    - active_only: Return only active products (default: true)
    - skip, limit: Pagination parameters

    Returns:
    - List of products offered by the supplier
    """
    products = await product.get_by_supplier(
        session,
        supplier_id=supplier_id,
        active_only=active_only,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [ProductList.model_validate(p) for p in products]


@router.get(
    "/category/{category}",
    response_model=List[ProductList],
    summary="Get products by category",
    description="Get all products in a specific category.",
)
async def get_products_by_category(
    category: str,
    session: AsyncSession = Depends(get_session),
    active_only: bool = Query(True, description="Return only active products"),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> List[ProductList]:
    """
    Get all products in a specific category.

    Path Parameters:
    - category: Category name (e.g., "Vegetables", "Dairy", "Meat")

    Query Parameters:
    - active_only: Return only active products
    - skip, limit: Pagination parameters

    Returns:
    - List of products in the category
    """
    products = await product.get_by_category(
        session,
        category=category,
        active_only=active_only,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [ProductList.model_validate(p) for p in products]


@router.get(
    "/featured",
    response_model=List[ProductList],
    summary="Get featured products",
    description="Get featured/promoted products.",
)
async def get_featured_products(
    session: AsyncSession = Depends(get_session),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
    limit: int = Query(20, ge=1, le=100, description="Maximum products to return"),
) -> List[ProductList]:
    """
    Get featured products.

    Query Parameters:
    - supplier_id: Optional supplier filter
    - limit: Maximum products (default: 20, max: 100)

    Returns:
    - List of featured products
    """
    products = await product.get_featured(
        session,
        supplier_id=supplier_id,
        limit=limit,
    )
    return [ProductList.model_validate(p) for p in products]


@router.get(
    "/low-stock",
    response_model=List[ProductList],
    summary="Get low stock products",
    description="Get products with stock below reorder level. Supplier owners only.",
)
async def get_low_stock_products(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> List[ProductList]:
    """
    Get products with low stock (below reorder level).

    Query Parameters:
    - supplier_id: Optional supplier filter (if not provided, uses user's supplier)
    - skip, limit: Pagination parameters

    Returns:
    - List of low-stock products

    Authorization:
    - If supplier_id not provided, returns products for user's supplier (must be supplier owner/staff)
    - If supplier_id provided, user must be that supplier's owner or have product:read permission
    """
    target_supplier_id = supplier_id

    # If no supplier_id provided, use current user's supplier
    if not target_supplier_id:
        if not current_user.supplier_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with any supplier",
            )
        target_supplier_id = current_user.supplier_id
    else:
        # Check if user has access to this supplier's data
        db_supplier = await supplier_crud.get(session, id=target_supplier_id)
        if not db_supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found",
            )

        is_owner = db_supplier.owner_id == current_user.id
        has_permission = current_user.has_permission("product:read")

        if not is_owner and not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this supplier's products",
            )

    products = await product.get_low_stock(
        session,
        supplier_id=target_supplier_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [ProductList.model_validate(p) for p in products]


@router.get(
    "/sku/{sku}",
    response_model=ProductRead,
    summary="Get product by SKU",
    description="Get product details by SKU and optional supplier.",
)
async def get_product_by_sku(
    sku: str,
    session: AsyncSession = Depends(get_session),
    supplier_id: Optional[UUID] = Query(None, description="Filter by supplier"),
) -> ProductRead:
    """
    Get product by SKU.

    Path Parameters:
    - sku: Stock Keeping Unit

    Query Parameters:
    - supplier_id: Optional supplier filter

    Returns:
    - Product details

    Raises:
    - 404: Product not found
    """
    db_product = await product.get_by_sku(
        session,
        sku=sku,
        supplier_id=supplier_id,
    )

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductRead.model_validate(db_product)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get product by ID",
    description="Get detailed information about a specific product.",
)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ProductRead:
    """
    Get product details by ID.

    Path Parameters:
    - product_id: UUID of the product

    Returns:
    - Detailed product information

    Raises:
    - 404: Product not found
    """
    db_product = await product.get(session, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductRead.model_validate(db_product)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update product",
    description="Update product information. Only supplier owner or admin can update.",
)
async def update_product(
    request: Request,
    product_id: UUID,
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ProductRead:
    """
    Update product information.

    Only the supplier owner or users with "product:update" permission can update.

    Path Parameters:
    - product_id: UUID of the product

    Request Body:
    - Any product fields to update (all optional)

    Returns:
    - Updated product record

    Raises:
    - 404: Product not found
    - 403: Not authorized (not supplier owner and no permission)
    """
    db_product = await product.get(session, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get the supplier
    db_supplier = await supplier_crud.get(session, id=db_product.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is supplier owner or has permission
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("product:update")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this product",
        )

    # Update product
    updated_product = await product.update(
        session,
        db_obj=db_product,
        obj_in=product_data,
        updated_by_id=current_user.id,
    )

    # Audit: Product update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Updated product: {updated_product.name_en} (SKU: {updated_product.sku})",
        changes=product_data.model_dump(exclude_unset=True),
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return ProductRead.model_validate(updated_product)


@router.patch(
    "/{product_id}/stock",
    response_model=ProductRead,
    summary="Update product stock",
    description="Update product stock quantity. Supplier owner only.",
)
async def update_product_stock(
    request: Request,
    product_id: UUID,
    stock_data: ProductStockUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ProductRead:
    """
    Update product stock quantity.

    Only supplier owner can update stock.

    Path Parameters:
    - product_id: UUID of the product

    Request Body:
    - stock_quantity: New stock quantity
    - notes: Optional notes about the update

    Returns:
    - Updated product record

    Raises:
    - 404: Product not found
    - 403: Not authorized
    """
    db_product = await product.get(session, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get the supplier
    db_supplier = await supplier_crud.get(session, id=db_product.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is supplier owner
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("product:update")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update stock for this product",
        )

    # Update stock
    updated_product = await product.update_stock(
        session,
        product_id=product_id,
        quantity=stock_data.stock_quantity,
        updated_by_id=current_user.id,
    )

    # Audit: Stock update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Updated stock for product: {updated_product.name_en} - New quantity: {stock_data.stock_quantity}",
        changes={
            "old_stock": str(db_product.stock_quantity),
            "new_stock": str(stock_data.stock_quantity),
            "notes": stock_data.notes,
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return ProductRead.model_validate(updated_product)


@router.post(
    "/{product_id}/toggle-active",
    response_model=ProductRead,
    summary="Toggle product active status",
    description="Activate or deactivate a product. Supplier owner only.",
)
async def toggle_product_active(
    request: Request,
    product_id: UUID,
    is_active: bool = Query(..., description="New active status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ProductRead:
    """
    Toggle product active status.

    Only supplier owner can toggle status.

    Path Parameters:
    - product_id: UUID of the product

    Query Parameters:
    - is_active: New active status (true/false)

    Returns:
    - Updated product record

    Raises:
    - 404: Product not found
    - 403: Not authorized
    """
    db_product = await product.get(session, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get the supplier
    db_supplier = await supplier_crud.get(session, id=db_product.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is supplier owner
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("product:update")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this product",
        )

    # Toggle active status
    updated_product = await product.toggle_active_status(
        session,
        product_id=product_id,
        is_active=is_active,
        updated_by_id=current_user.id,
    )

    # Audit: Status toggle
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"{'Activated' if is_active else 'Deactivated'} product: {updated_product.name_en}",
        changes={"is_active": is_active},
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return ProductRead.model_validate(updated_product)


@router.post(
    "/bulk/update-discount",
    response_model=MessageResponse,
    summary="Bulk update product discounts",
    description="Update discount for multiple products at once. Supplier owner or admin only.",
)
async def bulk_update_discounts(
    request: Request,
    bulk_data: ProductBulkPriceUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """
    Bulk update discount percentage for multiple products.

    Only supplier owner or users with "product:update" permission can update.

    Request Body:
    - product_ids: List of product IDs to update
    - discount_percentage: New discount percentage (0-100)

    Returns:
    - Success message with count of updated products

    Raises:
    - 403: Not authorized
    """
    # Verify user has permission or owns all products
    has_permission = current_user.has_permission("product:update")

    if not has_permission:
        # Check if user owns the suppliers of all products
        for product_id in bulk_data.product_ids:
            db_product = await product.get(session, id=product_id)
            if db_product:
                db_supplier = await supplier_crud.get(session, id=db_product.supplier_id)
                if db_supplier and db_supplier.owner_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to update all specified products",
                    )

    # Bulk update
    count = await product.bulk_update_discount(
        session,
        product_ids=bulk_data.product_ids,
        discount_percentage=bulk_data.discount_percentage,
        updated_by_id=current_user.id,
    )

    # Audit: Bulk update
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Bulk updated discount to {bulk_data.discount_percentage}% for {count} products",
        changes={
            "product_count": count,
            "discount_percentage": str(bulk_data.discount_percentage),
        },
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message=f"Successfully updated discount for {count} products")


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Delete product",
    description="Soft delete a product. Only supplier owner or admin can delete.",
)
async def delete_product(
    request: Request,
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """
    Soft delete a product.

    Only supplier owner or users with "product:delete" permission can delete.

    Path Parameters:
    - product_id: UUID of the product

    Returns:
    - Success message

    Raises:
    - 404: Product not found
    - 403: Not authorized
    """
    db_product = await product.get(session, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Get the supplier
    db_supplier = await supplier_crud.get(session, id=db_product.supplier_id)
    if not db_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check if user is supplier owner or has permission
    is_owner = db_supplier.owner_id == current_user.id
    has_permission = current_user.has_permission("product:delete")

    if not is_owner and not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this product",
        )

    # Soft delete
    await product.remove(session, id=product_id, deleted_by_id=current_user.id)

    # Audit: Product deletion
    await log_user_action(
        session=session,
        action=AuditAction.CUSTOM,
        actor_id=current_user.id,
        actor_email=current_user.email,
        details=f"Deleted product: {db_product.name_en} (SKU: {db_product.sku})",
        status=AuditStatus.SUCCESS,
        request=request,
    )

    return MessageResponse(message="Product deleted successfully")

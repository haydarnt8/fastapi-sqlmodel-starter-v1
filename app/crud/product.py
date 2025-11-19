"""
Product CRUD Operations

Handles all database operations for Product model including:
- Standard CRUD (create, read, update, delete)
- Advanced search with filters
- Stock management
- Bulk operations
- Low stock alerts
- Featured products
"""

from typing import List, Optional, Sequence
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    """CRUD operations for Product model."""

    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: ProductCreate,
        created_by_id: Optional[UUID] = None,
    ) -> Product:
        """
        Create a new product.

        Args:
            session: Database session
            obj_in: Product creation schema
            created_by_id: ID of user creating the product

        Returns:
            Created product instance
        """
        obj_in_data = obj_in.model_dump(exclude_unset=True)

        # Convert list fields to dict format for JSON storage
        if "tags" in obj_in_data and obj_in_data["tags"] is not None:
            obj_in_data["tags"] = {"tags": obj_in_data["tags"]}

        if "image_urls" in obj_in_data and obj_in_data["image_urls"] is not None:
            obj_in_data["image_urls"] = {"urls": obj_in_data["image_urls"]}

        if "search_keywords" in obj_in_data and obj_in_data["search_keywords"] is not None:
            obj_in_data["search_keywords"] = {"keywords": obj_in_data["search_keywords"]}

        # Set audit fields
        if created_by_id:
            obj_in_data["created_by_id"] = created_by_id
            obj_in_data["updated_by_id"] = created_by_id

        db_obj = Product(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: Product,
        obj_in: ProductUpdate,
        updated_by_id: Optional[UUID] = None,
    ) -> Product:
        """
        Update a product.

        Args:
            session: Database session
            db_obj: Existing product instance
            obj_in: Product update schema
            updated_by_id: ID of user updating the product

        Returns:
            Updated product instance
        """
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Convert list fields to dict format for JSON storage
        if "tags" in obj_data and obj_data["tags"] is not None:
            obj_data["tags"] = {"tags": obj_data["tags"]}

        if "image_urls" in obj_data and obj_data["image_urls"] is not None:
            obj_data["image_urls"] = {"urls": obj_data["image_urls"]}

        if "search_keywords" in obj_data and obj_data["search_keywords"] is not None:
            obj_data["search_keywords"] = {"keywords": obj_data["search_keywords"]}

        if updated_by_id:
            obj_data["updated_by_id"] = updated_by_id

        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_by_sku(
        self,
        session: AsyncSession,
        *,
        sku: str,
        supplier_id: Optional[UUID] = None,
    ) -> Optional[Product]:
        """
        Get product by SKU.

        Args:
            session: Database session
            sku: Stock Keeping Unit
            supplier_id: Optional supplier filter

        Returns:
            Product if found, None otherwise
        """
        statement = select(Product).where(
            and_(
                Product.sku == sku,
                Product.is_deleted == False,
            )
        )

        if supplier_id:
            statement = statement.where(Product.supplier_id == supplier_id)

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_barcode(
        self,
        session: AsyncSession,
        *,
        barcode: str,
    ) -> Optional[Product]:
        """
        Get product by barcode.

        Args:
            session: Database session
            barcode: Product barcode

        Returns:
            Product if found, None otherwise
        """
        statement = select(Product).where(
            and_(
                Product.barcode == barcode,
                Product.is_deleted == False,
            )
        )

        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_supplier(
        self,
        session: AsyncSession,
        *,
        supplier_id: UUID,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """
        Get all products for a supplier.

        Args:
            session: Database session
            supplier_id: Supplier ID
            active_only: Return only active products
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of products
        """
        statement = select(Product).where(
            and_(
                Product.supplier_id == supplier_id,
                Product.is_deleted == False,
            )
        )

        if active_only:
            statement = statement.where(Product.is_active == True)

        statement = statement.offset(skip).limit(limit).order_by(Product.created_at.desc())

        result = await session.execute(statement)
        return result.scalars().all()

    async def search(
        self,
        session: AsyncSession,
        *,
        query: Optional[str] = None,
        supplier_id: Optional[UUID] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        availability_status: Optional[str] = None,
        in_stock_only: bool = True,
        low_stock_only: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """
        Advanced product search with filters.

        Args:
            session: Database session
            query: Text search in name, SKU, description
            supplier_id: Filter by supplier
            category: Filter by category
            subcategory: Filter by subcategory
            min_price: Minimum price filter
            max_price: Maximum price filter
            is_active: Filter by active status
            is_featured: Filter featured products
            availability_status: Filter by availability
            in_stock_only: Show only in-stock products
            low_stock_only: Show only low-stock products
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of products matching filters
        """
        statement = select(Product).where(Product.is_deleted == False)

        # Text search
        if query:
            search_pattern = f"%{query}%"
            statement = statement.where(
                or_(
                    Product.name_ar.ilike(search_pattern),
                    Product.name_en.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                    Product.description_ar.ilike(search_pattern),
                    Product.description_en.ilike(search_pattern),
                )
            )

        # Supplier filter
        if supplier_id:
            statement = statement.where(Product.supplier_id == supplier_id)

        # Category filters
        if category:
            statement = statement.where(Product.category == category)

        if subcategory:
            statement = statement.where(Product.subcategory == subcategory)

        # Price range
        if min_price is not None:
            statement = statement.where(Product.unit_price >= min_price)

        if max_price is not None:
            statement = statement.where(Product.unit_price <= max_price)

        # Status filters
        if is_active is not None:
            statement = statement.where(Product.is_active == is_active)

        if is_featured is not None:
            statement = statement.where(Product.is_featured == is_featured)

        if availability_status:
            statement = statement.where(Product.availability_status == availability_status)

        # Stock filters
        if in_stock_only:
            statement = statement.where(
                and_(
                    Product.is_active == True,
                    Product.availability_status == "in_stock",
                    Product.stock_quantity > 0,
                )
            )

        if low_stock_only:
            statement = statement.where(Product.stock_quantity <= Product.reorder_level)

        # Sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        # Pagination
        statement = statement.offset(skip).limit(limit)

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_by_category(
        self,
        session: AsyncSession,
        *,
        category: str,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """
        Get products by category.

        Args:
            session: Database session
            category: Category name
            active_only: Return only active products
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of products in category
        """
        statement = select(Product).where(
            and_(
                Product.category == category,
                Product.is_deleted == False,
            )
        )

        if active_only:
            statement = statement.where(Product.is_active == True)

        statement = statement.offset(skip).limit(limit).order_by(Product.name_en)

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_featured(
        self,
        session: AsyncSession,
        *,
        supplier_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> Sequence[Product]:
        """
        Get featured products.

        Args:
            session: Database session
            supplier_id: Optional supplier filter
            limit: Maximum results

        Returns:
            List of featured products
        """
        statement = select(Product).where(
            and_(
                Product.is_featured == True,
                Product.is_active == True,
                Product.is_deleted == False,
            )
        )

        if supplier_id:
            statement = statement.where(Product.supplier_id == supplier_id)

        statement = statement.limit(limit).order_by(Product.created_at.desc())

        result = await session.execute(statement)
        return result.scalars().all()

    async def get_low_stock(
        self,
        session: AsyncSession,
        *,
        supplier_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """
        Get products with low stock (below reorder level).

        Args:
            session: Database session
            supplier_id: Optional supplier filter
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of low-stock products
        """
        statement = select(Product).where(
            and_(
                Product.stock_quantity <= Product.reorder_level,
                Product.is_deleted == False,
            )
        )

        if supplier_id:
            statement = statement.where(Product.supplier_id == supplier_id)

        statement = (
            statement.offset(skip)
            .limit(limit)
            .order_by(Product.stock_quantity.asc())
        )

        result = await session.execute(statement)
        return result.scalars().all()

    async def update_stock(
        self,
        session: AsyncSession,
        *,
        product_id: UUID,
        quantity: Decimal,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[Product]:
        """
        Update product stock quantity.

        Args:
            session: Database session
            product_id: Product ID
            quantity: New stock quantity
            updated_by_id: ID of user updating stock

        Returns:
            Updated product if found
        """
        product = await self.get(session, id=product_id)
        if not product:
            return None

        product.stock_quantity = quantity

        # Update availability status based on stock
        if quantity <= 0:
            product.availability_status = "out_of_stock"
        elif product.availability_status == "out_of_stock":
            product.availability_status = "in_stock"

        if updated_by_id:
            product.updated_by_id = updated_by_id

        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def adjust_stock(
        self,
        session: AsyncSession,
        *,
        product_id: UUID,
        quantity_change: Decimal,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[Product]:
        """
        Adjust product stock by adding/subtracting quantity.

        Args:
            session: Database session
            product_id: Product ID
            quantity_change: Amount to add (positive) or subtract (negative)
            updated_by_id: ID of user adjusting stock

        Returns:
            Updated product if found
        """
        product = await self.get(session, id=product_id)
        if not product:
            return None

        new_quantity = product.stock_quantity + quantity_change
        if new_quantity < 0:
            new_quantity = Decimal("0")

        return await self.update_stock(
            session,
            product_id=product_id,
            quantity=new_quantity,
            updated_by_id=updated_by_id,
        )

    async def toggle_active_status(
        self,
        session: AsyncSession,
        *,
        product_id: UUID,
        is_active: bool,
        updated_by_id: Optional[UUID] = None,
    ) -> Optional[Product]:
        """
        Toggle product active status.

        Args:
            session: Database session
            product_id: Product ID
            is_active: New active status
            updated_by_id: ID of user toggling status

        Returns:
            Updated product if found
        """
        product = await self.get(session, id=product_id)
        if not product:
            return None

        product.is_active = is_active

        if updated_by_id:
            product.updated_by_id = updated_by_id

        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def bulk_update_discount(
        self,
        session: AsyncSession,
        *,
        product_ids: List[UUID],
        discount_percentage: Decimal,
        updated_by_id: Optional[UUID] = None,
    ) -> int:
        """
        Bulk update discount for multiple products.

        Args:
            session: Database session
            product_ids: List of product IDs
            discount_percentage: New discount percentage
            updated_by_id: ID of user updating discounts

        Returns:
            Number of products updated
        """
        count = 0
        for product_id in product_ids:
            product = await self.get(session, id=product_id)
            if product:
                product.discount_percentage = discount_percentage
                if updated_by_id:
                    product.updated_by_id = updated_by_id
                session.add(product)
                count += 1

        await session.commit()
        return count

    async def get_count_by_supplier(
        self,
        session: AsyncSession,
        *,
        supplier_id: UUID,
        active_only: bool = True,
    ) -> int:
        """
        Get count of products for a supplier.

        Args:
            session: Database session
            supplier_id: Supplier ID
            active_only: Count only active products

        Returns:
            Product count
        """
        statement = select(func.count(Product.id)).where(
            and_(
                Product.supplier_id == supplier_id,
                Product.is_deleted == False,
            )
        )

        if active_only:
            statement = statement.where(Product.is_active == True)

        result = await session.execute(statement)
        return result.scalar_one()


# Create singleton instance
product = CRUDProduct(Product)

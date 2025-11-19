"""005_create_product_model

Revision ID: 7f9667deca63
Revises: 9ce5a211b285
Create Date: 2025-11-19 13:40:08.009101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9667deca63'
down_revision: Union[str, Sequence[str], None] = '9ce5a211b285'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create product table."""
    op.create_table(
        'product',
        # Primary Key
        sa.Column('id', sa.String(36), nullable=False),

        # Basic Information
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('barcode', sa.String(50), nullable=True),

        # Bilingual Information
        sa.Column('name_ar', sa.String(255), nullable=False),
        sa.Column('name_en', sa.String(255), nullable=False),
        sa.Column('description_ar', sa.String(2000), nullable=True),
        sa.Column('description_en', sa.String(2000), nullable=True),

        # Supplier Relationship
        sa.Column('supplier_id', sa.String(36), nullable=False),

        # Categorization
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),

        # Pricing
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='IQD'),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),

        # Inventory
        sa.Column('stock_quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('reorder_level', sa.Numeric(precision=10, scale=2), nullable=False, server_default='10.00'),
        sa.Column('unit_of_measure', sa.String(20), nullable=False),
        sa.Column('minimum_order_quantity', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1.00'),

        # Product Details
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('manufacturer', sa.String(200), nullable=True),
        sa.Column('origin_country', sa.String(100), nullable=True),
        sa.Column('shelf_life_days', sa.Integer(), nullable=True),
        sa.Column('storage_instructions', sa.String(500), nullable=True),

        # Media
        sa.Column('image_urls', sa.JSON(), nullable=True),
        sa.Column('primary_image_url', sa.String(500), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('availability_status', sa.String(50), nullable=False, server_default='in_stock'),

        # SEO & Search
        sa.Column('search_keywords', sa.JSON(), nullable=True),

        # Audit Fields (from BaseModel)
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(36), nullable=True),
        sa.Column('updated_by_id', sa.String(36), nullable=True),
        sa.Column('deleted_by_id', sa.String(36), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], name='fk_product_supplier_id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name='fk_product_created_by_id'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], name='fk_product_updated_by_id'),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id'], name='fk_product_deleted_by_id'),
    )

    # Create indexes for common queries
    op.create_index('ix_product_sku', 'product', ['sku'])
    op.create_index('ix_product_barcode', 'product', ['barcode'])
    op.create_index('ix_product_name_ar', 'product', ['name_ar'])
    op.create_index('ix_product_name_en', 'product', ['name_en'])
    op.create_index('ix_product_supplier_id', 'product', ['supplier_id'])
    op.create_index('ix_product_category', 'product', ['category'])
    op.create_index('ix_product_subcategory', 'product', ['subcategory'])
    op.create_index('ix_product_is_active', 'product', ['is_active'])
    op.create_index('ix_product_availability_status', 'product', ['availability_status'])

    # Composite indexes for common filter combinations
    op.create_index('ix_product_supplier_category', 'product', ['supplier_id', 'category'])
    op.create_index('ix_product_active_stock', 'product', ['is_active', 'availability_status'])


def downgrade() -> None:
    """Drop product table."""
    op.drop_index('ix_product_active_stock', table_name='product')
    op.drop_index('ix_product_supplier_category', table_name='product')
    op.drop_index('ix_product_availability_status', table_name='product')
    op.drop_index('ix_product_is_active', table_name='product')
    op.drop_index('ix_product_subcategory', table_name='product')
    op.drop_index('ix_product_category', table_name='product')
    op.drop_index('ix_product_supplier_id', table_name='product')
    op.drop_index('ix_product_name_en', table_name='product')
    op.drop_index('ix_product_name_ar', table_name='product')
    op.drop_index('ix_product_barcode', table_name='product')
    op.drop_index('ix_product_sku', table_name='product')
    op.drop_table('product')

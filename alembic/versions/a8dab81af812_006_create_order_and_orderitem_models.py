"""006_create_order_and_orderitem_models

Revision ID: a8dab81af812
Revises: 7f9667deca63
Create Date: 2025-11-19 13:43:04.818747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8dab81af812'
down_revision: Union[str, Sequence[str], None] = '7f9667deca63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create order and order_item tables."""

    # Create order table
    op.create_table(
        'order',
        # Primary Key
        sa.Column('id', sa.String(36), nullable=False),

        # Order Identification
        sa.Column('order_number', sa.String(50), nullable=False, unique=True),

        # Relationships
        sa.Column('restaurant_id', sa.String(36), nullable=False),
        sa.Column('supplier_id', sa.String(36), nullable=False),

        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),

        # Order Details
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.Column('internal_notes', sa.String(2000), nullable=True),
        sa.Column('special_instructions', sa.String(1000), nullable=True),

        # Financial Information
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('delivery_fee', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='IQD'),

        # Payment Information
        sa.Column('payment_status', sa.String(50), nullable=False, server_default='unpaid'),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('payment_due_date', sa.DateTime(), nullable=True),

        # Delivery Information
        sa.Column('delivery_address', sa.JSON(), nullable=True),
        sa.Column('delivery_date', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_notes', sa.String(1000), nullable=True),

        # Order Tracking Timestamps
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_by_id', sa.String(36), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.String(1000), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.String(1000), nullable=True),

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
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], name='fk_order_restaurant_id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], name='fk_order_supplier_id'),
        sa.ForeignKeyConstraint(['confirmed_by_id'], ['user.id'], name='fk_order_confirmed_by_id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name='fk_order_created_by_id'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], name='fk_order_updated_by_id'),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id'], name='fk_order_deleted_by_id'),
    )

    # Create indexes for order table
    op.create_index('ix_order_order_number', 'order', ['order_number'], unique=True)
    op.create_index('ix_order_restaurant_id', 'order', ['restaurant_id'])
    op.create_index('ix_order_supplier_id', 'order', ['supplier_id'])
    op.create_index('ix_order_status', 'order', ['status'])
    op.create_index('ix_order_payment_status', 'order', ['payment_status'])
    op.create_index('ix_order_delivery_date', 'order', ['delivery_date'])
    op.create_index('ix_order_submitted_at', 'order', ['submitted_at'])

    # Composite indexes for common queries
    op.create_index('ix_order_restaurant_status', 'order', ['restaurant_id', 'status'])
    op.create_index('ix_order_supplier_status', 'order', ['supplier_id', 'status'])
    op.create_index('ix_order_status_submitted', 'order', ['status', 'submitted_at'])
    op.create_index('ix_order_payment_status_due', 'order', ['payment_status', 'payment_due_date'])

    # Create order_item table
    op.create_table(
        'order_item',
        # Primary Key
        sa.Column('id', sa.String(36), nullable=False),

        # Foreign Keys
        sa.Column('order_id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),

        # Product Snapshot
        sa.Column('product_name_ar', sa.String(255), nullable=False),
        sa.Column('product_name_en', sa.String(255), nullable=False),
        sa.Column('product_sku', sa.String(100), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit_of_measure', sa.String(20), nullable=False),

        # Quantity and Pricing
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),

        # Item Details
        sa.Column('notes', sa.String(500), nullable=True),

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
        sa.ForeignKeyConstraint(['order_id'], ['order.id'], name='fk_orderitem_order_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], name='fk_orderitem_product_id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name='fk_orderitem_created_by_id'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], name='fk_orderitem_updated_by_id'),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id'], name='fk_orderitem_deleted_by_id'),
    )

    # Create indexes for order_item table
    op.create_index('ix_orderitem_order_id', 'order_item', ['order_id'])
    op.create_index('ix_orderitem_product_id', 'order_item', ['product_id'])

    # Composite index for common queries
    op.create_index('ix_orderitem_order_product', 'order_item', ['order_id', 'product_id'])


def downgrade() -> None:
    """Drop order and order_item tables."""

    # Drop order_item table
    op.drop_index('ix_orderitem_order_product', table_name='order_item')
    op.drop_index('ix_orderitem_product_id', table_name='order_item')
    op.drop_index('ix_orderitem_order_id', table_name='order_item')
    op.drop_table('order_item')

    # Drop order table
    op.drop_index('ix_order_payment_status_due', table_name='order')
    op.drop_index('ix_order_status_submitted', table_name='order')
    op.drop_index('ix_order_supplier_status', table_name='order')
    op.drop_index('ix_order_restaurant_status', table_name='order')
    op.drop_index('ix_order_submitted_at', table_name='order')
    op.drop_index('ix_order_delivery_date', table_name='order')
    op.drop_index('ix_order_payment_status', table_name='order')
    op.drop_index('ix_order_status', table_name='order')
    op.drop_index('ix_order_supplier_id', table_name='order')
    op.drop_index('ix_order_restaurant_id', table_name='order')
    op.drop_index('ix_order_order_number', table_name='order')
    op.drop_table('order')

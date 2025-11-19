"""003_create_supplier_model

Revision ID: 2d3e4dfb5e15
Revises: c76095baf297
Create Date: 2025-11-19 13:03:22.567454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d3e4dfb5e15'
down_revision: Union[str, Sequence[str], None] = 'c76095baf297'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create supplier table."""
    # Create supplier table
    op.create_table(
        'supplier',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_name_ar', sa.String(length=255), nullable=False),
        sa.Column('company_name_en', sa.String(length=255), nullable=False),
        sa.Column('trade_license', sa.String(length=100), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('description_ar', sa.String(length=1000), nullable=True),
        sa.Column('description_en', sa.String(length=1000), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_primary', sa.String(length=20), nullable=False),
        sa.Column('phone_secondary', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=False),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('product_categories', sa.JSON(), nullable=True),
        sa.Column('delivery_areas', sa.JSON(), nullable=True),
        sa.Column('minimum_order_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('delivery_fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('free_delivery_threshold', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('operating_hours', sa.JSON(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('verification_status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('verification_document_url', sa.String(length=500), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by_id', sa.String(length=36), nullable=True),
        sa.Column('accepts_cash', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('accepts_credit', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('allows_installments', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('payment_terms_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('average_rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('total_reviews', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_orders_completed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('auto_accept_orders', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('lead_time_hours', sa.Integer(), server_default='24', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),

        # Audit fields (from BaseModel)
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('updated_by_id', sa.String(length=36), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_id', sa.String(length=36), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['owner_id'], ['user.id']),
        sa.ForeignKeyConstraint(['verified_by_id'], ['user.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id']),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id']),
    )

    # Create indexes
    op.create_index(op.f('ix_supplier_city'), 'supplier', ['city'], unique=False)
    op.create_index(op.f('ix_supplier_email'), 'supplier', ['email'], unique=False)
    op.create_index(op.f('ix_supplier_is_verified'), 'supplier', ['is_verified'], unique=False)
    op.create_index(op.f('ix_supplier_is_active'), 'supplier', ['is_active'], unique=False)
    op.create_index(op.f('ix_supplier_owner_id'), 'supplier', ['owner_id'], unique=False)
    op.create_index(op.f('ix_supplier_is_deleted'), 'supplier', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_supplier_created_at'), 'supplier', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Drop supplier table."""
    # Drop indexes
    op.drop_index(op.f('ix_supplier_created_at'), table_name='supplier')
    op.drop_index(op.f('ix_supplier_is_deleted'), table_name='supplier')
    op.drop_index(op.f('ix_supplier_owner_id'), table_name='supplier')
    op.drop_index(op.f('ix_supplier_is_active'), table_name='supplier')
    op.drop_index(op.f('ix_supplier_is_verified'), table_name='supplier')
    op.drop_index(op.f('ix_supplier_email'), table_name='supplier')
    op.drop_index(op.f('ix_supplier_city'), table_name='supplier')

    # Drop table
    op.drop_table('supplier')

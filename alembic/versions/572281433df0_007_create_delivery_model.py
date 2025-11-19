"""007_create_delivery_model

Revision ID: 572281433df0
Revises: a8dab81af812
Create Date: 2025-11-19 14:05:07.474625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '572281433df0'
down_revision: Union[str, Sequence[str], None] = 'a8dab81af812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create delivery table."""
    # Create delivery table
    op.create_table(
        'delivery',
        # Primary key
        sa.Column('id', sa.String(length=36), nullable=False),

        # Relationships
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('driver_id', sa.String(length=36), nullable=True),

        # Status and Priority
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),

        # Pickup Location
        sa.Column('pickup_address', sa.String(length=500), nullable=False),
        sa.Column('pickup_city', sa.String(length=100), nullable=True),
        sa.Column('pickup_district', sa.String(length=100), nullable=True),
        sa.Column('pickup_latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('pickup_longitude', sa.Numeric(precision=11, scale=8), nullable=True),

        # Delivery Location
        sa.Column('delivery_address', sa.String(length=500), nullable=False),
        sa.Column('delivery_city', sa.String(length=100), nullable=True),
        sa.Column('delivery_district', sa.String(length=100), nullable=True),
        sa.Column('delivery_latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('delivery_longitude', sa.Numeric(precision=11, scale=8), nullable=True),

        # Distance and Fees
        sa.Column('estimated_distance_km', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('actual_distance_km', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('delivery_fee', sa.Numeric(precision=10, scale=2), nullable=False),

        # Real-time Tracking
        sa.Column('current_latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('current_longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('last_location_update', sa.DateTime(), nullable=True),
        sa.Column('location_history', sa.JSON(), nullable=True),

        # Workflow Timestamps
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('picked_up_at', sa.DateTime(), nullable=True),
        sa.Column('in_transit_at', sa.DateTime(), nullable=True),
        sa.Column('arrived_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),

        # Time Estimates
        sa.Column('estimated_pickup_time', sa.DateTime(), nullable=True),
        sa.Column('estimated_delivery_time', sa.DateTime(), nullable=True),

        # Proof of Delivery
        sa.Column('signature_url', sa.String(length=500), nullable=True),
        sa.Column('photo_urls', sa.JSON(), nullable=True),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=20), nullable=True),
        sa.Column('recipient_notes', sa.String(length=1000), nullable=True),

        # Failure/Cancellation
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('cancellation_reason', sa.String(length=500), nullable=True),

        # Notes and Instructions
        sa.Column('driver_notes', sa.String(length=1000), nullable=True),
        sa.Column('special_instructions', sa.String(length=1000), nullable=True),

        # Audit fields (from BaseModel)
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('updated_by_id', sa.String(length=36), nullable=True),
        sa.Column('deleted_by_id', sa.String(length=36), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['order_id'], ['order.id'], name='fk_delivery_order'),
        sa.ForeignKeyConstraint(['driver_id'], ['user.id'], name='fk_delivery_driver'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], name='fk_delivery_created_by'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['user.id'], name='fk_delivery_updated_by'),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['user.id'], name='fk_delivery_deleted_by'),
    )

    # Create indexes
    op.create_index('ix_delivery_order_id', 'delivery', ['order_id'])
    op.create_index('ix_delivery_driver_id', 'delivery', ['driver_id'])
    op.create_index('ix_delivery_status', 'delivery', ['status'])
    op.create_index('ix_delivery_priority', 'delivery', ['priority'])
    op.create_index('ix_delivery_delivery_city', 'delivery', ['delivery_city'])
    op.create_index('ix_delivery_assigned_at', 'delivery', ['assigned_at'])
    op.create_index('ix_delivery_delivered_at', 'delivery', ['delivered_at'])

    # Composite indexes for common query patterns
    op.create_index('ix_delivery_status_priority', 'delivery', ['status', 'priority'])
    op.create_index('ix_delivery_driver_status', 'delivery', ['driver_id', 'status'])
    op.create_index('ix_delivery_city_status', 'delivery', ['delivery_city', 'status'])


def downgrade() -> None:
    """Downgrade schema - Drop delivery table."""
    # Drop indexes
    op.drop_index('ix_delivery_city_status', table_name='delivery')
    op.drop_index('ix_delivery_driver_status', table_name='delivery')
    op.drop_index('ix_delivery_status_priority', table_name='delivery')
    op.drop_index('ix_delivery_delivered_at', table_name='delivery')
    op.drop_index('ix_delivery_assigned_at', table_name='delivery')
    op.drop_index('ix_delivery_delivery_city', table_name='delivery')
    op.drop_index('ix_delivery_priority', table_name='delivery')
    op.drop_index('ix_delivery_status', table_name='delivery')
    op.drop_index('ix_delivery_driver_id', table_name='delivery')
    op.drop_index('ix_delivery_order_id', table_name='delivery')

    # Drop table
    op.drop_table('delivery')

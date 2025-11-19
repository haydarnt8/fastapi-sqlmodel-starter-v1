"""002_create_restaurant_model

Revision ID: c76095baf297
Revises: 083f0b9370d7
Create Date: 2025-11-19 12:57:35.653385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c76095baf297'
down_revision: Union[str, Sequence[str], None] = '083f0b9370d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create restaurant table."""
    # Create restaurant table
    op.create_table(
        'restaurant',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name_ar', sa.String(length=255), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('business_registration', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_primary', sa.String(length=20), nullable=False),
        sa.Column('phone_secondary', sa.String(length=20), nullable=True),
        sa.Column('address_line1', sa.String(length=255), nullable=False),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('restaurant_type', sa.String(length=50), nullable=False),
        sa.Column('cuisine_type', sa.String(length=100), nullable=False),
        sa.Column('seating_capacity', sa.Integer(), nullable=True),
        sa.Column('operating_hours', sa.JSON(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('verification_status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('verification_document_url', sa.String(length=500), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by_id', sa.String(length=36), nullable=True),
        sa.Column('auto_accept_orders', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('preferred_payment_method', sa.String(length=50), server_default='cash', nullable=False),
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
    op.create_index(op.f('ix_restaurant_city'), 'restaurant', ['city'], unique=False)
    op.create_index(op.f('ix_restaurant_email'), 'restaurant', ['email'], unique=False)
    op.create_index(op.f('ix_restaurant_is_verified'), 'restaurant', ['is_verified'], unique=False)
    op.create_index(op.f('ix_restaurant_owner_id'), 'restaurant', ['owner_id'], unique=False)
    op.create_index(op.f('ix_restaurant_restaurant_type'), 'restaurant', ['restaurant_type'], unique=False)
    op.create_index(op.f('ix_restaurant_is_deleted'), 'restaurant', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_restaurant_created_at'), 'restaurant', ['created_at'], unique=False)

    # Note: Foreign key constraint from user.restaurant_id to restaurant.id
    # will be added when we uncomment the foreign_key in User model


def downgrade() -> None:
    """Downgrade schema - Drop restaurant table."""
    # Drop indexes
    op.drop_index(op.f('ix_restaurant_created_at'), table_name='restaurant')
    op.drop_index(op.f('ix_restaurant_is_deleted'), table_name='restaurant')
    op.drop_index(op.f('ix_restaurant_restaurant_type'), table_name='restaurant')
    op.drop_index(op.f('ix_restaurant_owner_id'), table_name='restaurant')
    op.drop_index(op.f('ix_restaurant_is_verified'), table_name='restaurant')
    op.drop_index(op.f('ix_restaurant_email'), table_name='restaurant')
    op.drop_index(op.f('ix_restaurant_city'), table_name='restaurant')

    # Drop table
    op.drop_table('restaurant')

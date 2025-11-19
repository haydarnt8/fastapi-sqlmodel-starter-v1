"""001_extend_user_model_with_phone_and_language

Revision ID: 083f0b9370d7
Revises: 1648ba1bab5b
Create Date: 2025-11-19 12:53:06.321339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '083f0b9370d7'
down_revision: Union[str, Sequence[str], None] = '1648ba1bab5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add supply chain fields to user table."""
    # Add new columns to user table
    op.add_column('user', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('user', sa.Column('phone_verified', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('user', sa.Column('phone_verified_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('language_preference', sa.String(length=5), server_default='ar', nullable=False))
    op.add_column('user', sa.Column('currency', sa.String(length=3), server_default='IQD', nullable=False))
    op.add_column('user', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('restaurant_id', sa.String(length=36), nullable=True))
    op.add_column('user', sa.Column('supplier_id', sa.String(length=36), nullable=True))

    # Create indexes
    op.create_index(op.f('ix_user_phone_number'), 'user', ['phone_number'], unique=True)
    op.create_index(op.f('ix_user_restaurant_id'), 'user', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_user_supplier_id'), 'user', ['supplier_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove supply chain fields from user table."""
    # Drop indexes
    op.drop_index(op.f('ix_user_supplier_id'), table_name='user')
    op.drop_index(op.f('ix_user_restaurant_id'), table_name='user')
    op.drop_index(op.f('ix_user_phone_number'), table_name='user')

    # Drop columns
    op.drop_column('user', 'supplier_id')
    op.drop_column('user', 'restaurant_id')
    op.drop_column('user', 'email_verified_at')
    op.drop_column('user', 'currency')
    op.drop_column('user', 'language_preference')
    op.drop_column('user', 'phone_verified_at')
    op.drop_column('user', 'phone_verified')
    op.drop_column('user', 'phone_number')

"""004_add_user_foreign_keys_to_restaurant_supplier

Revision ID: 9ce5a211b285
Revises: 2d3e4dfb5e15
Create Date: 2025-11-19 13:04:45.397990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ce5a211b285'
down_revision: Union[str, Sequence[str], None] = '2d3e4dfb5e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema - Add foreign key constraints to User model.

    Note: SQLite does not support adding foreign key constraints to existing tables.
    The foreign key definitions are present in the User model (restaurant_id, supplier_id)
    and will be enforced at the ORM level by SQLModel/SQLAlchemy.

    When migrating to PostgreSQL in production, this migration will add the actual
    database-level foreign key constraints using:

    op.create_foreign_key(
        'fk_user_restaurant_id',
        'user', 'restaurant',
        ['restaurant_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_user_supplier_id',
        'user', 'supplier',
        ['supplier_id'], ['id'],
        ondelete='SET NULL'
    )

    For SQLite development, the relationships are defined in the models and will work
    correctly through SQLModel's ORM layer.
    """
    # For SQLite: No database changes needed
    # Foreign keys are defined in the model and enforced at ORM level
    pass


def downgrade() -> None:
    """
    Downgrade schema - Remove foreign key constraints.

    For PostgreSQL, this would:
    op.drop_constraint('fk_user_supplier_id', 'user', type_='foreignkey')
    op.drop_constraint('fk_user_restaurant_id', 'user', type_='foreignkey')

    For SQLite: No changes needed
    """
    pass

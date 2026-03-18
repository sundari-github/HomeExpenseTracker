"""User: Delete Age. Add EmailAddress

Revision ID: c8c9cb903c6c
Revises: 
Create Date: 2026-03-07 15:34:54.752078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = 'c8c9cb903c6c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The context manager bundles everything into one atomic operation
    with op.batch_alter_table("User") as batch_op:
        batch_op.drop_column("Age")
        batch_op.add_column(sa.Column("EmailAddress", sa.String(), nullable=True))
        # batch_op.add_column(sa.Column("EmailAddress", sa.String(), nullable=False, server_default="test@email"))

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("User") as batch_op:
        batch_op.drop_column("EmailAddress")
        batch_op.add_column(sa.Column("Age", sa.Integer(), nullable=True))

"""add status and chunk_count

Revision ID: 004
Revises: 003
Create Date: 2026-05-31 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('documents', sa.Column('status', sa.String(length=50), nullable=True))
    op.add_column('documents', sa.Column('chunk_count', sa.Integer(), nullable=True))
    
    # Update existing rows to have default values
    op.execute("UPDATE documents SET status = 'processing' WHERE status IS NULL")
    op.execute("UPDATE documents SET chunk_count = 0 WHERE chunk_count IS NULL")
    
    # Alter columns to make them not nullable if they shouldn't be
    op.alter_column('documents', 'status', nullable=False)
    op.alter_column('documents', 'chunk_count', nullable=False)

def downgrade() -> None:
    op.drop_column('documents', 'chunk_count')
    op.drop_column('documents', 'status')

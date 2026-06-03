"""add diagram fields

Revision ID: 003
Revises: 002
Create Date: 2026-05-31 23:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('diagram_url', sa.String(length=1024), nullable=True))
    op.add_column('questions', sa.Column('diagram_type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('questions', 'diagram_type')
    op.drop_column('questions', 'diagram_url')

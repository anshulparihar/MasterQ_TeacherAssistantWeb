"""add missing columns

Revision ID: 006
Revises: 005
Create Date: 2026-06-01 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to documents
    op.add_column('documents', sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('documents', sa.Column('academic_level', sa.String(length=50), nullable=True))
    
    op.create_foreign_key(
        'fk_documents_subject_id_subjects',
        'documents', 'subjects',
        ['subject_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add columns to questions
    op.add_column('questions', sa.Column('explanation', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('hint', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('marks', sa.Float(), nullable=True))
    op.add_column('questions', sa.Column('is_recommendation', sa.Boolean(), server_default='false', nullable=False))
    
    # Alter topic_id to be nullable
    op.alter_column('questions', 'topic_id', existing_type=postgresql.UUID(as_uuid=True), nullable=True)

    # Create index on is_recommendation
    op.create_index(op.f('ix_questions_is_recommendation'), 'questions', ['is_recommendation'], unique=False)


def downgrade() -> None:
    # Downgrade questions
    op.drop_index(op.f('ix_questions_is_recommendation'), table_name='questions')
    
    op.alter_column('questions', 'topic_id', existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    
    op.drop_column('questions', 'is_recommendation')
    op.drop_column('questions', 'marks')
    op.drop_column('questions', 'hint')
    op.drop_column('questions', 'explanation')

    # Downgrade documents
    op.drop_constraint('fk_documents_subject_id_subjects', 'documents', type_='foreignkey')
    op.drop_column('documents', 'academic_level')
    op.drop_column('documents', 'subject_id')

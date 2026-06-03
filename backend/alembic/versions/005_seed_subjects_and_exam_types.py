"""seed subjects and exam types

Revision ID: 005_seed_subjects_and_exam_types
Revises: 004_add_status_and_chunk_count
Create Date: 2026-06-01 02:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import uuid

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create ad-hoc tables to use for the insert statement.
    subjects_table = table('subjects',
        column('id', sa.UUID(as_uuid=True)),
        column('name', sa.String())
    )

    exam_types_table = table('exam_types',
        column('id', sa.UUID(as_uuid=True)),
        column('name', sa.String()),
        column('guidelines', sa.JSON())
    )

    op.bulk_insert(subjects_table,
        [
            {'id': uuid.uuid4(), 'name': 'Physics'},
            {'id': uuid.uuid4(), 'name': 'Mathematics'},
            {'id': uuid.uuid4(), 'name': 'Biology'},
            {'id': uuid.uuid4(), 'name': 'Chemistry'},
            {'id': uuid.uuid4(), 'name': 'Computer Science'},
            {'id': uuid.uuid4(), 'name': 'History'}
        ]
    )

    op.bulk_insert(exam_types_table,
        [
            {'id': uuid.uuid4(), 'name': 'Mid-Term', 'guidelines': {'format': 'mixed', 'duration': '60m'}},
            {'id': uuid.uuid4(), 'name': 'Final Exam', 'guidelines': {'format': 'comprehensive', 'duration': '120m'}},
            {'id': uuid.uuid4(), 'name': 'Unit Test', 'guidelines': {'format': 'short', 'duration': '30m'}}
        ]
    )

def downgrade() -> None:
    op.execute("DELETE FROM subjects WHERE name IN ('Physics', 'Mathematics', 'Biology', 'Chemistry', 'Computer Science', 'History')")
    op.execute("DELETE FROM exam_types WHERE name IN ('Mid-Term', 'Final Exam', 'Unit Test')")

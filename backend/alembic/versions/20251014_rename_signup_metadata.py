"""rename signup metadata column

Revision ID: fd0cb6c4c33c
Revises: 
Create Date: 2025-10-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd0cb6c4c33c'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename column from metadata to signup_metadata
    op.alter_column('signups', 'metadata', new_column_name='signup_metadata')


def downgrade() -> None:
    # Rename column back from signup_metadata to metadata
    op.alter_column('signups', 'signup_metadata', new_column_name='metadata')

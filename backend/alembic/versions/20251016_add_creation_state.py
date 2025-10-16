"""add creation_state to projects

Revision ID: a8f9e3d2b1c5
Revises: fd0cb6c4c33c
Create Date: 2025-10-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a8f9e3d2b1c5'
down_revision = 'fd0cb6c4c33c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add creation_state column to projects table
    op.add_column('projects', sa.Column('creation_state', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove creation_state column from projects table
    op.drop_column('projects', 'creation_state')

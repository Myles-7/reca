"""Enable the PostgreSQL pgvector extension for the RECA foundation.

Revision ID: 0002_enable_pgvector_extension
Revises: 0001_reca_user_foundation
Create Date: 2026-07-29
"""

from alembic import op

revision = "0002_enable_pgvector_extension"
down_revision = "0001_reca_user_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # The extension may be shared by future migrations; leave it installed.
    pass

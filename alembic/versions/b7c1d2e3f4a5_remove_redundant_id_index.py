"""Remove redundant explicit index on the primary key.

Revision ID: b7c1d2e3f4a5
Revises: 4a2d9c7e1b6f
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b7c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "4a2d9c7e1b6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_urls_id", table_name="urls")


def downgrade() -> None:
    op.create_index("ix_urls_id", "urls", ["id"], unique=False)

"""Ensure each destination URL is stored only once.

Revision ID: 4a2d9c7e1b6f
Revises: 09289b5e4dca
"""
from typing import Sequence, Union

from alembic import op


revision: str = "4a2d9c7e1b6f"
down_revision: Union[str, Sequence[str], None] = "09289b5e4dca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_urls_long_url", "urls", ["long_url"])


def downgrade() -> None:
    op.drop_constraint("uq_urls_long_url", "urls", type_="unique")

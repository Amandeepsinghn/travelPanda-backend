"""add package inclusion and exclusion lines

Revision ID: c4d8f1a07b22
Revises: 6a9e86e3bcf9
Create Date: 2026-10-29 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d8f1a07b22"
down_revision: Union[str, Sequence[str], None] = "6a9e86e3bcf9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "package_terms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "kind IN ('inclusion', 'exclusion')",
            name="ck_package_terms_kind",
        ),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_package_terms_package_id"), "package_terms", ["package_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_package_terms_package_id"), table_name="package_terms")
    op.drop_table("package_terms")

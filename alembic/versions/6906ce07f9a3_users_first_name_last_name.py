"""users first_name last_name

Revision ID: 6906ce07f9a3
Revises: 8a9218b80be6
Create Date: 2026-10-04 12:35:15.407629

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6906ce07f9a3"
down_revision: Union[str, Sequence[str], None] = "8a9218b80be6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=120), nullable=True))

    op.execute(
        """
        UPDATE users
        SET
            first_name = COALESCE(NULLIF(split_part(full_name, ' ', 1), ''), full_name),
            last_name = COALESCE(
                NULLIF(trim(substring(full_name from position(' ' in full_name) + 1)), ''),
                ''
            )
        """
    )

    op.alter_column("users", "first_name", nullable=False)
    op.alter_column("users", "last_name", nullable=False)
    op.drop_column("users", "full_name")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("full_name", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )
    op.execute(
        """
        UPDATE users
        SET full_name = trim(both from concat_ws(' ', first_name, last_name))
        """
    )
    op.alter_column("users", "full_name", nullable=False)
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")

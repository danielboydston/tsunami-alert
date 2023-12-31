"""Status Categories and Statuses

Revision ID: 4634782fa9a3
Revises: 345edad6d6a7
Create Date: 2023-12-07 13:19:45.169512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '4634782fa9a3'
down_revision: Union[str, None] = '345edad6d6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

status_category_table = sa.sql.table(
    "statuscategory",
    sa.sql.column("id", sa.Integer),
    sa.sql.column("name", sa.String)
)

status_table = sa.sql.table(
    "status",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("category_id", sa.Integer)
)

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.bulk_insert(
        status_category_table,
        [
            {
                "id": 1,
                "name": "Active"
            },
            {
                "id": 2,
                "name": "Inactive"
            }
        ]
    )
    op.bulk_insert(
        status_table,
        [
            {
                "id": 1,
                "name": "Active",
                "category_id": 1
            },
            {
                "id": 2,
                "name": "Inactive",
                "category_id": 2
            }
        ]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

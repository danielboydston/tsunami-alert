"""Add bulletin discovery time

Revision ID: 345ccfa2cb7d
Revises: 54e22835e028
Create Date: 2023-12-07 11:49:21.771276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '345ccfa2cb7d'
down_revision: Union[str, None] = '54e22835e028'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

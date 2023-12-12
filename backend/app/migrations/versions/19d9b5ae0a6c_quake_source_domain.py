"""Quake Source Domain

Revision ID: 19d9b5ae0a6c
Revises: 6cec135daf8b
Create Date: 2023-12-09 15:16:15.911522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '19d9b5ae0a6c'
down_revision: Union[str, None] = '6cec135daf8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('earthquake', sa.Column('source_domain', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('earthquake', 'source_domain')
    # ### end Alembic commands ###
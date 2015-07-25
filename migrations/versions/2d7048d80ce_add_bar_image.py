"""Add bar image

Revision ID: 2d7048d80ce
Revises: a7a2780295
Create Date: 2015-07-25 16:29:59.095240

"""

# revision identifiers, used by Alembic.
revision = '2d7048d80ce'
down_revision = 'a7a2780295'

from alembic import op
import sqlalchemy_utils
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bars', sa.Column('image', sqlalchemy_utils.types.url.URLType(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bars', 'image')
    ### end Alembic commands ###
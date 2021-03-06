"""Add multimention table

Revision ID: 003
Revises: 002
Create Date: 2016-04-08 10:53:44.115348

"""

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('multimention',
    sa.Column('mmention_id', sa.Integer(), nullable=False),
    sa.Column('group_name', sa.String(), nullable=True),
    sa.Column('nick', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('mmention_id'),
    sa.UniqueConstraint('group_name', 'nick', name='_group_name_nick')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('multimention')
    ### end Alembic commands ###

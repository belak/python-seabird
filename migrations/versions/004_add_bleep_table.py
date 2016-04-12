"""Add bleep table

Revision ID: 004
Revises: 003
Create Date: 2016-04-12 07:22:49.777650

"""

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bleep',
    sa.Column('bad_word', sa.String(), nullable=False),
    sa.Column('replacement', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('bad_word')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('bleep')
    ### end Alembic commands ###

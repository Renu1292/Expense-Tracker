"""Add monthly_budget column to User

Revision ID: f7083af479b7
Revises: 
Create Date: 2025-05-16 08:12:28.145945

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7083af479b7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Expense_List')
    op.drop_table('users')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=150), nullable=False),
    sa.Column('email', sa.VARCHAR(length=150), nullable=False),
    sa.Column('password', sa.VARCHAR(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('Expense_List',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('date', sa.DATETIME(), nullable=True),
    sa.Column('title', sa.VARCHAR(length=200), nullable=False),
    sa.Column('amount', sa.FLOAT(), nullable=False),
    sa.Column('category', sa.VARCHAR(length=200), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###

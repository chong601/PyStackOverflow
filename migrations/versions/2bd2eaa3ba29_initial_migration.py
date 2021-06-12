"""Initial migration

Revision ID: 2bd2eaa3ba29
Revises: 
Create Date: 2021-06-10 12:07:12.629030

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2bd2eaa3ba29'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('stackoverflow_schema',
                    sa.Column('year', sa.Integer(), autoincrement=False, nullable=False,
                              comment='The year of the row the data represented'),
                    sa.Column('columns', sa.JSON(), nullable=False, comment='The columns represented by the year'),
                    sa.PrimaryKeyConstraint('year')
                    )
    op.create_table('stackoverflow_response',
                    sa.Column('response_id', sa.Integer(), nullable=False, comment='The anonymized ID of the response'),
                    sa.Column('year', sa.Integer(), nullable=False),
                    sa.Column('responses', sa.JSON(), nullable=False,
                              comment='The responses in JSON corresponding to the year of the data'),
                    sa.ForeignKeyConstraint(['year'], ['stackoverflow_schema.year'], ),
                    sa.PrimaryKeyConstraint('response_id')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('stackoverflow_response')
    op.drop_table('stackoverflow_schema')
    # ### end Alembic commands ###
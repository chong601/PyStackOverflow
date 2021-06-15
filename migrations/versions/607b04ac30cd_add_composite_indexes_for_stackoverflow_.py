"""Add composite indexes for stackoverflow_responses

Revision ID: 607b04ac30cd
Revises: 9f6b7e4e06c7
Create Date: 2021-06-15 21:02:35.286915

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '607b04ac30cd'
down_revision = '9f6b7e4e06c7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('idx_response_identifier', 'stackoverflow_response', ['response_id', 'respondent_id', 'response_year'], unique=False)
    op.create_index('idx_response_year_respondent', 'stackoverflow_response', ['respondent_id', 'response_year'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_response_year_respondent', table_name='stackoverflow_response')
    op.drop_index('idx_response_identifier', table_name='stackoverflow_response')
    # ### end Alembic commands ###

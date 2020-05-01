"""make ssn into text

Revision ID: c55f558a528e
Revises: 187b827bf5f3
Create Date: 2020-04-28 21:07:27.124968

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c55f558a528e"
down_revision = "187b827bf5f3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("employee", "tax_identifier_id")
    op.add_column("employee", sa.Column("tax_identifier", sa.Text()))
    op.drop_column("employer", "employer_fein")
    op.add_column("employer", sa.Column("employer_fein", sa.Text()))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("employee", "tax_identifier")
    op.add_column("employee", sa.Column("tax_identifier_id", postgresql.UUID(as_uuid=True)))
    op.drop_column("employer", "employer_fein")
    op.add_column("employer", sa.Column("employer_fein", postgresql.UUID(as_uuid=True)))
    # ### end Alembic commands ###

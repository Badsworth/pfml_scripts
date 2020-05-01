"""employee alter ytd qtr wages add contribution

Revision ID: 187b827bf5f3
Revises: 8d5f436b37e9
Create Date: 2020-04-28 16:44:51.844778

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "187b827bf5f3"
down_revision = "8d5f436b37e9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "wage_and_contribution_id",
        sa.Column("employee_fam_contribution", sa.Numeric(), nullable=False),
    )
    op.add_column(
        "wage_and_contribution_id",
        sa.Column("employee_med_contribution", sa.Numeric(), nullable=False),
    )
    op.add_column(
        "wage_and_contribution_id", sa.Column("employee_qtr_wages", sa.Numeric(), nullable=False)
    )
    op.add_column(
        "wage_and_contribution_id", sa.Column("employee_ytd_wages", sa.Numeric(), nullable=False)
    )
    op.drop_column("wage_and_contribution_id", "employer_ytd_wages")
    op.drop_column("wage_and_contribution_id", "employer_qtr_wages")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "wage_and_contribution_id",
        sa.Column("employer_qtr_wages", sa.NUMERIC(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "wage_and_contribution_id",
        sa.Column("employer_ytd_wages", sa.NUMERIC(), autoincrement=False, nullable=False),
    )
    op.drop_column("wage_and_contribution_id", "employee_ytd_wages")
    op.drop_column("wage_and_contribution_id", "employee_qtr_wages")
    op.drop_column("wage_and_contribution_id", "employee_med_contribution")
    op.drop_column("wage_and_contribution_id", "employee_fam_contribution")
    # ### end Alembic commands ###

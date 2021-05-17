"""PUB-195: Make FINEOS employer ID unique

Revision ID: 115d906a631f
Revises: e38c0a77a04b
Create Date: 2021-05-12 14:59:13.428406

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "115d906a631f"
down_revision = "e38c0a77a04b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_employer_fineos_employer_id", table_name="employer")
    op.create_index(
        op.f("ix_employer_fineos_employer_id"), "employer", ["fineos_employer_id"], unique=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_employer_fineos_employer_id"), table_name="employer")
    op.create_index(
        "ix_employer_fineos_employer_id", "employer", ["fineos_employer_id"], unique=False
    )
    # ### end Alembic commands ###

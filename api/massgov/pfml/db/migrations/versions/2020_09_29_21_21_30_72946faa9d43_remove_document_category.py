"""remove document category

Revision ID: 72946faa9d43
Revises: 2f571f16ffb6
Create Date: 2020-09-22 21:21:30.938016

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "72946faa9d43"
down_revision = "7115fde34652"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("document_document_category_id_fkey", "document", type_="foreignkey")
    op.drop_column("document", "document_category_id")
    op.drop_table("lk_document_category")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_document_category",
        sa.Column("document_category_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("document_category_description", sa.TEXT(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("document_category_id", name="lk_document_category_pkey"),
    )
    # nullable=True below, which is the opposite of initial state before column drop
    # would need some population script if we ever want to bring it back as required column
    op.add_column(
        "document",
        sa.Column("document_category_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "document_document_category_id_fkey",
        "document",
        "lk_document_category",
        ["document_category_id"],
        ["document_category_id"],
    )
    # ### end Alembic commands ###
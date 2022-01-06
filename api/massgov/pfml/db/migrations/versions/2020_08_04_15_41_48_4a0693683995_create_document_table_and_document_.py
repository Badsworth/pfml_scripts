"""create document table and document lookups

Revision ID: 4a0693683995
Revises: 1b9a5d22718b
Create Date: 2020-08-04 15:41:48.703667

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4a0693683995"
down_revision = "1b9a5d22718b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_content_type",
        sa.Column("content_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("content_type_description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("content_type_id"),
    )
    op.create_table(
        "lk_document_category",
        sa.Column("document_category_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_category_description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("document_category_id"),
    )
    op.create_table(
        "lk_document_type",
        sa.Column("document_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_type_description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("document_type_id"),
    )
    op.create_table(
        "document",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("document_category_id", sa.Integer(), nullable=False),
        sa.Column("document_type_id", sa.Integer(), nullable=False),
        sa.Column("content_type_id", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("fineos_id", sa.Text(), nullable=True),
        sa.Column("is_stored_in_s3", sa.Boolean(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["content_type_id"], ["lk_content_type.content_type_id"],),
        sa.ForeignKeyConstraint(
            ["document_category_id"], ["lk_document_category.document_category_id"],
        ),
        sa.ForeignKeyConstraint(["document_type_id"], ["lk_document_type.document_type_id"],),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"],),
        sa.PrimaryKeyConstraint("document_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("document")
    op.drop_table("lk_document_type")
    op.drop_table("lk_document_category")
    op.drop_table("lk_content_type")
    # ### end Alembic commands ###
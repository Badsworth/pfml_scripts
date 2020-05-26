"""Add relationship qualifier lookup and attribute

Revision ID: 045543f6292e
Revises: 918ba8aceb3b
Create Date: 2020-05-19 23:08:00.414189

"""

import csv
import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Integer, Text
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "045543f6292e"
down_revision = "918ba8aceb3b"
branch_labels = None
depends_on = None

tables = (
    "lk_frequency_or_duration",
    "lk_leave_reason",
    "lk_leave_reason_qualifier",
    "lk_leave_type",
    "lk_notification_method",
    "lk_relationship_qualifier",
    "lk_relationship_to_caregiver",
    "lk_occupation",
    "lk_payment_type",
    "lk_status",
)


lookup_table_to_data_map = {}
for table_name in tables:
    table_file = "../../seed/lookups/" + table_name + ".csv"
    file_path = os.path.join(os.path.dirname(__file__), table_file)

    with open(file_path, newline="") as csvfile:
        # read in the data
        reader = csv.DictReader(csvfile, delimiter=",")

        # get each row as an object into mapping table
        lookup_table_to_data_map[table_name] = []
        for row in reader:
            lookup_table_to_data_map[table_name].append(row)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_relationship_qualifier",
        sa.Column("relationship_qualifier", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("relationship_qualifier_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("relationship_qualifier"),
    )
    op.add_column("application", sa.Column("relationship_qualifier", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_relationship_qualifier",
        "application",
        "lk_relationship_qualifier",
        ["relationship_qualifier"],
        ["relationship_qualifier"],
    )
    # ### end Alembic commands ###
    for table_name in tables:
        # Truncate to refresh tables with existing rows.
        truncate_script = "delete from " + table_name
        op.execute(truncate_script)
        table_rows = lookup_table_to_data_map[table_name]
        table_column_names = list(table_rows[0].keys())
        table_handle = table(
            table_name, column(table_column_names[0], Integer), column(table_column_names[1], Text)
        )
        op.bulk_insert(table_handle, table_rows)


def downgrade():
    for table_name in tables:
        truncate_script = "delete from " + table_name
        op.execute(truncate_script)
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_relationship_qualifier", "application", type_="foreignkey")
    op.drop_column("application", "relationship_qualifier")
    op.drop_table("lk_relationship_qualifier")
    # ### end Alembic commands ###

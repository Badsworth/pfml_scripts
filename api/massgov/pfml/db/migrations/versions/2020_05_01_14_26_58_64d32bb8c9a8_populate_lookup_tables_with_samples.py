"""seed lookup tables
Revision ID: c55f558a528e
Revises: 88d2159c082c
Create Date: 2020-04-27 17:24:49.116239
"""

import csv

from alembic import op
from sqlalchemy import Integer, Text
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "64d32bb8c9a8"
down_revision = "c55f558a528e"
branch_labels = None
depends_on = None

tables = (
    "lk_address_type",
    "lk_claim_type",
    "lk_country",
    "lk_education_level",
    "lk_gender",
    "lk_geo_state",
    "lk_marital_status",
    "lk_occupation",
    "lk_payment_type",
    "lk_race",
    "lk_role",
    "lk_status",
)

lookup_table_to_data_map = {}
for table_name in tables:
    table_file = "massgov/pfml/db/seed/lookups/" + table_name + ".csv"
    with open(table_file, newline="") as csvfile:
        # read in the data
        reader = csv.DictReader(csvfile, delimiter=",")

        # get each row as an object into mapping table
        lookup_table_to_data_map[table_name] = []
        for row in reader:
            lookup_table_to_data_map[table_name].append(row)


def upgrade():
    for table_name in tables:
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

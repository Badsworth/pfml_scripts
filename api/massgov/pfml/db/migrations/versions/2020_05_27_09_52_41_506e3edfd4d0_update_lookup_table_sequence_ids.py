"""Update lookup table sequence ids

Revision ID: 506e3edfd4d0
Revises: 50c19eb439ae
Create Date: 2020-05-27 09:52:41.048553

"""
import csv
import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "506e3edfd4d0"
down_revision = "240cc1d6ea5e"
branch_labels = None
depends_on = None


# c55f558a528e
tables_05_01 = {
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
}

# 045543f6292e
tables_05_19 = {
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
}

tables = tables_05_01.union(tables_05_19)

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
    for table_name in tables:
        table_rows = lookup_table_to_data_map[table_name]
        table_column_names = list(table_rows[0].keys())
        key_column_name = table_column_names[0]
        op.execute(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', '{key_column_name}'), (SELECT MAX({key_column_name}) from {table_name}))"
        )


def downgrade():
    for table_name in tables:
        table_rows = lookup_table_to_data_map[table_name]
        table_column_names = list(table_rows[0].keys())
        key_column_name = table_column_names[0]
        op.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', '{key_column_name}'), 1)")

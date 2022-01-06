"""standardize lookup table names

Revision ID: 13e4d1158583
Revises: df90f87bb47d
Create Date: 2020-06-03 15:45:25.166292

"""
# import sqlalchemy as sa
from alembic import op

# from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "13e4d1158583"
down_revision = "df90f87bb47d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "lk_address_type", column_name="address_type", new_column_name="address_type_id"
    )
    op.alter_column("lk_geo_state", column_name="state_type", new_column_name="geo_state_id")
    op.alter_column(
        "lk_geo_state", column_name="state_description", new_column_name="geo_state_description"
    )
    op.alter_column("lk_country", column_name="country_type", new_column_name="country_id")
    op.alter_column("lk_claim_type", column_name="claim_type", new_column_name="claim_type_id")
    op.alter_column("lk_race", column_name="race_type", new_column_name="race_id")
    op.alter_column(
        "lk_marital_status", column_name="marital_status_type", new_column_name="marital_status_id"
    )
    op.alter_column("lk_gender", column_name="gender_type", new_column_name="gender_id")
    op.alter_column("lk_occupation", column_name="occupation_type", new_column_name="occupation_id")
    op.alter_column(
        "lk_education_level",
        column_name="education_level_type",
        new_column_name="education_level_id",
    )
    op.alter_column("lk_role", column_name="role_type", new_column_name="role_id")
    op.alter_column(
        "lk_payment_type", column_name="payment_type", new_column_name="payment_type_id"
    )
    op.alter_column("lk_status", column_name="status_type", new_column_name="status_id")
    op.alter_column(
        "payment_information", column_name="payment_type", new_column_name="payment_type_id"
    )
    op.alter_column("employee", column_name="race_type", new_column_name="race_id")
    op.alter_column(
        "employee", column_name="marital_status_type", new_column_name="marital_status_id"
    )
    op.alter_column("employee", column_name="gender_type", new_column_name="gender_id")
    op.alter_column("employee", column_name="occupation_type", new_column_name="occupation_id")
    op.alter_column(
        "employee", column_name="education_level_type", new_column_name="education_level_id"
    )
    op.alter_column("claim", column_name="claim_type", new_column_name="claim_type_id")
    op.alter_column("address", column_name="address_type", new_column_name="address_type_id")
    op.alter_column("address", column_name="country_type", new_column_name="country_id")
    op.alter_column("address", column_name="state_type", new_column_name="geo_state_id")
    op.alter_column("user", column_name="status_type", new_column_name="status_id")
    op.alter_column("link_user_role", column_name="role_type", new_column_name="role_id")
    op.alter_column(
        "lk_leave_reason", column_name="leave_reason", new_column_name="leave_reason_id"
    )
    op.alter_column(
        "lk_leave_reason",
        column_name="reason_description",
        new_column_name="leave_reason_description",
    )
    op.alter_column(
        "lk_leave_reason_qualifier",
        column_name="leave_reason_qualifier",
        new_column_name="leave_reason_qualifier_id",
    )
    op.alter_column(
        "lk_leave_reason_qualifier",
        column_name="reason_qualifier_description",
        new_column_name="leave_reason_qualifier_description",
    )
    op.alter_column("lk_leave_type", column_name="leave_type", new_column_name="leave_type_id")
    op.alter_column(
        "lk_relationship_to_caregiver",
        column_name="relationship",
        new_column_name="relationship_to_caregiver_id",
    )
    op.alter_column(
        "lk_relationship_to_caregiver",
        column_name="relationship_description",
        new_column_name="relationship_to_caregiver_description",
    )
    op.alter_column(
        "lk_relationship_qualifier",
        column_name="relationship_qualifier",
        new_column_name="relationship_qualifier_id",
    )
    op.alter_column(
        "lk_notification_method",
        column_name="notification_method",
        new_column_name="notification_method_id",
    )
    op.alter_column(
        "lk_frequency_or_duration",
        column_name="frequency_or_duration",
        new_column_name="frequency_or_duration_id",
    )
    op.alter_column(
        "lk_frequency_or_duration",
        column_name="frequency_duration_description",
        new_column_name="frequency_or_duration_description",
    )
    op.alter_column("application", column_name="occupation_type", new_column_name="occupation_id")
    op.alter_column("application", column_name="leave_type", new_column_name="leave_type_id")
    op.alter_column("application", column_name="leave_reason", new_column_name="leave_reason_id")
    op.alter_column(
        "application",
        column_name="leave_reason_qualifier",
        new_column_name="leave_reason_qualifier_id",
    )
    op.alter_column(
        "application",
        column_name="relationship_to_caregiver",
        new_column_name="relationship_to_caregiver_id",
    )
    op.alter_column(
        "application",
        column_name="relationship_qualifier",
        new_column_name="relationship_qualifier_id",
    )
    op.alter_column(
        "application",
        column_name="employer_notification_method",
        new_column_name="employer_notification_method_id",
    )
    op.alter_column("application", column_name="status", new_column_name="status_id")
    op.alter_column(
        "application_payment_preference",
        column_name="payment_type",
        new_column_name="payment_type_id",
    )
    op.alter_column("continuous_leave_period", column_name="status", new_column_name="status_id")
    op.alter_column(
        "reduced_schedule_leave_period", column_name="status", new_column_name="status_id"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "lk_address_type", column_name="address_type_id", new_column_name="address_type"
    )
    op.alter_column("lk_geo_state", column_name="geo_state_id", new_column_name="state_type")
    op.alter_column(
        "lk_geo_state", column_name="geo_state_description", new_column_name="state_description"
    )
    op.alter_column("lk_country", column_name="country_id", new_column_name="country_type")
    op.alter_column("lk_claim_type", column_name="claim_type_id", new_column_name="claim_type")
    op.alter_column("lk_race", column_name="race_id", new_column_name="race_type")
    op.alter_column(
        "lk_marital_status", column_name="marital_status_id", new_column_name="marital_status_type"
    )
    op.alter_column("lk_gender", column_name="gender_id", new_column_name="gender_type")
    op.alter_column("lk_occupation", column_name="occupation_id", new_column_name="occupation_type")
    op.alter_column(
        "lk_education_level",
        column_name="education_level_id",
        new_column_name="education_level_type",
    )
    op.alter_column("lk_role", column_name="role_id", new_column_name="role_type")
    op.alter_column(
        "lk_payment_type", column_name="payment_type_id", new_column_name="payment_type"
    )
    op.alter_column("lk_status", column_name="status_id", new_column_name="status_type")
    op.alter_column(
        "payment_information", column_name="payment_type_id", new_column_name="payment_type"
    )
    op.alter_column("employee", column_name="race_id", new_column_name="race_type")
    op.alter_column(
        "employee", column_name="marital_status_id", new_column_name="marital_status_type"
    )
    op.alter_column("employee", column_name="gender_id", new_column_name="gender_type")
    op.alter_column("employee", column_name="occupation_id", new_column_name="occupation_type")
    op.alter_column(
        "employee", column_name="education_level_id", new_column_name="education_level_type"
    )
    op.alter_column("claim", column_name="claim_type_id", new_column_name="claim_type")
    op.alter_column("address", column_name="address_type_id", new_column_name="address_type")
    op.alter_column("address", column_name="country_id", new_column_name="country_type")
    op.alter_column("address", column_name="geo_state_id", new_column_name="state_type")
    op.alter_column("user", column_name="status_id", new_column_name="status_type")
    op.alter_column("link_user_role", column_name="role_id", new_column_name="role_type")
    op.alter_column(
        "lk_leave_reason", column_name="leave_reason_id", new_column_name="leave_reason"
    )
    op.alter_column(
        "lk_leave_reason",
        column_name="leave_reason_description",
        new_column_name="reason_description",
    )
    op.alter_column(
        "lk_leave_reason_qualifier",
        column_name="leave_reason_qualifier_id",
        new_column_name="leave_reason_qualifier",
    )
    op.alter_column(
        "lk_leave_reason_qualifier",
        column_name="leave_reason_qualifier_description",
        new_column_name="reason_qualifier_description",
    )
    op.alter_column("lk_leave_type", column_name="leave_type_id", new_column_name="leave_type")
    op.alter_column(
        "lk_relationship_to_caregiver",
        column_name="relationship_to_caregiver_id",
        new_column_name="relationship",
    )
    op.alter_column(
        "lk_relationship_to_caregiver",
        column_name="relationship_to_caregiver_description",
        new_column_name="relationship_description",
    )
    op.alter_column(
        "lk_relationship_qualifier",
        column_name="relationship_qualifier_id",
        new_column_name="relationship_qualifier",
    )
    op.alter_column(
        "lk_notification_method",
        column_name="notification_method_id",
        new_column_name="notification_method",
    )
    op.alter_column(
        "lk_frequency_or_duration",
        column_name="frequency_or_duration_id",
        new_column_name="frequency_or_duration",
    )
    op.alter_column(
        "lk_frequency_or_duration",
        column_name="frequency_or_duration_description",
        new_column_name="frequency_duration_description",
    )
    op.alter_column("application", column_name="occupation_id", new_column_name="occupation_type")
    op.alter_column("application", column_name="leave_type_id", new_column_name="leave_type")
    op.alter_column("application", column_name="leave_reason_id", new_column_name="leave_reason")
    op.alter_column(
        "application",
        column_name="leave_reason_qualifier_id",
        new_column_name="leave_reason_qualifier",
    )
    op.alter_column(
        "application",
        column_name="relationship_to_caregiver_id",
        new_column_name="relationship_to_caregiver",
    )
    op.alter_column(
        "application",
        column_name="relationship_qualifier_id",
        new_column_name="relationship_qualifier",
    )
    op.alter_column(
        "application",
        column_name="employer_notification_method_id",
        new_column_name="employer_notification_method",
    )
    op.alter_column("application", column_name="status_id", new_column_name="status")
    op.alter_column(
        "application_payment_preference",
        column_name="payment_type_id",
        new_column_name="payment_type",
    )
    op.alter_column("continuous_leave_period", column_name="status_id", new_column_name="status")
    op.alter_column(
        "reduced_schedule_leave_period", column_name="status_id", new_column_name="status"
    )
    # ### end Alembic commands ###
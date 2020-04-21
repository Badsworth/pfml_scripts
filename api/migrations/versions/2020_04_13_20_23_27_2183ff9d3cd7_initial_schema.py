"""initial schema

Revision ID: 2183ff9d3cd7
Revises:
Create Date: 2020-04-13 20:23:27.279353

"""
import sqlalchemy as sa  # noqa: F401
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2183ff9d3cd7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "authorized_representative",
        sa.Column("authorized_representative_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("authorized_representative_id"),
    )
    op.create_table(
        "claim",
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("authorized_representative_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("claim_type", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("benefit_amount", sa.Numeric(), nullable=True),
        sa.Column("benefit_days", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("claim_id"),
    )
    op.create_table(
        "employer",
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_fein", sa.Integer(), nullable=True),
        sa.Column("employer_dba", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("employer_id"),
    )
    op.create_table(
        "health_care_provider",
        sa.Column("health_care_provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("health_care_provider_id"),
    )
    op.create_table(
        "lk_address_type",
        sa.Column("address_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("address_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("address_type"),
    )
    op.create_table(
        "lk_claim_type",
        sa.Column("claim_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("claim_type_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("claim_type"),
    )
    op.create_table(
        "lk_country",
        sa.Column("country_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("country_type"),
    )
    op.create_table(
        "lk_education_level",
        sa.Column("education_level_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("education_level_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("education_level_type"),
    )
    op.create_table(
        "lk_gender",
        sa.Column("gender_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("gender_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("gender_type"),
    )
    op.create_table(
        "lk_geo_state",
        sa.Column("state_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("state_type"),
    )
    op.create_table(
        "lk_marital_status",
        sa.Column("marital_status_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("marital_status_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("marital_status_type"),
    )
    op.create_table(
        "lk_occupation",
        sa.Column("occupation_type", sa.Integer(), nullable=False),
        sa.Column("occupation_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("occupation_type"),
    )
    op.create_table(
        "lk_payment_type",
        sa.Column("payment_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payment_type_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("payment_type"),
    )
    op.create_table(
        "lk_race",
        sa.Column("race_type", sa.Integer(), nullable=False),
        sa.Column("race_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("race_type"),
    )
    op.create_table(
        "lk_role",
        sa.Column("role_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("role_type"),
    )
    op.create_table(
        "lk_status",
        sa.Column("status_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status_description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("status_type"),
    )
    op.create_table(
        "wage_and_contribution_id",
        sa.Column("wage_and_contribution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_key", sa.String(), nullable=True),
        sa.Column("filing_period", sa.Date(), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_independent_contractor", sa.Boolean(), nullable=True),
        sa.Column("is_opted_in", sa.Boolean(), nullable=True),
        sa.Column("employer_ytd_wages", sa.Numeric(), nullable=False),
        sa.Column("employer_qtr_wages", sa.Numeric(), nullable=False),
        sa.Column("employer_med_contribution", sa.Numeric(), nullable=False),
        sa.Column("employer_fam_contribution", sa.Numeric(), nullable=False),
        sa.PrimaryKeyConstraint("wage_and_contribution_id"),
    )
    op.create_table(
        "address",
        sa.Column("address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_type", sa.Integer(), nullable=True),
        sa.Column("address_line_one", sa.String(), nullable=True),
        sa.Column("address_line_two", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("state_type", sa.Integer(), nullable=True),
        sa.Column("zip_code", sa.String(), nullable=True),
        sa.Column("country_type", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["address_type"], ["lk_address_type.address_type"],),
        sa.ForeignKeyConstraint(["country_type"], ["lk_country.country_type"],),
        sa.ForeignKeyConstraint(["state_type"], ["lk_geo_state.state_type"],),
        sa.PrimaryKeyConstraint("address_id"),
    )
    op.create_table(
        "payment_information",
        sa.Column("payment_info_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_type", sa.Integer(), nullable=True),
        sa.Column("bank_routing_nbr", sa.Integer(), nullable=True),
        sa.Column("bank_account_nbr", sa.Integer(), nullable=True),
        sa.Column("gift_card_nbr", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["payment_type"], ["lk_payment_type.payment_type"],),
        sa.PrimaryKeyConstraint("payment_info_id"),
    )
    op.create_table(
        "user",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("active_directory_id", sa.String(), nullable=True),
        sa.Column("status_type", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["status_type"], ["lk_status.status_type"],),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "employee",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tax_identifier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("middle_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("email_address", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("preferred_comm_method_type", sa.String(), nullable=True),
        sa.Column("payment_info_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("race_type", sa.Integer(), nullable=True),
        sa.Column("marital_status_type", sa.Integer(), nullable=True),
        sa.Column("gender_type", sa.Integer(), nullable=True),
        sa.Column("occupation_type", sa.Integer(), nullable=True),
        sa.Column("education_level_type", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["education_level_type"], ["lk_education_level.education_level_type"],
        ),
        sa.ForeignKeyConstraint(["gender_type"], ["lk_gender.gender_type"],),
        sa.ForeignKeyConstraint(
            ["marital_status_type"], ["lk_marital_status.marital_status_type"],
        ),
        sa.ForeignKeyConstraint(["occupation_type"], ["lk_occupation.occupation_type"],),
        sa.ForeignKeyConstraint(["payment_info_id"], ["payment_information.payment_info_id"],),
        sa.ForeignKeyConstraint(["race_type"], ["lk_race.race_type"],),
        sa.PrimaryKeyConstraint("employee_id"),
    )
    op.create_table(
        "link_employer_address",
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["address_id"], ["address.address_id"],),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.employer_id"],),
        sa.PrimaryKeyConstraint("employer_id", "address_id"),
    )
    op.create_table(
        "link_health_care_provider_address",
        sa.Column("health_care_provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["address_id"], ["address.address_id"],),
        sa.ForeignKeyConstraint(
            ["health_care_provider_id"], ["health_care_provider.health_care_provider_id"],
        ),
        sa.PrimaryKeyConstraint("health_care_provider_id", "address_id"),
    )
    op.create_table(
        "link_user_role",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_type", sa.Integer(), nullable=False),
        sa.Column("related_role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["role_type"], ["lk_role.role_type"],),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"],),
        sa.PrimaryKeyConstraint("user_id", "role_type"),
    )
    op.create_table(
        "link_authorized_rep_employee",
        sa.Column("authorized_representative_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["authorized_representative_id"],
            ["authorized_representative.authorized_representative_id"],
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"],),
        sa.PrimaryKeyConstraint("authorized_representative_id", "employee_id"),
    )
    op.create_table(
        "link_employee_address",
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["address_id"], ["address.address_id"],),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"],),
        sa.PrimaryKeyConstraint("employee_id", "address_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("link_employee_address")
    op.drop_table("link_authorized_rep_employee")
    op.drop_table("link_user_role")
    op.drop_table("link_health_care_provider_address")
    op.drop_table("link_employer_address")
    op.drop_table("employee")
    op.drop_table("user")
    op.drop_table("payment_information")
    op.drop_table("address")
    op.drop_table("wage_and_contribution_id")
    op.drop_table("lk_status")
    op.drop_table("lk_role")
    op.drop_table("lk_race")
    op.drop_table("lk_payment_type")
    op.drop_table("lk_occupation")
    op.drop_table("lk_marital_status")
    op.drop_table("lk_geo_state")
    op.drop_table("lk_gender")
    op.drop_table("lk_education_level")
    op.drop_table("lk_country")
    op.drop_table("lk_claim_type")
    op.drop_table("lk_address_type")
    op.drop_table("health_care_provider")
    op.drop_table("employer")
    op.drop_table("claim")
    op.drop_table("authorized_representative")
    # ### end Alembic commands ###

"""Adding Application data model

Revision ID: 918ba8aceb3b
Revises: 79e1405a1b3e
Create Date: 2020-05-13 20:53:16.282066

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "918ba8aceb3b"
down_revision = "721c1d788f1b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_frequency_or_duration",
        sa.Column("frequency_or_duration", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("frequency_duration_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("frequency_or_duration"),
    )
    op.create_table(
        "lk_leave_reason",
        sa.Column("leave_reason", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reason_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("leave_reason"),
    )
    op.create_table(
        "lk_leave_reason_qualifier",
        sa.Column("leave_reason_qualifier", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reason_qualifier_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("leave_reason_qualifier"),
    )
    op.create_table(
        "lk_leave_type",
        sa.Column("leave_type", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("leave_type_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("leave_type"),
    )
    op.create_table(
        "lk_notification_method",
        sa.Column("notification_method", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("notification_method_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("notification_method"),
    )
    op.create_table(
        "lk_relationship_to_caregiver",
        sa.Column("relationship", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("relationship_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("relationship"),
    )
    op.create_table(
        "application",
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nickname", sa.Text(), nullable=True),
        sa.Column("requestor", sa.Integer(), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("first_name", sa.Text(), nullable=True),
        sa.Column("last_name", sa.Text(), nullable=True),
        sa.Column("middle_initial", sa.Text(), nullable=True),
        sa.Column("occupation_type", sa.Integer(), nullable=True),
        sa.Column("relationship_to_caregiver", sa.Integer(), nullable=True),
        sa.Column("employer_notified", sa.Boolean(), nullable=True),
        sa.Column("employer_notification_date", sa.Date(), nullable=True),
        sa.Column("employer_notification_method", sa.Integer(), nullable=True),
        sa.Column("leave_type", sa.Integer(), nullable=True),
        sa.Column("leave_reason", sa.Integer(), nullable=True),
        sa.Column("leave_reason_qualifier", sa.Integer(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("updated_time", sa.DateTime(), nullable=True),
        sa.Column("completed_time", sa.DateTime(), nullable=True),
        sa.Column("submitted_time", sa.DateTime(), nullable=True),
        sa.Column("fineos_absence_id", sa.Text(), nullable=True),
        sa.Column("fineos_notification_case_id", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"],),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.employer_id"],),
        sa.ForeignKeyConstraint(
            ["employer_notification_method"], ["lk_notification_method.notification_method"],
        ),
        sa.ForeignKeyConstraint(["leave_reason"], ["lk_leave_reason.leave_reason"],),
        sa.ForeignKeyConstraint(
            ["leave_reason_qualifier"], ["lk_leave_reason_qualifier.leave_reason_qualifier"],
        ),
        sa.ForeignKeyConstraint(["leave_type"], ["lk_leave_type.leave_type"],),
        sa.ForeignKeyConstraint(["occupation_type"], ["lk_occupation.occupation_type"],),
        sa.ForeignKeyConstraint(
            ["relationship_to_caregiver"], ["lk_relationship_to_caregiver.relationship"],
        ),
        sa.ForeignKeyConstraint(["status"], ["lk_status.status_type"],),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"],),
        sa.PrimaryKeyConstraint("application_id"),
    )
    op.create_table(
        "wage_and_contribution_id",
        sa.Column("wage_and_contribution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_key", sa.Text(), nullable=True),
        sa.Column("filing_period", sa.Date(), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_independent_contractor", sa.Boolean(), nullable=True),
        sa.Column("is_opted_in", sa.Boolean(), nullable=True),
        sa.Column("employee_ytd_wages", sa.Numeric(), nullable=False),
        sa.Column("employee_qtr_wages", sa.Numeric(), nullable=False),
        sa.Column("employee_med_contribution", sa.Numeric(), nullable=False),
        sa.Column("employer_med_contribution", sa.Numeric(), nullable=False),
        sa.Column("employee_fam_contribution", sa.Numeric(), nullable=False),
        sa.Column("employer_fam_contribution", sa.Numeric(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"],),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.employer_id"],),
        sa.PrimaryKeyConstraint("wage_and_contribution_id"),
    )
    op.create_table(
        "application_payment_preference",
        sa.Column("payment_pref_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("payment_type", sa.Integer(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=True),
        sa.Column("account_name", sa.Text(), nullable=True),
        sa.Column("account_number", sa.Text(), nullable=True),
        sa.Column("routing_number", sa.Text(), nullable=True),
        sa.Column("type_of_account", sa.Text(), nullable=True),
        sa.Column("name_in_check", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"],),
        sa.ForeignKeyConstraint(["payment_type"], ["lk_payment_type.payment_type"],),
        sa.PrimaryKeyConstraint("payment_pref_id"),
    )
    op.create_table(
        "continuous_leave_period",
        sa.Column("leave_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=True),
        sa.Column("last_day_worked", sa.Date(), nullable=True),
        sa.Column("expected_return_to_work_date", sa.Date(), nullable=True),
        sa.Column("start_date_full_day", sa.Boolean(), nullable=True),
        sa.Column("start_date_off_hours", sa.Integer(), nullable=True),
        sa.Column("start_date_off_minutes", sa.Integer(), nullable=True),
        sa.Column("end_date_full_day", sa.Boolean(), nullable=True),
        sa.Column("end_date_off_hours", sa.Integer(), nullable=True),
        sa.Column("end_date_off_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"],),
        sa.ForeignKeyConstraint(["status"], ["lk_status.status_type"],),
        sa.PrimaryKeyConstraint("leave_period_id"),
    )
    op.create_table(
        "intermittent_leave_period",
        sa.Column("leave_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("frequency", sa.Integer(), nullable=True),
        sa.Column("frequency_interval", sa.Integer(), nullable=True),
        sa.Column("frequency_interval_basis", sa.Text(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("duration_basis", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"],),
        sa.PrimaryKeyConstraint("leave_period_id"),
    )
    op.create_table(
        "reduced_schedule_leave_period",
        sa.Column("leave_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=True),
        sa.Column("thursday_off_hours", sa.Integer(), nullable=True),
        sa.Column("thursday_off_minutes", sa.Integer(), nullable=True),
        sa.Column("friday_off_hours", sa.Integer(), nullable=True),
        sa.Column("friday_off_minutes", sa.Integer(), nullable=True),
        sa.Column("saturday_off_hours", sa.Integer(), nullable=True),
        sa.Column("saturday_off_minutes", sa.Integer(), nullable=True),
        sa.Column("sunday_off_hours", sa.Integer(), nullable=True),
        sa.Column("sunday_off_minutes", sa.Integer(), nullable=True),
        sa.Column("monday_off_hours", sa.Integer(), nullable=True),
        sa.Column("monday_off_minutes", sa.Integer(), nullable=True),
        sa.Column("tuesday_off_hours", sa.Integer(), nullable=True),
        sa.Column("tuesday_off_minutes", sa.Integer(), nullable=True),
        sa.Column("wednesday_off_hours", sa.Integer(), nullable=True),
        sa.Column("wednesday_off_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"],),
        sa.ForeignKeyConstraint(["status"], ["lk_status.status_type"],),
        sa.PrimaryKeyConstraint("leave_period_id"),
    )
    op.drop_table("wages_and_contributions")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "wages_and_contributions",
        sa.Column(
            "wage_and_contribution_id", postgresql.UUID(), autoincrement=False, nullable=False
        ),
        sa.Column("account_key", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("filing_period", sa.DATE(), autoincrement=False, nullable=True),
        sa.Column("employee_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.Column("employer_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.Column("is_independent_contractor", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("is_opted_in", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("employer_med_contribution", sa.NUMERIC(), autoincrement=False, nullable=False),
        sa.Column("employer_fam_contribution", sa.NUMERIC(), autoincrement=False, nullable=False),
        sa.Column("employee_fam_contribution", sa.NUMERIC(), autoincrement=False, nullable=False),
        sa.Column("employee_med_contribution", sa.NUMERIC(), autoincrement=False, nullable=False),
        sa.Column("employee_qtr_wages", sa.NUMERIC(), autoincrement=False, nullable=False),
        sa.Column("employee_ytd_wages", sa.NUMERIC(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.employee_id"],
            name="wage_and_contribution_id_employee_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["employer.employer_id"],
            name="wage_and_contribution_id_employer_id_fkey",
        ),
        sa.PrimaryKeyConstraint("wage_and_contribution_id", name="wage_and_contribution_id_pkey"),
    )
    op.drop_table("reduced_schedule_leave_period")
    op.drop_table("intermittent_leave_period")
    op.drop_table("continuous_leave_period")
    op.drop_table("application_payment_preference")
    op.drop_table("wage_and_contribution_id")
    op.drop_table("application")
    op.drop_table("lk_relationship_to_caregiver")
    op.drop_table("lk_notification_method")
    op.drop_table("lk_leave_type")
    op.drop_table("lk_leave_reason_qualifier")
    op.drop_table("lk_leave_reason")
    op.drop_table("lk_frequency_or_duration")
    # ### end Alembic commands ###

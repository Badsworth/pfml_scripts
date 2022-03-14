"""PUB-291: Add MMARS data staging tables

Revision ID: e60606ee01ba
Revises: 2341094462d0
Create Date: 2021-09-24 18:16:35.610058

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e60606ee01ba"
down_revision = "2341094462d0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "mmars_payment_data",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("mmars_payment_data_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("budget_fiscal_year", sa.Integer(), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("fiscal_period", sa.Integer(), nullable=True),
        sa.Column("pymt_doc_code", sa.Text(), nullable=True),
        sa.Column("pymt_doc_department_code", sa.Text(), nullable=True),
        sa.Column("pymt_doc_unit", sa.Text(), nullable=True),
        sa.Column("pymt_doc_identifier", sa.Text(), nullable=True),
        sa.Column("pymt_doc_version_no", sa.Text(), nullable=True),
        sa.Column("pymt_doc_vendor_line_no", sa.Text(), nullable=True),
        sa.Column("pymt_doc_comm_line_no", sa.Text(), nullable=True),
        sa.Column("pymt_doc_actg_line_no", sa.Text(), nullable=True),
        sa.Column("pymt_actg_line_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_discount_line_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_penalty_line_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_interest_line_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_backup_withholding_line_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_intercept_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_retainage_line_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_freight_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_default_intercept_fee_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_supplementary_intercept_fee_amount", sa.Numeric(), nullable=True),
        sa.Column("pymt_service_from_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("pymt_service_to_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("encumbrance_doc_code", sa.Text(), nullable=True),
        sa.Column("encumbrance_doc_dept", sa.Text(), nullable=True),
        sa.Column("encumbrance_doc_identifier", sa.Text(), nullable=True),
        sa.Column("encumbrance_vendor_line_no", sa.Text(), nullable=True),
        sa.Column("encumbrance_commodity_line_no", sa.Text(), nullable=True),
        sa.Column("encumbrance_accounting_line_no", sa.Text(), nullable=True),
        sa.Column("disb_doc_code", sa.Text(), nullable=True),
        sa.Column("disb_doc_department_code", sa.Text(), nullable=True),
        sa.Column("disb_doc_identifier", sa.Text(), nullable=True),
        sa.Column("disb_doc_version_no", sa.Text(), nullable=True),
        sa.Column("disb_vendor_line_no", sa.Text(), nullable=True),
        sa.Column("disb_commodity_line_no", sa.Text(), nullable=True),
        sa.Column("disb_actg_line_no", sa.Text(), nullable=True),
        sa.Column("disb_actg_line_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_check_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_discount_line_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_penalty_line_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_interest_line_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_backup_withholding_line_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_intercept_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_retainage_line_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_freight_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_default_intercept_fee_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_supplementary_intercept_fee_amount", sa.Numeric(), nullable=True),
        sa.Column("disb_doc_phase_code", sa.Text(), nullable=True),
        sa.Column("disb_doc_function_code", sa.Text(), nullable=True),
        sa.Column("actg_line_descr", sa.Text(), nullable=True),
        sa.Column("check_descr", sa.Text(), nullable=True),
        sa.Column("warrant_no", sa.Text(), nullable=True),
        sa.Column("warrant_select_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("check_eft_issue_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("bank_account_code", sa.Text(), nullable=True),
        sa.Column("check_eft_no", sa.Text(), nullable=True),
        sa.Column("cleared_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("appropriation", sa.Text(), nullable=True),
        sa.Column("appropriation_name", sa.Text(), nullable=True),
        sa.Column("object_class", sa.Text(), nullable=True),
        sa.Column("object_class_name", sa.Text(), nullable=True),
        sa.Column("object", sa.Text(), nullable=True),
        sa.Column("object_name", sa.Text(), nullable=True),
        sa.Column("income_type", sa.Text(), nullable=True),
        sa.Column("income_type_name", sa.Text(), nullable=True),
        sa.Column("form_type_indicator", sa.Text(), nullable=True),
        sa.Column("form_typ_ind_descr", sa.Text(), nullable=True),
        sa.Column("disbursement_frequency", sa.Text(), nullable=True),
        sa.Column("disbursement_frequency_name", sa.Text(), nullable=True),
        sa.Column("payment_lag", sa.Text(), nullable=True),
        sa.Column("fund", sa.Text(), nullable=True),
        sa.Column("fund_name", sa.Text(), nullable=True),
        sa.Column("fund_category", sa.Text(), nullable=True),
        sa.Column("fund_category_name", sa.Text(), nullable=True),
        sa.Column("major_program", sa.Text(), nullable=True),
        sa.Column("major_program_name", sa.Text(), nullable=True),
        sa.Column("program", sa.Text(), nullable=True),
        sa.Column("program_name", sa.Text(), nullable=True),
        sa.Column("phase", sa.Text(), nullable=True),
        sa.Column("phase_name", sa.Text(), nullable=True),
        sa.Column("activity", sa.Text(), nullable=True),
        sa.Column("activity_name", sa.Text(), nullable=True),
        sa.Column("function", sa.Text(), nullable=True),
        sa.Column("function_name", sa.Text(), nullable=True),
        sa.Column("reporting", sa.Text(), nullable=True),
        sa.Column("reporting_name", sa.Text(), nullable=True),
        sa.Column("vendor_customer_code", sa.Text(), nullable=True),
        sa.Column("legal_name", sa.Text(), nullable=True),
        sa.Column("address_id", sa.Text(), nullable=True),
        sa.Column("address_type", sa.Text(), nullable=True),
        sa.Column("address_line_1", sa.Text(), nullable=True),
        sa.Column("address_line_2", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("zip_code", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("vendor_invoice_no", sa.Text(), nullable=True),
        sa.Column("vendor_invoice_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("scheduled_payment_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("doc_function_code", sa.Text(), nullable=True),
        sa.Column("doc_function_code_name", sa.Text(), nullable=True),
        sa.Column("doc_phase_code", sa.Text(), nullable=True),
        sa.Column("doc_phase_name", sa.Text(), nullable=True),
        sa.Column("government_branch", sa.Text(), nullable=True),
        sa.Column("government_branch_name", sa.Text(), nullable=True),
        sa.Column("cabinet", sa.Text(), nullable=True),
        sa.Column("cabinet_name", sa.Text(), nullable=True),
        sa.Column("department", sa.Text(), nullable=True),
        sa.Column("department_name", sa.Text(), nullable=True),
        sa.Column("division", sa.Text(), nullable=True),
        sa.Column("division_name", sa.Text(), nullable=True),
        sa.Column("Group", sa.Text(), nullable=True),
        sa.Column("group_name", sa.Text(), nullable=True),
        sa.Column("Section", sa.Text(), nullable=True),
        sa.Column("section_name", sa.Text(), nullable=True),
        sa.Column("district", sa.Text(), nullable=True),
        sa.Column("district_name", sa.Text(), nullable=True),
        sa.Column("bureau", sa.Text(), nullable=True),
        sa.Column("bureau_name", sa.Text(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("unit_name", sa.Text(), nullable=True),
        sa.Column("sub_unit", sa.Text(), nullable=True),
        sa.Column("sub_unit_name", sa.Text(), nullable=True),
        sa.Column("doc_record_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("acceptance_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("doc_created_by", sa.Text(), nullable=True),
        sa.Column("doc_created_on", sa.TIMESTAMP(), nullable=True),
        sa.Column("doc_last_modified_by", sa.Text(), nullable=True),
        sa.Column("doc_last_modified_on", sa.TIMESTAMP(), nullable=True),
        sa.Column("NoFilter", sa.Text(), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.payment_id"]),
        sa.PrimaryKeyConstraint("mmars_payment_data_id"),
    )
    op.create_index(
        op.f("ix_mmars_payment_data_payment_id"), "mmars_payment_data", ["payment_id"], unique=False
    )
    op.create_table(
        "mmars_payment_refunds",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("mmars_payment_refunds_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legal_name", sa.Text(), nullable=True),
        sa.Column("vendor_customer_code", sa.Text(), nullable=True),
        sa.Column("activity", sa.Text(), nullable=True),
        sa.Column("activity_class", sa.Text(), nullable=True),
        sa.Column("activity_class_name", sa.Text(), nullable=True),
        sa.Column("activity_name", sa.Text(), nullable=True),
        sa.Column("appropriation", sa.Text(), nullable=True),
        sa.Column("appropriation_name", sa.Text(), nullable=True),
        sa.Column("program", sa.Text(), nullable=True),
        sa.Column("program_name", sa.Text(), nullable=True),
        sa.Column("check_eft_no", sa.Text(), nullable=True),
        sa.Column("acceptance_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("doc_record_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("posting_amount", sa.Numeric(), nullable=True),
        sa.Column("debit_credit_ind", sa.Text(), nullable=True),
        sa.Column("event_category", sa.Text(), nullable=True),
        sa.Column("event_category_name", sa.Text(), nullable=True),
        sa.Column("fund", sa.Text(), nullable=True),
        sa.Column("fund_name", sa.Text(), nullable=True),
        sa.Column("object", sa.Text(), nullable=True),
        sa.Column("object_name", sa.Text(), nullable=True),
        sa.Column("phase", sa.Text(), nullable=True),
        sa.Column("phase_name", sa.Text(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("unit_name", sa.Text(), nullable=True),
        sa.Column("doc_code", sa.Text(), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("closing_classification_code", sa.Text(), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.payment_id"]),
        sa.PrimaryKeyConstraint("mmars_payment_refunds_id"),
    )
    op.create_index(
        op.f("ix_mmars_payment_refunds_payment_id"),
        "mmars_payment_refunds",
        ["payment_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "employer", type_="foreignkey")  # type: ignore
    op.drop_index(op.f("ix_mmars_payment_refunds_payment_id"), table_name="mmars_payment_refunds")
    op.drop_table("mmars_payment_refunds")
    op.drop_index(op.f("ix_mmars_payment_data_payment_id"), table_name="mmars_payment_data")
    op.drop_table("mmars_payment_data")
    # ### end Alembic commands ###

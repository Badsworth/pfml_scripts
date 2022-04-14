import os

import pytest

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import State
from massgov.pfml.db.models.payments import (
    ACTIVE_WRITEBACK_RECORD_STATUS,
    AUDIT_REJECT_DETAIL_GROUPS,
    AUDIT_SKIPPED_DETAIL_GROUPS,
    PENDING_ACTIVE_WRITEBACK_RECORD_STATUS,
    AuditReportAction,
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    PaymentAuditReportType,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditDetails,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditReportStep,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_rejects import PaymentRejectsStep
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


"""
These tests aim to verify that everything required
for setting up audit reports is configured and working.
If anything isn't configured correctly, it tries to
help guide the developer to what they need to correct.
"""


@pytest.fixture
def payment_audit_report_step(initialize_factories_session, test_db_session):
    return PaymentAuditReportStep(db_session=test_db_session, log_entry_db_session=test_db_session)


@pytest.fixture
def payment_rejects_step(initialize_factories_session, test_db_session):
    return PaymentRejectsStep(db_session=test_db_session, log_entry_db_session=test_db_session)


def test_audit_report_types_configured():
    audit_report_types_to_validate = []
    for audit_report_type in PaymentAuditReportType.get_all():
        if "deprecated" not in audit_report_type.payment_audit_report_type_description.lower():
            audit_report_types_to_validate.append(audit_report_type)

    assert len(audit_report_types_to_validate) > 0

    # Figure out which audit report types are configured
    configured_audit_report_types = set()
    for audit_detail_group in AUDIT_REJECT_DETAIL_GROUPS + AUDIT_SKIPPED_DETAIL_GROUPS:
        if audit_detail_group.audit_report_type:
            configured_audit_report_types.add(
                audit_detail_group.audit_report_type.payment_audit_report_type_id
            )

    for audit_report_type in audit_report_types_to_validate:
        assert (
            audit_report_type.payment_audit_report_type_id in configured_audit_report_types
        ), f"Please add {audit_report_type.payment_audit_report_type_description} to the appropriate Audit Detail Group list in the payments.py file"


def test_audit_detail_groups():
    # Sanity test to validate that only Active writeback
    # status records are in the reject list and PendingActive (blank)
    # status records are in the skippped list.
    for audit_reject_detail_group in AUDIT_REJECT_DETAIL_GROUPS:
        assert (
            audit_reject_detail_group.writeback_transaction_status.writeback_record_status
            == ACTIVE_WRITEBACK_RECORD_STATUS
        )

    for audit_skipped_detail_group in AUDIT_SKIPPED_DETAIL_GROUPS:
        assert (
            audit_skipped_detail_group.writeback_transaction_status.writeback_record_status
            == PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
        )


def test_audit_report_type_column():
    # Sanity test that columns exist in the audit report.
    # This would likely fail elsewhere, but be clearer here.
    missing_columns = set()
    for audit_report_type in PaymentAuditReportType.get_all():
        if audit_report_type.payment_audit_report_column:
            if not hasattr(
                PAYMENT_AUDIT_CSV_HEADERS, audit_report_type.payment_audit_report_column
            ):
                missing_columns.add(audit_report_type.payment_audit_report_column)

            if not hasattr(PaymentAuditDetails, audit_report_type.payment_audit_report_column):
                missing_columns.add(audit_report_type.payment_audit_report_column)

    # If you are seeing this fail, please make sure to add
    # the columns to the delegated_payment_audit_csv definitions
    assert (
        len(missing_columns) == 0
    ), f"The following payment audit report types do not have configured columns for the audit report: {missing_columns}"


# Utility to run the steps for the given scenario
def run_steps(payment_audit_report_step, payment_rejects_step):
    payment_audit_report_step.run()

    s3_config = payments_config.get_s3_config()
    file_name = f"{payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT}.csv"
    audit_file_path = os.path.join(s3_config.dfml_report_outbound_path, file_name)
    audit_reject_file_path = os.path.join(
        s3_config.pfml_payment_rejects_archive_path,
        payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
        file_name,
    )
    file_util.copy_file(audit_file_path, audit_reject_file_path)

    payment_rejects_step.run()


def test_writeback_scenarios_for_audit_details(
    test_db_session, payment_audit_report_step, payment_rejects_step
):
    audit_detail_payment_pairs = []
    for audit_detail_group in AUDIT_REJECT_DETAIL_GROUPS + AUDIT_SKIPPED_DETAIL_GROUPS:
        if audit_detail_group.audit_report_type:
            payment = DelegatedPaymentFactory(test_db_session).get_or_create_payment_with_state(
                State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
            )

            stage_payment_audit_report_details(
                payment,
                audit_detail_group.audit_report_type,
                "Example message",
                None,
                test_db_session,
            )
            audit_detail_payment_pairs.append((audit_detail_group, payment))

    run_steps(payment_audit_report_step, payment_rejects_step)

    for audit_detail_group, payment in audit_detail_payment_pairs:
        latest_writeback_detail = (
            test_db_session.query(FineosWritebackDetails)
            .filter(FineosWritebackDetails.payment_id == payment.payment_id)
            .order_by(FineosWritebackDetails.created_at.desc())
            .first()
        )

        assert latest_writeback_detail

        # If just informational, then no default reject/skip so
        # it stays as it was with the status we added before sending the audit report
        audit_report_action = audit_detail_group.audit_report_type.payment_audit_report_action
        if audit_report_action == AuditReportAction.INFORMATIONAL:
            expected_writeback = FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS

        else:
            expected_writeback = audit_detail_group.writeback_transaction_status

        assert (
            latest_writeback_detail.transaction_status_id
            == expected_writeback.transaction_status_id
        ), f"Unexpected writeback for {audit_detail_group.audit_report_type.payment_audit_report_type_description}"

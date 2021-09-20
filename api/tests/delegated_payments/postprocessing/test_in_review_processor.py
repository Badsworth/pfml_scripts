import pytest

from massgov.pfml.db.models.factories import PaymentFactory
from massgov.pfml.db.models.payments import PaymentAuditReportDetails, PaymentAuditReportType
from massgov.pfml.delegated_payments.postprocessing.in_review_processor import InReviewProcessor
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
)


@pytest.fixture
def payment_post_processing_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return PaymentPostProcessingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


@pytest.fixture
def in_review_processor(payment_post_processing_step):
    return InReviewProcessor(payment_post_processing_step)


def test_process(in_review_processor, local_test_db_session):
    in_review_payment = PaymentFactory.create(leave_request_decision="In Review")
    in_review_processor.process(PaymentContainer(in_review_payment))

    approved_payment = PaymentFactory.create(leave_request_decision="Approved")
    in_review_processor.process(PaymentContainer(approved_payment))

    # Shouldn't happen due due to upstream validation
    # in the payment extract, but checking just in case
    unknown_payment = PaymentFactory.create(leave_request_decision=None)
    in_review_processor.process(PaymentContainer(unknown_payment))

    audit_report_details = local_test_db_session.query(PaymentAuditReportDetails).all()
    assert len(audit_report_details) == 1
    assert audit_report_details[0].payment_id == in_review_payment.payment_id
    assert (
        audit_report_details[0].audit_report_type_id
        == PaymentAuditReportType.LEAVE_PLAN_IN_REVIEW.payment_audit_report_type_id
    )

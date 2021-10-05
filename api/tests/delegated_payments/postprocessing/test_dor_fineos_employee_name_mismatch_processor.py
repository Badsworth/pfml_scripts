import pytest

from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory, PaymentFactory
from massgov.pfml.db.models.payments import PaymentAuditReportDetails
from massgov.pfml.delegated_payments.postprocessing.dor_fineos_employee_name_mismatch_processor import (
    DORFineosEmployeeNameMismatchProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)


@pytest.fixture
def payment_post_processing_step(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    return PaymentPostProcessingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


@pytest.fixture
def dor_fineos_employee_name_mismatch_processor(payment_post_processing_step):
    return DORFineosEmployeeNameMismatchProcessor(payment_post_processing_step)


# TODO use delegate payments factory PUB-277
def create_payment_with_name(dor_first_name, dor_last_name, fineos_first_name, fineos_last_name):
    employee = EmployeeFactory.create(first_name=dor_first_name, last_name=dor_last_name)
    claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim,
        fineos_employee_first_name=fineos_first_name,
        fineos_employee_last_name=fineos_last_name,
    )
    return payment


def test_processor_mixed(
    dor_fineos_employee_name_mismatch_processor,
    local_test_db_session,
    local_initialize_factories_session,
):
    # Exact or close matches
    payment = create_payment_with_name("Javier", "Valdez", "Javier", "Valdez")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, local_test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez", "Javier", "Valdez Jr.")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, local_test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez-Garcia", "Javier", "Valdez Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, local_test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, local_test_db_session) is None

    payment = create_payment_with_name("javier", "valdez garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, local_test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, local_test_db_session) is None

    # Mismatches
    payment_1 = create_payment_with_name("Sam", "Valdez-Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment_1)
    audit_report = _get_audit_report_details(payment_1, local_test_db_session)
    message = audit_report.details["message"]

    assert message == "\n".join(
        ["DOR Name: Sam Valdez-Garcia", "FINEOS Name: Javier Valdez-Garcia",]
    )

    payment_2 = create_payment_with_name("Javier", "Jones", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment_2)
    audit_report = _get_audit_report_details(payment_2, local_test_db_session)
    message = audit_report.details["message"]

    assert message == "\n".join(["DOR Name: Javier Jones", "FINEOS Name: Javier Valdez-Garcia",])

    payment_3 = create_payment_with_name("Sam", "Jones", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment_3)
    audit_report = _get_audit_report_details(payment_3, local_test_db_session)
    message = audit_report.details["message"]

    assert message == "\n".join(["DOR Name: Sam Jones", "FINEOS Name: Javier Valdez-Garcia",])


def _get_audit_report_details(payment, local_test_db_session):
    return (
        local_test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )

from typing import Optional

import pytest

from massgov.pfml.db.models.employees import PaymentTransactionType
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory, PaymentFactory
from massgov.pfml.db.models.payments import PaymentAuditReportDetails
from massgov.pfml.delegated_payments.postprocessing.dor_fineos_employee_name_mismatch_processor import (
    DORFineosEmployeeNameMismatchProcessor,
    trim_name,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)


@pytest.fixture
def payment_post_processing_step(
    initialize_factories_session,
    test_db_session,
):
    return PaymentPostProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


@pytest.fixture
def dor_fineos_employee_name_mismatch_processor(payment_post_processing_step):
    return DORFineosEmployeeNameMismatchProcessor(payment_post_processing_step)


# TODO use delegate payments factory PUB-277
def create_payment_with_name(
    dor_first_name,
    dor_last_name,
    fineos_first_name,
    fineos_last_name,
    payment_transaction_type_id: Optional[
        int
    ] = PaymentTransactionType.STANDARD.payment_transaction_type_id,
):
    employee = EmployeeFactory.create(first_name=dor_first_name, last_name=dor_last_name)
    claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim,
        fineos_employee_first_name=fineos_first_name,
        fineos_employee_last_name=fineos_last_name,
        payment_transaction_type_id=payment_transaction_type_id,
    )
    return payment


def test_processor_mixed(
    dor_fineos_employee_name_mismatch_processor,
    test_db_session,
    initialize_factories_session,
):
    ### Exact or close matches
    payment = create_payment_with_name("Javier", "Valdez", "Javier", "Valdez")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez", "Javier", "Valdez Jr.")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez Jr.", "Javier", "Valdez")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier M", "Valdez", "Javier", "Valdez")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez", "Javier M", "Valdez")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez-Garcia", "Javier", "Valdez Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("javier", "valdez garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    payment = create_payment_with_name("Javier", "Valdez-Garcia", "Javier", "Valdez_Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    ### Acceptable differences
    # First names different
    payment = create_payment_with_name("Javier", "Valdez-Garcia", "Joe", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None
    # Last names different
    payment = create_payment_with_name("Javier", "Valdez-Garcia", "Javier", "Smith")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None
    # Minor mispelling
    payment = create_payment_with_name("Javier", "Valdez-Garcia", "Javiir", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None
    # Minor mispelling
    payment = create_payment_with_name("Javier", "Valdes-Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    # Employer Reimbursement Payment
    payment = create_payment_with_name(
        "Javier",
        "Valdes-Garcia",
        "J",
        "Garcia",
        payment_transaction_type_id=PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id,
    )
    dor_fineos_employee_name_mismatch_processor.process(payment)
    assert _get_audit_report_details(payment, test_db_session) is None

    ### Mismatches
    payment_1 = create_payment_with_name("Sam", "Garcia-Valdez", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment_1)
    audit_report = _get_audit_report_details(payment_1, test_db_session)
    message = audit_report.details["message"]

    assert message == "\n".join(
        ["DOR Name: Sam Garcia-Valdez", "FINEOS Name: Javier Valdez-Garcia"]
    )

    payment_2 = create_payment_with_name("Javier", "Jones", "Joe", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment_2)
    audit_report = _get_audit_report_details(payment_2, test_db_session)
    message = audit_report.details["message"]

    assert message == "\n".join(["DOR Name: Javier Jones", "FINEOS Name: Joe Valdez-Garcia"])

    # Name too short, auto-fails
    payment_3 = create_payment_with_name("J", "Valdez-Garcia", "Javier", "Valdez-Garcia")
    dor_fineos_employee_name_mismatch_processor.process(payment_3)
    audit_report = _get_audit_report_details(payment_3, test_db_session)
    message = audit_report.details["message"]

    assert message == "\n".join(["DOR Name: J Valdez-Garcia", "FINEOS Name: Javier Valdez-Garcia"])


def _get_audit_report_details(payment, test_db_session):
    return (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )


def test_trim_name():
    expected = "abcabc"
    assert trim_name("abc abc") == expected
    assert trim_name("abc ,.-!@$#%#$^%$&*()_+==-abc!@#_%#$%123") == expected
    assert trim_name(",./;'[]abc abc") == expected
    assert trim_name("]][[][[[][]abc abc") == expected
    assert trim_name("///...,../abc abc") == expected

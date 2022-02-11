import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import (
    ClaimType,
    Payment,
    PaymentMethod,
    PaymentTransactionType,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    MmarsPaymentDataFactory,
    PaymentFactory,
)
from massgov.pfml.db.models.state import Flow, State
from massgov.pfml.delegated_payments.convert_mmars_data_step import ConvertMmarsDataStep
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationContainer,
    ValidationIssue,
    ValidationReason,
)


@pytest.fixture
def convert_mmars_data_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return ConvertMmarsDataStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_run_step(convert_mmars_data_step, local_test_db_session):
    employee = EmployeeFactory.create(ctr_vendor_customer_code="VC00001234")
    claim = ClaimFactory.create(employee=employee)

    mmars_data = MmarsPaymentDataFactory.create(
        vendor_invoice_no=f"{claim.fineos_absence_id}_1234",
        vendor_customer_code=employee.ctr_vendor_customer_code,
        disb_doc_code="EFT",
        activity="7247",
    )

    convert_mmars_data_step.run()

    # Verify one payment was created
    payments = local_test_db_session.query(Payment).all()
    assert len(payments) == 1
    payment = payments[0]

    local_test_db_session.refresh(mmars_data)
    assert payment.payment_id == mmars_data.payment_id
    assert payment.claim_id == claim.claim_id
    assert payment.employee_id == employee.employee_id
    assert payment.fineos_pei_c_value == "7326"
    assert payment.fineos_pei_i_value == "1234"
    assert payment.amount == mmars_data.pymt_actg_line_amount
    assert (
        payment.payment_transaction_type_id
        == PaymentTransactionType.STANDARD_LEGACY_MMARS.payment_transaction_type_id
    )
    assert payment.period_start_date == mmars_data.pymt_service_from_date.date()
    assert payment.period_end_date == mmars_data.pymt_service_to_date.date()
    assert payment.payment_date == mmars_data.warrant_select_date.date()
    assert payment.disb_check_eft_number == mmars_data.check_eft_no
    assert payment.disb_check_eft_issue_date == mmars_data.check_eft_issue_date.date()
    assert payment.disb_method_id == PaymentMethod.ACH.payment_method_id
    assert payment.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id
    assert payment.fineos_extract_import_log_id == convert_mmars_data_step.get_import_log_id()

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.LEGACY_MMARS_PAYMENTS, local_test_db_session
    )
    assert state_log.end_state_id == State.LEGACY_MMARS_PAYMENT_PAID.state_id

    assert not convert_mmars_data_step.validation_containers_with_issues

    # Re-running the step won't make more payments
    convert_mmars_data_step.run_step()

    # Verify still just a single payment
    payments = local_test_db_session.query(Payment).all()
    assert len(payments) == 1


def test_run_step_vcc_not_found_fallback(convert_mmars_data_step, local_test_db_session):
    employee = EmployeeFactory.create(ctr_vendor_customer_code=None)
    claim = ClaimFactory.create(employee=employee)

    mmars_data = MmarsPaymentDataFactory.create(
        vendor_invoice_no=f"{claim.fineos_absence_id}_1234", vendor_customer_code="VC00001234"
    )

    convert_mmars_data_step.run()

    # Verify one payment was created, and employee linked via the claim
    payments = local_test_db_session.query(Payment).all()
    assert len(payments) == 1
    payment = payments[0]

    local_test_db_session.refresh(mmars_data)
    assert payment.payment_id == mmars_data.payment_id
    assert payment.claim_id == claim.claim_id
    assert payment.employee_id == employee.employee_id


def test_run_step_claim_not_present(convert_mmars_data_step, local_test_db_session):
    employee = EmployeeFactory.create(ctr_vendor_customer_code="VC00001234")
    MmarsPaymentDataFactory.create(
        vendor_invoice_no="NTN-0001-ABS-01_1234",
        vendor_customer_code=employee.ctr_vendor_customer_code,
    )

    convert_mmars_data_step.run()

    payments = local_test_db_session.query(Payment).all()
    assert not payments

    assert convert_mmars_data_step.validation_containers_with_issues
    assert len(convert_mmars_data_step.validation_containers_with_issues) == 1
    issues = convert_mmars_data_step.validation_containers_with_issues[0].validation_issues
    assert issues == [ValidationIssue(ValidationReason.MISSING_IN_DB, "claim")]


def test_run_step_missing_vendor_invoice_no(convert_mmars_data_step, local_test_db_session):
    employee = EmployeeFactory.create(ctr_vendor_customer_code="VC00001234")
    ClaimFactory.create(employee=employee)

    MmarsPaymentDataFactory.create(
        vendor_invoice_no=None, vendor_customer_code=employee.ctr_vendor_customer_code
    )

    convert_mmars_data_step.run()

    payments = local_test_db_session.query(Payment).all()
    assert not payments

    # Verify the expected errors are found
    assert convert_mmars_data_step.validation_containers_with_issues
    assert len(convert_mmars_data_step.validation_containers_with_issues) == 1
    issues = convert_mmars_data_step.validation_containers_with_issues[0].validation_issues
    assert issues == [
        ValidationIssue(ValidationReason.INVALID_VALUE, "absence_case_number"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "fineos_pei_i_value"),
        ValidationIssue(ValidationReason.MISSING_IN_DB, "claim"),
    ]


def test_process_payment_existing_payment(convert_mmars_data_step):
    employee = EmployeeFactory.create(ctr_vendor_customer_code="VC00001234")
    claim = ClaimFactory.create(employee=employee)

    existing_payment = PaymentFactory.create(
        claim=claim, fineos_pei_c_value="7326", fineos_pei_i_value="1234"
    )
    mmars_data = MmarsPaymentDataFactory.create(
        vendor_invoice_no=f"{claim.fineos_absence_id}_1234",
        vendor_customer_code=employee.ctr_vendor_customer_code,
    )
    validation_container = ValidationContainer(mmars_data.vendor_invoice_no)

    payment = convert_mmars_data_step.process_payment(
        mmars_data, claim, employee, "1234", validation_container
    )
    assert not payment

    assert validation_container.has_validation_issues()
    assert validation_container.validation_issues == [
        ValidationIssue(
            ValidationReason.RECEIVED_PAYMENT_CURRENTLY_BEING_PROCESSED,
            f"Payment {existing_payment.payment_id} already exists, was consumed on {existing_payment.fineos_extraction_date}",
        )
    ]


def test_process_payment_missing_fields(convert_mmars_data_step):
    employee = EmployeeFactory.create(ctr_vendor_customer_code="VC00001234")
    claim = ClaimFactory.create(employee=employee)

    # Create a record missing all the fields we look for
    mmars_data = MmarsPaymentDataFactory.create(
        vendor_invoice_no=f"{claim.fineos_absence_id}_1234",
        vendor_customer_code=employee.ctr_vendor_customer_code,
        pymt_service_from_date=None,
        pymt_service_to_date=None,
        warrant_select_date=None,
        pymt_actg_line_amount=None,
        check_eft_no=None,
        check_eft_issue_date=None,
        disb_doc_code=None,
        activity=None,
    )
    validation_container = ValidationContainer(mmars_data.vendor_invoice_no)

    payment = convert_mmars_data_step.process_payment(
        mmars_data, claim, employee, "1234", validation_container
    )
    assert not payment

    assert validation_container.has_validation_issues()
    assert validation_container.validation_issues == [
        ValidationIssue(ValidationReason.INVALID_VALUE, "pymt_service_from_date"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "pymt_service_to_date"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "warrant_select_date"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "pymt_actg_line_amount"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "check_eft_no"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "check_eft_issue_date"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "disb_doc_code"),
        ValidationIssue(ValidationReason.INVALID_VALUE, "activity"),
    ]


def test_get_payment_method(convert_mmars_data_step):
    mmars_data = MmarsPaymentDataFactory.build(disb_doc_code="EFT")
    payment_method = convert_mmars_data_step.get_payment_method(mmars_data)
    assert (
        payment_method and payment_method.payment_method_id == PaymentMethod.ACH.payment_method_id
    )

    mmars_data = MmarsPaymentDataFactory.build(disb_doc_code="AD")
    payment_method = convert_mmars_data_step.get_payment_method(mmars_data)
    assert (
        payment_method and payment_method.payment_method_id == PaymentMethod.CHECK.payment_method_id
    )

    mmars_data = MmarsPaymentDataFactory.build(disb_doc_code="Something else")
    payment_method = convert_mmars_data_step.get_payment_method(mmars_data)
    assert not payment_method


def test_get_claim_type(convert_mmars_data_step):
    mmars_data = MmarsPaymentDataFactory.build(activity="7246")
    claim_type = convert_mmars_data_step.get_claim_type(mmars_data)
    assert claim_type and claim_type.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id

    mmars_data = MmarsPaymentDataFactory.build(activity="7247")
    claim_type = convert_mmars_data_step.get_claim_type(mmars_data)
    assert claim_type and claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id

    mmars_data = MmarsPaymentDataFactory.build(activity="Something else")
    claim_type = convert_mmars_data_step.get_claim_type(mmars_data)
    assert not claim_type

import copy
import json
from datetime import date

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_payment_extract as extractor
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.datetime
from massgov.pfml.db.models.employees import (
    AddressType,
    BankAccountType,
    Employee,
    Payment,
    PaymentMethod,
    PaymentTransactionType,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
    StateLog,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ExperianAddressPairFactory,
    ImportLogFactory,
    PaymentFactory,
    ReferenceFileFactory,
)
from massgov.pfml.db.models.geo import GeoState
from massgov.pfml.db.models.payments import (
    FineosExtractVbiRequestedAbsence,
    FineosExtractVpei,
    FineosExtractVpeiClaimDetails,
    FineosExtractVpeiPaymentDetails,
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
)
from massgov.pfml.db.models.state import Flow, LkState, State
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationIssue,
    ValidationReason,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.mock.fineos_extract_data import FineosPaymentData
from massgov.pfml.util.converters.str_to_numeric import str_to_int

EXPECTED_OUTCOME = {"message": "Success"}

### UTILITY METHODS


@pytest.fixture
def payment_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return extractor.PaymentExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def local_payment_extract_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return extractor.PaymentExtractStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def add_db_records_from_fineos_data(
    db_session,
    fineos_data,
    is_id_proofed=True,
    add_address=True,
    add_employee=True,
    add_eft=True,
    add_claim=True,
    add_employer=True,
    add_payment=False,
    additional_payment_state=None,
    prenote_state=PrenoteState.APPROVED,
    missing_fineos_name=False,
    has_exempt_employer=False,
):
    factory_args = {}
    if missing_fineos_name:
        factory_args["fineos_employee_first_name"] = None
        factory_args["fineos_employee_last_name"] = None

    if has_exempt_employer:
        factory_args["employer_exempt_family"] = True
        factory_args["employer_exempt_medical"] = True
        factory_args["employer_exempt_commence_date"] = date(2021, 1, 1)
        factory_args["employer_exempt_cease_date"] = date(2021, 1, 31)
        factory_args["absence_period_start_date"] = date(2021, 1, 15)

    factory = DelegatedPaymentFactory(
        db_session,
        ssn=fineos_data.tin,
        fineos_absence_id=fineos_data.absence_case_number,
        fineos_pei_c_value=fineos_data.c_value,
        fineos_pei_i_value=fineos_data.i_value,
        prenote_state=prenote_state,
        is_id_proofed=is_id_proofed,
        add_address=add_address,
        add_employee=add_employee,
        add_employer=add_employer,
        add_pub_eft=add_eft,
        add_claim=add_claim,
        add_payment=add_payment,
        **factory_args,
    )

    factory.create_all()

    if add_payment:
        factory.get_or_create_payment_with_state(additional_payment_state)


def validate_pei_writeback_state_for_payment(
    payment,
    db_session,
    is_invalid=False,
    is_issue_in_system=False,
    is_leave_in_review=False,
    is_pending_prenote=False,
    is_rejected_prenote=False,
    is_exempt_employer=False,
):
    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, db_session
    )

    writeback_details = (
        db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .one_or_none()
    )

    assert state_log
    assert state_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id

    assert writeback_details

    if is_invalid:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.FAILED_AUTOMATED_VALIDATION.transaction_status_id
        )
    elif is_issue_in_system:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.DATA_ISSUE_IN_SYSTEM.transaction_status_id
        )
    elif is_leave_in_review:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.LEAVE_IN_REVIEW.transaction_status_id
        )
    elif is_pending_prenote:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.PENDING_PRENOTE.transaction_status_id
        )
    elif is_rejected_prenote:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.PRENOTE_ERROR.transaction_status_id
        )
    elif is_exempt_employer:
        assert (
            writeback_details.transaction_status_id
            == FineosWritebackTransactionStatus.EXEMPT_EMPLOYER.transaction_status_id
        )


def validate_non_standard_payment_state(non_standard_payment: Payment, payment_state: LkState):
    assert len(non_standard_payment.state_logs) == 2
    assert set([state_log.end_state_id for state_log in non_standard_payment.state_logs]) == set(
        [payment_state.state_id, State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id,]
    )


def validate_withholding(
    withholding_payment: Payment,
    withholding_payment_data: FineosPaymentData,
    payment_state: LkState,
    payment_transaction_type: PaymentTransactionType,
):
    assert withholding_payment.claim_id
    assert withholding_payment.employee_id is None
    assert str(withholding_payment.amount) == withholding_payment_data.payment_amount
    assert withholding_payment.period_start_date == massgov.pfml.util.datetime.datetime_str_to_date(
        withholding_payment_data.payment_start_period
    )
    assert withholding_payment.period_end_date == massgov.pfml.util.datetime.datetime_str_to_date(
        withholding_payment_data.payment_end_period
    )
    assert (
        withholding_payment.payment_transaction_type.payment_transaction_type_id
        == payment_transaction_type.payment_transaction_type_id
    )
    assert len(withholding_payment.state_logs) == 1
    assert set([state_log.end_state_id for state_log in withholding_payment.state_logs]) == set(
        [payment_state.state_id,]
    )


def stage_data(
    records,
    db_session,
    reference_file=None,
    import_log=None,
    claimant_reference_file=None,
    claimant_import_log=None,
    additional_vpei_records=None,
    additional_payment_detail_records=None,
    additional_claim_detail_records=None,
    additional_requested_absence_records=None,
):
    if not reference_file:
        reference_file = ReferenceFileFactory.create(
            reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )
    if not import_log:
        import_log = ImportLogFactory.create()

    if not claimant_reference_file:
        claimant_reference_file = ReferenceFileFactory.create(
            reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
        )
    if not claimant_import_log:
        claimant_import_log = ImportLogFactory.create()

    for record in records:
        instance = payments_util.create_staging_table_instance(
            record.get_vpei_record(), FineosExtractVpei, reference_file, import_log.import_log_id
        )
        db_session.add(instance)
        instance = payments_util.create_staging_table_instance(
            record.get_payment_details_record(),
            FineosExtractVpeiPaymentDetails,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)
        instance = payments_util.create_staging_table_instance(
            record.get_claim_details_record(),
            FineosExtractVpeiClaimDetails,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)
        instance = payments_util.create_staging_table_instance(
            record.get_requested_absence_record(),
            FineosExtractVbiRequestedAbsence,
            claimant_reference_file,
            claimant_import_log.import_log_id,
        )
        db_session.add(instance)

    if additional_vpei_records:
        for vpei_record in additional_vpei_records:
            instance = payments_util.create_staging_table_instance(
                vpei_record.get_vpei_record(),
                FineosExtractVpei,
                reference_file,
                import_log.import_log_id,
            )
            db_session.add(instance)

    if additional_payment_detail_records:
        for payment_detail_record in additional_payment_detail_records:
            instance = payments_util.create_staging_table_instance(
                payment_detail_record.get_payment_details_record(),
                FineosExtractVpeiPaymentDetails,
                reference_file,
                import_log.import_log_id,
            )
            db_session.add(instance)

    if additional_claim_detail_records:
        for claim_detail_record in additional_claim_detail_records:
            instance = payments_util.create_staging_table_instance(
                claim_detail_record.get_claim_details_record(),
                FineosExtractVpeiClaimDetails,
                reference_file,
                import_log.import_log_id,
            )
            db_session.add(instance)

    if additional_requested_absence_records:
        for requested_absence_record in additional_claim_detail_records:
            instance = payments_util.create_staging_table_instance(
                requested_absence_record.get_requested_absence_record(),
                FineosExtractVbiRequestedAbsence,
                claimant_reference_file,
                claimant_import_log.import_log_id,
            )
            db_session.add(instance)

    db_session.commit()


### TESTS BEGIN


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_run_step_happy_path(
    local_payment_extract_step, local_test_db_session,
):
    payment_data_eft = FineosPaymentData()
    payment_data_check = FineosPaymentData(payment_method="Check")
    add_db_records_from_fineos_data(local_test_db_session, payment_data_eft)
    add_db_records_from_fineos_data(local_test_db_session, payment_data_check)

    payment_datasets = [payment_data_eft, payment_data_check]
    stage_data(payment_datasets, local_test_db_session)

    local_payment_extract_step.run()

    for payment_data in payment_datasets:
        payment = (
            local_test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == payment_data.c_value,
                Payment.fineos_pei_i_value == payment_data.i_value,
            )
            .first()
        )
        assert payment.vpei_id is not None

        # Validate all of the payment fields that were set
        assert payment.period_start_date == massgov.pfml.util.datetime.datetime_str_to_date(
            payment_data.payment_start_period
        )
        assert payment.period_end_date == massgov.pfml.util.datetime.datetime_str_to_date(
            payment_data.payment_end_period
        )
        assert payment.payment_date == massgov.pfml.util.datetime.datetime_str_to_date(
            payment_data.payment_date
        )
        assert payment.fineos_extraction_date == date(2021, 1, 13)
        assert str(payment.amount) == payment_data.payment_amount
        assert (
            payment.fineos_extract_import_log_id == local_payment_extract_step.get_import_log_id()
        )

        # One payment details record should have same values
        # as the payment
        assert len(payment.payment_details) == 1
        payment_details = payment.payment_details[0]
        assert payment_details.period_start_date == payment.period_start_date
        assert payment_details.period_end_date == payment.period_end_date
        assert payment_details.amount == payment.amount

        claim = payment.claim
        assert claim

        employee = claim.employee
        assert employee

        assert payment.fineos_leave_request_id is not None
        assert payment.fineos_leave_request_id == str_to_int(payment_data.leave_request_id)
        assert payment.fineos_employee_first_name == employee.fineos_employee_first_name
        assert payment.fineos_employee_middle_name == employee.fineos_employee_middle_name
        assert payment.fineos_employee_last_name == employee.fineos_employee_last_name

        mailing_address = payment.experian_address_pair.fineos_address
        assert mailing_address
        assert mailing_address.address_line_one == payment_data.payment_address_1
        assert mailing_address.address_line_two is None
        assert mailing_address.city == payment_data.city
        assert mailing_address.geo_state.geo_state_description == payment_data.state
        assert mailing_address.zip_code == payment_data.zip_code
        assert mailing_address.address_type_id == AddressType.MAILING.address_type_id

        employee_addresses = employee.employee_addresses.all()
        assert (
            len(employee_addresses) == 2
        )  # 1 created in setup_process_tests, 1 created during the step itself
        assert employee_addresses[1].employee_id == employee.employee_id
        assert employee_addresses[1].address_id == mailing_address.address_id

        reference_files = payment.reference_files
        assert len(reference_files) == 1
        reference_file = reference_files[0].reference_file
        assert (
            reference_file.reference_file_type_id
            == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )
        # Verify that there is exactly one successful state log per payment
        state_logs = payment.state_logs
        assert len(state_logs) == 1
        state_log = state_logs[0]
        assert state_log.outcome == EXPECTED_OUTCOME
        assert state_log.end_state_id == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id

        pub_efts = employee.pub_efts.all()

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        # The 2nd record is also family leave, the other two are medical leave
        if payment_data.payment_method == "Check":
            assert payment.disb_method_id == PaymentMethod.CHECK.payment_method_id
            assert payment.pub_eft_id is None
            assert payment.has_eft_update is False
            assert len(pub_efts) == 1  # One prior one created by setup logic

        else:
            assert payment.disb_method_id == PaymentMethod.ACH.payment_method_id
            assert payment.pub_eft
            assert str(payment.pub_eft.routing_nbr) == payment_data.routing_nbr
            assert str(payment.pub_eft.account_nbr) == payment_data.account_nbr
            assert (
                payment.pub_eft.bank_account_type_id
                == BankAccountType.CHECKING.bank_account_type_id
            )
            assert payment.has_eft_update is False

            assert len(pub_efts) == 1  # A prior one from setup logic
            assert payment.pub_eft_id in [pub_eft.pub_eft_id for pub_eft in employee.pub_efts]

        assert payment.exclude_from_payment_status is False
    # Verify a few of the metrics were added to the import log table
    import_log_report = json.loads(payment.fineos_extract_import_log.report)
    assert import_log_report["standard_valid_payment_count"] == 2


def test_run_step_multiple_times(
    local_payment_extract_step, local_test_db_session,
):
    # Test what happens if we run multiple times on the same data
    # After the first run, the step should no-op as the reference file
    # has already been processed.
    payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(local_test_db_session, payment_data)

    payment_datasets = [payment_data]
    stage_data(payment_datasets, local_test_db_session)

    # First run
    local_payment_extract_step.run()

    # Make sure the processed ID is set.
    reference_files = (
        local_test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
        )
        .all()
    )
    assert len(reference_files) == 1
    assert (
        reference_files[0].processed_import_log_id == local_payment_extract_step.get_import_log_id()
    )

    payments_after_first_run = local_test_db_session.query(Payment).all()
    assert len(payments_after_first_run) == 1

    # Run again a few times
    local_payment_extract_step.run()
    local_payment_extract_step.run()
    local_payment_extract_step.run()

    payments_after_all_runs = local_test_db_session.query(Payment).all()
    assert len(payments_after_all_runs) == 1


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_prior_payment_exists_is_being_processed(
    local_payment_extract_step, local_test_db_session,
):
    payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session,
        payment_data,
        add_payment=True,
        additional_payment_state=State.DELEGATED_PAYMENT_COMPLETE,
    )

    stage_data([payment_data], local_test_db_session)

    local_payment_extract_step.run()

    payments = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .all()
    )
    # There will be both a prior payment and a new payment
    assert len(payments) == 2

    new_payment = [
        payment
        for payment in payments
        if payment.state_logs[0].end_state_id != State.DELEGATED_PAYMENT_COMPLETE.state_id
    ][0]

    assert new_payment.exclude_from_payment_status is True

    state_log = state_log_util.get_latest_state_log_in_flow(
        new_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome == {
        "message": "Active Payment Error - Contact FINEOS",
        "validation_container": {
            "record_key": f"C={payment_data.c_value},I={payment_data.i_value}",
            "validation_issues": [
                {
                    "reason": "ReceivedPaymentCurrentlyBeingProcessed",
                    "details": "We received a payment that is already being processed. It is currently in state [Payment complete].",
                }
            ],
        },
    }
    # No writeback made for active payment errors
    pei_writeback_state = state_log_util.get_latest_state_log_in_flow(
        new_payment, Flow.DELEGATED_PEI_WRITEBACK, local_test_db_session
    )
    assert pei_writeback_state is None


def test_process_extract_data_one_bad_record(
    local_payment_extract_step, local_test_db_session,
):
    # This payment will end up in an error state
    # because we don't have an TIN/employee/claim associated with them
    payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session, payment_data, add_employee=False, add_claim=False
    )

    stage_data([payment_data], local_test_db_session)
    local_payment_extract_step.run()

    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .first()
    )
    # Payment is created even when employee cannot be found
    assert payment

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )

    assert payment.claim_id is None
    assert (
        state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
    )
    assert state_log.outcome == {
        "message": "Error processing payment record",
        "validation_container": {
            "record_key": f"C={payment_data.c_value},I={payment_data.i_value}",
            "validation_issues": [
                {"reason": "MissingInDB", "details": f"tax_identifier: {payment_data.tin}"},
                {"reason": "MissingInDB", "details": f"claim: {payment_data.absence_case_number}"},
            ],
        },
    }
    validate_pei_writeback_state_for_payment(
        payment, local_test_db_session, is_issue_in_system=True
    )


def test_process_extract_data_no_employer_on_claim(
    local_payment_extract_step, local_test_db_session,
):
    # This payment will end up in an error state
    # because the employer is exempt for the payment
    payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(local_test_db_session, payment_data, add_employer=False)

    stage_data([payment_data], local_test_db_session)
    local_payment_extract_step.run()

    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .first()
    )

    assert payment
    assert not payment.claim.employer

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
    )
    assert state_log.outcome == {
        "message": "Error processing payment record",
        "validation_container": {
            "record_key": f"C={payment_data.c_value},I={payment_data.i_value}",
            "validation_issues": [
                {
                    "reason": "MissingInDB",
                    "details": f"Claim {payment.claim.fineos_absence_id} does not have an employer associated with it",
                },
            ],
        },
    }
    validate_pei_writeback_state_for_payment(
        payment, local_test_db_session, is_issue_in_system=True
    )


def test_process_extract_data_employer_exempt(
    local_payment_extract_step, local_test_db_session,
):
    # This payment will end up in an error state
    # because the employer is exempt for the payment
    payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(local_test_db_session, payment_data, has_exempt_employer=True)

    stage_data([payment_data], local_test_db_session)
    local_payment_extract_step.run()

    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .first()
    )

    assert payment
    assert payment.claim.employer
    employer = payment.claim.employer

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
    assert state_log.outcome == {
        "message": "Error processing payment record",
        "validation_container": {
            "record_key": f"C={payment_data.c_value},I={payment_data.i_value}",
            "validation_issues": [
                {
                    "reason": "EmployerExempt",
                    "details": f"Employer {employer.fineos_employer_id} is exempt for dates {employer.exemption_commence_date} - {employer.exemption_cease_date}",
                },
            ],
        },
    }
    validate_pei_writeback_state_for_payment(
        payment, local_test_db_session, is_exempt_employer=True
    )


def test_process_extract_data_employer_exempt_non_standard_payment(
    local_payment_extract_step, local_test_db_session,
):
    # Show that non-standard payments don't error
    # due to employer exempt
    payment_data = FineosPaymentData(
        event_type="Overpayment", event_reason="Unknown", payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, payment_data, has_exempt_employer=True)

    stage_data([payment_data], local_test_db_session)
    local_payment_extract_step.run()

    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .first()
    )
    assert payment
    validate_non_standard_payment_state(payment, State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT)


def test_process_extract_data_rollback(
    local_payment_extract_step, local_test_db_session, monkeypatch,
):
    payment_data_eft = FineosPaymentData()
    payment_data_check = FineosPaymentData(payment_method="Check")
    add_db_records_from_fineos_data(local_test_db_session, payment_data_eft)
    add_db_records_from_fineos_data(local_test_db_session, payment_data_check)

    payment_datasets = [payment_data_eft, payment_data_check]
    stage_data(payment_datasets, local_test_db_session)

    # Override the method that moves files at the end to throw
    # an error so that everything will rollback
    def err_method(*args):
        raise Exception("Fake Error")

    monkeypatch.setattr(local_payment_extract_step, "_setup_state_log", err_method)

    with pytest.raises(Exception, match="Fake Error"):
        local_payment_extract_step.run()

    # Make certain that there are no payments or state logs in the DB
    payments = local_test_db_session.query(Payment).all()
    assert len(payments) == 0
    state_logs = local_test_db_session.query(StateLog).all()
    assert len(state_logs) == 0


def test_process_extract_data_no_existing_address_eft(
    local_payment_extract_step, local_test_db_session,
):
    payment_data_eft = FineosPaymentData()
    payment_data_check = FineosPaymentData(payment_method="Check")
    add_db_records_from_fineos_data(
        local_test_db_session, payment_data_eft, add_eft=False, add_address=False
    )
    add_db_records_from_fineos_data(
        local_test_db_session, payment_data_check, add_eft=False, add_address=False
    )

    payment_datasets = [payment_data_eft, payment_data_check]
    stage_data(payment_datasets, local_test_db_session)
    local_payment_extract_step.run()

    for payment_data in payment_datasets:
        payment = (
            local_test_db_session.query(Payment)
            .filter(
                Payment.fineos_pei_c_value == payment_data.c_value,
                Payment.fineos_pei_i_value == payment_data.i_value,
            )
            .first()
        )

        employee = payment.claim.employee
        assert employee

        mailing_address = payment.experian_address_pair.fineos_address
        assert mailing_address
        assert mailing_address.address_line_one == payment_data.payment_address_1
        assert mailing_address.address_line_two is None
        assert mailing_address.city == payment_data.city
        assert mailing_address.geo_state.geo_state_description == payment_data.state
        assert mailing_address.zip_code == payment_data.zip_code
        assert mailing_address.address_type_id == AddressType.MAILING.address_type_id
        assert payment.has_address_update is True

        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_session
        )

        pub_efts = employee.pub_efts.all()

        # Payment 2 uses CHECK over ACH, so some logic differs for it.
        if payment_data.payment_method == "Check":
            assert not mailing_address.address_line_two

            assert payment.disb_method_id == PaymentMethod.CHECK.payment_method_id
            assert payment.pub_eft_id is None
            assert payment.has_eft_update is False
            assert len(pub_efts) == 0  # Not set by setup logic, shouldn't be set at all now
            assert state_log.outcome == EXPECTED_OUTCOME
            assert state_log.end_state_id == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id

        else:

            assert payment.disb_method_id == PaymentMethod.ACH.payment_method_id
            assert payment.pub_eft
            assert str(payment.pub_eft.routing_nbr) == payment_data.routing_nbr
            assert str(payment.pub_eft.account_nbr) == payment_data.account_nbr
            assert (
                payment.pub_eft.bank_account_type_id
                == BankAccountType.CHECKING.bank_account_type_id
            )
            assert payment.pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id
            assert payment.has_eft_update is True

            assert len(pub_efts) == 1
            assert payment.pub_eft_id == pub_efts[0].pub_eft_id

            # The EFT info was new, so the payment is in an error state
            assert state_log.outcome == {
                "message": "Error processing payment record",
                "validation_container": {
                    "record_key": f"C={payment_data.c_value},I={payment_data.i_value}",
                    "validation_issues": [
                        {"reason": "EFTPending", "details": "New EFT info found, prenote required"}
                    ],
                },
            }
            assert (
                state_log.end_state_id
                == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
            )

            # There is also a state log for the payment in the PEI writeback flow
            validate_pei_writeback_state_for_payment(
                payment, local_test_db_session, is_pending_prenote=True
            )

            # Verify that there is exactly one successful state log per employee that uses ACH
            state_logs = employee.state_logs
            assert len(state_logs) == 1
            state_log = state_logs[0]
            assert "Initiated DELEGATED_EFT flow for employee" in state_log.outcome["message"]
            assert state_log.end_state_id == State.DELEGATED_EFT_SEND_PRENOTE.state_id


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_existing_payment(
    local_payment_extract_step, local_test_db_session,
):

    payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session,
        payment_data,
        add_payment=True,
        additional_payment_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
    )

    stage_data([payment_data], local_test_db_session)
    local_payment_extract_step.run()

    payments = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data.c_value,
            Payment.fineos_pei_i_value == payment_data.i_value,
        )
        .all()
    )

    # There will be both a prior payment and a new payment
    assert len(payments) == 2

    for payment in payments:
        # Verify that there is exactly one successful state log per payment
        state_logs = payment.state_logs
        assert len(state_logs) == 1
        state_log = state_logs[0]
        # The state ID will be either the prior state ID or the new successful one
        assert state_log.end_state_id in [
            State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id,
        ]
        if state_log.end_state_id == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id:
            assert state_log.outcome == EXPECTED_OUTCOME


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_minimal_viable_payment(
    local_payment_extract_step, local_test_db_session,
):
    # This test creates a payment with absolutely no data besides the bare
    # minimum to be viable to create a payment, this is done in order
    # to test that all of our validations work, and all of the missing data
    # edge cases are accounted for and handled appropriately. This shouldn't
    # ever be a real scenario, but might encompass small pieces of something real

    # C & I value are the bare minimum to have a payment
    fineos_data = FineosPaymentData(False, c_value="1000", i_value="1")
    stage_data([fineos_data], local_test_db_session)
    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    payment = local_test_db_session.query(Payment).one_or_none()
    assert payment
    assert payment.claim is None

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome["message"] == "Error processing payment record"
    assert state_log.outcome["validation_container"]["record_key"] == "C=1000,I=1"
    # Not going to exactly match the errors here as there are many
    # and they may adjust in the future
    assert len(state_log.outcome["validation_container"]["validation_issues"]) >= 7

    # Payment is not added to the PEI writeback flow because we don't know the type of payment
    validate_pei_writeback_state_for_payment(payment, local_test_db_session, is_invalid=True)


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_minimal_viable_standard_payment(
    local_payment_extract_step, local_test_db_session,
):
    # Same as the above test, but we setup enough to make a "standard" payment

    # C & I value are the bare minimum to have a payment
    fineos_data = FineosPaymentData(
        False, c_value="1000", i_value="1", event_type="PaymentOut", payment_amount="100.00"
    )
    stage_data([fineos_data], local_test_db_session)
    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    payment = local_test_db_session.query(Payment).one_or_none()
    assert payment
    assert payment.vpei_id is not None
    assert payment.claim is None

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome["message"] == "Error processing payment record"
    assert state_log.outcome["validation_container"]["record_key"] == "C=1000,I=1"
    # Not going to exactly match the errors here as there are many
    # and they may adjust in the future
    assert len(state_log.outcome["validation_container"]["validation_issues"]) >= 11

    # Payment is also added to the PEI writeback error flow
    validate_pei_writeback_state_for_payment(payment, local_test_db_session, is_invalid=True)


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_leave_request_decision_validation(
    local_payment_extract_step, local_test_db_session,
):

    medical_claim_type_record = FineosPaymentData(claim_type="Employee")
    approved_record = FineosPaymentData(leave_request_decision="Approved")
    in_review_record = FineosPaymentData(leave_request_decision="In Review")
    rejected_record = FineosPaymentData(leave_request_decision="Rejected")
    unknown_record = FineosPaymentData(leave_request_decision="Pending")

    # setup both payments in DB
    add_db_records_from_fineos_data(local_test_db_session, approved_record)
    add_db_records_from_fineos_data(local_test_db_session, unknown_record)
    add_db_records_from_fineos_data(local_test_db_session, in_review_record)
    add_db_records_from_fineos_data(local_test_db_session, rejected_record)
    add_db_records_from_fineos_data(local_test_db_session, medical_claim_type_record)

    stage_data(
        [
            approved_record,
            unknown_record,
            in_review_record,
            rejected_record,
            medical_claim_type_record,
        ],
        local_test_db_session,
    )

    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    approved_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == approved_record.c_value,
            Payment.fineos_pei_i_value == approved_record.i_value,
        )
        .one_or_none()
    )
    assert approved_payment
    assert len(approved_payment.state_logs) == 1
    assert (
        approved_payment.state_logs[0].end_state_id
        == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id
    )

    in_review_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == in_review_record.c_value,
            Payment.fineos_pei_i_value == in_review_record.i_value,
        )
        .one_or_none()
    )
    assert in_review_payment
    assert len(in_review_payment.state_logs) == 2
    validate_pei_writeback_state_for_payment(
        in_review_payment, local_test_db_session, is_leave_in_review=True,
    )
    state_log = state_log_util.get_latest_state_log_in_flow(
        in_review_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )

    rejected_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == rejected_record.c_value,
            Payment.fineos_pei_i_value == rejected_record.i_value,
        )
        .one_or_none()
    )
    assert rejected_payment
    assert len(rejected_payment.state_logs) == 2
    state_log = state_log_util.get_latest_state_log_in_flow(
        rejected_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
    validate_pei_writeback_state_for_payment(
        rejected_payment, local_test_db_session, is_invalid=True
    )

    unknown_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == unknown_record.c_value,
            Payment.fineos_pei_i_value == unknown_record.i_value,
        )
        .one_or_none()
    )
    assert unknown_payment
    assert len(unknown_payment.state_logs) == 2
    state_log = state_log_util.get_latest_state_log_in_flow(
        unknown_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
    validate_pei_writeback_state_for_payment(
        unknown_payment, local_test_db_session, is_invalid=True
    )

    medical_claim_type_record = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == medical_claim_type_record.c_value,
            Payment.fineos_pei_i_value == medical_claim_type_record.i_value,
        )
        .one_or_none()
    )

    assert medical_claim_type_record
    assert len(medical_claim_type_record.state_logs) == 1
    assert (
        medical_claim_type_record.state_logs[0].end_state_id
        == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id
    )

    import_log_report = json.loads(rejected_payment.fineos_extract_import_log.report)
    assert import_log_report["in_review_leave_request_count"] == 1
    assert import_log_report["not_approved_leave_request_count"] == 2
    assert import_log_report["standard_valid_payment_count"] == 2


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_not_id_proofed(
    local_test_db_session, local_payment_extract_step,
):
    datasets = []
    # This tests that a payment with a claim missing ID proofing with be rejected

    standard_payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session, standard_payment_data, is_id_proofed=False
    )
    datasets.append(standard_payment_data)
    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    standard_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == standard_payment_data.i_value)
        .one_or_none()
    )
    state_log = state_log_util.get_latest_state_log_in_flow(
        standard_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
    )

    issues = state_log.outcome["validation_container"]["validation_issues"]
    assert len(issues) == 1
    assert issues[0] == {
        "reason": "ClaimNotIdProofed",
        "details": f"Claim {standard_payment_data.absence_case_number} has not been ID proofed",
    }
    validate_pei_writeback_state_for_payment(
        standard_payment, local_test_db_session, is_issue_in_system=True
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_no_fineos_name(local_test_db_session, local_payment_extract_step):
    datasets = []
    # This tests that a payment with a claim missing ID proofing with be rejected

    standard_payment_data = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session, standard_payment_data, missing_fineos_name=True
    )
    datasets.append(standard_payment_data)
    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    standard_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == standard_payment_data.i_value)
        .one_or_none()
    )
    state_log = state_log_util.get_latest_state_log_in_flow(
        standard_payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )

    assert (
        state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
    )
    issues = state_log.outcome["validation_container"]["validation_issues"]
    assert len(issues) == 1
    assert issues[0] == {
        "reason": "MissingFineosName",
        "details": f"Missing name from FINEOS on employee {standard_payment.claim.employee.employee_id}",
    }
    validate_pei_writeback_state_for_payment(
        standard_payment, local_test_db_session, is_issue_in_system=True
    )

    import_log_report = json.loads(standard_payment.fineos_extract_import_log.report)
    assert import_log_report["employee_fineos_name_missing"] == 1


def test_process_extract_is_adhoc(
    local_payment_extract_step, local_test_db_session,
):
    fineos_adhoc_data = FineosPaymentData(amalgamationc="Adhoc1234")
    add_db_records_from_fineos_data(local_test_db_session, fineos_adhoc_data)
    fineos_standard_data = FineosPaymentData(amalgamationc="Some other value")
    add_db_records_from_fineos_data(local_test_db_session, fineos_standard_data)

    stage_data([fineos_adhoc_data, fineos_standard_data], local_test_db_session)

    local_payment_extract_step.run()

    # The adhoc payment should be valid and have that column set to True
    adhoc_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == fineos_adhoc_data.c_value,
            Payment.fineos_pei_i_value == fineos_adhoc_data.i_value,
        )
        .one_or_none()
    )
    assert adhoc_payment.is_adhoc_payment
    assert len(adhoc_payment.state_logs) == 1
    assert (
        adhoc_payment.state_logs[0].end_state_id
        == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id
    )

    # Any other value for that column will create a valid payment with the column False
    standard_payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == fineos_standard_data.c_value,
            Payment.fineos_pei_i_value == fineos_standard_data.i_value,
        )
        .one_or_none()
    )
    assert not standard_payment.is_adhoc_payment
    assert len(standard_payment.state_logs) == 1
    assert (
        standard_payment.state_logs[0].end_state_id
        == State.PAYMENT_READY_FOR_ADDRESS_VALIDATION.state_id
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_multiple_payment_details(
    local_test_db_session, local_payment_extract_step,
):
    # Create a standard payment, but give it a few payment periods
    # by creating several copies of the payment data, but the others have
    # other random dates/amounts
    fineos_payment_data = FineosPaymentData(
        payment_start="2021-01-01 12:00:00",
        payment_end="2021-01-01 12:00:00",
        payment_amount="100.00",
        balancing_amount="100.10",
        business_net_amount="100.01",
    )
    add_db_records_from_fineos_data(local_test_db_session, fineos_payment_data)

    datasets = [fineos_payment_data]
    for i in range(2, 5):  # 2, 3, 4
        additional_data = copy.deepcopy(fineos_payment_data)
        additional_data.include_vpei = False
        additional_data.include_claim_details = False
        additional_data.include_requested_absence = False
        additional_data.payment_amount = f"{i}00.00"
        additional_data.balancing_amount = f"{i}00.10"
        additional_data.business_net_amount = f"{i}00.01"

        additional_data.payment_start_period = f"2021-01-0{i} 12:00:00"
        additional_data.payment_end_period = f"2021-01-0{i} 12:00:00"

        datasets.append(additional_data)

    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == fineos_payment_data.c_value,
            Payment.fineos_pei_i_value == fineos_payment_data.i_value,
        )
        .one_or_none()
    )

    payment_details = payment.payment_details
    assert len(payment_details) == 4

    # Verify the payment details were parsed correctly
    payment_details.sort(key=lambda payment_detail: payment_detail.period_start_date)
    for i, payment_detail in enumerate(payment_details, start=1):
        assert str(payment_detail.amount) == f"{i}00.10"
        assert str(payment_detail.business_net_amount) == f"{i}00.01"
        assert str(payment_detail.period_start_date) == f"2021-01-0{i}"
        assert str(payment_detail.period_end_date) == f"2021-01-0{i}"

    # Verify a few values on the payment itself
    assert str(payment.amount) == "100.00"  # The file generates with the first value
    assert str(payment.period_start_date) == "2021-01-01"  # Earliest date in list
    assert str(payment.period_end_date) == "2021-01-04"  # Latest date in list


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_additional_payment_types(
    local_test_db_session, local_payment_extract_step,
):
    datasets = []
    # This tests that the behavior of non-standard payment types are handled properly
    # All of these are setup as EFT payments, but we won't create EFT information for them
    # or reject them for not being prenoted yet.

    # Create a zero dollar payment
    zero_dollar_data = FineosPaymentData(
        payment_amount="0.00", payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, zero_dollar_data, add_eft=False)
    datasets.append(zero_dollar_data)

    # Create an overpayment
    # note that the event reason for an overpayment is Unknown which is treated as
    # None in our approach, setting it here to make sure that doesn't cause a validation issue.
    overpayment_data = FineosPaymentData(
        event_type="Overpayment", event_reason="Unknown", payment_method="Elec Funds Transfer"
    )

    add_db_records_from_fineos_data(local_test_db_session, overpayment_data, add_eft=False)
    datasets.append(overpayment_data)

    # Create a cancellation
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation",
        payment_amount="-123.45",
        payment_method="Elec Funds Transfer",
    )
    add_db_records_from_fineos_data(local_test_db_session, cancellation_data, add_eft=False)
    datasets.append(cancellation_data)

    # Unknown - negative payment amount, but PaymentOut
    negative_payment_out_data = FineosPaymentData(
        event_type="PaymentOut", payment_amount="-100.00", payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, negative_payment_out_data, add_eft=False)
    datasets.append(negative_payment_out_data)

    # Unknown - missing payment amount
    no_payment_out_data = FineosPaymentData(
        payment_amount=None, payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(local_test_db_session, no_payment_out_data, add_eft=False)
    datasets.append(no_payment_out_data)

    # Unknown - missing event type
    missing_event_payment_out_data = FineosPaymentData(
        event_type=None, payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(
        local_test_db_session, missing_event_payment_out_data, add_eft=False
    )
    datasets.append(missing_event_payment_out_data)

    # Create a record for an employer reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
        payment_method="Elec Funds Transfer",
    )
    add_db_records_from_fineos_data(
        local_test_db_session, employer_reimbursement_data, add_eft=False
    )
    datasets.append(employer_reimbursement_data)

    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    # No PUB EFT records should exist
    assert len(local_test_db_session.query(PubEft).all()) == 0

    # Zero dollar payment should be in DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    zero_dollar_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == zero_dollar_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        zero_dollar_payment, State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    )

    # Overpayment should be in DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    overpayment_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == overpayment_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        overpayment_payment, State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    )

    # ACH Cancellation should be in DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    cancellation_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == cancellation_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        cancellation_payment, State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    )

    # Negative payment will cause an unknown transaction type which is restartable
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    negative_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == negative_payment_out_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        negative_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    # No payment amount means the payment needs to be updated, so we error
    # the payment and add it to two states.
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    no_amount_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == no_payment_out_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        no_amount_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    # No event type means the payment needs to be updated, so we error
    # the payment and add it to two states.
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    missing_event_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == missing_event_payment_out_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        missing_event_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    # Employer reimbursement should be in DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    employer_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == employer_reimbursement_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        employer_payment, State.DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_additional_payment_types_can_be_missing_other_files(
    local_test_db_session, local_payment_extract_step,
):
    # This tests that the behavior of non-standard payment types are handled properly
    # In every scenario, only the VPEI file and payment details file
    # contains information for the records, and it will
    # fail to find anything in the other files. For non-standard payments, this will not
    # error them, and they will be moved to their respective success states, albeit without
    # finding a claim to attach to, and with several pieces of information missing. It is however
    # enough for our purposes of creating reports and sending them in a writeback.
    datasets = []

    # Create a zero dollar payment
    zero_dollar_data = FineosPaymentData(
        payment_amount="0.00",
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=True,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, zero_dollar_data, add_eft=False)
    datasets.append(zero_dollar_data)

    # Create an overpayment
    # note that the event reason for an overpayment is Unknown which is treated as
    # None in our approach, setting it here to make sure that doesn't cause a validation issue.
    overpayment_data = FineosPaymentData(
        event_type="Overpayment",
        event_reason="Unknown",
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=True,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, overpayment_data, add_eft=False)
    datasets.append(overpayment_data)

    # Create a cancellation
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation",
        payment_amount="-123.45",
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=True,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(local_test_db_session, cancellation_data, add_eft=False)
    datasets.append(cancellation_data)

    # Create a record for an employer reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
        payment_method="Elec Funds Transfer",
        include_claim_details=False,
        include_payment_details=True,
        include_requested_absence=False,
    )
    add_db_records_from_fineos_data(
        local_test_db_session, employer_reimbursement_data, add_eft=False
    )
    datasets.append(employer_reimbursement_data)

    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    # No PUB EFT records should exist
    assert len(local_test_db_session.query(PubEft).all()) == 0

    # Zero dollar payment should be in DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    zero_dollar_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == zero_dollar_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        zero_dollar_payment, State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    )
    assert zero_dollar_payment.claim_id is None

    # Overpayment should be in DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    overpayment_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == overpayment_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        overpayment_payment, State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    )
    assert overpayment_payment.claim_id is None

    # ACH Cancellation should be in DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    cancellation_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == cancellation_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        cancellation_payment, State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    )
    assert cancellation_payment.claim_id is None

    # Employer reimbursement should be in DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    employer_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == employer_reimbursement_data.i_value)
        .one_or_none()
    )
    validate_non_standard_payment_state(
        employer_payment, State.DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    )
    assert employer_payment.claim_id is None


def test_process_extract_additional_payment_types_can_be_missing_all_additional_datasets_and_claim(
    local_test_db_session, local_payment_extract_step
):
    # This tests that non-standard payments can be missing a claim
    # and will still be successful as long as the employee exists
    datasets = []

    # Create a zero dollar payment
    zero_dollar_data = FineosPaymentData(payment_amount="0.00")
    add_db_records_from_fineos_data(
        local_test_db_session, zero_dollar_data, add_claim=False, add_eft=False
    )
    datasets.append(zero_dollar_data)

    # Create an overpayment
    # note that the event reason for an overpayment is Unknown which is treated as
    # None in our approach, setting it here to make sure that doesn't cause a validation issue.
    for overpayment_type in payments_util.Constants.OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS:
        overpayment_data = FineosPaymentData(
            event_type=overpayment_type.payment_transaction_type_description,
            event_reason="Unknown",
            payment_method="Elec Funds Transfer",
            include_claim_details=False,
            include_payment_details=False,
            include_requested_absence=False,
        )
        add_db_records_from_fineos_data(
            local_test_db_session, overpayment_data, add_claim=False, add_eft=False
        )
        datasets.append(overpayment_data)

    # Create a cancellation
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation", payment_amount="-123.45",
    )
    add_db_records_from_fineos_data(
        local_test_db_session, cancellation_data, add_claim=False, add_eft=False
    )
    datasets.append(cancellation_data)

    # Unknown - negative payment amount, but PaymentOut
    negative_payment_out_data = FineosPaymentData(event_type="PaymentOut", payment_amount="-100.00")
    add_db_records_from_fineos_data(
        local_test_db_session, negative_payment_out_data, add_claim=False, add_eft=False
    )
    datasets.append(negative_payment_out_data)

    # Unknown - missing payment amount
    no_payment_out_data = FineosPaymentData(
        payment_amount=None, payment_method="Elec Funds Transfer"
    )
    add_db_records_from_fineos_data(
        local_test_db_session, no_payment_out_data, add_claim=False, add_eft=False
    )
    datasets.append(no_payment_out_data)

    # Unknown - missing event type
    missing_event_payment_out_data = FineosPaymentData(event_type=None)
    add_db_records_from_fineos_data(
        local_test_db_session, missing_event_payment_out_data, add_claim=False, add_eft=False
    )
    datasets.append(missing_event_payment_out_data)

    # Create a record for an employer reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
    )
    add_db_records_from_fineos_data(
        local_test_db_session, employer_reimbursement_data, add_claim=False, add_eft=False
    )
    datasets.append(employer_reimbursement_data)

    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    # No PUB EFT records should exist, overpayments won't make those
    assert len(local_test_db_session.query(PubEft).all()) == 0

    for (
        overpayment_type_id
    ) in payments_util.Constants.OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS_IDS:
        overpayment = (
            local_test_db_session.query(Payment)
            .filter(Payment.payment_transaction_type_id == overpayment_type_id)
            .one_or_none()
        )

        # Successfully processes without error
        validate_non_standard_payment_state(
            overpayment, State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
        )
        # But no claim as no record of it in the extract file
        assert overpayment.claim_id is None
    # No PUB EFT records should exist
    assert len(local_test_db_session.query(PubEft).all()) == 0

    # Zero dollar payment should be in DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    zero_dollar_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == zero_dollar_data.i_value)
        .one_or_none()
    )
    assert zero_dollar_payment.claim_id is None
    assert zero_dollar_payment.employee_id
    validate_non_standard_payment_state(
        zero_dollar_payment, State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT
    )

    # ACH Cancellation should be in DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    cancellation_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == cancellation_data.i_value)
        .one_or_none()
    )
    assert cancellation_payment.claim_id is None
    assert cancellation_payment.employee_id
    validate_non_standard_payment_state(
        cancellation_payment, State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION
    )

    # Negative payment will cause an unknown transaction type which is restartable
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    negative_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == negative_payment_out_data.i_value)
        .one_or_none()
    )
    assert negative_payment.claim_id is None
    assert negative_payment.employee_id
    validate_non_standard_payment_state(
        negative_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    # No payment amount means the payment needs to be updated, so we error
    # the payment and add it to two states.
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    no_amount_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == no_payment_out_data.i_value)
        .one_or_none()
    )
    assert no_amount_payment.claim_id is None
    assert no_amount_payment.employee_id
    validate_non_standard_payment_state(
        no_amount_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    # No event type means the payment needs to be updated, so we error
    # the payment and add it to two states.
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT and
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    missing_event_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == missing_event_payment_out_data.i_value)
        .one_or_none()
    )
    assert missing_event_payment.claim_id is None
    assert missing_event_payment.employee_id
    validate_non_standard_payment_state(
        missing_event_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    )

    # Employer reimbursement should be in DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    employer_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == employer_reimbursement_data.i_value)
        .one_or_none()
    )
    assert employer_payment.claim_id is None
    assert employer_payment.employee_id is None  # We don't fetch the employee for employers
    validate_non_standard_payment_state(
        employer_payment, State.DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_additional_payment_types_still_require_employee(
    local_test_db_session, local_payment_extract_step
):
    # This tests that non-standard payments can be missing a claim
    # and will still be successful as long as the employee exists

    # Create a zero dollar payment
    zero_dollar_data = FineosPaymentData(payment_amount="0.00")
    add_db_records_from_fineos_data(local_test_db_session, zero_dollar_data, add_employee=False)

    stage_data([zero_dollar_data], local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    # The payment will error because the employee isn't found
    zero_dollar_payment = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == zero_dollar_data.i_value)
        .one_or_none()
    )
    assert zero_dollar_payment.claim_id
    assert zero_dollar_payment.employee_id is None
    validate_non_standard_payment_state(
        zero_dollar_payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_tax_withholding_payment_types(
    local_test_db_session, local_payment_extract_step,
):
    datasets = []

    # This tests that the behavior of tax withholding payment types are handled properly
    # All of these are setup as EFT payments, but we won't create EFT information for them
    # or reject them for not being prenoted yet.

    # Create a State Tax Withholding
    state_withholding_amount = "20.50"
    state_start = "2021-01-14 12:00:00"
    state_end = "2021-01-20 12:00:00"
    state_withholding_data = FineosPaymentData(
        event_type="PaymentOut",
        tin=extractor.STATE_TAX_WITHHOLDING_TIN,
        payment_amount=state_withholding_amount,
        payment_start=state_start,
        payment_end=state_end,
        payment_method="Elec Funds Transfer",
    )

    add_db_records_from_fineos_data(local_test_db_session, state_withholding_data, add_eft=False)
    datasets.append(state_withholding_data)

    # Create a Federal Tax Withholding
    federal_withholding_amount = "110.00"
    federal_start = "2021-01-14 12:00:00"
    federal_end = "2021-01-20 12:00:00"
    federal_withholding_data = FineosPaymentData(
        event_type="PaymentOut",
        tin=extractor.FEDERAL_TAX_WITHHOLDING_TIN,
        payment_amount=federal_withholding_amount,
        payment_start=federal_start,
        payment_end=federal_end,
        payment_method="Elec Funds Transfer",
    )

    add_db_records_from_fineos_data(local_test_db_session, federal_withholding_data, add_eft=False)
    datasets.append(federal_withholding_data)

    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    # Validate Tax Withholding, and state should be in STATE_WITHHOLDING_READY_FOR_PROCESSING
    state_withholding = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == state_withholding_data.i_value)
        .one_or_none()
    )
    validate_withholding(
        state_withholding,
        state_withholding_data,
        State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
        PaymentTransactionType.STATE_TAX_WITHHOLDING,
    )

    # Validate Tax Withholding, and state should be in FEDERAL_WITHHOLDING_READY_FOR_PROCESSING
    federal_withholding = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == federal_withholding_data.i_value)
        .one_or_none()
    )
    validate_withholding(
        federal_withholding,
        federal_withholding_data,
        State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
        PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_invalid_tax_withholding_payment_types(
    local_test_db_session, local_payment_extract_step,
):
    datasets = []

    # This tests that invalid tax withholding payment types are handled properly
    # All of these are setup as EFT payments, but we won't create EFT information for them
    # or reject them for not being prenoted yet.

    # Create a State Tax Withholding
    state_withholding_amount = None
    state_start = "2021-01-14 12:00:00"
    state_end = "2021-01-20 12:00:00"
    state_withholding_data = FineosPaymentData(
        event_type="PaymentOut",
        tin=extractor.STATE_TAX_WITHHOLDING_TIN,
        payment_amount=state_withholding_amount,
        payment_start=state_start,
        payment_end=state_end,
        payment_method="Elec Funds Transfer",
    )

    add_db_records_from_fineos_data(local_test_db_session, state_withholding_data, add_eft=False)
    datasets.append(state_withholding_data)

    stage_data(datasets, local_test_db_session)

    # Run the extract process
    local_payment_extract_step.run()

    # Validate Tax Withholding, and state should be in:
    # DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    # DELEGATED_ADD_TO_FINEOS_WRITEBACK
    state_withholding = (
        local_test_db_session.query(Payment)
        .filter(Payment.fineos_pei_i_value == state_withholding_data.i_value)
        .one_or_none()
    )
    assert len(state_withholding.state_logs) == 2
    assert set([state_log.end_state_id for state_log in state_withholding.state_logs]) == set(
        [
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id,
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id,
        ]
    )


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_extract_data_minimal_viable_withholding_payment(
    local_payment_extract_step, local_test_db_session,
):
    # Setup enough to make a tax withholding payment
    # This test creates a tax withholding with absolutely no data besides the bare
    # minimum to be viable to create a payment, this is done in order
    # to test that all of our validations work, and all of the missing data
    # edge cases are accounted for and handled appropriately.

    # C & I value are the bare minimum to have a payment
    fineos_data = FineosPaymentData(
        False,
        c_value="1000",
        i_value="1",
        event_type="PaymentOut",
        tin=extractor.STATE_TAX_WITHHOLDING_TIN,
        payment_amount="100.00",
    )
    stage_data([fineos_data], local_test_db_session)
    # We deliberately do no DB setup, there will not be any prior employee or claim
    local_payment_extract_step.run()

    payment = local_test_db_session.query(Payment).one_or_none()
    assert payment
    assert payment.vpei_id is not None
    assert payment.claim is None

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id

    assert state_log.outcome["message"] == "Error processing payment record"
    assert state_log.outcome["validation_container"]["record_key"] == "C=1000,I=1"
    # Not going to exactly match the errors here as there are many
    # and they may adjust in the future
    assert len(state_log.outcome["validation_container"]["validation_issues"]) >= 5

    # Payment is also added to the PEI writeback error flow
    validate_pei_writeback_state_for_payment(payment, local_test_db_session, is_invalid=True)


def make_payment_data_from_fineos_data(fineos_data):
    reference_file = ReferenceFileFactory.build(
        reference_file_type_id=ReferenceFileType.FINEOS_PAYMENT_EXTRACT.reference_file_type_id
    )
    import_log = ImportLogFactory.build()

    claimant_reference_file = ReferenceFileFactory.build(
        reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
    )
    claimant_import_log = ImportLogFactory.build()

    vpei_record = payments_util.create_staging_table_instance(
        fineos_data.get_vpei_record(), FineosExtractVpei, reference_file, import_log.import_log_id
    )
    payment_details_record = payments_util.create_staging_table_instance(
        fineos_data.get_payment_details_record(),
        FineosExtractVpeiPaymentDetails,
        reference_file,
        import_log.import_log_id,
    )
    claim_details_record = payments_util.create_staging_table_instance(
        fineos_data.get_claim_details_record(),
        FineosExtractVpeiClaimDetails,
        reference_file,
        import_log.import_log_id,
    )
    # The requested absence file is consumed during the claimant extract process
    requested_absence_record = payments_util.create_staging_table_instance(
        fineos_data.get_requested_absence_record(),
        FineosExtractVbiRequestedAbsence,
        claimant_reference_file,
        claimant_import_log.import_log_id,
    )

    return (
        f"C={fineos_data.c_value},I={fineos_data.i_value}",
        extractor.PaymentData(
            fineos_data.c_value,
            fineos_data.i_value,
            vpei_record,
            [payment_details_record],
            claim_details_record,
            requested_absence_record,
        ),
    )


def test_validation_missing_fields(initialize_factories_session):
    # This test is specifically aimed at verifying we check for required parameters

    # Create a fineos dataset that only contains C/I values with all other values empty
    # We want to make sure "" and Unknown are treated the same, so set a few to Unknown
    fineos_data = FineosPaymentData(
        False,
        c_value="1000",
        i_value="1",
        leave_request_id="1001",
        leave_request_decision="Unknown",
        payment_amount="Unknown",
    )
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "AMOUNT_MONAMT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "EVENTTYPE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCE_CASECREATIONDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BALANCINGAMOU_MONAMT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BUSINESSNETBE_MONAMT"),
            ValidationIssue(
                ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
                "Unknown payment scenario encountered. Payment Amount: None, Event Type: None, Event Reason: ",
            ),
        ]
    )

    assert expected_missing_values == set(validation_container.validation_issues)

    # Set the event type to PaymentOut and give it a valid amount so that
    # it expects it to be a valid payment that requires payment method and several
    # payment detail and claim detail related fields
    fineos_data.event_type = "PaymentOut"
    fineos_data.payment_amount = "100.00"
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUEST_DECISION"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTMETHOD"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCE_CASECREATIONDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BALANCINGAMOU_MONAMT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BUSINESSNETBE_MONAMT"),
        ]
    )
    assert expected_missing_values == set(validation_container.validation_issues)

    # Set the payment method to Check and verify it additionally adds errors for those missing
    fineos_data.payment_method = "Check"
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUEST_DECISION"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD1"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD4"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTADD6"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTPOSTCO"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCE_CASECREATIONDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BALANCINGAMOU_MONAMT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BUSINESSNETBE_MONAMT"),
        ]
    )
    assert expected_missing_values == set(validation_container.validation_issues)

    # Set the payment method to EFT and verify it additionally adds errors for those missing
    fineos_data.payment_method = "Elec Funds Transfer"
    ci_index, payment_data = make_payment_data_from_fineos_data(fineos_data)

    validation_container = payment_data.validation_container
    assert validation_container.record_key == str(ci_index)
    expected_missing_values = set(
        [
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCECASENU"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "LEAVEREQUEST_DECISION"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEESOCNUMBE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTSTARTP"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTENDPER"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYMENTDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEIDENTIFI"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEBANKSORT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEACCOUNTN"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "PAYEEACCOUNTT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEREASON_COVERAGE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCE_CASECREATIONDATE"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BALANCINGAMOU_MONAMT"),
            ValidationIssue(ValidationReason.MISSING_FIELD, "BUSINESSNETBE_MONAMT"),
        ]
    )

    assert expected_missing_values == set(validation_container.validation_issues)


def test_validation_param_length(initialize_factories_session, set_exporter_env_vars):
    # Create a fineos dataset that is generated with happy values, but override
    # ones we want to test the length.

    # Routing number too short
    fineos_data = FineosPaymentData(payment_method="Elec Funds Transfer", routing_nbr="123")
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYEEBANKSORT: 123"),
            ValidationIssue(ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM, "PAYEEBANKSORT: 123"),
        ]
    ) == set(payment_data.validation_container.validation_issues)

    # Routing/account number too long
    long_num = "1" * 50
    fineos_data = FineosPaymentData(
        payment_method="Elec Funds Transfer", routing_nbr=long_num, account_nbr=long_num
    )
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, f"PAYEEBANKSORT: {long_num}"),
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, f"PAYEEACCOUNTN: {long_num}"),
            ValidationIssue(
                ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM, f"PAYEEBANKSORT: {long_num}"
            ),
        ]
    ) == set(payment_data.validation_container.validation_issues)

    # ZIP too short + formatted incorrectly
    fineos_data = FineosPaymentData(payment_method="Check", zip_code="123")
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "PAYMENTPOSTCO: 123"),
            ValidationIssue(ValidationReason.INVALID_VALUE, "PAYMENTPOSTCO: 123"),
        ]
    ) == set(payment_data.validation_container.validation_issues)

    # ZIP too long + formatted incorrectly
    fineos_data = FineosPaymentData(payment_method="Check", zip_code="1234567890123456")
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_LONG, "PAYMENTPOSTCO: 1234567890123456"),
            ValidationIssue(ValidationReason.INVALID_VALUE, "PAYMENTPOSTCO: 1234567890123456"),
        ]
    ) == set(payment_data.validation_container.validation_issues)


def test_validation_lookup_validators(initialize_factories_session, set_exporter_env_vars):
    # Create a fineos dataset that is generated with happy values, but override
    # ones we want to test the lookup validators.

    # Verify payment method lookup validator
    fineos_data = FineosPaymentData(payment_method="Gold")
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYMENTMETHOD: Gold")]
    ) == set(payment_data.validation_container.validation_issues)

    # Verify account type lookup validator
    fineos_data = FineosPaymentData(payment_method="Elec Funds Transfer", account_type="Vault")
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYEEACCOUNTT: Vault")]
    ) == set(payment_data.validation_container.validation_issues)

    # Verify state lookup validator
    fineos_data = FineosPaymentData(payment_method="Check", state="NotAState")
    _, payment_data = make_payment_data_from_fineos_data(fineos_data)
    assert set(
        [ValidationIssue(ValidationReason.INVALID_LOOKUP_VALUE, "PAYMENTADD6: NotAState")]
    ) == set(payment_data.validation_container.validation_issues)


def test_validation_payment_amount(initialize_factories_session, set_exporter_env_vars):
    # When doing validation, we verify that payment amount
    # must be a numeric value
    invalid_payment_amounts = ["words", "300-00", "400.xx", "-----5"]

    for invalid_payment_amount in invalid_payment_amounts:
        fineos_data = FineosPaymentData(payment_amount=invalid_payment_amount)
        _, payment_data = make_payment_data_from_fineos_data(fineos_data)
        assert set(
            [
                ValidationIssue(
                    ValidationReason.INVALID_VALUE, f"AMOUNT_MONAMT: {invalid_payment_amount}",
                ),
                ValidationIssue(
                    ValidationReason.INVALID_VALUE,
                    f"BALANCINGAMOU_MONAMT: {invalid_payment_amount}",
                ),
                ValidationIssue(
                    ValidationReason.INVALID_VALUE,
                    f"BUSINESSNETBE_MONAMT: {invalid_payment_amount}",
                ),
                ValidationIssue(
                    ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE,
                    "Unknown payment scenario encountered. Payment Amount: None, Event Type: PaymentOut, Event Reason: Automatic Main Payment",
                ),
            ]
        ) == set(payment_data.validation_container.validation_issues)


def test_validation_zip_code(initialize_factories_session, set_exporter_env_vars):
    # When doing validation, we verify that a zip code must be
    # either ##### or #####-####
    invalid_zips = ["abcde", "1234567", "-12345", "12345-000"]

    for invalid_zip in invalid_zips:
        fineos_data = FineosPaymentData(payment_method="Check", zip_code=invalid_zip)
        _, payment_data = make_payment_data_from_fineos_data(fineos_data)
        assert set(
            [ValidationIssue(ValidationReason.INVALID_VALUE, f"PAYMENTPOSTCO: {invalid_zip}")]
        ) == set(payment_data.validation_container.validation_issues)


def test_validation_routing_number(initialize_factories_session, set_exporter_env_vars):
    # All of these routing numbers will fail the checksum validation
    # See: api/massgov/pfml/util/routing_number_validation.py for math
    invalid_routing_numbers = ["111111111", "222222222", "333333333"]
    for invalid_routing_number in invalid_routing_numbers:
        fineos_data = FineosPaymentData(
            payment_method="Elec Funds Transfer", routing_nbr=invalid_routing_number
        )
        _, payment_data = make_payment_data_from_fineos_data(fineos_data)
        assert set(
            [
                ValidationIssue(
                    ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM,
                    f"PAYEEBANKSORT: {invalid_routing_number}",
                )
            ]
        ) == set(payment_data.validation_container.validation_issues)


def test_get_payment_transaction_type(initialize_factories_session, set_exporter_env_vars):
    # get_payment_transaction_type is called as part of the constructor
    # and sets payment_transaction_type accordingly.

    # note the defaults for FineosPaymentData make a standard payment
    standard_data = FineosPaymentData()
    _, payment_data = make_payment_data_from_fineos_data(standard_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.STANDARD.payment_transaction_type_id
    )

    # Zero Dollar Payment
    zero_dollar_data = FineosPaymentData(payment_amount="0.00")
    _, payment_data = make_payment_data_from_fineos_data(zero_dollar_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
    )

    # Employer Reimbursement
    employer_reimbursement_data = FineosPaymentData(
        event_reason=extractor.AUTO_ALT_EVENT_REASON,
        event_type=extractor.PAYMENT_OUT_TRANSACTION_TYPE,
        payee_identifier=extractor.TAX_IDENTIFICATION_NUMBER,
    )
    _, payment_data = make_payment_data_from_fineos_data(employer_reimbursement_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
    )

    # There are multiple values that can create an overpayment
    for overpayment_payment_transaction_type in extractor.OVERPAYMENT_PAYMENT_TRANSACTION_TYPES:
        # Event reason is always unknown for overpayments in the real data
        overpayment_data = FineosPaymentData(
            event_type=overpayment_payment_transaction_type.payment_transaction_type_description,
            event_reason="Unknown",
        )
        _, payment_data = make_payment_data_from_fineos_data(overpayment_data)
        assert not payment_data.validation_container.has_validation_issues()
        assert (
            payment_data.payment_transaction_type.payment_transaction_type_id
            == overpayment_payment_transaction_type.payment_transaction_type_id
        )

    # Cancellation payment
    cancellation_data = FineosPaymentData(
        event_type="PaymentOut Cancellation", payment_amount="-100.00"
    )
    _, payment_data = make_payment_data_from_fineos_data(cancellation_data)
    assert not payment_data.validation_container.has_validation_issues()
    assert (
        payment_data.payment_transaction_type.payment_transaction_type_id
        == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
    )

    ### Various unknown scenarios
    # Can't be a negative payment when event_type=PaymentOut (the default)
    negative_payment_data = FineosPaymentData(payment_amount="-100.00")
    # Event type is always used if payment amount is not 0
    unknown_event_type_data = FineosPaymentData(event_type="Yet another overpayment event type")
    # A payment missing everything
    bare_minimum_payment_data = FineosPaymentData(False, c_value="1000", i_value="1")

    for unknown_data in [negative_payment_data, unknown_event_type_data, bare_minimum_payment_data]:
        _, payment_data = make_payment_data_from_fineos_data(unknown_data)
        assert payment_data.validation_container.has_validation_issues()
        assert (
            payments_util.ValidationReason.UNEXPECTED_PAYMENT_TRANSACTION_TYPE
            in payment_data.validation_container.get_reasons()
        )
        assert (
            payment_data.payment_transaction_type.payment_transaction_type_id
            == PaymentTransactionType.UNKNOWN.payment_transaction_type_id
        )


@pytest.mark.parametrize(
    "prenote_state",
    [(PrenoteState.REJECTED), (PrenoteState.PENDING_PRE_PUB), (PrenoteState.PENDING_WITH_PUB)],
)
@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_eft_existing_eft_matches_and_not_approved(
    local_payment_extract_step, local_test_db_session, prenote_state,
):
    # This is the happiest of paths, we've already got the EFT info for the
    # employee and it has already been prenoted.
    payment_data_eft = FineosPaymentData()
    add_db_records_from_fineos_data(
        local_test_db_session, payment_data_eft, prenote_state=prenote_state
    )
    stage_data([payment_data_eft], local_test_db_session)

    # Run the process
    local_payment_extract_step.run()

    # Verify the payment isn't marked as having an EFT update
    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data_eft.c_value,
            Payment.fineos_pei_i_value == payment_data_eft.i_value,
        )
        .first()
    )
    assert payment is not None
    assert payment.has_eft_update is False
    # The payment should still be connected to the EFT record
    assert payment.pub_eft
    assert str(payment.pub_eft.routing_nbr) == payment_data_eft.routing_nbr
    assert str(payment.pub_eft.account_nbr) == payment_data_eft.account_nbr
    assert payment.pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id

    state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )

    # Pending prenotes get put into a restartable error state
    if prenote_state.prenote_state_id in [
        PrenoteState.PENDING_PRE_PUB.prenote_state_id,
        PrenoteState.PENDING_WITH_PUB.prenote_state_id,
    ]:
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_id
        )
    else:
        assert (
            state_log.end_state_id == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
        )
    issues = state_log.outcome["validation_container"]["validation_issues"]
    assert len(issues) == 1
    assert (
        issues[0]["details"]
        == f"EFT prenote has not been approved, is currently in state [{prenote_state.prenote_state_description}]"
    )

    # Payment is also added to the PEI writeback error flow
    validate_pei_writeback_state_for_payment(
        payment,
        local_test_db_session,
        is_rejected_prenote=prenote_state.prenote_state_id
        == PrenoteState.REJECTED.prenote_state_id,
        is_pending_prenote=prenote_state.prenote_state_id
        in [
            PrenoteState.PENDING_PRE_PUB.prenote_state_id,
            PrenoteState.PENDING_WITH_PUB.prenote_state_id,
        ],
    )

    # There should not be a DELEGATED_EFT_SEND_PRENOTE record
    assert len(payment.claim.employee.state_logs) == 0


@freeze_time("2021-01-13 11:12:12", tz_offset=5)  # payments_util.get_now returns EST time
def test_update_experian_address_pair_fineos_address_no_update(
    local_payment_extract_step, local_test_db_session,
):
    # update_experian_address_pair_fineos_address() has 2 possible outcomes:
    #   1. There is no change to address
    #   2. We create a new ExperianAddressPair
    # In this test, we cover #1. #2 is covered by other tests.
    payment_data_check = FineosPaymentData(payment_method="Check")
    add_db_records_from_fineos_data(local_test_db_session, payment_data_check)
    stage_data([payment_data_check], local_test_db_session)

    # Set an employee to have the same address we know is going to be extracted
    employee = (
        local_test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == payment_data_check.tin)
        .first()
    )
    assert employee is not None

    # Add the expected address to another payment associated with the employee
    address_pair = ExperianAddressPairFactory(
        fineos_address=AddressFactory.create(
            address_line_one=payment_data_check.payment_address_1,
            address_line_two=payment_data_check.payment_address_2,
            city=payment_data_check.city,
            geo_state_id=GeoState.get_id(payment_data_check.state),
            zip_code=payment_data_check.zip_code,
        )
    )

    payment = DelegatedPaymentFactory(
        local_test_db_session, employee=employee, experian_address_pair=address_pair
    ).get_or_create_payment()

    # Run the process
    local_payment_extract_step.run()
    local_test_db_session.expire_all()

    # Verify the payment isn't marked as having an address update
    payment = (
        local_test_db_session.query(Payment)
        .filter(
            Payment.fineos_pei_c_value == payment_data_check.c_value,
            Payment.fineos_pei_i_value == payment_data_check.i_value,
        )
        .first()
    )
    assert payment is not None
    assert payment.has_address_update is False
    assert payment.experian_address_pair_id == address_pair.fineos_address_id


def test_get_active_payment_state(payment_extract_step, test_db_session):
    non_restartable_states = [
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
    ]
    restartable_states = payments_util.Constants.RESTARTABLE_PAYMENT_STATES

    # Non restartable states should return the state.
    for non_restartable_state in non_restartable_states:
        # Create and load a payment in the non restartable state.
        payment = DelegatedPaymentFactory(
            test_db_session, payment_end_state_message=EXPECTED_OUTCOME["message"]
        ).get_or_create_payment_with_state(non_restartable_state)

        # Create a payment with the same C/I value
        new_payment = PaymentFactory.build(
            fineos_pei_c_value=payment.fineos_pei_c_value,
            fineos_pei_i_value=payment.fineos_pei_i_value,
        )

        # We should find that state associated with the payment
        found_state = payment_extract_step.get_active_payment_state(new_payment)
        assert found_state
        assert found_state.state_id == non_restartable_state.state_id

    for restartable_state in restartable_states:
        # Create and load a payment in the restartable state.
        payment = DelegatedPaymentFactory(
            test_db_session, payment_end_state_message=EXPECTED_OUTCOME["message"]
        ).get_or_create_payment_with_state(restartable_state)

        # Create a payment with the same C/I value
        new_payment = PaymentFactory.build(
            fineos_pei_c_value=payment.fineos_pei_c_value,
            fineos_pei_i_value=payment.fineos_pei_i_value,
        )
        # We should not find anything
        found_state = payment_extract_step.get_active_payment_state(new_payment)
        assert found_state is None

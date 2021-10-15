import copy
import json
from typing import Optional

import pytest

import massgov.pfml.delegated_payments.delegated_fineos_claimant_extract as claimant_extract
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    ImportLog,
    PrenoteState,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    ImportLogFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVbiRequestedAbsenceSom,
)
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationIssue,
    ValidationReason,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.mock.fineos_extract_data import FineosClaimantData
from massgov.pfml.util import datetime


@pytest.fixture
def claimant_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return claimant_extract.ClaimantExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def local_claimant_extract_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return claimant_extract.ClaimantExtractStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def add_db_records_from_fineos_data(
    db_session,
    fineos_data,
    add_employee=True,
    add_employer=True,
    add_eft=True,
    add_claim=False,  # By default, we want to make it in the tests
    prenote_state=PrenoteState.APPROVED,
    **kwargs,
):
    """
    Wrapper method for the delegated payment factory to assist
    with some defaults specific to the claimant extract tests
    """

    # The factory doesn't yet make the employer, so do it here
    employer = None
    if add_employer:
        employer = EmployerFactory(fineos_employer_id=fineos_data.employer_customer_num)

    factory = DelegatedPaymentFactory(
        db_session,
        ssn=fineos_data.ssn,
        add_employee=add_employee,
        add_employer=add_employer,
        employer=employer,
        add_pub_eft=add_eft,
        prenote_state=prenote_state,
        prenote_response_at=datetime.datetime(2020, 12, 6, 12, 0, 0),
        routing_nbr=fineos_data.routing_nbr,
        account_nbr=fineos_data.account_nbr,
        fineos_absence_id=fineos_data.absence_case_number,
        add_claim=add_claim,
        add_payment=False,  # Don't bother, not needed for this test
        **kwargs,
    )
    factory.create_all()  # EFT/claim/employee

    return factory.employee, factory.claim


def stage_data(
    records,
    db_session,
    reference_file=None,
    import_log=None,
    additional_requested_absence_som_records=None,
    additional_employee_feed_records=None,
):
    if not reference_file:
        reference_file = ReferenceFileFactory.create(
            reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id
        )
    if not import_log:
        import_log = ImportLogFactory.create()

    for record in records:
        instance = payments_util.create_staging_table_instance(
            record.get_requested_absence_record(),
            FineosExtractVbiRequestedAbsenceSom,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)
        instance = payments_util.create_staging_table_instance(
            record.get_employee_feed_record(),
            FineosExtractEmployeeFeed,
            reference_file,
            import_log.import_log_id,
        )
        db_session.add(instance)

    if additional_requested_absence_som_records:
        for requested_absence_som_record in additional_requested_absence_som_records:
            instance = payments_util.create_staging_table_instance(
                requested_absence_som_record.get_requested_absence_record(),
                FineosExtractVbiRequestedAbsenceSom,
                reference_file,
                import_log.import_log_id,
            )
            db_session.add(instance)

    if additional_employee_feed_records:
        for employee_feed_record in additional_employee_feed_records:
            instance = payments_util.create_staging_table_instance(
                employee_feed_record.get_employee_feed_record(),
                FineosExtractEmployeeFeed,
                reference_file,
                import_log.import_log_id,
            )
            db_session.add(instance)

    db_session.commit()


def test_run_step_happy_path(
    local_claimant_extract_step, local_test_db_session,
):

    claimant_data = FineosClaimantData()
    employee, _ = add_db_records_from_fineos_data(
        local_test_db_session,
        claimant_data,
        add_eft=False,
        fineos_employee_first_name="Original-FINEOS-First",
        fineos_employee_last_name="Original-FINEOS-Last",
    )

    stage_data([claimant_data], local_test_db_session)

    local_claimant_extract_step.run()

    claim = (
        local_test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == claimant_data.absence_case_number)
        .first()
    )

    assert claim is not None
    assert claim.employee_id == employee.employee_id

    assert claim.fineos_notification_id == claimant_data.notification_number
    assert claim.fineos_absence_status_id == AbsenceStatus.APPROVED.absence_status_id
    assert claim.absence_period_start_date == payments_util.datetime_str_to_date(
        claimant_data.leave_request_start
    )
    assert claim.absence_period_end_date == payments_util.datetime_str_to_date(
        claimant_data.leave_request_end
    )
    assert claim.is_id_proofed is True
    assert claim.employer.fineos_employer_id == int(claimant_data.employer_customer_num)

    updated_employee = (
        local_test_db_session.query(Employee)
        .filter(Employee.fineos_customer_number == claimant_data.customer_number)
        .one_or_none()
    )

    assert updated_employee is not None
    # We are not updating first or last name with FINEOS data as DOR is source of truth.
    assert updated_employee.first_name == employee.first_name
    assert updated_employee.last_name == employee.last_name
    # Make sure we have captured the claimant name in fineos specific employee columns (initial fineos names from above overwritten)
    assert updated_employee.fineos_employee_first_name == claimant_data.fineos_employee_first_name
    assert updated_employee.fineos_employee_last_name == claimant_data.fineos_employee_last_name
    assert updated_employee.date_of_birth == datetime.date(1980, 1, 1)
    assert updated_employee.fineos_customer_number is not None

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == claimant_data.routing_nbr
    assert pub_efts[0].pub_eft.account_nbr == claimant_data.account_nbr
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id

    # Make sure we have captured the claimant name in pub_eft
    assert (
        pub_efts[0].pub_eft.fineos_employee_first_name == claimant_data.fineos_employee_first_name
    )
    assert pub_efts[0].pub_eft.fineos_employee_last_name == claimant_data.fineos_employee_last_name

    # Confirm StateLogs
    eft_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.DELEGATED_EFT_SEND_PRENOTE,
        db_session=local_test_db_session,
    )
    assert len(eft_state_logs) == 1
    assert eft_state_logs[0].import_log_id == local_claimant_extract_step.get_import_log_id()

    claim_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.CLAIM,
        end_state=State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
        db_session=local_test_db_session,
    )
    assert len(claim_state_logs) == 1
    assert claim_state_logs[0].import_log_id == local_claimant_extract_step.get_import_log_id()
    assert claim_state_logs[0].claim_id == claim.claim_id

    # Confirm metrics added to import log
    import_log = (
        local_test_db_session.query(ImportLog)
        .filter(ImportLog.import_log_id == local_claimant_extract_step.get_import_log_id())
        .first()
    )
    import_log_report = json.loads(import_log.report)
    assert import_log_report["valid_claim_count"] == 1


def test_run_step_existing_approved_eft_info(
    local_claimant_extract_step, local_test_db_session,
):
    # Very similar to the happy path test, but EFT info has already been
    # previously approved and we do not need to start the prenoting process

    claimant_data = FineosClaimantData()
    add_db_records_from_fineos_data(
        local_test_db_session, claimant_data, prenote_state=PrenoteState.APPROVED
    )
    stage_data([claimant_data], local_test_db_session)

    local_claimant_extract_step.run()

    updated_employee = (
        local_test_db_session.query(Employee)
        .filter(Employee.fineos_customer_number == claimant_data.customer_number)
        .one_or_none()
    )

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == claimant_data.routing_nbr
    assert pub_efts[0].pub_eft.account_nbr == claimant_data.account_nbr
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.APPROVED.prenote_state_id

    # We should not have added it to the EFT state flow
    # and there shouldn't have been any errors
    eft_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.DELEGATED_EFT_SEND_PRENOTE,
        db_session=local_test_db_session,
    )
    assert len(eft_state_logs) == 0

    claim_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.CLAIM,
        end_state=State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
        db_session=local_test_db_session,
    )
    assert len(claim_state_logs) == 1
    assert claim_state_logs[0].import_log_id == local_claimant_extract_step.get_import_log_id()
    assert claim_state_logs[0].claim.employee_id == updated_employee.employee_id


def test_run_step_existing_rejected_eft_info(
    local_claimant_extract_step, local_test_db_session,
):
    # Very similar to the happy path test, but EFT info has already been
    # previously rejected and thus it goes into an error state instead

    claimant_data = FineosClaimantData()
    add_db_records_from_fineos_data(
        local_test_db_session, claimant_data, prenote_state=PrenoteState.REJECTED
    )
    stage_data([claimant_data], local_test_db_session)

    local_claimant_extract_step.run()

    updated_employee = (
        local_test_db_session.query(Employee)
        .filter(Employee.fineos_customer_number == claimant_data.customer_number)
        .one_or_none()
    )

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == claimant_data.routing_nbr
    assert pub_efts[0].pub_eft.account_nbr == claimant_data.account_nbr
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id

    # We should not have added it to the EFT state flow
    eft_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.DELEGATED_EFT_SEND_PRENOTE,
        db_session=local_test_db_session,
    )
    assert len(eft_state_logs) == 0

    # and there would have been a single error on the claims state log
    claim_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.CLAIM,
        end_state=State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT,
        db_session=local_test_db_session,
    )
    assert len(claim_state_logs) == 1
    assert claim_state_logs[0].import_log_id == local_claimant_extract_step.get_import_log_id()
    assert claim_state_logs[0].claim.employee_id == updated_employee.employee_id
    claim = claim_state_logs[0].claim
    assert len(claim.state_logs) == 1
    assert claim.state_logs[0].outcome["validation_container"]["validation_issues"] == [
        {
            "reason": "EFTRejected",
            "details": "EFT prenote was rejected - cannot pay with this account info",
        }
    ]


def test_run_step_no_employee(
    local_claimant_extract_step, local_test_db_session,
):
    claimant_data = FineosClaimantData()
    stage_data([claimant_data], local_test_db_session)

    local_claimant_extract_step.run()

    claim: Optional[Claim] = (
        local_test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == claimant_data.absence_case_number)
        .one_or_none()
    )

    # Claim still gets created even if employee doesn't exist
    assert claim
    assert claim.employee_id is None

    assert len(claim.state_logs) == 1
    assert claim.state_logs[0].outcome["validation_container"]["validation_issues"] == [
        {"reason": "MissingInDB", "details": f"tax_identifier: {claimant_data.ssn}"},
        {
            "reason": "MissingInDB",
            "details": f"employer customer number: {claimant_data.employer_customer_num}",
        },
    ]


def format_claimant_data() -> FineosClaimantData:
    return FineosClaimantData(
        absence_case_number="NTN-001-ABS-01",
        notification_number="NTN-001",
        absence_case_status="Adjudication",
        leave_request_start="2021-02-14",
        leave_request_end="2021-02-28",
        leave_type="Family",
        leave_request_evidence="Satisfied",
        customer_number="12345",
        ssn="123456789",
        date_of_birth="1967-04-27",
        payment_method="Elec Funds Transfer",
        routing_nbr="111111118",
        account_nbr="123456789",
        account_type="Checking",
    )


@pytest.fixture
def formatted_claim(initialize_factories_session) -> Claim:
    employer = EmployerFactory()
    claim = ClaimFactory(
        fineos_notification_id="NTN-001",
        fineos_absence_id="NTN-001-ABS-01",
        employer_id=employer.employer_id,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
        absence_period_start_date=datetime.date(2021, 2, 10),
        absence_period_end_date=datetime.date(2021, 2, 16),
    )

    return claim


def make_claimant_data_from_fineos_data(fineos_data):
    reference_file = ReferenceFileFactory.build()
    requested_absence = payments_util.create_staging_table_instance(
        fineos_data.get_requested_absence_record(),
        FineosExtractVbiRequestedAbsenceSom,
        reference_file,
        None,
    )
    employee_feed = payments_util.create_staging_table_instance(
        fineos_data.get_employee_feed_record(), FineosExtractEmployeeFeed, reference_file, None
    )

    return claimant_extract.ClaimantData(
        fineos_data.absence_case_number, [requested_absence], [employee_feed]
    )


def make_claimant_data_with_incorrect_request_absence(fineos_data):
    # This method guarantees the request absence fields ABSENCEPERIOD_CLASSID, ABSENCEPERIOD_INDEXID are set to Unknown
    reference_file = ReferenceFileFactory.build()

    raw_requested_absence = fineos_data.get_requested_absence_record()
    raw_requested_absence["ABSENCEPERIOD_CLASSID"] = "Unknown"
    raw_requested_absence["ABSENCEPERIOD_INDEXID"] = "Unknown"
    requested_absence = payments_util.create_staging_table_instance(
        raw_requested_absence, FineosExtractVbiRequestedAbsenceSom, reference_file, None,
    )
    employee_feed = payments_util.create_staging_table_instance(
        fineos_data.get_employee_feed_record(), FineosExtractEmployeeFeed, reference_file, None
    )

    return claimant_extract.ClaimantData(
        fineos_data.absence_case_number, [requested_absence], [employee_feed]
    )


def test_create_or_update_claim_happy_path_new_claim(claimant_extract_step, test_db_session):
    # Create claimant data, and make sure there aren't any initial validation issues
    claimant_data = make_claimant_data_from_fineos_data(format_claimant_data())
    assert len(claimant_data.validation_container.validation_issues) == 0

    claim = claimant_extract_step.create_or_update_claim(claimant_data)

    assert claim is not None
    # New claim not yet persisted to DB
    assert claim.fineos_notification_id == "NTN-001"
    assert claim.fineos_absence_id == "NTN-001-ABS-01"
    assert claim.fineos_absence_status_id == AbsenceStatus.ADJUDICATION.absence_status_id
    assert claim.absence_period_start_date == datetime.date(2021, 2, 14)
    assert claim.absence_period_end_date == datetime.date(2021, 2, 28)
    assert claim.is_id_proofed is True


def test_create_or_update_claim_happy_path_update_claim(claimant_extract_step, formatted_claim):
    # Create claimant data, and make sure there aren't any initial validation issues
    claimant_data = make_claimant_data_from_fineos_data(format_claimant_data())
    assert len(claimant_data.validation_container.validation_issues) == 0

    claim = claimant_extract_step.create_or_update_claim(claimant_data)

    assert claim is not None
    # Existing claim, check claim_id
    assert claim.claim_id == formatted_claim.claim_id
    assert claim.fineos_notification_id == "NTN-001"
    assert claim.fineos_absence_id == "NTN-001-ABS-01"
    assert claim.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id
    assert claim.fineos_absence_status_id == AbsenceStatus.ADJUDICATION.absence_status_id
    assert claim.absence_period_start_date == datetime.date(2021, 2, 14)
    assert claim.absence_period_end_date == datetime.date(2021, 2, 28)
    assert claim.is_id_proofed is True


def test_create_or_update_claim_invalid_values(claimant_extract_step):
    # Create claimant data with just an absence case number
    fineos_data = FineosClaimantData(generate_defaults=False, absence_case_number="NTN-001-ABS-01")
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    # The number of required fields we pull out of the requested absence file
    assert len(set(claimant_data.validation_container.validation_issues)) == 10

    # The claim will be created, but with just an absence case number
    claim = claimant_extract_step.create_or_update_claim(claimant_data)
    assert claim is not None
    # New claim not yet persisted to DB
    assert claim.fineos_notification_id is None
    assert claim.fineos_absence_id == "NTN-001-ABS-01"
    assert claim.fineos_absence_status_id is None
    assert claim.absence_period_start_date is None
    assert claim.absence_period_end_date is None
    assert not claim.is_id_proofed


def test_create_or_update_absence_period_happy_path(claimant_extract_step, test_db_session):
    # Create claimant data, and make sure there aren't any initial validation issues
    formatted_claimant_data = FineosClaimantData(
        absence_case_number="ABS_001",
        leave_request_start="2021-02-14",
        leave_request_end="2021-02-28",
        leave_request_id=5,
        leave_request_evidence="Satisfied",
        absence_period_c_value=1448,
        absence_period_i_value=1,
    )
    claimant_data = make_claimant_data_from_fineos_data(formatted_claimant_data)
    assert len(claimant_data.validation_container.validation_issues) == 0

    absence_period_data = claimant_data.absence_period_data
    assert len(absence_period_data) == 1

    absence_period_info = absence_period_data[0]

    claim = claimant_extract_step.create_or_update_claim(claimant_data)
    absence_period = claimant_extract_step.create_or_update_absence_period(
        absence_period_info, claim, claimant_data
    )

    assert claim is not None
    assert absence_period is not None

    assert absence_period.claim_id == claim.claim_id
    assert absence_period.fineos_absence_period_class_id == 1448
    assert absence_period.fineos_absence_period_index_id == 1
    assert absence_period.is_id_proofed is True
    assert absence_period.absence_period_start_date == datetime.date(2021, 2, 14)
    assert absence_period.absence_period_end_date == datetime.date(2021, 2, 28)
    assert absence_period.fineos_leave_request_id == 5

    # Create new claimant data to update existing absence_period. We make sure the claim and claimant_data's
    # absence_period_c_value and absence_period_i_value remain unchanged.
    new_formatted_claimant_data = FineosClaimantData(
        absence_case_number="ABS_001",
        leave_request_start="2021-03-07",
        leave_request_end="2021-12-11",
        leave_request_id=2,
        leave_request_evidence="UnSatisfied",
        absence_period_c_value=1448,
        absence_period_i_value=1,
    )

    new_claimant_data = make_claimant_data_from_fineos_data(new_formatted_claimant_data)
    assert len(new_claimant_data.validation_container.validation_issues) == 0

    new_absence_period_data = new_claimant_data.absence_period_data

    assert len(new_absence_period_data) == 1

    new_absence_period_info = new_absence_period_data[0]
    absence_period = claimant_extract_step.create_or_update_absence_period(
        new_absence_period_info, claim, new_claimant_data
    )

    assert absence_period is not None

    assert absence_period.claim_id == claim.claim_id
    assert absence_period.fineos_absence_period_class_id == 1448
    assert absence_period.fineos_absence_period_index_id == 1
    assert absence_period.is_id_proofed is False
    assert absence_period.absence_period_start_date == datetime.date(2021, 3, 7)
    assert absence_period.absence_period_end_date == datetime.date(2021, 12, 11)
    assert absence_period.fineos_leave_request_id == 2


def test_create_or_update_absence_period_invalid_values(claimant_extract_step, test_db_session):
    # Create claimant data with just an absence case number
    fineos_data = FineosClaimantData(
        generate_defaults=False,
        absence_case_number="NTN-001-ABS-01",
        absence_period_c_value=1010,
        absence_period_i_value=201,
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    # The number of required fields we pull out of the requested absence file
    assert len(set(claimant_data.validation_container.validation_issues)) == 8

    # The claim will be created, but with just an absence case number
    absence_period_data = claimant_data.absence_period_data
    assert len(absence_period_data) == 1

    absence_period_info = absence_period_data[0]

    claim = claimant_extract_step.create_or_update_claim(claimant_data)
    absence_period = claimant_extract_step.create_or_update_absence_period(
        absence_period_info, claim, claimant_data
    )

    assert claim is not None
    assert absence_period is not None

    assert absence_period.claim_id == claim.claim_id
    assert absence_period.fineos_absence_period_class_id == 1010
    assert absence_period.fineos_absence_period_index_id == 201
    assert absence_period.is_id_proofed is None
    assert absence_period.absence_period_start_date is None
    assert absence_period.absence_period_end_date is None
    assert absence_period.fineos_leave_request_id is None


def test_update_absence_period_with_mismatching_claim_id(claimant_extract_step, test_db_session):
    # We test if an absence period with matching absence_period.(class_id, index_id) has a mis-match on
    # absence_period.claim_id and claim.claim_id

    # Create claimant data with just an absence case number
    formatted_claimant_data_1 = FineosClaimantData(
        absence_case_number="NTN-001-ABS-01", absence_period_c_value=1448, absence_period_i_value=1,
    )

    claimant_data_1 = make_claimant_data_from_fineos_data(formatted_claimant_data_1)
    assert len(claimant_data_1.validation_container.validation_issues) == 0

    # The claim will be created, but with just an absence case number
    absence_period_data = claimant_data_1.absence_period_data
    assert len(absence_period_data) == 1

    absence_period_info_1 = absence_period_data[0]

    claim_1 = claimant_extract_step.create_or_update_claim(claimant_data_1)
    absence_period_1 = claimant_extract_step.create_or_update_absence_period(
        absence_period_info_1, claim_1, claimant_data_1
    )

    assert claim_1 is not None
    assert absence_period_1 is not None

    formatted_claimant_data_2 = FineosClaimantData(
        absence_case_number="NTN-001-ABS-02", absence_period_c_value=1448, absence_period_i_value=1,
    )

    claimant_data_2 = make_claimant_data_from_fineos_data(formatted_claimant_data_2)
    assert len(claimant_data_2.validation_container.validation_issues) == 0

    # The claim will be created, but with just an absence case number
    absence_period_data = claimant_data_2.absence_period_data
    assert len(absence_period_data) == 1

    absence_period_info_2 = absence_period_data[0]

    claim_2 = claimant_extract_step.create_or_update_claim(claimant_data_2)
    absence_period_2 = claimant_extract_step.create_or_update_absence_period(
        absence_period_info_2, claim_2, claimant_data_2
    )

    assert claim_2 is not None
    assert absence_period_2 is None
    assert len(claimant_data_2.validation_container.validation_issues) == 1

    validation_issue = claimant_data_2.validation_container.validation_issues[0]

    assert validation_issue.reason == ValidationReason.CLAIMANT_MISMATCH


def test_create_or_update_absence_period_with_incomplete_request_absence_data(
    claimant_extract_step, test_db_session
):
    # Create claimant data, with request absence fields ABSENCEPERIOD_CLASSID, ABSENCEPERIOD_INDEXID as Unknown
    formatted_claimant_data = FineosClaimantData(
        leave_request_start="2021-02-14",
        leave_request_end="2021-02-28",
        leave_request_id=5,
        leave_request_evidence="UnSatisfied",
    )
    claimant_data = make_claimant_data_with_incorrect_request_absence(formatted_claimant_data)
    assert len(claimant_data.validation_container.validation_issues) == 2

    assert claimant_data.validation_container.validation_issues == [
        ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEPERIOD_CLASSID"),
        ValidationIssue(ValidationReason.MISSING_FIELD, "ABSENCEPERIOD_INDEXID"),
    ]

    absence_period_data = claimant_data.absence_period_data
    assert len(absence_period_data) == 0


def test_create_or_update_absence_period_with_duplicated_rows_but_different_id_proofing(
    claimant_extract_step, test_db_session
):
    # Create two exact claimant data, except leave_request_evidence as Satisfied for one and empty string for other
    formatted_claimant_data_1 = FineosClaimantData(
        absence_case_number="ABS_001",
        leave_request_start="2021-02-14",
        leave_request_end="2021-02-28",
        leave_request_id=5,
        leave_request_evidence=" ",
        absence_period_c_value=1448,
        absence_period_i_value=1,
    )

    claimant_data_1 = make_claimant_data_from_fineos_data(formatted_claimant_data_1)
    assert len(claimant_data_1.validation_container.validation_issues) == 0

    absence_period_data = claimant_data_1.absence_period_data
    assert len(absence_period_data) == 1

    absence_period_info = absence_period_data[0]

    claim = claimant_extract_step.create_or_update_claim(claimant_data_1)
    absence_period = claimant_extract_step.create_or_update_absence_period(
        absence_period_info, claim, claimant_data_1
    )

    assert claim is not None
    assert absence_period is not None

    assert absence_period.claim_id == claim.claim_id
    assert absence_period.fineos_absence_period_class_id == 1448
    assert absence_period.fineos_absence_period_index_id == 1
    assert absence_period.is_id_proofed is None
    assert absence_period.absence_period_start_date == datetime.date(2021, 2, 14)
    assert absence_period.absence_period_end_date == datetime.date(2021, 2, 28)
    assert absence_period.fineos_leave_request_id == 5

    formatted_claimant_data_2 = FineosClaimantData(
        absence_case_number="ABS_001",
        leave_request_start="2021-02-14",
        leave_request_end="2021-02-28",
        leave_request_id=5,
        leave_request_evidence="Satisfied",
        absence_period_c_value=1448,
        absence_period_i_value=1,
    )
    claimant_data_2 = make_claimant_data_from_fineos_data(formatted_claimant_data_2)
    assert len(claimant_data_2.validation_container.validation_issues) == 0

    absence_period_data = claimant_data_2.absence_period_data
    assert len(absence_period_data) == 1

    absence_period_info = absence_period_data[0]

    claim = claimant_extract_step.create_or_update_claim(claimant_data_2)
    absence_period = claimant_extract_step.create_or_update_absence_period(
        absence_period_info, claim, claimant_data_2
    )

    assert claim is not None
    assert absence_period is not None

    assert absence_period.claim_id == claim.claim_id
    assert absence_period.fineos_absence_period_class_id == 1448
    assert absence_period.fineos_absence_period_index_id == 1
    assert absence_period.is_id_proofed is True
    assert absence_period.absence_period_start_date == datetime.date(2021, 2, 14)
    assert absence_period.absence_period_end_date == datetime.date(2021, 2, 28)
    assert absence_period.fineos_leave_request_id == 5


def test_update_employee_info_happy_path(claimant_extract_step, test_db_session, formatted_claim):
    claimant_data = make_claimant_data_from_fineos_data(format_claimant_data())

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    employee = claimant_extract_step.update_employee_info(claimant_data, formatted_claim)

    assert len(claimant_data.validation_container.validation_issues) == 0
    assert employee is not None
    assert employee.date_of_birth == datetime.date(1967, 4, 27)


def test_update_employee_info_not_in_db(claimant_extract_step, formatted_claim):
    claimant_data = make_claimant_data_from_fineos_data(format_claimant_data())

    tax_identifier = TaxIdentifierFactory(tax_identifier="987654321")
    EmployeeFactory(tax_identifier=tax_identifier)

    employee = claimant_extract_step.update_employee_info(claimant_data, formatted_claim)

    assert employee is None


def test_update_eft_info_happy_path(claimant_extract_step, test_db_session):
    fineos_data = FineosClaimantData(
        routing_nbr="111111118", account_nbr="123456789", account_type="Checking"
    )
    employee, _ = add_db_records_from_fineos_data(test_db_session, fineos_data, add_eft=False)
    assert len(employee.pub_efts.all()) == 0

    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    claimant_extract_step.update_eft_info(claimant_data, employee)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "111111118"
    assert pub_efts[0].pub_eft.account_nbr == "123456789"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id


def test_update_eft_info_validation_issues(claimant_extract_step, test_db_session):
    # Routing number doesn't pass checksum, but is correct length
    fineos_data = FineosClaimantData(
        routing_nbr="111111111", account_nbr="123456789", account_type="Checking"
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)
    employee, _ = add_db_records_from_fineos_data(test_db_session, fineos_data, add_eft=False)
    assert len(employee.pub_efts.all()) == 0

    claimant_extract_step.update_eft_info(claimant_data, employee)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert set(
        [ValidationIssue(ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM, "SORTCODE: 111111111")]
    ) == set(claimant_data.validation_container.validation_issues)

    # Routing number incorrect length.
    fineos_data = FineosClaimantData(
        routing_nbr="123", account_nbr="123456789", account_type="Checking"
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    claimant_extract_step.update_eft_info(claimant_data, employee)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "SORTCODE: 123"),
            ValidationIssue(ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM, "SORTCODE: 123"),
        ]
    ) == set(claimant_data.validation_container.validation_issues)

    # Account number incorrect length.
    long_num = "123456789012345678"
    fineos_data = FineosClaimantData(
        routing_nbr="111111118", account_nbr=long_num, account_type="Checking",
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    claimant_extract_step.update_eft_info(claimant_data, employee)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert set(
        [ValidationIssue(ValidationReason.FIELD_TOO_LONG, f"ACCOUNTNO: {long_num}"),]
    ) == set(claimant_data.validation_container.validation_issues)
    assert len(updated_employee.pub_efts.all()) == 0

    # Account type incorrect.
    fineos_data = FineosClaimantData(
        routing_nbr="111111118",
        account_nbr="12345678901234567",
        account_type="Certificate of Deposit",
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    claimant_extract_step.update_eft_info(claimant_data, employee)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert set(
        [
            ValidationIssue(
                ValidationReason.INVALID_LOOKUP_VALUE, "ACCOUNTTYPE: Certificate of Deposit"
            )
        ]
    ) == set(claimant_data.validation_container.validation_issues)
    assert len(updated_employee.pub_efts.all()) == 0

    # Account type and Routing number incorrect.
    fineos_data = FineosClaimantData(
        routing_nbr="12345678",
        account_nbr="12345678901234567",
        account_type="Certificate of Deposit",
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

    claimant_extract_step.update_eft_info(claimant_data, employee)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert set(
        [
            ValidationIssue(ValidationReason.FIELD_TOO_SHORT, "SORTCODE: 12345678"),
            ValidationIssue(ValidationReason.ROUTING_NUMBER_FAILS_CHECKSUM, "SORTCODE: 12345678"),
            ValidationIssue(
                ValidationReason.INVALID_LOOKUP_VALUE, "ACCOUNTTYPE: Certificate of Deposit"
            ),
        ]
    ) == set(claimant_data.validation_container.validation_issues)
    assert len(updated_employee.pub_efts.all()) == 0


def test_run_step_validation_issues(
    claimant_extract_step, test_db_session, formatted_claim,
):
    # Create some validation issues
    fineos_data = FineosClaimantData(
        routing_nbr="",
        leave_request_end="",
        date_of_birth="",
        fineos_employee_first_name="",
        fineos_employee_last_name="",
    )

    employee_before, _ = add_db_records_from_fineos_data(
        test_db_session, fineos_data, add_eft=False
    )

    stage_data([fineos_data], test_db_session)

    # Run the process
    claimant_extract_step.run_step()

    # Verify the Employee was still updated with valid fields
    employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_before.employee_id)
        .one_or_none()
    )
    assert employee
    assert employee.fineos_customer_number == fineos_data.customer_number
    assert employee.date_of_birth == employee_before.date_of_birth

    # Because one piece of EFT info was invalid, we did not create it
    assert len(employee.pub_efts.all()) == 0

    # Verify the claim was still created despite an invalid field (that isn't set)
    assert len(employee.claims) == 1
    claim = employee.claims[0]
    assert claim.fineos_absence_id == fineos_data.absence_case_number
    assert claim.employee_id == employee.employee_id
    assert claim.fineos_notification_id == fineos_data.notification_number
    assert (
        claim.claim_type_id
        == payments_util.get_mapped_claim_type(fineos_data.leave_type).claim_type_id
    )
    assert claim.fineos_absence_status_id == AbsenceStatus.get_id(fineos_data.absence_case_status)
    assert claim.absence_period_start_date is not None
    assert claim.absence_period_end_date is None  # Due to being empty
    assert claim.is_id_proofed
    assert claim.employer.fineos_employer_id == int(fineos_data.employer_customer_num)

    # Verify the state logs and outcome
    assert len(claim.state_logs) == 1
    state_log = claim.state_logs[0]
    assert (
        state_log.end_state_id == State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT.state_id
    )
    validation_issues = state_log.outcome["validation_container"]["validation_issues"]
    assert validation_issues == [
        {"reason": "MissingField", "details": "ABSENCEPERIOD_END"},
        {
            "reason": "MissingField",
            "details": "ABSENCEPERIOD_END",
        },  # ABSENCEPERIOD_END is processed twice
        {"reason": "MissingField", "details": "DATEOFBIRTH"},
        {"reason": "MissingField", "details": "FIRSTNAMES"},
        {"reason": "MissingField", "details": "LASTNAME"},
        {"reason": "MissingField", "details": "SORTCODE"},
    ]


def test_run_step_minimal_viable_claim(
    claimant_extract_step, test_db_session,
):
    # Create a record with only an absence case number
    # This should still end up created in the DB, but with
    # significant validation issues
    fineos_data = FineosClaimantData(
        False, include_employee_feed=False, absence_case_number="ABS-001"
    )

    stage_data([fineos_data], test_db_session)

    # Run the process
    claimant_extract_step.run_step()

    claim = test_db_session.query(Claim).one_or_none()
    assert claim
    assert claim.fineos_absence_id == fineos_data.absence_case_number
    assert claim.employee_id is None
    assert claim.fineos_notification_id is None
    assert claim.claim_type_id is None
    assert claim.fineos_absence_status_id is None
    assert claim.absence_period_start_date is None
    assert claim.absence_period_end_date is None
    assert claim.is_id_proofed is False

    # Verify the state logs and outcome
    assert len(claim.state_logs) == 1
    state_log = claim.state_logs[0]
    assert (
        state_log.end_state_id == State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT.state_id
    )
    validation_issues = state_log.outcome["validation_container"]["validation_issues"]

    assert validation_issues == [
        {"reason": "MissingField", "details": "ABSENCEPERIOD_START"},
        {"reason": "MissingField", "details": "ABSENCEPERIOD_END"},
        {"reason": "MissingField", "details": "ABSENCEPERIOD_CLASSID"},
        {"reason": "MissingField", "details": "ABSENCEPERIOD_INDEXID"},
        {"reason": "MissingField", "details": "LEAVEREQUEST_ID"},
        {"reason": "MissingField", "details": "NOTIFICATION_CASENUMBER"},
        {"reason": "MissingField", "details": "ABSENCEREASON_COVERAGE"},
        {"reason": "MissingField", "details": "ABSENCE_CASESTATUS"},
        {
            "reason": "MissingField",
            "details": "ABSENCEPERIOD_START",
        },  # ABSENCEPERIOD_START is processed twice
        {
            "reason": "MissingField",
            "details": "ABSENCEPERIOD_END",
        },  # ABSENCEPERIOD_END is processed twice
        {"reason": "MissingField", "details": "EMPLOYEE_CUSTOMERNO"},
        {"reason": "MissingField", "details": "EMPLOYER_CUSTOMERNO"},
        {
            "reason": "ClaimNotIdProofed",
            "details": "Claim has not been ID proofed, LEAVEREQUEST_EVIDENCERESULTTYPE is not Satisfied",
        },
    ]


def test_run_step_not_id_proofed(
    claimant_extract_step, test_db_session,
):
    fineos_data = FineosClaimantData(leave_request_evidence="Rejected")

    add_db_records_from_fineos_data(test_db_session, fineos_data)
    stage_data([fineos_data], test_db_session)

    # Run the process
    claimant_extract_step.run_step()

    # Validate the claim was created properly
    claim = test_db_session.query(Claim).one_or_none()
    assert claim
    assert claim.fineos_absence_id == fineos_data.absence_case_number
    assert claim.employee_id is not None
    assert claim.fineos_notification_id == fineos_data.notification_number
    assert (
        claim.claim_type_id
        == payments_util.get_mapped_claim_type(fineos_data.leave_type).claim_type_id
    )
    assert claim.fineos_absence_status_id == AbsenceStatus.get_id(fineos_data.absence_case_status)
    assert claim.absence_period_start_date is not None
    assert claim.absence_period_end_date is not None
    assert not claim.is_id_proofed

    # Verify the state logs
    assert len(claim.state_logs) == 1
    state_log = claim.state_logs[0]
    assert (
        state_log.end_state_id == State.DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT.state_id
    )


def test_run_step_no_default_payment_pref(
    claimant_extract_step, test_db_session,
):
    # Create records without a default payment preference
    # None of the payment preference related fields will be set
    fineos_data = FineosClaimantData(
        default_payment_pref="N",
        payment_method="Elec Funds Transfer",
        account_nbr="123456789",
        routing_nbr="111111118",
        account_type="Checking",
    )

    employee_before, _ = add_db_records_from_fineos_data(
        test_db_session, fineos_data, add_eft=False
    )

    stage_data([fineos_data], test_db_session)

    # Run the process
    claimant_extract_step.run_step()

    # Verify the Employee was still updated
    employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_before.employee_id)
        .one_or_none()
    )
    assert employee
    assert employee.fineos_customer_number == fineos_data.customer_number

    # Because the payment preferences weren't the default, no EFT records are created
    assert len(employee.pub_efts.all()) == 0

    # The claim still is attached to the employee
    assert len(employee.claims) == 1
    claim = employee.claims[0]
    assert claim.fineos_absence_id == fineos_data.absence_case_number
    assert claim.employee_id == employee.employee_id


def test_run_step_mix_of_payment_prefs(
    claimant_extract_step, test_db_session,
):
    # Create a record that isn't a default payment preference
    # then create another record with the same customer number & absence case number
    # but with default payment preference set to Y
    # We will use the default payment preference and ignore the other record
    not_default_fineos_data = FineosClaimantData(
        default_payment_pref="N",
        payment_method="Check",
        account_nbr="Unknown",
        routing_nbr="Unknown",
        account_type="Unknown",
    )

    default_fineos_data = copy.deepcopy(not_default_fineos_data)
    default_fineos_data.default_payment_pref = "Y"
    default_fineos_data.payment_method = "Elec Funds Transfer"
    default_fineos_data.account_nbr = "123456789"
    default_fineos_data.routing_nbr = "111111118"
    default_fineos_data.account_type = "Checking"

    # Create the employee record
    employee_before, _ = add_db_records_from_fineos_data(
        test_db_session, default_fineos_data, add_eft=False
    )

    stage_data(
        [default_fineos_data],
        test_db_session,
        additional_employee_feed_records=[not_default_fineos_data],
    )

    # Run the process
    claimant_extract_step.run_step()

    # Verify the Employee was updated
    employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_before.employee_id)
        .one_or_none()
    )
    assert employee
    assert employee.fineos_customer_number == default_fineos_data.customer_number

    # The default payment preferences were used.
    pub_efts = employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == default_fineos_data.routing_nbr
    assert pub_efts[0].pub_eft.account_nbr == default_fineos_data.account_nbr
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id

    # The claim was attached to the employee
    assert len(employee.claims) == 1
    claim = employee.claims[0]
    assert claim.fineos_absence_id == default_fineos_data.absence_case_number
    assert claim.employee_id == employee.employee_id

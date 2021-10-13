import copy
import json
import os
import tempfile
from typing import List, Optional

import boto3
import pytest

import massgov.pfml.delegated_payments.delegated_fineos_claimant_extract as claimant_extract
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
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
    EmployeePubEftPairFactory,
    EmployerFactory,
    PubEftFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.db.models.payments import (
    FineosExtractEmployeeFeed,
    FineosExtractVbiRequestedAbsenceSom,
)
from massgov.pfml.delegated_payments.delegated_config import get_s3_config
from massgov.pfml.delegated_payments.delegated_payments_util import (
    ValidationIssue,
    ValidationReason,
)
from massgov.pfml.delegated_payments.mock.fineos_extract_data import (
    FineosClaimantData,
    create_fineos_claimant_extract_files,
)
from massgov.pfml.util import datetime
from tests.delegated_payments.conftest import upload_file_to_s3


@pytest.fixture
def claimant_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return claimant_extract.ClaimantExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def upload_fineos_data(tmp_path, mock_s3_bucket, fineos_dataset):
    folder_path = os.path.join(f"s3://{mock_s3_bucket}", "cps/inbound/received")
    date_of_extract = datetime.datetime.strptime("2020-01-01-11-30-00", "%Y-%m-%d-%H-%M-%S")
    create_fineos_claimant_extract_files(fineos_dataset, folder_path, date_of_extract)


@pytest.fixture
def local_claimant_extract_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return claimant_extract.ClaimantExtractStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


@pytest.fixture
def emp_updates_path(tmp_path, mock_fineos_s3_bucket):
    requested_absence_file_name = "2020-12-21-19-20-42-VBI_REQUESTEDABSENCE_SOM.csv"
    content_line_one = '"NOTIFICATION_CASENUMBER","ABSENCE_CASENUMBER","ABSENCE_CASETYPENAME","ABSENCE_CASESTATUS","ABSENCE_CASEOWNER","ABSENCE_CASECREATIONDATE","ABSENCE_CASELASTUPDATEDATE","ABSENCE_INTAKESOURCE","ABSENCE_NOTIFIEDBY","EMPLOYEE_CUSTOMERNO","EMPLOYEE_MANAGER_CUSTOMERNO","EMPLOYEE_ADDTL_MNGR_CUSTOMERNO","EMPLOYER_CUSTOMERNO","EMPLOYER_NAME","EMPLOYMENT_CLASSID","EMPLOYMENT_INDEXID","LEAVEREQUEST_ID","LEAVEREQUEST_NOTIFICATIONDATE","LEAVEREQUEST_LASTUPDATEDATE","LEAVEREQUEST_ORIGINALREQUEST","LEAVEREQUEST_EVIDENCERESULTTYPE","LEAVEREQUEST_DECISION","LEAVEREQUEST_DIAGNOSIS","ABSENCEREASON_CLASSID","ABSENCEREASON_INDEXID","ABSENCEREASON_NAME","ABSENCEREASON_QUALIFIER1","ABSENCEREASON_QUALIFIER2","ABSENCEREASON_COVERAGE","PRIMARY_RELATIONSHIP_NAME","PRIMARY_RELATIONSHIP_QUAL1","PRIMARY_RELATIONSHIP_QUAL2","PRIMARY_RELATIONSHIP_COVER","SECONDARY_RELATIONSHIP_NAME","SECONDARY_RELATIONSHIP_QUAL1","SECONDARY_RELATIONSHIP_QUAL2","SECONDARY_RELATIONSHIP_COVER","ABSENCEPERIOD_CLASSID","ABSENCEPERIOD_INDEXID","ABSENCEPERIOD_TYPE","ABSENCEPERIOD_STATUS","ABSENCEPERIOD_START","ABSENCEPERIOD_END","EPISODE_FREQUENCY_COUNT","EPISODE_FREQUENCY_PERIOD","EPISODIC_FREQUENCY_PERIOD_UNIT","EPISODE_DURATION","EPISODIC_DURATION_UNIT"'
    content_line_two = '"NTN-2922","NTN-2922-ABS-01","Absence Case","Adjudication","SaviLinx","2020-11-02 09:52:11","2020-11-02 09:53:10","Phone","Employee","339","","2825","96","Wayne Enterprises","14453","8524","2198","2020-11-02 00:00:00","2020-11-02 09:53:30","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6236","Time off period","Please Select","2021-01-15 00:00:00","2021-01-18 00:00:00","","","Please Select","","Please Select"'
    content_line_two_case_two = '"NTN-2922","NTN-2922-ABS-02","Absence Case","Adjudication","SaviLinx","2020-11-02 09:52:11","2020-11-02 09:53:10","Phone","Employee","339","","2825","96","Wayne Enterprises","14453","8524","2198","2020-11-02 00:00:00","2020-11-02 09:53:30","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6237","Time off period","Please Select","2021-01-15 00:00:00","2021-01-18 00:00:00","","","Please Select","","Please Select"'
    content_line_three = '"NTN-2923","NTN-2923-ABS-01","Absence Case","Adjudication","SaviLinx","2020-11-02 09:57:26","2020-11-02 10:03:18","Phone","Employee","3277","","2825","96","Wayne Enterprises","14453","8525","2199","2020-11-01 00:00:00","2020-11-02 10:03:18","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6238","Time off period","Please Select","2021-02-19 00:00:00","2021-02-19 00:00:00","","","Please Select","","Please Select"'
    content_line_four = '"NTN-1308","NTN-1308-ABS-01","Absence Case","Adjudication","SaviLinx","2020-10-22 21:09:24","2020-10-22 21:09:33","Self-Service","Employee","339","","2825","96","Wayne Enterprises","14453","7310","997","2020-10-22 21:09:24","2020-10-22 21:09:33","1","Satisfied","Pending","","14412","19","Serious Health Condition - Employee","Not Work Related","Sickness","Employee","","","","Please Select","","","","Please Select","14449","4230","Time off period","Known","2021-05-13 00:00:00","2021-07-22 00:00:00","","","Please Select","","Please Select"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_two_case_two}\n{content_line_three}\n{content_line_four}"

    requested_absence_file = tmp_path / requested_absence_file_name
    requested_absence_file.write_text(content)
    upload_file_to_s3(
        requested_absence_file,
        mock_fineos_s3_bucket,
        f"DT2/dataexports/{requested_absence_file_name}",
    )

    employee_feed_file_name = "2020-12-21-19-20-42-Employee_feed.csv"
    content_line_one = '"C","I","LASTUPDATEDATE","FIRSTNAMES","INITIALS","LASTNAME","PLACEOFBIRTH","DATEOFBIRTH","DATEOFDEATH","ISDECEASED","REALDOB","TITLE","NATIONALITY","COUNTRYOFBIRT","SEX","MARITALSTATUS","DISABLED","NATINSNO","CUSTOMERNO","REFERENCENO","IDENTIFICATIO","UNVERIFIED","STAFF","GROUPCLIENT","SECUREDCLIENT","SELFSERVICEEN","SOURCESYSTEM","C_OCPRTAD_CORRESPONDENC","I_OCPRTAD_CORRESPONDENC","EXTCONSENT","EXTCONFIRMFLAG","EXTMASSID","EXTOUTOFSTATEID","PREFERREDCONT","C_BNKBRNCH_BANKBRANCH","I_BNKBRNCH_BANKBRANCH","PREFERRED_CONTACT_METHOD","DEFPAYMENTPREF","PAYMENT_PREFERENCE","PAYMENTMETHOD","PAYMENTADDRES","ADDRESS1","ADDRESS2","ADDRESS3","ADDRESS4","ADDRESS5","ADDRESS6","ADDRESS7","POSTCODE","COUNTRY","VERIFICATIONS","ACCOUNTNAME","ACCOUNTNO","BANKCODE","SORTCODE","ACCOUNTTYPE","ACTIVE_ABSENCE_FLAG"'
    content_line_two = '"11536","1268","2020-12-03 13:52:33","Glennie","","Balistreri","","1980-01-01 00:00:00","","0","0","480000","3040000","672000","32000","64000","0","881778956","339","2ebb0217-8379-47ba-922d-64aa3a3064c5","8736000","0","0","0","0","0","8032000","11737","1269","0","1","123456789","","1056000","","","Unknown","N","","Elec Funds Transfer","Associated Party Address","456 Park St","","","Oakland","","CA","","94612","672007","7808000","Glennie Balistreri","623546789","","623546789","Checking","Y"'
    content_line_three = '"11536","1268","2020-12-03 13:52:33","Glennie","","Balistreri","","1980-01-01 00:00:00","","0","0","480000","3040000","672000","32000","64000","0","881778956","339","2ebb0217-8379-47ba-922d-64aa3a3064c5","8736000","0","0","0","0","0","8032000","11737","1269","0","1","123456789","","1056000","","","Unknown","Y","","Elec Funds Transfer","Associated Party Address","123 Main St","","","Oakland","","CA","","94612","672007","7808000","Glennie Balistreri","123546784","","123546784","Checking","Y"'
    content_line_four = '"11536","12915","2020-12-11 11:22:22","Alice","","Halvorson","","1976-08-21 00:00:00","","0","0","480000","3040000","672000","32000","64000","0","534242831","3277","77b4d544-2142-44dc-9dca-325b53d175a2","8736000","0","0","0","0","0","8032000","11737","10959","0","1","S56010286","","1056000","","","Unknown","Y","","Elec Funds Transfer","Associated Party Address","95166 Pouros Well","","","Ahmadstad","","LA","","24920","672007","7808000","Alice Halvorson","5555555555","","011401533","Savings","Y"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}\n{content_line_four}"

    employee_feed_file = tmp_path / employee_feed_file_name
    employee_feed_file.write_text(content)
    upload_file_to_s3(
        employee_feed_file, mock_fineos_s3_bucket, f"DT2/dataexports/{employee_feed_file_name}"
    )

    # Add another file to test that our file processing ignores non-dated files
    other_file_name = "config.csv"
    content_line_one = "Text"
    other_file = tmp_path / other_file_name
    other_file.write_text(content_line_one)
    upload_file_to_s3(other_file, mock_fineos_s3_bucket, f"DT2/dataexports/{other_file_name}")


def create_malformed_fineos_extract(tmp_path, mock_fineos_s3_bucket, bad_fineos_extract):
    file_prefix = "2020-12-21-19-20-42-"

    bad_content_line_one = "Some,Other,Column,Names"
    bad_content_line_two = "1,2,3,4"
    bad_content = "\n".join([bad_content_line_one, bad_content_line_two])

    for claimant_extract_file in payments_util.CLAIMANT_EXTRACT_FILES:
        if claimant_extract_file == bad_fineos_extract:
            content = bad_content
        else:
            # Make the second line just the field names again so it
            # gets found (we'll never get to parsing)
            content_line = ",".join(claimant_extract_file.field_names)
            content = "\n".join([content_line, content_line])

        file_name = f"{file_prefix}{claimant_extract_file.file_name}"
        claimant_file = tmp_path / file_name
        claimant_file.write_text(content)
        upload_file_to_s3(claimant_file, mock_fineos_s3_bucket, f"DT2/dataexports/{file_name}")


def test_run_step_happy_path(
    local_claimant_extract_step,
    local_test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(
        tax_identifier=tax_identifier,
        fineos_employee_first_name="Glennie-original",
        fineos_employee_last_name="Balistreri-original",
    )
    assert employee.fineos_employee_first_name == "Glennie-original"
    assert employee.fineos_employee_last_name == "Balistreri-original"

    employer = EmployerFactory(fineos_employer_id=96)

    local_claimant_extract_step.run()

    # Requested absences file artifact above has three records but only one with the
    # LEAVEREQUEST_EVIDENCERESULTTYPE != Satisfied
    claims: List[Claim] = (
        local_test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == "NTN-1308-ABS-01")
        .all()
    )

    assert len(claims) == 1
    claim = claims[0]

    assert claim is not None
    assert claim.employee_id == employee.employee_id

    assert claim.fineos_notification_id == "NTN-1308"
    assert claim.claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id
    assert (
        claim.fineos_absence_status.absence_status_id
        == AbsenceStatus.ADJUDICATION.absence_status_id
    )
    assert claim.absence_period_start_date == datetime.date(2021, 5, 13)
    assert claim.absence_period_end_date == datetime.date(2021, 7, 22)
    assert claim.is_id_proofed is True
    assert claim.employer_id == employer.employer_id

    updated_employee = (
        local_test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    # Sample employee file above has two records for Glennie. Only one has the
    # DEFPAYMENTPREF flag set to Y, with the EFT instructions tested
    # here.
    assert updated_employee is not None
    # We are not updating first or last name with FINEOS data as DOR is source of truth.
    assert updated_employee.first_name != "Glennie"
    assert updated_employee.last_name != "Balistreri"
    # Make sure we have captured the claimant name in fineos specific employee columns (initial fineos names from above overwritten)
    assert updated_employee.fineos_employee_first_name == "Glennie"
    assert updated_employee.fineos_employee_last_name == "Balistreri"
    assert updated_employee.date_of_birth == datetime.date(1980, 1, 1)
    assert updated_employee.fineos_customer_number is not None

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123546784"
    assert pub_efts[0].pub_eft.account_nbr == "123546784"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id

    # Make sure we have captured the claimant name in pub_eft
    assert pub_efts[0].pub_eft.fineos_employee_first_name == "Glennie"
    assert pub_efts[0].pub_eft.fineos_employee_last_name == "Balistreri"

    # Confirm StateLogs
    eft_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.DELEGATED_EFT_SEND_PRENOTE,
        db_session=local_test_db_session,
    )
    assert len(eft_state_logs) == 1
    assert eft_state_logs[0].import_log_id == 1

    claim_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.CLAIM,
        end_state=State.DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS,
        db_session=local_test_db_session,
    )
    assert len(claim_state_logs) == 1
    assert claim_state_logs[0].import_log_id == 1
    assert claim_state_logs[0].claim_id == claim.claim_id

    # Confirm metrics added to import log
    import_log = local_test_db_session.query(ImportLog).first()
    import_log_report = json.loads(import_log.report)
    assert import_log_report["evidence_not_id_proofed_count"] == 3
    assert import_log_report["valid_claim_count"] == 1


@pytest.mark.parametrize(
    "claimant_extract_file",
    payments_util.CLAIMANT_EXTRACT_FILES,
    ids=payments_util.CLAIMANT_EXTRACT_FILE_NAMES,
)
def test_run_step_malformed_extracts(
    claimant_extract_file,
    mock_fineos_s3_bucket,
    local_claimant_extract_step,
    set_exporter_env_vars,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-12-20")
    create_malformed_fineos_extract(tmp_path, mock_fineos_s3_bucket, claimant_extract_file)

    with pytest.raises(
        Exception,
        match=f"FINEOS extract {claimant_extract_file.file_name} is missing required fields",
    ):
        local_claimant_extract_step.run()


def test_run_step_existing_approved_eft_info(
    local_claimant_extract_step,
    local_test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
):
    # Very similar to the happy path test, but EFT info has already been
    # previously approved and we do not need to start the prenoting process
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    # Add the eft
    EmployeePubEftPairFactory.create(
        employee=employee,
        pub_eft=PubEftFactory.create(
            prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
            routing_nbr="123546784",
            account_nbr="123546784",
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        ),
    )

    EmployerFactory(fineos_employer_id=96)

    local_claimant_extract_step.run()

    updated_employee = (
        local_test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123546784"
    assert pub_efts[0].pub_eft.account_nbr == "123546784"
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
    assert claim_state_logs[0].import_log_id == 1
    assert claim_state_logs[0].claim.employee_id == updated_employee.employee_id


def test_run_step_existing_rejected_eft_info(
    local_claimant_extract_step,
    local_test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
):
    # Very similar to the happy path test, but EFT info has already been
    # previously rejected and thus it goes into an error state instead
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    # Add the eft
    EmployeePubEftPairFactory.create(
        employee=employee,
        pub_eft=PubEftFactory.create(
            prenote_state_id=PrenoteState.REJECTED.prenote_state_id,
            routing_nbr="123546784",
            account_nbr="123546784",
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
            prenote_response_at=datetime.datetime(2020, 12, 6, 12, 0, 0),
        ),
    )

    EmployerFactory(fineos_employer_id=96)

    local_claimant_extract_step.run()

    updated_employee = (
        local_test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123546784"
    assert pub_efts[0].pub_eft.account_nbr == "123546784"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id

    # We should not have added it to the EFT state flow
    eft_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=State.DELEGATED_EFT_SEND_PRENOTE,
        db_session=local_test_db_session,
    )
    assert len(eft_state_logs) == 0

    # and there would have been a single error on the claims state log for the good record
    claims: List[Claim] = (
        local_test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == "NTN-1308-ABS-01")
        .all()
    )
    assert len(claims) == 1
    claim = claims[0]
    assert len(claim.state_logs) == 1
    assert claim.state_logs[0].outcome["validation_container"]["validation_issues"] == [
        {
            "reason": "EFTRejected",
            "details": "EFT prenote was rejected - cannot pay with this account info",
        }
    ]


def test_run_step_no_employee(
    local_claimant_extract_step,
    local_test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2020-12-20")

    local_claimant_extract_step.run()

    claim: Optional[Claim] = (
        local_test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == "NTN-1308-ABS-01")
        .one_or_none()
    )

    # Claim still gets created even if employee doesn't exist
    assert claim
    assert claim.employee_id is None

    assert len(claim.state_logs) == 1
    assert claim.state_logs[0].outcome["validation_container"]["validation_issues"] == [
        {"reason": "MissingInDB", "details": "tax_identifier: 881778956"},
        {"reason": "MissingInDB", "details": "employer customer number: 96"},
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
    extract_data = claimant_extract.ExtractData(
        payments_util.CLAIMANT_EXTRACT_FILE_NAMES, "2021-02-21"
    )

    employee_feeds = [fineos_data.get_employee_feed_record()]
    extract_data.employee_feed.indexed_data = {fineos_data.customer_number: employee_feeds}

    requested_absences = [fineos_data.get_requested_absence_record()]

    extract_data.requested_absence_info.indexed_data = {
        fineos_data.absence_case_number: requested_absences
    }

    return claimant_extract.ClaimantData(
        extract_data, fineos_data.absence_case_number, requested_absences
    )


def make_claimant_data_with_incorrect_request_absence(fineos_data):
    # This method guarantees the request absence fields ABSENCEPERIOD_CLASSID, ABSENCEPERIOD_INDEXID are set to Unknown
    extract_data = claimant_extract.ExtractData(
        payments_util.CLAIMANT_EXTRACT_FILE_NAMES, "2021-02-21"
    )

    employee_feeds = [fineos_data.get_employee_feed_record()]
    extract_data.employee_feed.indexed_data = {fineos_data.customer_number: employee_feeds}

    requested_absence = fineos_data.get_requested_absence_record()
    requested_absence["ABSENCEPERIOD_CLASSID"] = "Unknown"
    requested_absence["ABSENCEPERIOD_INDEXID"] = "Unknown"

    requested_absences = [requested_absence]
    extract_data.requested_absence_info.indexed_data = {
        fineos_data.absence_case_number: requested_absences
    }

    return claimant_extract.ClaimantData(
        extract_data, fineos_data.absence_case_number, requested_absences
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


def test_create_or_update_claim_happy_path_update_claim(
    claimant_extract_step, test_db_session, formatted_claim
):
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


def test_create_or_update_claim_invalid_values(claimant_extract_step, test_db_session):
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

    print(new_absence_period_data)

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


def add_employee_feed(extract_data: claimant_extract.ExtractData):
    employee_feed_extract = claimant_extract.Extract("test/location/employee_info")
    employee_feed_extract.indexed_data = {
        "12345": {
            "NATINSNO": "123456789",
            "DATEOFBIRTH": "1967-04-27",
            "PAYMENTMETHOD": "Elec Funds Transfer",
            "CUSTOMERNO": "12345",
            "SORTCODE": "111111118",
            "ACCOUNTNO": "123456789",
            "ACCOUNTTYPE": "Checking",
        }
    }
    extract_data.employee_feed = employee_feed_extract


def test_update_employee_info_happy_path(claimant_extract_step, test_db_session, formatted_claim):
    claimant_data = make_claimant_data_from_fineos_data(format_claimant_data())

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    employee = claimant_extract_step.update_employee_info(claimant_data, formatted_claim)

    assert len(claimant_data.validation_container.validation_issues) == 0
    assert employee is not None
    assert employee.date_of_birth == datetime.date(1967, 4, 27)


def test_update_employee_info_not_in_db(claimant_extract_step, test_db_session, formatted_claim):
    claimant_data = make_claimant_data_from_fineos_data(format_claimant_data())

    tax_identifier = TaxIdentifierFactory(tax_identifier="987654321")
    EmployeeFactory(tax_identifier=tax_identifier)

    employee = claimant_extract_step.update_employee_info(claimant_data, formatted_claim)

    assert employee is None


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    claimant_extract_step,
    test_db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")

    s3 = boto3.client("s3")

    def add_s3_files(prefix):
        for expected_file_name in payments_util.CLAIMANT_EXTRACT_FILE_NAMES:
            key = f"{prefix}{expected_file_name}"
            s3.put_object(Bucket=mock_fineos_s3_bucket, Key=key, Body="a,b,c")

    def get_download_directory(tmp_path, directory_name):
        directory = tmp_path / directory_name
        directory.mkdir()
        return directory

    # add files
    add_s3_files("DT2/dataexports/2020-01-01-11-30-00/2020-01-01-11-30-00-")
    add_s3_files("DT2/dataexports/2020-01-02-11-30-00/2020-01-02-11-30-00-")
    add_s3_files("DT2/dataexports/2020-01-03-11-30-00/2020-01-03-11-30-00-")
    add_s3_files("DT2/dataexports/2020-01-04-11-30-00-")

    # add reference files for processed folders
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_extract_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                "2020-01-01-11-30-00", ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_extract_archive_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                "2020-01-03-11-30-00", ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id,
    )

    # confirm all unprocessed files were downloaded
    claimant_extract_step.run()

    destination_folder = os.path.join(
        get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
    )
    skipped_folder = os.path.join(
        get_s3_config().pfml_fineos_extract_archive_path,
        payments_util.Constants.S3_INBOUND_SKIPPED_DIR,
    )
    processed_files = file_util.list_files(destination_folder, recursive=True)

    skipped_files = file_util.list_files(skipped_folder, recursive=True)
    assert len(processed_files) == 2
    assert len(skipped_files) == 2

    for file in skipped_files:
        assert file.startswith("2020-01-02-11-30-00")

    expected_file_names = []
    for date_file in payments_util.CLAIMANT_EXTRACT_FILE_NAMES:
        for unprocessed_date in ["2020-01-02-11-30-00", "2020-01-04-11-30-00"]:
            expected_file_names.append(
                f"{payments_util.get_date_group_folder_name(unprocessed_date, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT)}/{unprocessed_date}-{date_file}"
            )

    for processed_file in processed_files:
        assert processed_file in expected_file_names

    copied_files = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session,
        payments_util.CLAIMANT_EXTRACT_FILE_NAMES,
        ReferenceFileType.FINEOS_CLAIMANT_EXTRACT,
    )
    assert len(copied_files) == 0


def test_update_eft_info_happy_path(claimant_extract_step, test_db_session):
    employee = EmployeeFactory.create()
    assert len(employee.pub_efts.all()) == 0

    fineos_data = FineosClaimantData(
        routing_nbr="111111118", account_nbr="123456789", account_type="Checking"
    )
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
    employee = EmployeeFactory()
    assert len(employee.pub_efts.all()) == 0

    # Routing number doesn't pass checksum, but is correct length
    fineos_data = FineosClaimantData(
        routing_nbr="111111111", account_nbr="123456789", account_type="Checking"
    )
    claimant_data = make_claimant_data_from_fineos_data(fineos_data)

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
    claimant_extract_step,
    test_db_session,
    formatted_claim,
    tmp_path,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    # Create some validation issues
    fineos_data = FineosClaimantData(
        routing_nbr="",
        leave_request_end="",
        date_of_birth="",
        fineos_employee_first_name="",
        fineos_employee_last_name="",
    )

    # Create the employee record
    tax_identifier = TaxIdentifierFactory(tax_identifier=fineos_data.ssn)
    employee_before = EmployeeFactory(tax_identifier=tax_identifier)

    # Create the employer record
    employer = EmployerFactory(fineos_employer_id=fineos_data.employer_customer_num)

    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_data])

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
    assert claim.employer_id == employer.employer_id

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
    claimant_extract_step,
    test_db_session,
    tmp_path,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    # Create a record with only an absence case number
    # This should still end up created in the DB, but with
    # significant validation issues
    fineos_data = FineosClaimantData(
        False, include_employee_feed=False, absence_case_number="ABS-001"
    )

    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_data])

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
    claimant_extract_step,
    test_db_session,
    tmp_path,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    fineos_data = FineosClaimantData(leave_request_evidence="Rejected")

    # Create the employee record
    tax_identifier = TaxIdentifierFactory(tax_identifier=fineos_data.ssn)
    EmployeeFactory(tax_identifier=tax_identifier)

    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_data])

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
    claimant_extract_step,
    test_db_session,
    tmp_path,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    # Create records without a default payment preference
    # None of the payment preference related fields will be set
    fineos_data = FineosClaimantData(
        default_payment_pref="N",
        payment_method="Elec Funds Transfer",
        account_nbr="123456789",
        routing_nbr="111111118",
        account_type="Checking",
    )

    # Create the employee record
    tax_identifier = TaxIdentifierFactory(tax_identifier=fineos_data.ssn)
    employee_before = EmployeeFactory(tax_identifier=tax_identifier)

    upload_fineos_data(tmp_path, mock_s3_bucket, [fineos_data])

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
    claimant_extract_step,
    test_db_session,
    tmp_path,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
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
    tax_identifier = TaxIdentifierFactory(tax_identifier=default_fineos_data.ssn)
    employee_before = EmployeeFactory(tax_identifier=tax_identifier)

    upload_fineos_data(tmp_path, mock_s3_bucket, [not_default_fineos_data, default_fineos_data])

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


def test_run_step_skip_prenote_flag(
    claimant_extract_step,
    test_db_session,
    tmp_path,
    mock_s3_bucket,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_CLAIMANT_EXTRACT_MAX_HISTORY_DATE", "2019-12-31")
    monkeypatch.setenv("SKIP_PRENOTING", "1")

    claimant_data = FineosClaimantData(
        default_payment_pref="Y",
        payment_method="Elec Funds Transfer",
        account_nbr="123456789",
        routing_nbr="111111118",
        account_type="Checking",
    )

    # Create the employee record
    tax_identifier = TaxIdentifierFactory(tax_identifier=claimant_data.ssn)
    employee_before = EmployeeFactory(tax_identifier=tax_identifier)
    assert len(employee_before.pub_efts.all()) == 0

    upload_fineos_data(tmp_path, mock_s3_bucket, [claimant_data])

    # Run the process
    claimant_extract_step.run_step()

    # Verify the Employee was updated
    employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_before.employee_id)
        .one_or_none()
    )
    assert employee

    # We didn't attach the EFT record because of the flag
    pub_efts = employee.pub_efts.all()
    assert len(pub_efts) == 0


def test_extract_to_staging_tables(emp_updates_path, claimant_extract_step, test_db_session):
    tempdir = tempfile.mkdtemp()
    date = "2020-12-21-19-20-42"
    test_file_name1 = "Employee_feed.csv"
    test_file_name2 = "VBI_REQUESTEDABSENCE_SOM.csv"

    test_file_path1 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name1}")
    test_file_path2 = os.path.join(os.path.dirname(__file__), f"test_files/{test_file_name2}")

    test_file_names = [test_file_path1, test_file_path2]

    extract_data = claimant_extract.ExtractData(test_file_names, date)
    claimant_extract_step.download_and_index_data(extract_data, tempdir)

    test_db_session.commit()

    requested_absence_info_data = test_db_session.query(FineosExtractVbiRequestedAbsenceSom).all()
    employee_feed_data = test_db_session.query(FineosExtractEmployeeFeed).all()

    ref_file = extract_data.reference_file

    assert len(requested_absence_info_data) == 4
    assert len(employee_feed_data) == 3

    for data in requested_absence_info_data:
        assert data.reference_file_id == ref_file.reference_file_id

    for data in employee_feed_data:
        assert data.reference_file_id == ref_file.reference_file_id

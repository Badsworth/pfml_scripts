import json
import os
import tempfile
from typing import Dict, List, Optional, Tuple

import boto3
import pytest

import massgov.pfml.delegated_payments.delegated_fineos_claimant_extract as claimant_extract
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    EmployeeLog,
    ImportLog,
    PaymentMethod,
    PrenoteState,
    ReferenceFileType,
    State,
    StateLog,
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
from massgov.pfml.util import datetime
from tests.delegated_payments.conftest import upload_file_to_s3

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def claimant_extract_step(initialize_factories_session, test_db_session, test_db_other_session):
    return claimant_extract.ClaimantExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def emp_updates_path(tmp_path, mock_fineos_s3_bucket):
    requested_absence_file_name = "2020-12-21-19-20-42-VBI_REQUESTEDABSENCE_SOM.csv"
    content_line_one = '"NOTIFICATION_CASENUMBER","ABSENCE_CASENUMBER","ABSENCE_CASETYPENAME","ABSENCE_CASESTATUS","ABSENCE_CASEOWNER","ABSENCE_CASECREATIONDATE","ABSENCE_CASELASTUPDATEDATE","ABSENCE_INTAKESOURCE","ABSENCE_NOTIFIEDBY","EMPLOYEE_CUSTOMERNO","EMPLOYEE_MANAGER_CUSTOMERNO","EMPLOYEE_ADDTL_MNGR_CUSTOMERNO","EMPLOYER_CUSTOMERNO","EMPLOYER_NAME","EMPLOYMENT_CLASSID","EMPLOYMENT_INDEXID","LEAVEREQUEST_ID","LEAVEREQUEST_NOTIFICATIONDATE","LEAVEREQUEST_LASTUPDATEDATE","LEAVEREQUEST_ORIGINALREQUEST","LEAVEREQUEST_EVIDENCERESULTTYPE","LEAVEREQUEST_DECISION","LEAVEREQUEST_DIAGNOSIS","ABSENCEREASON_CLASSID","ABSENCEREASON_INDEXID","ABSENCEREASON_NAME","ABSENCEREASON_QUALIFIER1","ABSENCEREASON_QUALIFIER2","ABSENCEREASON_COVERAGE","PRIMARY_RELATIONSHIP_NAME","PRIMARY_RELATIONSHIP_QUAL1","PRIMARY_RELATIONSHIP_QUAL2","PRIMARY_RELATIONSHIP_COVER","SECONDARY_RELATIONSHIP_NAME","SECONDARY_RELATIONSHIP_QUAL1","SECONDARY_RELATIONSHIP_QUAL2","SECONDARY_RELATIONSHIP_COVER","ABSENCEPERIOD_CLASSID","ABSENCEPERIOD_INDEXID","ABSENCEPERIOD_TYPE","ABSENCEPERIOD_STATUS","ABSENCEPERIOD_START","ABSENCEPERIOD_END","EPISODE_FREQUENCY_COUNT","EPISODE_FREQUENCY_PERIOD","EPISODIC_FREQUENCY_PERIOD_UNIT","EPISODE_DURATION","EPISODIC_DURATION_UNIT"'
    content_line_two = '"NTN-2922","NTN-2922-ABS-01","Absence Case","Adjudication","SaviLinx","2020-11-02 09:52:11","2020-11-02 09:53:10","Phone","Employee","339","","2825","96","Wayne Enterprises","14453","8524","2198","2020-11-02 00:00:00","2020-11-02 09:53:30","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6236","Time off period","Please Select","2021-01-15 00:00:00","2021-01-18 00:00:00","","","Please Select","","Please Select"'
    content_line_two_case_two = '"NTN-2922","NTN-2922-ABS-02","Absence Case","Adjudication","SaviLinx","2020-11-02 09:52:11","2020-11-02 09:53:10","Phone","Employee","339","","2825","96","Wayne Enterprises","14453","8524","2198","2020-11-02 00:00:00","2020-11-02 09:53:30","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6236","Time off period","Please Select","2021-01-15 00:00:00","2021-01-18 00:00:00","","","Please Select","","Please Select"'
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
    content_line_three = '"11536","1268","2020-12-03 13:52:33","Glennie","","Balistreri","","1980-01-01 00:00:00","","0","0","480000","3040000","672000","32000","64000","0","881778956","339","2ebb0217-8379-47ba-922d-64aa3a3064c5","8736000","0","0","0","0","0","8032000","11737","1269","0","1","123456789","","1056000","","","Unknown","Y","","Elec Funds Transfer","Associated Party Address","123 Main St","","","Oakland","","CA","","94612","672007","7808000","Glennie Balistreri","123546789","","123546789","Checking","Y"'
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


def test_run_step_happy_path(
    claimant_extract_step,
    test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    EmployerFactory(fineos_employer_id=96)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    claimant_extract_step.run()

    # Requested absences file artifact above has three records but only one with the
    # LEAVEREQUEST_EVIDENCERESULTTYPE != Satisfied
    claims: List[Claim] = (
        test_db_session.query(Claim).filter(Claim.fineos_absence_id == "NTN-1308-ABS-01").all()
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

    updated_employee = (
        test_db_session.query(Employee)
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
    assert updated_employee.date_of_birth == datetime.date(1980, 1, 1)

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123546789"
    assert pub_efts[0].pub_eft.account_nbr == "123546789"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id

    # Confirm StateLogs
    state_logs = test_db_session.query(StateLog).all()

    updated_employee_state_log_count = 2

    assert len(state_logs) == updated_employee_state_log_count
    assert len(updated_employee.state_logs) == updated_employee_state_log_count

    # Confirm 1 state log for DELEGATED_EFT flow
    for state_log in updated_employee.state_logs:
        assert state_log.end_state_id in [
            State.DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS.state_id,
            State.DELEGATED_EFT_SEND_PRENOTE.state_id,
        ]

        assert state_log.import_log_id == 1

    # Confirm metrics added to import log
    import_log = test_db_session.query(ImportLog).first()
    import_log_report = json.loads(import_log.report)
    assert import_log_report["evidence_not_id_proofed_count"] == 3
    assert import_log_report["valid_claimant_count"] == 1

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_run_step_existing_approved_eft_info(
    claimant_extract_step,
    test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
    create_triggers,
):
    # Very similar to the happy path test, but EFT info has already been
    # previously approved and we do not need to start the prenoting process
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    # Add the eft
    EmployeePubEftPairFactory.create(
        employee=employee,
        pub_eft=PubEftFactory.create(
            prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
            routing_nbr="123546789",
            account_nbr="123546789",
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        ),
    )

    EmployerFactory(fineos_employer_id=96)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    claimant_extract_step.run()

    updated_employee = (
        test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123546789"
    assert pub_efts[0].pub_eft.account_nbr == "123546789"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.APPROVED.prenote_state_id
    # We should not have added it to the EFT state flow
    # and there shouldn't have been any errors
    assert len(updated_employee.state_logs) == 1
    assert (
        updated_employee.state_logs[0].end_state_id
        == State.DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS.state_id
    )


def test_run_step_existing_rejected_eft_info(
    claimant_extract_step,
    test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
    create_triggers,
):
    # Very similar to the happy path test, but EFT info has already been
    # previously rejected and thus it goes into an error state instead
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    # Add the eft
    EmployeePubEftPairFactory.create(
        employee=employee,
        pub_eft=PubEftFactory.create(
            prenote_state_id=PrenoteState.REJECTED.prenote_state_id,
            routing_nbr="123546789",
            account_nbr="123546789",
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
            prenote_response_at=datetime.datetime(2020, 12, 6, 12, 0, 0),
        ),
    )

    EmployerFactory(fineos_employer_id=96)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    claimant_extract_step.run()

    updated_employee = (
        test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123546789"
    assert pub_efts[0].pub_eft.account_nbr == "123546789"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id
    # We should not have added it to the EFT state flow
    # and there would have been a single error
    assert len(updated_employee.state_logs) == 1
    assert (
        updated_employee.state_logs[0].end_state_id
        == State.DELEGATED_CLAIMANT_ADD_TO_CLAIMANT_EXTRACT_ERROR_REPORT.state_id
    )
    assert updated_employee.state_logs[0].outcome["validation_container"]["validation_issues"] == [
        {
            "reason": "EFTRejected",
            "details": "EFT prenote was rejected - cannot pay with this account info",
        }
    ]


def test_run_step_no_employee(
    claimant_extract_step,
    test_db_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    claimant_extract_step.run()

    claim: Optional[Claim] = (
        test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == "NTN-1308-ABS-01")
        .one_or_none()
    )

    assert claim is None

    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 0

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def format_absence_data() -> Tuple[claimant_extract.ExtractData, Dict[str, str]]:
    extract_data = claimant_extract.ExtractData([], "2021-02-21")

    requested_absence = {
        "ABSENCE_CASENUMBER": "NTN-001-ABS-01",
        "NOTIFICATION_CASENUMBER": "NTN-001",
        "ABSENCE_CASESTATUS": "Adjudication",
        "ABSENCEPERIOD_START": "2021-02-14",
        "ABSENCEPERIOD_END": "2021-02-28",
        "ABSENCEREASON_COVERAGE": "Family",
        "LEAVEREQUEST_EVIDENCERESULTTYPE": "Satisfied",
        "EMPLOYEE_CUSTOMERNO": "12345",
    }

    return extract_data, requested_absence


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


def test_create_or_update_claim_happy_path_new_claim(claimant_extract_step, test_db_session):

    extract_data, requested_absence = format_absence_data()

    validation_container, claim = claimant_extract_step.create_or_update_claim(
        extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 0
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

    extract_data, requested_absence = format_absence_data()

    validation_container, claim = claimant_extract_step.create_or_update_claim(
        extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 0
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

    extract_data, requested_absence = format_absence_data()
    # Set absences status to invalid value
    requested_absence["ABSENCE_CASESTATUS"] = "Invalid Value"

    validation_container, claim = claimant_extract_step.create_or_update_claim(
        extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 1
    assert claim.fineos_absence_status_id is None

    extract_data, requested_absence = format_absence_data()
    # Set start date to empty string
    requested_absence["ABSENCEPERIOD_START"] = ""

    validation_container, claim = claimant_extract_step.create_or_update_claim(
        extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 1
    assert claim.absence_period_start_date is None

    extract_data, requested_absence = format_absence_data()
    # Set end date to empty string
    requested_absence["ABSENCEPERIOD_END"] = ""

    validation_container, claim = claimant_extract_step.create_or_update_claim(
        extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 1
    assert claim.absence_period_end_date is None


def add_employee_feed(extract_data: claimant_extract.ExtractData):
    employee_feed_extract = claimant_extract.Extract("test/location/employee_info")
    employee_feed_extract.indexed_data = {
        "12345": {
            "NATINSNO": "123456789",
            "DATEOFBIRTH": "1967-04-27",
            "PAYMENTMETHOD": "Elec Funds Transfer",
            "CUSTOMERNO": "12345",
            "SORTCODE": "123456789",
            "ACCOUNTNO": "123456789",
            "ACCOUNTTYPE": "Checking",
        }
    }
    extract_data.employee_feed = employee_feed_extract


def test_update_employee_info_happy_path(claimant_extract_step, test_db_session, formatted_claim):
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(record_key=absence_case_id)

    employee = claimant_extract_step.update_employee_info(
        extract_data, requested_absence, formatted_claim, validation_container
    )

    assert len(validation_container.validation_issues) == 0
    assert employee is not None
    assert employee.date_of_birth == datetime.date(1967, 4, 27)


def test_update_employee_info_not_in_db(claimant_extract_step, test_db_session, formatted_claim):
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)

    tax_identifier = TaxIdentifierFactory(tax_identifier="987654321")
    EmployeeFactory(tax_identifier=tax_identifier)

    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(record_key=absence_case_id)

    employee = claimant_extract_step.update_employee_info(
        extract_data, requested_absence, formatted_claim, validation_container
    )

    assert employee is None


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    claimant_extract_step,
    test_db_session,
    tmp_path,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2019-12-31")

    s3 = boto3.client("s3")

    def add_s3_files(prefix):
        for expected_file_name in claimant_extract.expected_file_names:
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
            get_s3_config().pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                "2020-01-01-11-30-00", ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                "2020-01-03-11-30-00", ReferenceFileType.FINEOS_CLAIMANT_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.FINEOS_CLAIMANT_EXTRACT.reference_file_type_id,
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    # confirm all unprocessed files were downloaded
    claimant_extract_step.run()

    destination_folder = os.path.join(
        get_s3_config().pfml_fineos_inbound_path, payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
    )
    skipped_folder = os.path.join(
        get_s3_config().pfml_fineos_inbound_path, payments_util.Constants.S3_INBOUND_SKIPPED_DIR,
    )
    processed_files = file_util.list_files(destination_folder, recursive=True)

    skipped_files = file_util.list_files(skipped_folder, recursive=True)
    assert len(processed_files) == 2
    assert len(skipped_files) == 2

    for file in skipped_files:
        assert file.startswith("2020-01-02-11-30-00")

    expected_file_names = []
    for date_file in claimant_extract.expected_file_names:
        for unprocessed_date in ["2020-01-02-11-30-00", "2020-01-04-11-30-00"]:
            expected_file_names.append(
                f"{payments_util.get_date_group_folder_name(unprocessed_date, ReferenceFileType.FINEOS_CLAIMANT_EXTRACT)}/{unprocessed_date}-{date_file}"
            )

    for processed_file in processed_files:
        assert processed_file in expected_file_names

    copied_files = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session,
        claimant_extract.expected_file_names,
        ReferenceFileType.FINEOS_CLAIMANT_EXTRACT,
    )
    assert len(copied_files) == 0

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_update_eft_info_happy_path(claimant_extract_step, test_db_session):
    employee = EmployeeFactory.create()
    assert len(employee.pub_efts.all()) == 0

    eft_entry = {"SORTCODE": "123456789", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    claimant_extract_step.update_eft_info(
        eft_entry, employee, PaymentMethod.ACH.payment_method_id, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    pub_efts = updated_employee.pub_efts.all()
    assert len(pub_efts) == 1
    assert pub_efts[0].pub_eft.routing_nbr == "123456789"
    assert pub_efts[0].pub_eft.account_nbr == "123456789"
    assert pub_efts[0].pub_eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    assert pub_efts[0].pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id


def test_update_eft_info_validation_issues(claimant_extract_step, test_db_session):
    employee = EmployeeFactory()
    assert len(employee.pub_efts.all()) == 0

    none_payment_method_id = None

    # Routing number incorrect length.
    eft_entry = {"SORTCODE": "12345678", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    claimant_extract_step.update_eft_info(
        eft_entry, employee, none_payment_method_id, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert len(updated_employee.pub_efts.all()) == 0

    # Account number incorrect length.
    eft_entry = {
        "SORTCODE": "123456789",
        "ACCOUNTNO": "12345678901234567890123456789012345678901234567890",
        "ACCOUNTTYPE": "Checking",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    claimant_extract_step.update_eft_info(
        eft_entry, employee, none_payment_method_id, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert len(updated_employee.pub_efts.all()) == 0

    # Account type incorrect.
    eft_entry = {
        "SORTCODE": "123456789",
        "ACCOUNTNO": "123456789012345678901234567890",
        "ACCOUNTTYPE": "Certificate of Deposit",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    claimant_extract_step.update_eft_info(
        eft_entry, employee, none_payment_method_id, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert len(updated_employee.pub_efts.all()) == 0

    # Account type and Routing number incorrect.
    eft_entry = {
        "SORTCODE": "12345678",
        "ACCOUNTNO": "123456789012345678901234567890",
        "ACCOUNTTYPE": "Certificate of Deposit",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    claimant_extract_step.update_eft_info(
        eft_entry, employee, none_payment_method_id, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 2
    assert len(updated_employee.pub_efts.all()) == 0


def test_process_records_to_db_validation_issues(
    claimant_extract_step, test_db_session, formatted_claim
):
    # Setup
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)
    # Create some validation issues
    extract_data.employee_feed.indexed_data["12345"]["SORTCODE"] = ""
    requested_absence["ABSENCEPERIOD_END"] = ""
    extract_data.requested_absence_info = claimant_extract.Extract(
        "test/location/requested_absence"
    )
    extract_data.requested_absence_info.indexed_data["NTN-001-ABS-01"] = requested_absence

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    # Run the process
    claimant_extract_step.process_records_to_db(extract_data)

    # Verify the state logs
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 1

    state_log = state_logs[0]
    assert (
        state_log.end_state_id
        == State.DELEGATED_CLAIMANT_ADD_TO_CLAIMANT_EXTRACT_ERROR_REPORT.state_id
    )


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
    claimant_extract_step.extract_to_staging_tables(extract_data)

    test_db_session.commit()

    requested_absence_info_data = test_db_session.query(FineosExtractVbiRequestedAbsenceSom).all()
    employee_feed_data = test_db_session.query(FineosExtractEmployeeFeed).all()

    ref_file = extract_data.reference_file

    assert len(requested_absence_info_data) == 4
    assert len(employee_feed_data) == 2

    for data in requested_absence_info_data:
        assert data.reference_file_id == ref_file.reference_file_id

    for data in employee_feed_data:
        assert data.reference_file_id == ref_file.reference_file_id

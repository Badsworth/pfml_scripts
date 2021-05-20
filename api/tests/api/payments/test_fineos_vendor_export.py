import os
from typing import Dict, List, Optional, Tuple

import boto3
import pytest
from sqlalchemy import func

import massgov.pfml.payments.fineos_vendor_export as vendor_export
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.api.util import state_log_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    EmployeeLog,
    Flow,
    GeoState,
    LatestStateLog,
    PaymentMethod,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    CtrAddressPairFactory,
    EftFactory,
    EmployeeFactory,
    EmployerFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.payments.config import get_s3_config
from massgov.pfml.util import datetime
from tests.api.payments.conftest import upload_file_to_s3

# every test in here requires real resources
pytestmark = pytest.mark.integration


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

    leave_plan_info_file_name = "2020-12-21-19-20-42-LeavePlan_info.csv"
    content_line_one = '"ABSENCE_CASENUMBER","PAIDLEAVE_CASENUMBER","PAIDLEAVEBENEFIT_CASENUMBER","PEI_I","PEI_C","LP_C","LP_I","ALIAS","SHORTNAME","LEAVETYPE","BENEFITRIGHTYPE"'
    content_line_two = '"NTN-1307-ABS-01","PL ABS-1307","PL ABS-1307-PL ABS-01","","","14400","313","MA PFML - Employee","MA PFML - Employee","EE Medical Leave","Absence Benefit"'
    content_line_three = '"NTN-1308-ABS-01","PL ABS-1308","PL ABS-1308-PL ABS-01","","","14400","315","MA PFML - Family","MA PFML - Family","Family Medical Leave","Absence Benefit"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    leave_plan_info_file = tmp_path / leave_plan_info_file_name
    leave_plan_info_file.write_text(content)
    upload_file_to_s3(
        leave_plan_info_file, mock_fineos_s3_bucket, f"DT2/dataexports/{leave_plan_info_file_name}"
    )

    # Add another file to test that our file processing ignores non-dated files
    other_file_name = "config.csv"
    content_line_one = "Text"
    other_file = tmp_path / other_file_name
    other_file.write_text(content_line_one)
    upload_file_to_s3(
        leave_plan_info_file, mock_fineos_s3_bucket, f"DT2/dataexports/{other_file_name}"
    )


def test_process_vendor_extract_data_happy_path(
    test_db_session,
    initialize_factories_session,
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

    vendor_export.process_vendor_extract_data(test_db_session)

    claims: List[Claim] = (test_db_session.query(Claim).all())

    assert claims[0].fineos_notification_id == "NTN-2922"
    assert claims[0].is_id_proofed is False

    assert len(claims) == 3
    claim = claims[2]

    assert claim is not None
    assert claim.employee_id == employee.employee_id
    # assert claim.employer_id == employer.employer_id  # TODO - See comment in update_employee_info

    assert claim.fineos_notification_id == "NTN-1308"
    assert claim.claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id
    assert (
        claim.fineos_absence_status.absence_status_id
        == AbsenceStatus.ADJUDICATION.absence_status_id
    )
    assert claim.absence_period_start_date == datetime.date(2021, 5, 13)
    assert claim.absence_period_end_date == datetime.date(2021, 7, 22)
    assert claim.is_id_proofed is True

    updated_employee: Optional[Employee] = (
        test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    # Sample employee file above has two records for Glennie. Only one has the
    # DEFPAYMENTPREF flag set to Y, with the address and EFT instructions tested
    # here.
    assert updated_employee is not None
    # We are not updating first or last name with FINEOS data as DOR is source of truth.
    assert updated_employee.first_name != "Glennie"
    assert updated_employee.last_name != "Balistreri"
    assert updated_employee.date_of_birth == datetime.date(1980, 1, 1)
    assert updated_employee.payment_method.payment_method_id == PaymentMethod.ACH.payment_method_id

    assert updated_employee.ctr_address_pair.fineos_address.address_line_one == "123 Main St"
    assert updated_employee.ctr_address_pair.fineos_address.address_line_two == ""
    assert updated_employee.ctr_address_pair.fineos_address.city == "Oakland"
    assert updated_employee.ctr_address_pair.fineos_address.geo_state_id == GeoState.CA.geo_state_id
    assert updated_employee.ctr_address_pair.fineos_address.zip_code == "94612"

    assert updated_employee.eft.routing_nbr == "123546789"
    assert updated_employee.eft.account_nbr == "123546789"
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )

    # Confirm StateLogs
    state_logs = test_db_session.query(StateLog).all()

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # updated_employee_state_log_count = 2
    updated_employee_state_log_count = 1

    assert len(state_logs) == updated_employee_state_log_count
    assert len(updated_employee.state_logs) == updated_employee_state_log_count

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # Confirm 1 state log for VENDOR_EFT flow
    # assert (
    #     test_db_session.query(func.count(StateLog.state_log_id))
    #     .filter(StateLog.end_state_id == State.EFT_REQUEST_RECEIVED.state_id)
    #     .scalar()
    #     == 1
    # )

    # Confirm 1 state log for VENDOR_CHECK flow
    assert (
        test_db_session.query(func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.IDENTIFY_MMARS_STATUS.state_id)
        .scalar()
        == 1
    )

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_vendor_extract_step(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
    create_triggers,
):
    # Verify that the VendorExtractStep.run_step() is functionally equivalent to calling
    # process_vendor_extract_data() directly.
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    EmployerFactory(fineos_employer_id=96)

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 1

    vendor_export.VendorExtractStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    ).run_step()

    # Requested absences file artifact above has three records but only one with the
    # LEAVEREQUEST_EVIDENCERESULTTYPE == Satisfied
    claims: List[Claim] = (
        test_db_session.query(Claim).filter(Claim.fineos_absence_id == "NTN-1308-ABS-01").all()
    )

    assert len(claims) == 1
    claim = claims[0]

    assert claim is not None
    assert claim.employee_id == employee.employee_id
    # assert claim.employer_id == employer.employer_id  # TODO - See comment in update_employee_info

    assert claim.fineos_notification_id == "NTN-1308"
    assert claim.claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id
    assert (
        claim.fineos_absence_status.absence_status_id
        == AbsenceStatus.ADJUDICATION.absence_status_id
    )
    assert claim.absence_period_start_date == datetime.date(2021, 5, 13)
    assert claim.absence_period_end_date == datetime.date(2021, 7, 22)
    assert claim.is_id_proofed is True

    updated_employee: Optional[Employee] = (
        test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .one_or_none()
    )

    # Sample employee file above has two records for Glennie. Only one has the
    # DEFPAYMENTPREF flag set to Y, with the address and EFT instructions tested
    # here.
    assert updated_employee is not None
    # We are not updating first or last name with FINEOS data as DOR is source of truth.
    assert updated_employee.first_name != "Glennie"
    assert updated_employee.last_name != "Balistreri"
    assert updated_employee.date_of_birth == datetime.date(1980, 1, 1)
    assert updated_employee.payment_method.payment_method_id == PaymentMethod.ACH.payment_method_id

    assert updated_employee.ctr_address_pair.fineos_address.address_line_one == "123 Main St"
    assert updated_employee.ctr_address_pair.fineos_address.address_line_two == ""
    assert updated_employee.ctr_address_pair.fineos_address.city == "Oakland"
    assert updated_employee.ctr_address_pair.fineos_address.geo_state_id == GeoState.CA.geo_state_id
    assert updated_employee.ctr_address_pair.fineos_address.zip_code == "94612"

    assert updated_employee.eft.routing_nbr == "123546789"
    assert updated_employee.eft.account_nbr == "123546789"
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )

    # Confirm StateLogs
    state_logs = test_db_session.query(StateLog).all()

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # updated_employee_state_log_count = 2
    updated_employee_state_log_count = 1

    assert len(state_logs) == updated_employee_state_log_count
    assert len(updated_employee.state_logs) == updated_employee_state_log_count

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # Confirm 1 state log for VENDOR_EFT flow
    # assert (
    #     test_db_session.query(func.count(StateLog.state_log_id))
    #     .filter(StateLog.end_state_id == State.EFT_REQUEST_RECEIVED.state_id)
    #     .scalar()
    #     == 1
    # )

    # Confirm 1 state log for VENDOR_CHECK flow
    assert (
        test_db_session.query(func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.IDENTIFY_MMARS_STATUS.state_id)
        .scalar()
        == 1
    )

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_process_vendor_extract_data_no_employee(
    test_db_session,
    initialize_factories_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    vendor_export.process_vendor_extract_data(test_db_session)

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


def format_absence_data() -> Tuple[vendor_export.ExtractData, Dict[str, str]]:
    leave_plan_extract = vendor_export.Extract("test/location/leave_plan")
    leave_plan_extract.indexed_data = {
        "NTN-001-ABS-01": {
            "ABSENCE_CASENUMBER": "NTN-001-ABS-01",
            "LEAVETYPE": "Family Medical Leave",
        }
    }
    extract_data = vendor_export.ExtractData([], "2021-02-21")
    extract_data.leave_plan_info = leave_plan_extract

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


def test_create_or_update_claim_happy_path_new_claim(test_db_session, initialize_factories_session):

    extract_data, requested_absence = format_absence_data()

    validation_container, claim = vendor_export.create_or_update_claim(
        test_db_session, extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 0
    assert claim is not None
    # New claim not yet persisted to DB
    assert claim.fineos_notification_id == "NTN-001"
    assert claim.fineos_absence_id == "NTN-001-ABS-01"
    # ClaimType logic commented out by other PR so commenting this assertion.
    # assert claim.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id
    assert claim.fineos_absence_status_id == AbsenceStatus.ADJUDICATION.absence_status_id
    assert claim.absence_period_start_date == datetime.date(2021, 2, 14)
    assert claim.absence_period_end_date == datetime.date(2021, 2, 28)
    assert claim.is_id_proofed is True


def test_create_or_update_claim_happy_path_update_claim(
    test_db_session, initialize_factories_session, formatted_claim
):

    extract_data, requested_absence = format_absence_data()

    validation_container, claim = vendor_export.create_or_update_claim(
        test_db_session, extract_data, requested_absence
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


def test_create_or_update_claim_no_leave_plan_match(test_db_session, initialize_factories_session):

    extract_data, requested_absence = format_absence_data()
    # Change key to force unmatch.
    requested_absence["ABSENCE_CASENUMBER"] = "NTN-002-ABS-01"

    validation_container, claim = vendor_export.create_or_update_claim(
        test_db_session, extract_data, requested_absence
    )

    # Leave plan match logic commented out by other PR so commenting validation assertion
    # and checking claim is not none. Why was leave plan match commented out?
    # assert len(validation_container.validation_issues) == 1
    assert claim is not None


def test_create_or_update_claim_invalid_values(test_db_session, initialize_factories_session):

    extract_data, requested_absence = format_absence_data()
    # Set absences status to invalid value
    requested_absence["ABSENCE_CASESTATUS"] = "Invalid Value"

    validation_container, claim = vendor_export.create_or_update_claim(
        test_db_session, extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 1
    assert claim.fineos_absence_status_id is None

    extract_data, requested_absence = format_absence_data()
    # Set start date to empty string
    requested_absence["ABSENCEPERIOD_START"] = ""

    validation_container, claim = vendor_export.create_or_update_claim(
        test_db_session, extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 1
    assert claim.absence_period_start_date is None

    extract_data, requested_absence = format_absence_data()
    # Set end date to empty string
    requested_absence["ABSENCEPERIOD_END"] = ""

    validation_container, claim = vendor_export.create_or_update_claim(
        test_db_session, extract_data, requested_absence
    )

    assert len(validation_container.validation_issues) == 1
    assert claim.absence_period_end_date is None


def add_employee_feed(extract_data: vendor_export.ExtractData):
    employee_feed_extract = vendor_export.Extract("test/location/employee_info")
    employee_feed_extract.indexed_data = {
        "12345": {
            "NATINSNO": "123456789",
            "DATEOFBIRTH": "1967-04-27",
            "PAYMENTMETHOD": "Elec Funds Transfer",
            "CUSTOMERNO": "12345",
            "ADDRESS1": "456 Park Avenue",
            "ADDRESS2": "",
            "ADDRESS4": "New York",
            "ADDRESS6": "NY",
            "POSTCODE": "11020",
            "SORTCODE": "123456789",
            "ACCOUNTNO": "123456789",
            "ACCOUNTTYPE": "Checking",
        }
    }
    extract_data.employee_feed = employee_feed_extract


def test_update_employee_info_happy_path(
    test_db_session, initialize_factories_session, formatted_claim
):
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(record_key=absence_case_id)

    employee, has_vendor_update = vendor_export.update_employee_info(
        test_db_session, extract_data, requested_absence, formatted_claim, validation_container
    )

    assert len(validation_container.validation_issues) == 0
    assert employee is not None
    assert employee.date_of_birth == datetime.date(1967, 4, 27)
    assert employee.payment_method_id == PaymentMethod.ACH.payment_method_id
    assert has_vendor_update is True


def test_update_employee_info_dob_not_required(
    test_db_session, initialize_factories_session, formatted_claim
):
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)
    fineos_customer_number = "12345"
    extract_data.employee_feed.indexed_data[fineos_customer_number]["DATEOFBIRTH"] = ""

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier, date_of_birth="1970-04-27")

    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(record_key=absence_case_id)

    employee, has_vendor_update = vendor_export.update_employee_info(
        test_db_session, extract_data, requested_absence, formatted_claim, validation_container
    )

    # Assert no validation issues even though date of birth field was missing
    assert len(validation_container.validation_issues) == 0
    # Assert date of birth was not wiped out
    assert employee.date_of_birth == datetime.date(1970, 4, 27)


def test_update_employee_info_payment_method_check_eft_issues(
    test_db_session, initialize_factories_session, formatted_claim
):
    """Test that EFT validation is skipped when payment method is not EFT."""
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)
    fineos_customer_number = "12345"
    # Set payment method to check.
    extract_data.employee_feed.indexed_data[fineos_customer_number]["PAYMENTMETHOD"] = "Check"
    # Routing number is too short.
    extract_data.employee_feed.indexed_data[fineos_customer_number]["SORTCODE"] = "1"

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(record_key=absence_case_id)

    employee, has_vendor_update = vendor_export.update_employee_info(
        test_db_session, extract_data, requested_absence, formatted_claim, validation_container
    )

    # Assert no validation issues even though eft fields had validation issues.
    assert len(validation_container.validation_issues) == 0
    # Assert payment method is check.
    assert employee.payment_method_id == PaymentMethod.CHECK.payment_method_id
    # Assert employee has no associated eft data.
    assert employee.eft is None


def test_update_employee_info_not_in_db(
    test_db_session, initialize_factories_session, formatted_claim
):
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)

    tax_identifier = TaxIdentifierFactory(tax_identifier="987654321")
    EmployeeFactory(tax_identifier=tax_identifier)

    absence_case_id = str(requested_absence.get("ABSENCE_CASENUMBER"))
    validation_container = payments_util.ValidationContainer(record_key=absence_case_id)

    employee, has_vendor_update = vendor_export.update_employee_info(
        test_db_session, extract_data, requested_absence, formatted_claim, validation_container
    )

    assert employee is None
    assert has_vendor_update is False


def test_update_mailing_address_happy_path(test_db_session, initialize_factories_session):
    employee = EmployeeFactory()
    feed_entry = {
        "ADDRESS1": "456 Park Avenue",
        "ADDRESS2": "",
        "ADDRESS4": "New York",
        "ADDRESS6": "NY",
        "POSTCODE": "11020",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_address_update = vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert updated_employee.ctr_address_pair.fineos_address.address_line_one == "456 Park Avenue"
    assert updated_employee.ctr_address_pair.fineos_address.address_line_two == ""
    assert updated_employee.ctr_address_pair.fineos_address.city == "New York"
    assert updated_employee.ctr_address_pair.fineos_address.geo_state_id == GeoState.NY.geo_state_id
    assert updated_employee.ctr_address_pair.fineos_address.zip_code == "11020"
    assert has_address_update is True


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
    create_triggers,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2019-12-31")

    s3 = boto3.client("s3")

    def add_s3_files(prefix):
        for expected_file_name in vendor_export.expected_file_names:
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
                "2020-01-01-11-30-00", ReferenceFileType.VENDOR_CLAIM_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.VENDOR_CLAIM_EXTRACT.reference_file_type_id,
    )
    ReferenceFileFactory.create(
        file_location=os.path.join(
            get_s3_config().pfml_fineos_inbound_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            payments_util.get_date_group_folder_name(
                "2020-01-03-11-30-00", ReferenceFileType.VENDOR_CLAIM_EXTRACT
            ),
        ),
        reference_file_type_id=ReferenceFileType.VENDOR_CLAIM_EXTRACT.reference_file_type_id,
    )

    employee_log_count_before = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_before == 0

    # confirm all unprocessed files were downloaded
    vendor_export.process_vendor_extract_data(test_db_session)
    destination_folder = os.path.join(
        get_s3_config().pfml_fineos_inbound_path, payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
    )
    processed_files = file_util.list_files(destination_folder, recursive=True)
    assert len(processed_files) == 6

    expected_file_names = []
    for date_file in vendor_export.expected_file_names:
        for unprocessed_date in ["2020-01-02-11-30-00", "2020-01-04-11-30-00"]:
            expected_file_names.append(
                f"{payments_util.get_date_group_folder_name(unprocessed_date, ReferenceFileType.VENDOR_CLAIM_EXTRACT)}/{unprocessed_date}-{date_file}"
            )

    for processed_file in processed_files:
        assert processed_file in expected_file_names

    # confirm no files will be copied in a subsequent copy
    copied_files = payments_util.copy_fineos_data_to_archival_bucket(
        test_db_session, vendor_export.expected_file_names, ReferenceFileType.VENDOR_CLAIM_EXTRACT
    )
    assert not copied_files

    employee_log_count_after = test_db_session.query(EmployeeLog).count()
    assert employee_log_count_after == employee_log_count_before


def test_update_mailing_address_validation_issues(test_db_session, initialize_factories_session):
    employee = EmployeeFactory()

    # Invalid zip code
    feed_entry = {
        "ADDRESS1": "456 Park Avenue",
        "ADDRESS2": "",
        "ADDRESS4": "New York",
        "ADDRESS6": "NY",
        "POSTCODE": "1102",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_address_update = vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert updated_employee.ctr_address_pair is None
    assert has_address_update is False

    # Invalid Geo State Code
    feed_entry = {
        "ADDRESS1": "456 Park Avenue",
        "ADDRESS2": "",
        "ADDRESS4": "New York",
        "ADDRESS6": "NZ",
        "POSTCODE": "11020",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_address_update = vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert updated_employee.ctr_address_pair is None
    assert has_address_update is False

    # Missing address line 1 and incorrect Geo State Code
    feed_entry = {
        "ADDRESS1": "",
        "ADDRESS2": "",
        "ADDRESS4": "New York",
        "ADDRESS6": "NZ",
        "POSTCODE": "11020",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_address_update = vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 2
    assert updated_employee.ctr_address_pair is None
    assert has_address_update is False


def test_update_eft_info_happy_path(test_db_session, initialize_factories_session):
    employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)

    assert employee.eft is None

    eft_entry = {"SORTCODE": "123456789", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert updated_employee.eft.routing_nbr == "123456789"
    assert updated_employee.eft.account_nbr == "123456789"
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )
    assert has_eft_update is True

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # state_log = state_log_util.get_latest_state_log_in_flow(
    #     employee, Flow.VENDOR_EFT, test_db_session
    # )
    # assert state_log
    # assert state_log.end_state_id == State.EFT_REQUEST_RECEIVED.state_id


def test_update_eft_info_update_existing(test_db_session, initialize_factories_session):
    employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)
    eft = EftFactory.create()
    employee.eft = eft
    test_db_session.add(employee)
    test_db_session.add(eft)
    test_db_session.commit()

    assert employee.eft is not None

    eft_entry = {"SORTCODE": "123456789", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert updated_employee.eft.eft_id == eft.eft_id
    assert updated_employee.eft.routing_nbr == "123456789"
    assert updated_employee.eft.account_nbr == "123456789"
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )
    assert has_eft_update is True

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # state_log = state_log_util.get_latest_state_log_in_flow(
    #     employee, Flow.VENDOR_EFT, test_db_session
    # )
    # assert state_log
    # assert state_log.end_state_id == State.EFT_REQUEST_RECEIVED.state_id


def test_update_eft_info_is_same_eft_no_prior_state(test_db_session, initialize_factories_session):
    employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)
    eft = EftFactory.create()
    employee.eft = eft
    test_db_session.add(employee)
    test_db_session.add(eft)
    test_db_session.commit()

    assert employee.eft is not None

    eft_entry = {
        "SORTCODE": eft.routing_nbr,
        "ACCOUNTNO": eft.account_nbr,
        "ACCOUNTTYPE": eft.bank_account_type.bank_account_type_description,
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert updated_employee.eft.eft_id == eft.eft_id
    assert updated_employee.eft.routing_nbr == eft.routing_nbr
    assert updated_employee.eft.account_nbr == eft.account_nbr
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )
    assert has_eft_update is True

    # TODO: Restore this test after we have a long-term solution for the hotfix in API-1370.
    #
    # state_log = state_log_util.get_latest_state_log_in_flow(
    #     employee, Flow.VENDOR_EFT, test_db_session
    # )
    # assert state_log.end_state_id == State.EFT_REQUEST_RECEIVED.state_id


def test_update_eft_info_is_same_eft_has_prior_eft_state(
    test_db_session, initialize_factories_session
):
    employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)
    eft = EftFactory.create()
    employee.eft = eft
    test_db_session.add(employee)
    test_db_session.add(eft)
    test_db_session.commit()

    assert employee.eft is not None

    eft_entry = {
        "SORTCODE": eft.routing_nbr,
        "ACCOUNTNO": eft.account_nbr,
        "ACCOUNTTYPE": eft.bank_account_type.bank_account_type_description,
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    state_log_util.create_finished_state_log(
        associated_model=employee,
        end_state=State.EFT_PENDING,
        outcome=state_log_util.build_outcome("Foo"),
        db_session=test_db_session,
    )

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert updated_employee.eft.eft_id == eft.eft_id
    assert updated_employee.eft.routing_nbr == eft.routing_nbr
    assert updated_employee.eft.account_nbr == eft.account_nbr
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )
    assert has_eft_update is False

    state_log = state_log_util.get_latest_state_log_in_flow(
        employee, Flow.VENDOR_EFT, test_db_session
    )
    assert state_log.end_state_id == State.EFT_PENDING.state_id


def test_update_eft_info_validation_issues(test_db_session, initialize_factories_session):
    employee = EmployeeFactory()

    # Routing number incorrect length.
    eft_entry = {"SORTCODE": "12345678", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert updated_employee.eft is None
    assert has_eft_update is False

    # Account number incorrect length.
    eft_entry = {
        "SORTCODE": "123456789",
        "ACCOUNTNO": "12345678901234567890123456789012345678901234567890",
        "ACCOUNTTYPE": "Checking",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert updated_employee.eft is None
    assert has_eft_update is False

    # Account type incorrect.
    eft_entry = {
        "SORTCODE": "123456789",
        "ACCOUNTNO": "123456789012345678901234567890",
        "ACCOUNTTYPE": "Certificate of Deposit",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1
    assert updated_employee.eft is None
    assert has_eft_update is False

    # Account type and Routing number incorrect.
    eft_entry = {
        "SORTCODE": "12345678",
        "ACCOUNTNO": "123456789012345678901234567890",
        "ACCOUNTTYPE": "Certificate of Deposit",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    has_eft_update = vendor_export.update_eft_info(
        test_db_session, eft_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 2
    assert updated_employee.eft is None
    assert has_eft_update is False


# TODO: Add test if there are no validation issues with EFT
def test_process_records_to_db_validation_issues(
    test_db_session, initialize_factories_session, formatted_claim
):
    # Setup
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)
    # Create some validation issues
    extract_data.employee_feed.indexed_data["12345"]["SORTCODE"] = ""
    requested_absence["ABSENCEPERIOD_END"] = ""
    extract_data.requested_absence_info = vendor_export.Extract("test/location/requested_absence")
    extract_data.requested_absence_info.indexed_data["NTN-001-ABS-01"] = requested_absence

    tax_identifier = TaxIdentifierFactory(tax_identifier="123456789")
    EmployeeFactory(tax_identifier=tax_identifier)

    # Run the process
    vendor_export.process_records_to_db(extract_data, test_db_session)

    # Verify the state logs
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 1

    state_log = state_logs[0]
    assert state_log.end_state_id == State.ADD_TO_VENDOR_EXPORT_ERROR_REPORT.state_id


def test_process_records_to_db_no_vendor_updates_has_prior_eft_state(
    test_db_session, initialize_factories_session, formatted_claim
):
    # Setup
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)
    extract_data.requested_absence_info = vendor_export.Extract("test/location/requested_absence")
    extract_data.requested_absence_info.indexed_data["NTN-001-ABS-01"] = requested_absence

    # Create an employee with address and EFT that exactly matches the input
    # Make the DOB different. That should not trigger the VENDOR_CHECK state change
    tax_identifier = TaxIdentifierFactory.create(tax_identifier="123456789")
    eft = EftFactory.create(
        routing_nbr=extract_data.employee_feed.indexed_data["12345"]["SORTCODE"],
        account_nbr=extract_data.employee_feed.indexed_data["12345"]["ACCOUNTNO"],
        bank_account_type_id=2,
    )
    address = AddressFactory.create(
        address_line_one=extract_data.employee_feed.indexed_data["12345"]["ADDRESS1"],
        address_line_two=extract_data.employee_feed.indexed_data["12345"]["ADDRESS2"],
        city=extract_data.employee_feed.indexed_data["12345"]["ADDRESS4"],
        geo_state_id=GeoState.NY.geo_state_id,
        zip_code=extract_data.employee_feed.indexed_data["12345"]["POSTCODE"],
    )
    ctr_address_pair = CtrAddressPairFactory.create(fineos_address=address,)
    employee = EmployeeFactory.create(
        tax_identifier=tax_identifier,
        date_of_birth="1967-04-27",
        eft=eft,
        ctr_address_pair=ctr_address_pair,
    )

    # Create a statelog for this employee to verify the state doesn't change
    state_log_util.create_finished_state_log(
        associated_model=employee,
        end_state=State.VCC_ERROR_REPORT_SENT,
        outcome=state_log_util.build_outcome("Foo"),
        db_session=test_db_session,
    )

    # Create a state log for the VENDOR_EFT flow
    state_log_util.create_finished_state_log(
        associated_model=employee,
        end_state=State.EFT_PENDING,
        outcome=state_log_util.build_outcome("Foo"),
        db_session=test_db_session,
    )

    # Verify the state log
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 2

    # Run the process
    vendor_export.process_records_to_db(extract_data, test_db_session)

    # Verify both state logs are in the same state
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 3

    for state_log in state_logs:
        assert state_log.end_state_id in [
            State.VCC_ERROR_REPORT_SENT.state_id,
            State.EFT_PENDING.state_id,
        ]


def test_process_records_to_db_no_vendor_updates_has_prior_validation_issues(
    test_db_session, initialize_factories_session, formatted_claim
):
    # Setup
    extract_data, requested_absence = format_absence_data()
    add_employee_feed(extract_data)
    extract_data.requested_absence_info = vendor_export.Extract("test/location/requested_absence")
    extract_data.requested_absence_info.indexed_data["NTN-001-ABS-01"] = requested_absence

    # Create an employee with address and EFT that exactly matches the input
    # Make the DOB different. That should not trigger the VENDOR_CHECK state change
    tax_identifier = TaxIdentifierFactory.create(tax_identifier="123456789")
    eft = EftFactory.create(
        routing_nbr=extract_data.employee_feed.indexed_data["12345"]["SORTCODE"],
        account_nbr=extract_data.employee_feed.indexed_data["12345"]["ACCOUNTNO"],
        bank_account_type_id=2,
    )
    address = AddressFactory.create(
        address_line_one=extract_data.employee_feed.indexed_data["12345"]["ADDRESS1"],
        address_line_two=extract_data.employee_feed.indexed_data["12345"]["ADDRESS2"],
        city=extract_data.employee_feed.indexed_data["12345"]["ADDRESS4"],
        geo_state_id=GeoState.NY.geo_state_id,
        zip_code=extract_data.employee_feed.indexed_data["12345"]["POSTCODE"],
    )
    ctr_address_pair = CtrAddressPairFactory.create(fineos_address=address,)
    employee = EmployeeFactory.create(
        tax_identifier=tax_identifier,
        # date_of_birth="1967-04-27",
        eft=eft,
        ctr_address_pair=ctr_address_pair,
    )

    # Create a statelog for this employee to verify the state doesn't change
    state_log_util.create_finished_state_log(
        associated_model=employee,
        end_state=State.VENDOR_EXPORT_ERROR_REPORT_SENT,
        outcome=state_log_util.build_outcome("Vendor Check Foo"),
        db_session=test_db_session,
    )

    # Create a state log for the VENDOR_EFT flow
    state_log_util.create_finished_state_log(
        associated_model=employee,
        end_state=State.EFT_PENDING,
        outcome=state_log_util.build_outcome("Vendor EFT Foo"),
        db_session=test_db_session,
    )

    # Verify the state log
    state_logs = test_db_session.query(StateLog).all()
    assert len(state_logs) == 2

    # Run the process
    vendor_export.process_records_to_db(extract_data, test_db_session)

    # Verify the EFT state log is in the same state and the Vendor Check state
    # log is now in IDENTIFY_MMARS_STATUS
    state_logs = test_db_session.query(StateLog).join(LatestStateLog).all()
    assert len(state_logs) == 2
    for state_log in state_logs:
        assert state_log.end_state_id in [
            State.IDENTIFY_MMARS_STATUS.state_id,
            State.EFT_PENDING.state_id,
        ]

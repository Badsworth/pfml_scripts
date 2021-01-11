import os
from typing import List, Optional

import boto3
import pytest

import massgov.pfml.payments.fineos_vendor_export as vendor_export
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    Claim,
    ClaimType,
    Employee,
    GeoState,
    PaymentMethod,
    ReferenceFileType,
)
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.payments.config import get_s3_config
from massgov.pfml.util import datetime
from tests.api.payments.conftest import upload_file_to_s3


@pytest.fixture
def emp_updates_path(tmp_path, mock_fineos_s3_bucket):
    requested_absence_file_name = "2020-12-21-19-20-42-VBI_REQUESTEDABSENCE_SOM.csv"
    content_line_one = '"NOTIFICATION_CASENUMBER","ABSENCE_CASENUMBER","ABSENCE_CASETYPENAME","ABSENCE_CASESTATUS","ABSENCE_CASEOWNER","ABSENCE_CASECREATIONDATE","ABSENCE_CASELASTUPDATEDATE","ABSENCE_INTAKESOURCE","ABSENCE_NOTIFIEDBY","EMPLOYEE_CUSTOMERNO","EMPLOYEE_MANAGER_CUSTOMERNO","EMPLOYEE_ADDTL_MNGR_CUSTOMERNO","EMPLOYER_CUSTOMERNO","EMPLOYER_NAME","EMPLOYMENT_CLASSID","EMPLOYMENT_INDEXID","LEAVEREQUEST_ID","LEAVEREQUEST_NOTIFICATIONDATE","LEAVEREQUEST_LASTUPDATEDATE","LEAVEREQUEST_ORIGINALREQUEST","LEAVEREQUEST_EVIDENCERESULTTYPE","LEAVEREQUEST_DECISION","LEAVEREQUEST_DIAGNOSIS","ABSENCEREASON_CLASSID","ABSENCEREASON_INDEXID","ABSENCEREASON_NAME","ABSENCEREASON_QUALIFIER1","ABSENCEREASON_QUALIFIER2","ABSENCEREASON_COVERAGE","PRIMARY_RELATIONSHIP_NAME","PRIMARY_RELATIONSHIP_QUAL1","PRIMARY_RELATIONSHIP_QUAL2","PRIMARY_RELATIONSHIP_COVER","SECONDARY_RELATIONSHIP_NAME","SECONDARY_RELATIONSHIP_QUAL1","SECONDARY_RELATIONSHIP_QUAL2","SECONDARY_RELATIONSHIP_COVER","ABSENCEPERIOD_CLASSID","ABSENCEPERIOD_INDEXID","ABSENCEPERIOD_TYPE","ABSENCEPERIOD_STATUS","ABSENCEPERIOD_START","ABSENCEPERIOD_END","EPISODE_FREQUENCY_COUNT","EPISODE_FREQUENCY_PERIOD","EPISODIC_FREQUENCY_PERIOD_UNIT","EPISODE_DURATION","EPISODIC_DURATION_UNIT"'
    content_line_two = '"NTN-2922","NTN-2922-ABS-01","Absence Case","Adjudication","SaviLinx","2020-11-02 09:52:11","2020-11-02 09:53:10","Phone","Employee","339","","2825","96","Wayne Enterprises","14453","8524","2198","2020-11-02 00:00:00","2020-11-02 09:53:30","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6236","Time off period","Please Select","2021-01-15 00:00:00","2021-01-18 00:00:00","","","Please Select","","Please Select"'
    content_line_three = '"NTN-2923","NTN-2923-ABS-01","Absence Case","Adjudication","SaviLinx","2020-11-02 09:57:26","2020-11-02 10:03:18","Phone","Employee","3277","","2825","96","Wayne Enterprises","14453","8525","2199","2020-11-01 00:00:00","2020-11-02 10:03:18","1","Pending","Pending","","14412","7","Child Bonding","Adoption","","Family","","","","Please Select","","","","Please Select","14449","6238","Time off period","Please Select","2021-02-19 00:00:00","2021-02-19 00:00:00","","","Please Select","","Please Select"'
    content_line_four = '"NTN-1308","NTN-1308-ABS-01","Absence Case","Adjudication","SaviLinx","2020-10-22 21:09:24","2020-10-22 21:09:33","Self-Service","Employee","339","","2825","96","Wayne Enterprises","14453","7310","997","2020-10-22 21:09:24","2020-10-22 21:09:33","1","Satisfied","Pending","","14412","19","Serious Health Condition - Employee","Not Work Related","Sickness","Employee","","","","Please Select","","","","Please Select","14449","4230","Time off period","Known","2021-05-13 00:00:00","2021-07-22 00:00:00","","","Please Select","","Please Select"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}\n{content_line_four}"

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


def test_process_vendor_extract_data_happy_path(
    test_db_session,
    initialize_factories_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    tax_identifier = TaxIdentifierFactory(tax_identifier="881778956")
    employee = EmployeeFactory(tax_identifier=tax_identifier)
    employer = EmployerFactory(fineos_employer_id=96)

    vendor_export.process_vendor_extract_data(test_db_session)

    # Requested absences file artifact above has three records but only one with the
    # LEAVEREQUEST_EVIDENCERESULTTYPE != Satisfied
    claims: List[Claim] = (
        test_db_session.query(Claim).filter(Claim.fineos_absence_id == "NTN-1308-ABS-01").all()
    )

    assert len(claims) == 1
    claim = claims[0]

    assert claim is not None
    assert claim.employee_id == employee.employee_id
    assert claim.employer_id == employer.employer_id

    assert claim.fineos_notification_id == "NTN-1308"
    assert claim.claim_type.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id
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

    assert updated_employee.eft.routing_nbr == 123546789
    assert updated_employee.eft.account_nbr == 123546789
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )


def test_process_vendor_extract_data_no_employee(
    test_db_session,
    initialize_factories_session,
    emp_updates_path,
    set_exporter_env_vars,
    monkeypatch,
):
    monkeypatch.setenv("FINEOS_VENDOR_MAX_HISTORY_DATE", "2020-12-20")

    vendor_export.process_vendor_extract_data(test_db_session)

    claim: Claim = (
        test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == "NTN-1308-ABS-01")
        .one_or_none()
    )

    assert claim is None


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

    vendor_export.update_mailing_address(
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


def test_process_extract_unprocessed_folder_files(
    mock_fineos_s3_bucket,
    set_exporter_env_vars,
    test_db_session,
    tmp_path,
    initialize_factories_session,
    monkeypatch,
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

    vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1

    assert updated_employee.ctr_address_pair is None

    # Invalid Geo State Code
    feed_entry = {
        "ADDRESS1": "456 Park Avenue",
        "ADDRESS2": "",
        "ADDRESS4": "New York",
        "ADDRESS6": "NZ",
        "POSTCODE": "11020",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1

    assert updated_employee.ctr_address_pair is None

    # Missing address line 1 and incorrect Geo State Code
    feed_entry = {
        "ADDRESS1": "",
        "ADDRESS2": "",
        "ADDRESS4": "New York",
        "ADDRESS6": "NZ",
        "POSTCODE": "11020",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_mailing_address(
        test_db_session, feed_entry, employee, validation_container
    )

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 2

    assert updated_employee.ctr_address_pair is None


def test_update_eft_info_happy_path(test_db_session, initialize_factories_session):
    employee = EmployeeFactory()

    eft_entry = {"SORTCODE": "123456789", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_eft_info(test_db_session, eft_entry, employee, validation_container)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert updated_employee.eft.routing_nbr == 123456789
    assert updated_employee.eft.account_nbr == 123456789
    assert (
        updated_employee.eft.bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id
    )


def test_update_eft_info_validation_issues(test_db_session, initialize_factories_session):
    employee = EmployeeFactory()

    # Routing number incorrect length.
    eft_entry = {"SORTCODE": "12345678", "ACCOUNTNO": "123456789", "ACCOUNTTYPE": "Checking"}
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_eft_info(test_db_session, eft_entry, employee, validation_container)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1

    assert updated_employee.eft is None

    # Account number incorrect length.
    eft_entry = {
        "SORTCODE": "123456789",
        "ACCOUNTNO": "12345678901234567890123456789012345678901234567890",
        "ACCOUNTTYPE": "Checking",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_eft_info(test_db_session, eft_entry, employee, validation_container)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1

    assert updated_employee.eft is None

    # Account type incorrect.
    eft_entry = {
        "SORTCODE": "123456789",
        "ACCOUNTNO": "123456789012345678901234567890",
        "ACCOUNTTYPE": "Certificate of Deposit",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_eft_info(test_db_session, eft_entry, employee, validation_container)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 1

    assert updated_employee.eft is None

    # Account type and Routing number incorrect.
    eft_entry = {
        "SORTCODE": "12345678",
        "ACCOUNTNO": "123456789012345678901234567890",
        "ACCOUNTTYPE": "Certificate of Deposit",
    }
    validation_container = payments_util.ValidationContainer(record_key=employee.employee_id)

    vendor_export.update_eft_info(test_db_session, eft_entry, employee, validation_container)

    updated_employee: Optional[Employee] = test_db_session.query(Employee).filter(
        Employee.employee_id == employee.employee_id
    ).one_or_none()

    assert len(validation_container.validation_issues) == 2

    assert updated_employee.eft is None

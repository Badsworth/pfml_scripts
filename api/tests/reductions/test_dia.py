import os
from datetime import date

import boto3
import pytest

from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory, TaxIdentifierFactory
from massgov.pfml.payments.payments_util import get_now
from massgov.pfml.reductions.dia import (
    Constants,
    create_list_of_approved_claimants,
    format_claims_for_dia_claimant_list,
    get_approved_claims,
    get_approved_claims_info_csv_path,
)


@pytest.fixture
def set_up(test_db_session, initialize_factories_session):
    start_date = date(2021, 1, 28)
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee_info = {
        "date_of_birth": date(1979, 11, 12),
        "first_name": "John",
        "last_name": "Doe",
        "tax_identifier": tax_id,
    }

    employee1 = EmployeeFactory.create(**employee_info)
    employee2 = EmployeeFactory.create(**employee_info)
    ClaimFactory.create(
        employee=employee1,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=start_date,
    )
    ClaimFactory.create(
        employee=employee2,
        fineos_absence_status_id=AbsenceStatus.DECLINED.absence_status_id,
        absence_period_start_date=start_date,
    )

    approved_claims = get_approved_claims(test_db_session)

    return approved_claims


@pytest.fixture
def set_up_invalid_data(test_db_session, initialize_factories_session):
    start_date = date(2021, 1, 28)
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee_info = {
        "date_of_birth": date(1979, 11, 12),
        "first_name": "Jo,hn",
        "last_name": "Doe",
        "tax_identifier": tax_id,
    }

    employee1 = EmployeeFactory.create(**employee_info)
    employee2 = EmployeeFactory.create(**employee_info)
    ClaimFactory.create(
        employee=employee1,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=start_date,
    )
    ClaimFactory.create(
        employee=employee2,
        fineos_absence_status_id=AbsenceStatus.DECLINED.absence_status_id,
        absence_period_start_date=start_date,
    )

    approved_claims = get_approved_claims(test_db_session)

    return approved_claims


def test_get_approved_claims(set_up, test_db_session):
    approved_claims = set_up
    assert len(approved_claims) == 1


def test_format_claims_for_dia_claimant_list(set_up):
    approved_claims = set_up
    claim = approved_claims[0]
    employee = claim.employee
    approved_claims_dia_info = format_claims_for_dia_claimant_list(approved_claims)

    for approved_claim in approved_claims_dia_info:
        assert approved_claim[Constants.CASE_ID_FIELD] == claim.fineos_absence_id
        assert (
            approved_claim[Constants.BENEFIT_START_DATE_FIELD]
            == Constants.TEMPORARY_BENEFIT_START_DATE
        )
        assert approved_claim[Constants.FIRST_NAME_FIELD] == employee.first_name
        assert approved_claim[Constants.LAST_NAME_FIELD] == employee.last_name
        assert approved_claim[Constants.BIRTH_DATE_FIELD] == employee.date_of_birth.strftime(
            Constants.DATE_OF_BIRTH_FORMAT
        )
        assert isinstance(approved_claim[Constants.BIRTH_DATE_FIELD], str)
        assert approved_claim[Constants.SSN_FIELD] == employee.tax_identifier.tax_identifier
        assert "-" not in approved_claim[Constants.SSN_FIELD]


def test_get_approved_claims_info_csv_path(set_up):
    approved_employees = set_up
    approved_claims_dia_info = format_claims_for_dia_claimant_list(approved_employees)
    file_path = get_approved_claims_info_csv_path(approved_claims_dia_info)
    file_name = (
        Constants.CLAIMAINT_LIST_FILENAME_PREFIX
        + get_now().strftime(Constants.CLAIMAINT_LIST_FILENAME_TIME_FORMAT)
        + ".csv"
    )

    assert file_path.name == file_name


def test_get_approved_claims_info_csv_path_invalid_data(set_up_invalid_data):
    approved_employees = set_up_invalid_data

    with pytest.raises(ValueError):
        approved_claims_dia_info = format_claims_for_dia_claimant_list(approved_employees)
        get_approved_claims_info_csv_path(approved_claims_dia_info)


def test_create_list_of_approved_claimants(monkeypatch, mock_s3_bucket, test_db_session, set_up):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "pfml/inbox"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_OUTBOUND_DIRECTORY_PATH", dest_dir)

    approved_employees = set_up
    approved_claims_dia_info = format_claims_for_dia_claimant_list(approved_employees)
    file_path = get_approved_claims_info_csv_path(approved_claims_dia_info)

    create_list_of_approved_claimants(test_db_session)

    # Expect that the file to appear in the mock_s3_bucket.
    s3 = boto3.client("s3")

    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    if object_list:
        assert len(object_list) == 1
        dest_filepath = os.path.join(dest_dir, file_path.name)
        assert object_list[0]["Key"] == dest_filepath

    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DIA_CLAIMANT_LIST.reference_file_type_id
        )
        .all()
    )
    state_log = (
        test_db_session.query(StateLog)
        .filter_by(end_state_id=State.DIA_CLAIMANT_LIST_CREATED.state_id)
        .all()
    )

    assert len(ref_file) == 1
    assert len(state_log) == 1
    assert ref_file[0].file_location == os.path.join(s3_bucket_uri, dest_dir, file_path.name)

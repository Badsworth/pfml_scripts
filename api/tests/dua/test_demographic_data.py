import os
from datetime import date, datetime

import pytest
from freezegun import freeze_time

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    DuaEmployeeDemographics,
    EmployeePushToFineosQueue,
    Gender,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.factories import (
    DuaEmployeeDemographicsFactory,
    DuaReportingUnitFactory,
    EmployeeFactory,
    EmployeeOccupationFactory,
    EmployeeWithFineosNumberFactory,
    EmployerFactory,
    OrganizationUnitFactory,
)
from massgov.pfml.dua.config import get_moveit_config, get_transfer_config
from massgov.pfml.dua.demographics import (
    download_demographics_file_from_moveit,
    load_demographics_file,
    set_employee_occupation_from_demographic_data,
)
from massgov.pfml.util.batch.log import LogEntry


def get_mock_data():
    return ReferenceFile(
        file_location=os.path.join(
            os.path.dirname(__file__), "test_files", "test_dua_demographic_data.csv"
        )
    )


def get_mock_data_next():
    return ReferenceFile(
        file_location=os.path.join(
            os.path.dirname(__file__), "test_files", "test_dua_demographic_data_other.csv"
        )
    )


@pytest.fixture
def add_test_employees(initialize_factories_session):
    return [
        EmployeeFactory.create(fineos_customer_number="1234567"),
        EmployeeFactory.create(fineos_customer_number="7654321"),
        EmployeeFactory.create(fineos_customer_number="1111111"),
        EmployeeFactory.create(fineos_customer_number="2222222", gender_id=Gender.WOMAN.gender_id),
        EmployeeFactory.create(fineos_customer_number="3333333"),
        EmployeeFactory.create(fineos_customer_number="4444444"),
        EmployeeFactory.create(fineos_customer_number="5555555"),
        EmployeeFactory.create(fineos_customer_number="6666666"),
        EmployeeFactory.create(fineos_customer_number="7777777"),
        EmployeeFactory.create(fineos_customer_number="8888888"),
        EmployeeFactory.create(fineos_customer_number="9999999"),
    ]


def test_import_multiple_files_new_data(test_db_session, monkeypatch, mock_s3_bucket):
    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_data()
        transfer_config = get_transfer_config()
        load_demographics_file(test_db_session, reference_file, log_entry, transfer_config)

        metrics = log_entry.metrics

        # 11 rows in the file (not counting headers)
        assert metrics["total_dua_demographics_row_count"] == 11
        assert metrics["inserted_dua_demographics_row_count"] == 10
        assert metrics["successful_dua_demographics_reference_files_count"] == 1
        assert metrics["pending_dua_demographics_reference_files_count"] == 1

        found_data_to_validate = False

        processed_records = (test_db_session.query(DuaEmployeeDemographics)).all()
        for record in processed_records:
            if record.fineos_customer_number == "1234567":
                found_data_to_validate = True
                assert record.gender_code == "F"
                assert record.occupation_code == "1120"
                assert record.occupation_description == "Sales Managers"
                assert record.employer_fein == ""
                assert record.employer_reporting_unit_number == ""

        # Make sure we are validate at least one row
        assert found_data_to_validate
        assert len(processed_records) == 10

        reference_file_next = get_mock_data_next()
        load_demographics_file(test_db_session, reference_file_next, log_entry, transfer_config)

        # 2 new rows in this file
        assert metrics["inserted_dua_demographics_row_count"] == 12


def test_update_employee_demographics_file_mode(test_db_session, monkeypatch, mock_s3_bucket):

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_data()
        transfer_config = get_transfer_config()
        load_demographics_file(test_db_session, reference_file, log_entry, transfer_config)

        metrics = log_entry.metrics

        # 11 rows in the file (not counting headers)
        assert metrics["total_dua_demographics_row_count"] == 11
        assert metrics["successful_dua_demographics_reference_files_count"] == 1
        assert metrics["pending_dua_demographics_reference_files_count"] == 1

        processed_records = (test_db_session.query(DuaEmployeeDemographics)).all()

        assert len(processed_records) == 10


def test_set_employee_occupation_from_demographics_data(
    test_db_session, initialize_factories_session
):

    with LogEntry(test_db_session, "test log entry") as log_entry:
        employer = EmployerFactory()

        org_unit = OrganizationUnitFactory(name="Foo", employer=employer)

        reporting_unit_with_org_unit = DuaReportingUnitFactory(organization_unit=org_unit)

        # Rows pointing to an employee we don't have a record of shouldn't crash things
        DuaEmployeeDemographicsFactory(
            fineos_customer_number="999",
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_with_org_unit.dua_id,
        )

        # Rows pointing to an employer we don't have a record of shouldn't crash things
        DuaEmployeeDemographicsFactory(
            fineos_customer_number="1234567",
            employer_fein="",
            employer_reporting_unit_number=reporting_unit_with_org_unit.dua_id,
        )

        # Scenario where org unit id will be set on an existing occupation
        employee_without_existing_org_unit = EmployeeFactory(
            fineos_customer_number="1234567", gender_id=Gender.WOMAN.gender_id,
        )

        employee_without_existing_org_unit_occupation = EmployeeOccupationFactory(
            employee=employee_without_existing_org_unit, employer=employer
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_without_existing_org_unit.fineos_customer_number,
            date_of_birth=date(1978, 2, 17),
            gender_code="F",
            occupation_code=1120,
            occupation_description="Sales Managers",
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_with_org_unit.dua_id,
        )

        # Scenario where org unit id can't be found
        employee_no_matching_org_unit = EmployeeFactory(fineos_customer_number="7654321")

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_no_matching_org_unit.fineos_customer_number,
            date_of_birth=date(1979, 10, 13),
            gender_code="M",
            occupation_code=1120,
            occupation_description="Marketing Managers",
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number="1001",  # non existant dua_reporting_unit dua_id
        )

        # Scenario where org unit id is skipped
        org_unit_not_dua = OrganizationUnitFactory(name="Non-DUA org unit", employer=employer)

        employee_with_existing_org_unit = EmployeeFactory(fineos_customer_number="1111111")

        employee_occupation_two = EmployeeOccupationFactory(
            employee=employee_with_existing_org_unit,
            employer=employer,
            organization_unit_id=org_unit_not_dua.organization_unit_id,
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_with_existing_org_unit.fineos_customer_number,
            date_of_birth=date(1998, 5, 6),
            gender_code="M",
            occupation_code=5191,
            occupation_description="Packaging and Filling Machine Operators and Tenders",
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_with_org_unit.dua_id,
        )

        # Scenario where EmployeeOccupation is created
        employee_no_previous_occupation = EmployeeFactory(fineos_customer_number="4444444")

        assert employee_no_previous_occupation.employee_occupations.count() == 0

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_no_previous_occupation.fineos_customer_number,
            date_of_birth=date(1995, 3, 18),
            gender_code="F",
            occupation_code=2920,
            occupation_description="Licensed Practical and Licensed Vocational Nurses",
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_with_org_unit.dua_id,
        )

        # No matching Org Unit for the listed DUA Reporting Unit
        reporting_unit_no_org_unit = DuaReportingUnitFactory(
            organization_unit=None, organization_unit_id=None
        )

        employee_no_matching_dua_reporting_unit = EmployeeWithFineosNumberFactory()

        employee_occupation_no_matching_dua_reporting_unit = EmployeeOccupationFactory(
            employee=employee_no_matching_dua_reporting_unit, employer=employer
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_no_matching_dua_reporting_unit.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_no_org_unit.dua_id,
        )

        test_db_session.commit()

        set_employee_occupation_from_demographic_data(test_db_session, log_entry=log_entry)

        metrics = log_entry.metrics

        assert metrics["missing_dua_reporting_unit_count"] == 1
        assert metrics["created_employee_occupation_count"] == 1
        assert metrics["occupation_org_unit_skipped_count"] == 1
        assert metrics["occupation_org_unit_set_count"] == 1
        assert metrics["dua_reporting_unit_missing_fineos_org_unit_count"] == 1

        assert (
            employee_without_existing_org_unit_occupation.organization_unit_id
            == org_unit.organization_unit_id
        )

        assert employee_occupation_two.organization_unit_id == org_unit_not_dua.organization_unit_id
        assert employee_occupation_no_matching_dua_reporting_unit.organization_unit_id is None

        assert employee_no_previous_occupation.employee_occupations.count() == 1

        eligibility_updates = (
            test_db_session.query(EmployeePushToFineosQueue)
            .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
            .all()
        )
        assert len(eligibility_updates) == 1

        assert (
            eligibility_updates[0].employee_id
            == employee_without_existing_org_unit_occupation.employee_id
        )
        assert eligibility_updates[0].employer_id == employer.employer_id


def test_set_employee_occupation_from_demographics_data_multiple_dua_records(
    test_db_session, initialize_factories_session
):
    with LogEntry(test_db_session, "test log entry") as log_entry:
        employer = EmployerFactory()

        org_unit_one = OrganizationUnitFactory(employer=employer)
        org_unit_two = OrganizationUnitFactory(employer=employer)

        reporting_unit_one = DuaReportingUnitFactory(organization_unit=org_unit_one)
        reporting_unit_two = DuaReportingUnitFactory(organization_unit=org_unit_two)

        employee = EmployeeWithFineosNumberFactory()

        employee_occupation = EmployeeOccupationFactory(employee=employee, employer=employer)

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_one.dua_id,
            created_at=datetime(2021, 11, 1),
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_two.dua_id,
            created_at=datetime(2021, 11, 2),
        )

        test_db_session.commit()

        set_employee_occupation_from_demographic_data(test_db_session, log_entry=log_entry)

        metrics = log_entry.metrics

        assert metrics["occupation_org_unit_set_count"] == 1

        assert employee_occupation.organization_unit_id == org_unit_two.organization_unit_id

        eligibility_updates = (
            test_db_session.query(EmployeePushToFineosQueue)
            .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
            .all()
        )
        assert len(eligibility_updates) == 1

        assert eligibility_updates[0].employee_id == employee.employee_id
        assert eligibility_updates[0].employer_id == employer.employer_id


def test_set_employee_occupation_from_demographics_data_multiple_dua_records_time_filter(
    test_db_session, initialize_factories_session
):
    with LogEntry(test_db_session, "test log entry") as log_entry:
        employer = EmployerFactory()

        org_unit_one = OrganizationUnitFactory(employer=employer)
        org_unit_two = OrganizationUnitFactory(employer=employer)

        reporting_unit_one = DuaReportingUnitFactory(organization_unit=org_unit_one)
        reporting_unit_two = DuaReportingUnitFactory(organization_unit=org_unit_two)

        employee = EmployeeWithFineosNumberFactory()

        employee_occupation = EmployeeOccupationFactory(employee=employee, employer=employer)

        employee_not_updated = EmployeeWithFineosNumberFactory()

        employee_not_updated_occupation = EmployeeOccupationFactory(
            employee=employee_not_updated, employer=employer
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_not_updated.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_one.dua_id,
            created_at=datetime(2021, 11, 1),
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_two.dua_id,
            created_at=datetime(2021, 11, 2),
        )

        test_db_session.commit()

        set_employee_occupation_from_demographic_data(
            test_db_session, log_entry=log_entry, after_created_at=datetime(2021, 11, 2)
        )

        metrics = log_entry.metrics

        assert metrics == {"occupation_org_unit_set_count": 1}

        assert employee_occupation.organization_unit_id == org_unit_two.organization_unit_id
        assert employee_not_updated_occupation.organization_unit_id is None

        eligibility_updates = (
            test_db_session.query(EmployeePushToFineosQueue)
            .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
            .all()
        )
        assert len(eligibility_updates) == 1

        assert eligibility_updates[0].employee_id == employee.employee_id
        assert eligibility_updates[0].employer_id == employer.employer_id


def test_set_employee_occupation_from_demographics_data_multiple_employers(
    test_db_session, initialize_factories_session
):
    with LogEntry(test_db_session, "test log entry") as log_entry:
        employer_one = EmployerFactory()
        employer_two = EmployerFactory()

        org_unit_one = OrganizationUnitFactory(employer=employer_one)
        org_unit_two = OrganizationUnitFactory(employer=employer_two)

        reporting_unit_one = DuaReportingUnitFactory(organization_unit=org_unit_one)
        reporting_unit_two = DuaReportingUnitFactory(organization_unit=org_unit_two)

        employee = EmployeeWithFineosNumberFactory()

        employee_occupation_one = EmployeeOccupationFactory(
            employee=employee, employer=employer_one
        )

        employee_occupation_two = EmployeeOccupationFactory(
            employee=employee, employer=employer_two
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee.fineos_customer_number,
            employer_fein=employer_one.employer_fein,
            employer_reporting_unit_number=reporting_unit_one.dua_id,
        )

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee.fineos_customer_number,
            employer_fein=employer_two.employer_fein,
            employer_reporting_unit_number=reporting_unit_two.dua_id,
        )

        test_db_session.commit()

        set_employee_occupation_from_demographic_data(test_db_session, log_entry=log_entry)

        metrics = log_entry.metrics

        assert metrics["occupation_org_unit_set_count"] == 2

        assert employee_occupation_one.organization_unit_id == org_unit_one.organization_unit_id
        assert employee_occupation_two.organization_unit_id == org_unit_two.organization_unit_id

        eligibility_updates = (
            test_db_session.query(EmployeePushToFineosQueue)
            .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
            .all()
        )
        assert len(eligibility_updates) == 2

        assert {
            (eligibility_updates[0].employee_id, eligibility_updates[0].employer_id),
            (eligibility_updates[1].employee_id, eligibility_updates[1].employer_id),
        } == {
            (employee.employee_id, employer_one.employer_id),
            (employee.employee_id, employer_two.employer_id),
        }


def test_set_employee_occupation_from_demographics_data_missing_ids(
    test_db_session, initialize_factories_session
):
    # It shouldn't be possible for a DuaEmployeeDemographics row to be missing a
    # `fineos_customer_number`, but just in case.
    with LogEntry(test_db_session, "test log entry") as log_entry:
        employer = EmployerFactory()

        org_unit_one = OrganizationUnitFactory(employer=employer)
        org_unit_two = OrganizationUnitFactory(employer=employer)

        reporting_unit_one = DuaReportingUnitFactory(organization_unit=org_unit_one)
        reporting_unit_two = DuaReportingUnitFactory(organization_unit=org_unit_two)

        # null customer number
        employee_one = EmployeeFactory(fineos_customer_number=None)

        EmployeeOccupationFactory(employee=employee_one, employer=employer)

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_one.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_one.dua_id,
            created_at=datetime(2021, 11, 1),
        )

        # empty customer number
        employee_two = EmployeeFactory(fineos_customer_number="")

        EmployeeOccupationFactory(employee=employee_two, employer=employer)

        DuaEmployeeDemographicsFactory(
            fineos_customer_number=employee_two.fineos_customer_number,
            employer_fein=employer.employer_fein,
            employer_reporting_unit_number=reporting_unit_two.dua_id,
            created_at=datetime(2021, 11, 2),
        )

        test_db_session.commit()

        set_employee_occupation_from_demographic_data(test_db_session, log_entry=log_entry)

        metrics = log_entry.metrics

        assert metrics == {}

        eligibility_updates = (
            test_db_session.query(EmployeePushToFineosQueue)
            .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
            .all()
        )
        assert len(eligibility_updates) == 0


@freeze_time("2020-12-07")
def test_update_employee_demographics_moveit_mode(
    initialize_factories_session,
    test_db_session,
    monkeypatch,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
):

    source_directory_path = "dua/pending"
    archive_directory_path = "dua/archive"
    moveit_pickup_path = "upload/DFML/DUA/Inbound"

    monkeypatch.setenv("DUA_TRANSFER_BASE_PATH", "local_s3/agency_transfer")
    monkeypatch.setenv("OUTBOUND_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("ARCHIVE_DIRECTORY_PATH", archive_directory_path)
    monkeypatch.setenv("MOVEIT_SFTP_URI", "sftp://foo@bar.com")
    monkeypatch.setenv("MOVEIT_SSH_KEY", "foo")

    pending_directory = f"local_s3/agency_transfer/{source_directory_path}"
    archive_directory = f"local_s3/agency_transfer/{archive_directory_path}"

    with LogEntry(test_db_session, "test log entry") as log_entry:
        reference_file = get_mock_data()
        filename = "DUA_DFML_CLM_DEM_202012070000.csv"
        filepath = os.path.join(moveit_pickup_path, filename)
        mock_sftp_client._add_file(filepath, file_util.read_file(reference_file.file_location))

        transfer_config = get_transfer_config()
        moveit_config = get_moveit_config()

        reference_files = (
            download_demographics_file_from_moveit(
                test_db_session,
                log_entry,
                transfer_config=transfer_config,
                moveit_config=moveit_config,
            ),
        )
        assert len(file_util.list_files(pending_directory)) == 1
        assert len(file_util.list_files(archive_directory)) == 0
        assert len(reference_files) == 1

        reference_files = (
            test_db_session.query(ReferenceFile).filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.DUA_DEMOGRAPHICS_FILE.reference_file_type_id
            )
        ).all()
        for file in reference_files:
            load_demographics_file(
                test_db_session, file, log_entry, move_files=True, transfer_config=transfer_config
            )

        assert len(file_util.list_files(pending_directory)) == 0
        assert len(file_util.list_files(archive_directory)) == 1

        metrics = log_entry.metrics

        # 10 rows in the file (not counting headers)
        assert metrics["total_dua_demographics_row_count"] == 11

        assert metrics["successful_dua_demographics_reference_files_count"] == 1
        assert metrics["pending_dua_demographics_reference_files_count"] == 1

        reference_files = download_demographics_file_from_moveit(
            test_db_session, log_entry, transfer_config=transfer_config, moveit_config=moveit_config
        )
        assert len(reference_files) == 0

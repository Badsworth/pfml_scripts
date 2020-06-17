import pytest

import dor_test_data as test_data
import massgov.pfml.dor.importer.import_dor as import_dor
import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
from massgov.pfml.db.models.employees import AddressType, Country, Employee, Employer, GeoState
from massgov.pfml.dor.importer.lib.decrypter import Utf8Decrypter

# every test in here requires real resources
pytestmark = pytest.mark.integration

decrypter = Utf8Decrypter()
employee_file = "DORDFML_20200519120622"
employer_file = "DORDFMLEMP_20200519120622"


@pytest.fixture
def test_fs_path_for_s3(tmp_path):
    file_name1 = "DORDFML_20200519120622"
    employer_quarter_line = test_data.get_employer_quarter_line()
    employee_quarter_line = test_data.get_employee_quarter_line()
    content1 = "{}\n{}".format(employer_quarter_line, employee_quarter_line)

    file_name2 = "DORDFMLEMP_20200519120622"
    content2 = test_data.get_employer_info_line()

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name1
    test_file.write_text(content1)
    test_file2 = test_folder / file_name2
    test_file2.write_text(content2)

    return test_folder


@pytest.fixture
def dor_employer_lookups(test_db_session):

    # setup employer expected lookup values
    state = GeoState(geo_state_description="MA")
    test_db_session.add(state)

    country = Country(country_description="US")
    test_db_session.add(country)

    return (state, country)


def test_employer_import(test_db_session, dor_employer_lookups):

    # perform import
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    report = import_dor.ImportReport()

    report_log_entry = dor_persistence_util.create_import_log_entry(test_db_session, report)
    assert report_log_entry.import_log_id is not None
    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, employers, report, report_log_entry.import_log_id
    )

    # confirm expected columns are persisted
    employer_id = account_key_to_employer_id_map[employer_payload["account_key"]]
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(
        employer_payload, persisted_employer, report_log_entry.import_log_id
    )

    persisted_employer_address = dor_persistence_util.get_employer_address(
        test_db_session, employer_id
    )
    assert persisted_employer_address is not None

    persisted_address = dor_persistence_util.get_address(
        test_db_session, persisted_employer_address.address_id
    )
    assert persisted_address is not None

    state, country = dor_employer_lookups
    validate_employer_address_persistence(
        employer_payload, persisted_address, AddressType.BUSINESS, state, country
    )

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0
    assert report.unmodified_employers_count == 0


def test_employer_update(test_db_session, dor_employer_lookups):
    # perform initial import
    new_employer_payload = test_data.get_new_employer()
    report = import_dor.ImportReport()

    report_log_entry = dor_persistence_util.create_import_log_entry(test_db_session, report)
    assert report_log_entry.import_log_id is not None

    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, [new_employer_payload], report, report_log_entry.import_log_id
    )
    employer_id = account_key_to_employer_id_map[new_employer_payload["account_key"]]

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0

    # confirm unchanged update date will be skipped
    updated_employer_payload_to_skip = test_data.get_updated_employer_except_update_date()
    import_dor.import_employers(
        test_db_session, [updated_employer_payload_to_skip], report, report_log_entry.import_log_id
    )
    existing_employer = test_db_session.query(Employer).get(employer_id)

    with pytest.raises(AssertionError):
        validate_employer_persistence(
            updated_employer_payload_to_skip, existing_employer, report_log_entry.import_log_id
        )

    assert report.updated_employers_count == 0
    assert report.unmodified_employers_count == 1
    assert report.unmodified_employer_ids == [str(employer_id)]

    # confirm expected columns are now updated
    updated_employer_payload = test_data.get_updated_employer()
    import_dor.import_employers(
        test_db_session, [updated_employer_payload], report, report_log_entry.import_log_id
    )
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(
        updated_employer_payload, persisted_employer, report_log_entry.import_log_id
    )

    persisted_employer_address = dor_persistence_util.get_employer_address(
        test_db_session, employer_id
    )
    assert persisted_employer_address is not None

    persisted_address = dor_persistence_util.get_address(
        test_db_session, persisted_employer_address.address_id
    )
    assert persisted_address is not None

    state, country = dor_employer_lookups
    validate_employer_address_persistence(
        updated_employer_payload, persisted_address, AddressType.BUSINESS, state, country
    )

    assert report.updated_employers_count == 1
    assert report.updated_employer_ids == [str(employer_id)]


def test_employee_wage_data_create(test_db_session, dor_employer_lookups):

    # create empty report
    report = import_dor.ImportReport()

    report_log_entry = dor_persistence_util.create_import_log_entry(test_db_session, report)
    assert report_log_entry.import_log_id is not None

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, employers, report, report_log_entry.import_log_id
    )

    # perform employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()
    employer_quarter_info = test_data.get_employer_quarter_info()

    employee_id_by_ssn = import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employer_quarter_info],
        [employee_wage_data_payload],
        report,
        report_log_entry.import_log_id,
    )

    employee_id = employee_id_by_ssn[employee_wage_data_payload["employee_ssn"]]
    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(
        employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
    )

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, employee_id, employee_wage_data_payload["filing_period"]
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(
        employee_wage_data_payload, persisted_wage_info, report_log_entry.import_log_id
    )

    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0
    assert report.unmodified_employees_count == 0

    assert report.created_wages_and_contributions_count == 1
    assert report.updated_wages_and_contributions_count == 0
    assert report.unmodified_wages_and_contributions_count == 0


def test_employee_wage_data_update(test_db_session, dor_employer_lookups):

    # create empty report
    report = import_dor.ImportReport()

    report_log_entry = dor_persistence_util.create_import_log_entry(test_db_session, report)
    assert report_log_entry.import_log_id is not None

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, employers, report, report_log_entry.import_log_id
    )

    # perform initial employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()
    employer_quarter_info = test_data.get_employer_quarter_info()

    employee_id_by_ssn = import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employer_quarter_info],
        [employee_wage_data_payload],
        report,
        report_log_entry.import_log_id,
    )
    employee_id = employee_id_by_ssn[employee_wage_data_payload["employee_ssn"]]

    # confirm that non amended employer_quarter_info skips update
    updated_employee_wage_data_payload = test_data.get_updated_employee_wage_data()
    import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employer_quarter_info],
        [updated_employee_wage_data_payload],
        report,
        report_log_entry.import_log_id,
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)
    assert persisted_employee is not None

    with pytest.raises(AssertionError):
        validate_employee_persistence(
            updated_employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
        )

    assert report.unmodified_employees_count == 1
    assert report.unmodified_employee_ids == [str(employee_id)]
    assert report.unmodified_wages_and_contributions_count == 1
    assert report.updated_employees_count == 0
    assert report.updated_wages_and_contributions_count == 0

    # confirm amended updates are persisted
    employer_quarter_info_amended = test_data.get_employer_quarter_info_amended()
    import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employer_quarter_info_amended],
        [updated_employee_wage_data_payload],
        report,
        report_log_entry.import_log_id,
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(
        updated_employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
    )

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, employee_id, updated_employee_wage_data_payload["filing_period"]
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(
        updated_employee_wage_data_payload, persisted_wage_info, report_log_entry.import_log_id
    )

    assert report.updated_employees_count == 1
    assert report.updated_employee_ids == [str(employee_id)]
    assert report.updated_wages_and_contributions_count == 1


# == Validation Helpers ==


def validate_employee_persistence(employee_wage_payload, employee_row, import_log_id):
    assert employee_row.tax_identifier == employee_wage_payload["employee_ssn"]
    assert employee_row.first_name == employee_wage_payload["employee_first_name"]
    assert employee_row.last_name == employee_wage_payload["employee_last_name"]
    assert employee_row.latest_import_log_id == import_log_id


def validate_wage_persistence(employee_wage_payload, wage_row, import_log_id):
    assert wage_row.is_independent_contractor == employee_wage_payload["independent_contractor"]
    assert wage_row.is_opted_in == employee_wage_payload["opt_in"]
    assert wage_row.employee_ytd_wages == employee_wage_payload["employee_ytd_wages"]
    assert wage_row.employee_qtr_wages == employee_wage_payload["employee_qtr_wages"]
    assert wage_row.employee_med_contribution == employee_wage_payload["employee_medical"]
    assert wage_row.employer_med_contribution == employee_wage_payload["employer_medical"]
    assert wage_row.employee_fam_contribution == employee_wage_payload["employee_family"]
    assert wage_row.employer_fam_contribution == employee_wage_payload["employer_family"]
    assert wage_row.latest_import_log_id == import_log_id


def validate_employer_persistence(employer_payload, employer_row, import_log_id):
    assert employer_row.employer_fein == employer_payload["fein"]
    assert employer_row.employer_name == employer_payload["employer_name"]
    assert employer_row.family_exemption == employer_payload["family_exemption"]
    assert employer_row.medical_exemption == employer_payload["medical_exemption"]
    assert employer_row.exemption_commence_date == employer_payload["exemption_commence_date"]
    assert employer_row.exemption_cease_date == employer_payload["exemption_cease_date"]
    assert employer_row.dor_updated_date == employer_payload["updated_date"]
    assert employer_row.latest_import_log_id == import_log_id


def validate_employer_address_persistence(
    employer_payload, address_row, business_address_type, state, country
):
    assert address_row.address_type_id == business_address_type.address_type_id
    assert address_row.address_line_one == employer_payload["employer_address_street"]
    assert address_row.city == employer_payload["employer_address_city"]
    assert address_row.geo_state_id == state.geo_state_id
    assert address_row.zip_code == employer_payload["employer_address_zip"]
    assert address_row.country_id == country.country_id


def test_get_files_for_import_grouped_by_date(test_fs_path_for_s3):
    files_by_date = import_dor.get_files_for_import_grouped_by_date(str(test_fs_path_for_s3))
    assert files_by_date == {"20200519": [employer_file, employee_file]}


def test_parse_employee_file(test_fs_path_for_s3):
    employee_wage_data = test_data.get_new_employee_wage_data()
    employer_quarter_info = test_data.get_employer_quarter_info()

    employers_info, employees_info = import_dor.parse_employee_file(
        str(test_fs_path_for_s3), employee_file, decrypter
    )
    assert employers_info[0] == employer_quarter_info
    assert employees_info[0] == employee_wage_data


def test_parse_employer_file(test_fs_path_for_s3):
    employer_quarter_info = test_data.get_new_employer()

    employers_info = import_dor.parse_employer_file(
        str(test_fs_path_for_s3), employer_file, decrypter
    )
    assert employers_info[0] == employer_quarter_info

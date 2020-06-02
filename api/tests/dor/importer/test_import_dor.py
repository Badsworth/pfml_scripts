from datetime import datetime
from decimal import Decimal

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
    content1 = "A0000000000420200331Bell, Hunt and Weiss                                                                                                                                                                                                                                           673429455T2020062220200308120622\nB0000000000420200331Rachel                                                                                                                                                                                                                                                         Jones                                                                                                                                                                                                                                                          814700000NN            34689.35            34689.35               86.03              129.04               45.10                0.00"

    file_name2 = "DORDFMLEMP_20200519120622"
    content2 = "00000000001Anderson, Barber and Johnson                                                                                                                                                                                                                                   24467406564034 Angela Mews                                                                                                                                                                                                                                              North Kaylabury               NY935463801Anderson, Barber and Johnson                                                                                                                                                                                                                                   TF999912319999123120200322120622"

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
    business_address_type = AddressType(address_description="Business")
    test_db_session.add(business_address_type)

    state = GeoState(state_description="MA")
    test_db_session.add(state)

    country = Country(country_description="US")
    test_db_session.add(country)

    return (business_address_type, state, country)


def test_employer_import(test_db_session, dor_employer_lookups):

    # perform import
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    report = import_dor.ImportReport()
    account_key_to_employer_id_map = import_dor.import_employers(test_db_session, employers, report)

    # confirm expected columns are persisted
    employer_id = account_key_to_employer_id_map[employer_payload["account_key"]]
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(employer_payload, persisted_employer)

    persisted_employer_address = dor_persistence_util.get_employer_address(
        test_db_session, employer_id
    )
    assert persisted_employer_address is not None

    persisted_address = dor_persistence_util.get_address(
        test_db_session, persisted_employer_address.address_id
    )
    assert persisted_address is not None

    business_address_type, state, country = dor_employer_lookups
    validate_employer_address_persistence(
        employer_payload, persisted_address, business_address_type, state, country
    )

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0
    assert report.unmodified_employers_count == 0


def test_employer_update(test_db_session, dor_employer_lookups):

    # perform initial import
    new_employer_payload = test_data.get_new_employer()
    report = import_dor.ImportReport()
    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, [new_employer_payload], report
    )
    employer_id = account_key_to_employer_id_map[new_employer_payload["account_key"]]

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0

    # confirm unchanged update date will be skipped
    updated_employer_payload_to_skip = test_data.get_updated_employer_except_update_date()
    import_dor.import_employers(test_db_session, [updated_employer_payload_to_skip], report)
    existing_employer = test_db_session.query(Employer).get(employer_id)

    with pytest.raises(AssertionError):
        validate_employer_persistence(updated_employer_payload_to_skip, existing_employer)

    assert report.updated_employers_count == 0
    assert report.unmodified_employers_count == 1
    assert report.unmodified_employer_ids == [str(employer_id)]

    # confirm expected columns are now updated
    updated_employer_payload = test_data.get_updated_employer()
    import_dor.import_employers(test_db_session, [updated_employer_payload], report)
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(updated_employer_payload, persisted_employer)

    persisted_employer_address = dor_persistence_util.get_employer_address(
        test_db_session, employer_id
    )
    assert persisted_employer_address is not None

    persisted_address = dor_persistence_util.get_address(
        test_db_session, persisted_employer_address.address_id
    )
    assert persisted_address is not None

    business_address_type, state, country = dor_employer_lookups
    validate_employer_address_persistence(
        updated_employer_payload, persisted_address, business_address_type, state, country
    )

    assert report.updated_employers_count == 1
    assert report.updated_employer_ids == [str(employer_id)]


def test_employee_wage_data_create(test_db_session, dor_employer_lookups):

    # create empty report
    report = import_dor.ImportReport()

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    account_key_to_employer_id_map = import_dor.import_employers(test_db_session, employers, report)

    # perform employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()
    employer_quarter_info = test_data.get_employer_quarter_info()

    employee_id_by_ssn = import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employer_quarter_info],
        [employee_wage_data_payload],
        report,
    )

    employee_id = employee_id_by_ssn[employee_wage_data_payload["employee_ssn"]]
    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(employee_wage_data_payload, persisted_employee)

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, employee_id, employee_wage_data_payload["filing_period"]
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(employee_wage_data_payload, persisted_wage_info)

    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0
    assert report.unmodified_employees_count == 0

    assert report.created_wages_and_contributions_count == 1
    assert report.updated_wages_and_contributions_count == 0
    assert report.unmodified_wages_and_contributions_count == 0


def test_employee_wage_data_update(test_db_session, dor_employer_lookups):

    # create empty report
    report = import_dor.ImportReport()

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    account_key_to_employer_id_map = import_dor.import_employers(test_db_session, employers, report)

    # perform initial employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()
    employer_quarter_info = test_data.get_employer_quarter_info()

    employee_id_by_ssn = import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employer_quarter_info],
        [employee_wage_data_payload],
        report,
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
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)
    assert persisted_employee is not None

    with pytest.raises(AssertionError):
        validate_employee_persistence(updated_employee_wage_data_payload, persisted_employee)

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
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(updated_employee_wage_data_payload, persisted_employee)

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, employee_id, updated_employee_wage_data_payload["filing_period"]
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(updated_employee_wage_data_payload, persisted_wage_info)

    assert report.updated_employees_count == 1
    assert report.updated_employee_ids == [str(employee_id)]
    assert report.updated_wages_and_contributions_count == 1


# == Validation Helpers ==


def validate_employee_persistence(employee_wage_payload, employee_row):
    assert employee_row.tax_identifier == employee_wage_payload["employee_ssn"]
    assert employee_row.first_name == employee_wage_payload["employee_first_name"]
    assert employee_row.last_name == employee_wage_payload["employee_last_name"]


def validate_wage_persistence(employee_wage_payload, wage_row):
    assert wage_row.is_independent_contractor == employee_wage_payload["independent_contractor"]
    assert wage_row.is_opted_in == employee_wage_payload["opt_in"]
    assert wage_row.employee_ytd_wages == employee_wage_payload["employee_ytd_wages"]
    assert wage_row.employee_qtr_wages == employee_wage_payload["employee_qtr_wages"]
    assert wage_row.employee_med_contribution == employee_wage_payload["employee_medical"]
    assert wage_row.employer_med_contribution == employee_wage_payload["employer_medical"]
    assert wage_row.employee_fam_contribution == employee_wage_payload["employee_family"]
    assert wage_row.employer_fam_contribution == employee_wage_payload["employer_family"]


def validate_employer_persistence(employer_payload, employer_row):
    assert employer_row.employer_fein == employer_payload["fein"]
    assert employer_row.employer_name == employer_payload["employer_name"]
    assert employer_row.family_exemption == employer_payload["family_exemption"]
    assert employer_row.medical_exemption == employer_payload["medical_exemption"]
    assert employer_row.exemption_commence_date == employer_payload["exemption_commence_date"]
    assert employer_row.exemption_cease_date == employer_payload["exemption_cease_date"]
    assert employer_row.dor_updated_date == employer_payload["updated_date"]


def validate_employer_address_persistence(
    employer_payload, address_row, business_address_type, state, country
):
    assert address_row.address_type == business_address_type.address_type
    assert address_row.address_line_one == employer_payload["employer_address_street"]
    assert address_row.city == employer_payload["employer_address_city"]
    assert address_row.state_type == state.state_type
    assert address_row.zip_code == employer_payload["employer_address_zip"]
    assert address_row.country_type == country.country_type


def test_get_files_for_import_grouped_by_date(test_fs_path_for_s3):
    files_by_date = import_dor.get_files_for_import_grouped_by_date(str(test_fs_path_for_s3))
    assert files_by_date == {"20200519": [employer_file, employee_file]}


def test_parse_employee_file(test_fs_path_for_s3):
    employee_wage_data = {
        "record_type": "B",
        "account_key": "00000000004",
        "filing_period": datetime(2020, 3, 31, 0, 0),
        "employee_first_name": "Rachel",
        "employee_last_name": "Jones",
        "employee_ssn": "814700000",
        "independent_contractor": False,
        "opt_in": False,
        "employee_ytd_wages": Decimal("34689.35"),
        "employee_qtr_wages": Decimal("34689.35"),
        "employee_medical": Decimal("86.03"),
        "employer_medical": Decimal("129.04"),
        "employee_family": Decimal("45.10"),
        "employer_family": Decimal("0.00"),
    }

    employer_quarter_info = {
        "record_type": "A",
        "account_key": "00000000004",
        "filing_period": datetime(2020, 3, 31, 0, 0),
        "employer_name": "Bell, Hunt and Weiss",
        "employer_fein": "673429455",
        "amended_flag": True,
        "received_date": datetime(2020, 6, 22, 0, 0),
        "updated_date": datetime(2020, 3, 8, 12, 6, 22),
    }

    employers_info, employees_info = import_dor.parse_employee_file(
        str(test_fs_path_for_s3), employee_file, decrypter
    )
    assert employers_info[0] == employer_quarter_info
    assert employees_info[0] == employee_wage_data


def test_parse_employer_file(test_fs_path_for_s3):
    employer_quarter_info = {
        "account_key": "00000000001",
        "employer_name": "Anderson, Barber and Johnson",
        "fein": "244674065",
        "employer_address_street": "64034 Angela Mews",
        "employer_address_city": "North Kaylabury",
        "employer_address_state": "NY",
        "employer_address_zip": "935463801",
        "employer_dba": "Anderson, Barber and Johnson",
        "family_exemption": True,
        "medical_exemption": False,
        "exemption_commence_date": datetime(9999, 12, 31, 0, 0),
        "exemption_cease_date": datetime(9999, 12, 31, 0, 0),
        "updated_date": datetime(2020, 3, 22, 12, 6, 22),
    }

    employers_info = import_dor.parse_employer_file(
        str(test_fs_path_for_s3), employer_file, decrypter
    )
    assert employers_info[0] == employer_quarter_info

from datetime import date, datetime
from decimal import Decimal

import pytest

import massgov.pfml.dor.importer.import_dor as import_dor
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


def test_employer_import(test_db_session):

    from massgov.pfml.db.models.employees import (
        AddressType,
        GeoState,
        Country,
        Employer,
        EmployerAddress,
        Address,
    )

    # create import payload
    account_key = "00000000001"
    employer_name = "Anderson, Barber and Johnson"
    fein = "244674065"
    employer_address_street = "64034 Angela Mews"
    employer_address_city = "North Kaylabury"
    employer_address_state = "MA"
    employer_address_zip = "935463801"
    family_exemption = True
    medical_exemption = False
    exemption_commence_date = date(2020, 1, 1)
    exemption_cease_date = date(2020, 12, 31)
    updated_date = datetime(2020, 5, 10, 0, 0, 0)

    employers = [
        {
            "account_key": account_key,
            "employer_name": employer_name,
            "fein": fein,
            "employer_address_street": employer_address_street,
            "employer_address_city": employer_address_city,
            "employer_address_state": employer_address_state,
            "employer_address_zip": employer_address_zip,
            "employer_dba": employer_name,
            "family_exemption": family_exemption,
            "medical_exemption": medical_exemption,
            "exemption_commence_date": exemption_commence_date,
            "exemption_cease_date": exemption_cease_date,
            "updated_date": updated_date,
        }
    ]

    # setup expected lookup values
    business_address_type = AddressType(address_description="Business")
    test_db_session.add(business_address_type)

    state = GeoState(state_description="MA")
    test_db_session.add(state)

    country = Country(country_description="US")
    test_db_session.add(country)

    # create report parameter
    report = import_dor.ImportReport(
        start=datetime.now().isoformat(), employer_file="test_file", employee_file="test_file"
    )

    # perform import
    account_key_to_employer_id_map = import_dor.import_employers(test_db_session, employers, report)

    # commit pending changes to db
    test_db_session.commit()

    # confirm expected columns are persisted
    employer_id = account_key_to_employer_id_map[account_key]
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer.employer_id == employer_id
    assert persisted_employer.employer_fein == fein
    assert persisted_employer.employer_name == employer_name
    assert persisted_employer.family_exemption == family_exemption
    assert persisted_employer.medical_exemption == medical_exemption
    assert persisted_employer.exemption_commence_date == exemption_commence_date
    assert persisted_employer.exemption_cease_date == exemption_cease_date
    assert persisted_employer.dor_updated_date == updated_date

    persisted_employer_address = (
        test_db_session.query(EmployerAddress)
        .filter(EmployerAddress.employer_id == employer_id)
        .first()
    )
    assert persisted_employer_address is not None

    persisted_address = (
        test_db_session.query(Address)
        .filter(Address.address_id == persisted_employer_address.address_id)
        .first()
    )
    assert persisted_address.address_type == business_address_type.address_type
    assert persisted_address.address_line_one == employer_address_street
    assert persisted_address.city == employer_address_city
    assert persisted_address.state_type == state.state_type
    assert persisted_address.zip_code == employer_address_zip
    assert persisted_address.country_type == country.country_type

    assert report.created_employers_count == 1


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

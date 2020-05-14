from datetime import date, datetime

import pytest

import massgov.pfml.dor.importer.import_dor as import_dor

# every test in here requires real resources
pytestmark = pytest.mark.integration


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

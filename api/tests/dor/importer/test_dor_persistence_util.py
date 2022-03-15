#
# Tests for massgov.pfml.dor.importer.dor_persistence_util.
#

import copy
import datetime
import random
from decimal import Decimal
from typing import List

import pytest
from sqlalchemy.orm.exc import NoResultFound

import massgov.pfml.dor.importer.lib.dor_persistence_util as util
from massgov.pfml.db.models.base import uuid_gen
from massgov.pfml.db.models.employees import (
    EmployerQuarterlyContribution,
    WagesAndContributionsHistory,
)
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    EmployerQuarterlyContributionFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.db.models.geo import Country, GeoState

sample_employee_file = "DORDFML_20200519120622"
sample_employer_file = "DORDFMLEMP_20200519120622"

# === test helper functions empty returns and exception raises ===


def test_get_wages_and_contributions_by_employee_ids(test_db_session, initialize_factories_session):
    empty_wages = util.get_wages_and_contributions_by_employee_ids(test_db_session, [])
    assert len(empty_wages) == 0

    employer = EmployerFactory.create()
    employee1 = EmployeeFactory.create()
    employee2 = EmployeeFactory.create()
    WagesAndContributionsFactory.create(
        employee=employee1, employer=employer, filing_period=datetime.date(2020, 6, 30)
    )
    WagesAndContributionsFactory.create(
        employee=employee1, employer=employer, filing_period=datetime.date(2020, 9, 30)
    )
    WagesAndContributionsFactory.create(
        employee=employee2, employer=employer, filing_period=datetime.date(2020, 9, 30)
    )
    wages = util.get_wages_and_contributions_by_employee_ids(
        test_db_session, [employee1.employee_id, employee2.employee_id]
    )
    assert len(wages) == 3


def test_get_wages_and_contributions_by_employee_id_and_filling_period(test_db_session):
    wage_row = util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, uuid_gen(), uuid_gen(), datetime.date.today()
    )

    assert wage_row is None


def test_get_employer_by_fein(test_db_session):
    employer_row = util.get_employer_by_fein(test_db_session, "00-000000000")

    assert employer_row is None


def test_employer_dict_to_country_and_state_values(test_db_session):
    valid_us_address = {"employer_address_state": "MA", "employer_address_country": "USA"}

    country_id, state_id, state_text = util.employer_dict_to_country_and_state_values(
        valid_us_address
    )

    assert country_id == Country.get_id(valid_us_address["employer_address_country"])
    assert state_id == GeoState.get_id(valid_us_address["employer_address_state"])
    assert state_text is None

    invalid_us_state = {"employer_address_state": "QC", "employer_address_country": "USA"}

    with pytest.raises(KeyError):
        util.employer_dict_to_country_and_state_values(invalid_us_state)

    valid_international_address = {
        "employer_address_state": "QC",
        "employer_address_country": "CAN",
    }

    country_id, state_id, state_text = util.employer_dict_to_country_and_state_values(
        valid_international_address
    )

    assert country_id == Country.get_id(valid_international_address["employer_address_country"])
    assert state_id is None
    assert state_text == valid_international_address["employer_address_state"]


def test_get_employer_address(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_employer_address(test_db_session, uuid_gen())


def test_get_address(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_address(test_db_session, uuid_gen())


def test_check_and_update_employee(test_db_session, initialize_factories_session):
    employee = EmployeeFactory.create(first_name="Jane", last_name="Smith")

    unmodified_employee_info = {"employee_first_name": "Jane", "employee_last_name": "Smith"}
    updated = util.check_and_update_employee(
        employee, unmodified_employee_info, random.randint(1, 100)
    )

    assert not updated
    assert len(test_db_session.dirty) == 0

    modified_employee_info = {"employee_first_name": "Jane", "employee_last_name": "Williams"}
    updated = util.check_and_update_employee(
        employee, modified_employee_info, random.randint(1, 100)
    )

    assert updated
    assert len(test_db_session.dirty) == 1


def test_check_and_update_wages_and_contributions(test_db_session, initialize_factories_session):
    payload = {
        "independent_contractor": True,
        "opt_in": True,
        "employee_ytd_wages": Decimal("15234.58"),
        "employee_qtr_wages": Decimal("15234.58"),
        "employee_medical": Decimal("456.00"),
        "employer_medical": Decimal("1384.58"),
        "employee_family": Decimal("0.00"),
        "employer_family": Decimal("0.00"),
    }

    wages_row = WagesAndContributionsFactory.create(
        is_independent_contractor=payload["independent_contractor"],
        is_opted_in=payload["opt_in"],
        employee_ytd_wages=payload["employee_ytd_wages"],
        employee_qtr_wages=payload["employee_qtr_wages"],
        employee_med_contribution=payload["employee_medical"],
        employer_med_contribution=payload["employer_medical"],
        employee_fam_contribution=payload["employee_family"],
        employer_fam_contribution=payload["employer_family"],
    )

    wage_history_records: List[WagesAndContributionsHistory] = []

    existing_import_log = wages_row.latest_import_log_id
    updated = util.check_and_update_wages_and_contributions(
        wages_row, payload, random.randint(1, 100), wage_history_records
    )

    assert len(wage_history_records) == 0
    assert not updated
    assert len(test_db_session.dirty) == 0

    updated_wages_payload = copy.deepcopy(payload)
    updated_wages_payload["employer_medical"] = Decimal("1384.64")

    updated = util.check_and_update_wages_and_contributions(
        wages_row, updated_wages_payload, random.randint(1, 100), wage_history_records
    )

    assert len(wage_history_records) == 1
    # Currently Unpersisted
    wage_history_record = wage_history_records[0]
    assert wage_history_record.wages_and_contributions_history_id is None
    # Records previous value
    assert wage_history_record.employer_med_contribution == Decimal("1384.58")
    # Records all new values
    assert wage_history_record.wage_and_contribution_id == wages_row.wage_and_contribution_id
    assert wage_history_record.is_independent_contractor == wages_row.is_independent_contractor
    assert wage_history_record.is_opted_in == wages_row.is_opted_in
    assert wage_history_record.employee_ytd_wages == wages_row.employee_ytd_wages
    assert wage_history_record.employee_qtr_wages == wages_row.employee_qtr_wages
    assert wage_history_record.employee_med_contribution == wages_row.employee_med_contribution
    assert wage_history_record.employee_fam_contribution == wages_row.employee_fam_contribution
    assert wage_history_record.employer_fam_contribution == wages_row.employer_fam_contribution
    assert wage_history_record.import_log_id == existing_import_log

    assert updated
    assert len(test_db_session.dirty) == 1


def test_check_and_update_employer_quarterly_contribution(
    test_db_session, initialize_factories_session
):
    payload = {
        "total_pfml_contribution": Decimal("15234.58"),
        "received_date": datetime.date(2021, 6, 21),
        "pfm_account_id": "12345678912345",
        "updated_date": datetime.datetime(2021, 6, 22, 19, 1, 12),
    }

    employer = EmployerFactory.create()
    employer_contribution_row = EmployerQuarterlyContribution(
        employer_id=employer.employer_id,
        filing_period=datetime.date(2020, 6, 30),
        pfm_account_id="12345678912345",
        employer_total_pfml_contribution=Decimal("15234.58"),
        dor_received_date=datetime.datetime(2021, 6, 21, 0, 0, 0),
        dor_updated_date=datetime.datetime(2021, 6, 22, 19, 1, 12),
    )
    test_db_session.add(employer_contribution_row)
    test_db_session.commit()

    updated = util.check_and_update_employer_quarterly_contribution(
        employer_contribution_row, payload, 10
    )

    assert not updated
    assert len(test_db_session.dirty) == 0

    modified_payload = copy.deepcopy(payload)
    modified_payload["total_pfml_contribution"] = Decimal("15234.64")

    updated = util.check_and_update_employer_quarterly_contribution(
        employer_contribution_row, modified_payload, 20
    )

    assert updated
    assert len(test_db_session.dirty) == 1
    assert employer_contribution_row.employer_total_pfml_contribution == Decimal("15234.64")
    assert employer_contribution_row.latest_import_log_id == 20


def test_check_and_update_employer_quarterly_contribution_update_twice(
    test_db_session, initialize_factories_session
):
    payload = {
        "total_pfml_contribution": Decimal("20.00"),
        "received_date": datetime.date(2021, 6, 21),
        "pfm_account_id": "12345678912345",
        "updated_date": datetime.datetime(2021, 6, 22, 19, 1, 12),
    }

    employer = EmployerFactory.create()
    employer_contribution_row = EmployerQuarterlyContribution(
        employer_id=employer.employer_id,
        filing_period=datetime.date(2020, 6, 30),
        pfm_account_id="12345678912345",
        employer_total_pfml_contribution=Decimal("10.00"),
        dor_received_date=datetime.datetime(2021, 6, 10, 0, 0, 0),
        dor_updated_date=datetime.datetime(2021, 6, 11, 18, 0, 12),
    )
    test_db_session.add(employer_contribution_row)
    test_db_session.commit()

    updated = util.check_and_update_employer_quarterly_contribution(
        employer_contribution_row, payload, 10
    )

    assert updated
    assert employer_contribution_row.employer_total_pfml_contribution == Decimal("20.00")
    assert employer_contribution_row.latest_import_log_id == 10

    updated = util.check_and_update_employer_quarterly_contribution(
        employer_contribution_row, payload, 10
    )

    assert not updated


def test_dict_to_employee_removes_underscores_in_names():
    underscored_employee_info = {
        "employee_first_name": "Jane_Foo",
        "employee_last_name": "Bar_Smith_",
    }
    underscored_employee = util.dict_to_employee(
        underscored_employee_info, 1, uuid_gen(), TaxIdentifierFactory.tax_identifier_id
    )

    assert underscored_employee.first_name == "Jane Foo"
    assert underscored_employee.last_name == "Bar Smith"


def test_get_employers_by_account_key(test_db_session, employers):
    entries = util.get_employers_by_account_key(
        test_db_session, {"44100000001", "44100000002", "44100000003", "44100099999"}
    )
    assert entries == {
        "44100000001": employers[0].employer_id,
        "44100000002": employers[1].employer_id,
        "44100000003": employers[2].employer_id,
    }


def test_get_employer_quarterly_info_by_employer_id(test_db_session, employers):
    contrib1 = EmployerQuarterlyContributionFactory.create(
        employer=employers[0], filing_period=datetime.date(2021, 3, 31)
    )
    contrib2 = EmployerQuarterlyContributionFactory.create(
        employer=employers[0], filing_period=datetime.date(2021, 6, 30)
    )
    contrib3 = EmployerQuarterlyContributionFactory.create(
        employer=employers[2], filing_period=datetime.date(2021, 3, 31)
    )

    quarterly_map = util.get_employer_quarterly_info_by_employer_id(
        test_db_session, {e.employer_id for e in employers}
    )

    assert quarterly_map == {
        (employers[0].employer_id, datetime.date(2021, 3, 31)): contrib1,
        (employers[0].employer_id, datetime.date(2021, 6, 30)): contrib2,
        (employers[2].employer_id, datetime.date(2021, 3, 31)): contrib3,
    }

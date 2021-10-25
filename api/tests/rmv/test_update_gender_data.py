from typing import NoReturn

import requests

from massgov.pfml.api.config import RMVAPIBehavior
from massgov.pfml.db.models.employees import AbsenceStatus, Gender
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
)
from massgov.pfml.rmv.caller import ApiCaller, LazyApiCaller, MockZeepCaller
from massgov.pfml.rmv.client import RmvClient
from massgov.pfml.rmv.update_gender_data import get_claimants_to_scrape, update_gender_data


class TimeoutZeepCaller(LazyApiCaller[None], ApiCaller[None]):
    def __init__(self):
        pass

    def get(self):
        return self

    def VendorLicenseInquiry(self, **kwargs) -> NoReturn:
        raise requests.Timeout("test timeout")


def test_get_claimants_to_scrape(test_db_session, initialize_factories_session):
    # existing employee without any claims should not be included
    EmployeeWithFineosNumberFactory.create()

    # existing employee with claims, but without DoB (should not be included)
    employee_one = EmployeeFactory.create()
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee_one
    )

    # eligible claimant - gender is not set, DoB is set
    employee_two = EmployeeWithFineosNumberFactory.create()
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee_two
    )

    # eligible claimant with multiple claims (should only be included once)
    employee_three = EmployeeWithFineosNumberFactory.create()
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee_three
    )
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.CLOSED.absence_status_id, employee=employee_three
    )
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id, employee=employee_three
    )

    # claimant with gender set (should not be included)
    employee4 = EmployeeWithFineosNumberFactory.create(gender_id=Gender.WOMAN.gender_id)
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee4
    )

    # we should only see the unique employees with claims
    assert get_claimants_to_scrape(test_db_session) == [
        employee_two,
        employee_three,
    ]


def test_update_gender_data_successfully(test_db_session, initialize_factories_session):
    employee = EmployeeWithFineosNumberFactory.create(first_name="John")
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee
    )
    claimants = [employee]

    caller = MockZeepCaller({"Sex": "MALE"})
    rmv_client = RmvClient(caller)
    report = update_gender_data(test_db_session, rmv_client, RMVAPIBehavior.NO_MOCK, claimants)

    assert employee.gender_id == Gender.MAN.gender_id
    assert report.total_claimants_count == 1
    assert report.claimants_updated_count == 1
    assert report.claimants_errored_count == 0
    assert report.status == "Gender data update completed successfully."


def test_update_gender_data_customer_not_found(test_db_session, initialize_factories_session):
    employee = EmployeeWithFineosNumberFactory.create(first_name="John")
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee
    )
    claimants = [employee]

    caller = MockZeepCaller({"Acknowledgement": "INVALIDRESULTS_CUSTOMER_NOT_FOUND"})
    rmv_client = RmvClient(caller)
    report = update_gender_data(test_db_session, rmv_client, RMVAPIBehavior.NO_MOCK, claimants)

    assert employee.gender_id is None
    assert report.total_claimants_count == 1
    assert report.claimants_updated_count == 0
    assert report.claimants_errored_count == 1
    assert report.claimants_skipped_count == 0
    assert report.status == "Gender data update completed successfully."


def test_update_gender_data_invalid_rmv_sex_data(test_db_session, initialize_factories_session):
    employee = EmployeeWithFineosNumberFactory.create(first_name="John")
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee
    )
    claimants = [employee]

    caller = MockZeepCaller({"Sex": "J"})
    rmv_client = RmvClient(caller)
    report = update_gender_data(test_db_session, rmv_client, RMVAPIBehavior.NO_MOCK, claimants)

    assert employee.gender_id is None
    assert report.total_claimants_count == 1
    assert report.claimants_updated_count == 0
    assert report.claimants_errored_count == 1
    assert report.claimants_skipped_count == 0
    assert report.status == "Gender data update completed successfully."


def test_update_gender_data_missing_rmv_sex_data(test_db_session, initialize_factories_session):
    employee = EmployeeWithFineosNumberFactory.create(first_name="John")
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee
    )
    claimants = [employee]

    caller = MockZeepCaller({"Sex": None})
    rmv_client = RmvClient(caller)
    report = update_gender_data(test_db_session, rmv_client, RMVAPIBehavior.NO_MOCK, claimants)

    assert employee.gender_id is None
    assert report.total_claimants_count == 1
    assert report.claimants_updated_count == 0
    assert report.claimants_errored_count == 1
    assert report.claimants_skipped_count == 0
    assert report.status == "Gender data update completed successfully."


def test_update_gender_data_timeout(test_db_session, initialize_factories_session):
    employee_one = EmployeeWithFineosNumberFactory.create(first_name="John")
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee_one
    )
    employee_two = EmployeeWithFineosNumberFactory.create(first_name="John")
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee_two
    )
    claimants = [employee_one, employee_two]

    caller = TimeoutZeepCaller()
    rmv_client = RmvClient(caller)
    report = update_gender_data(test_db_session, rmv_client, RMVAPIBehavior.NO_MOCK, claimants)

    assert employee_one.gender_id is None
    assert employee_two.gender_id is None
    assert report.total_claimants_count == 2
    assert report.claimants_updated_count == 0
    assert report.claimants_errored_count == 1
    assert report.claimants_skipped_count == 0
    assert report.status == "Gender data update terminated early."

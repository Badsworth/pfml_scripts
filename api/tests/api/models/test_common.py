from datetime import date

from massgov.pfml.api.constants.application import (
    CARING_LEAVE_EARLIEST_START_DATE,
    PFML_PROGRAM_LAUNCH_DATE,
)
from massgov.pfml.api.models.common import get_computed_start_dates
from massgov.pfml.db.models.applications import LeaveReason


def test_computed_start_dates_for_application_with_no_reason():
    earliest_start_date = date(2021, 1, 15)
    leave_reason = None
    computed_start_dates = get_computed_start_dates(earliest_start_date, leave_reason)
    assert computed_start_dates.same_reason is None
    assert computed_start_dates.other_reason is None


def test_computed_start_dates_for_application_with_no_leave_periods():
    earliest_start_date = None
    leave_reason = LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description
    computed_start_dates = get_computed_start_dates(earliest_start_date, leave_reason)
    assert computed_start_dates.same_reason is None
    assert computed_start_dates.other_reason is None


def test_computed_start_dates_for_leave_with_prior_year_before_launch():
    earliest_start_date = date(2021, 1, 15)
    leave_reason = LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description
    computed_start_dates = get_computed_start_dates(earliest_start_date, leave_reason)
    assert computed_start_dates.same_reason == PFML_PROGRAM_LAUNCH_DATE
    assert computed_start_dates.other_reason == PFML_PROGRAM_LAUNCH_DATE


def test_computed_start_dates_for_caring_leave_with_prior_year_before_launch():
    earliest_start_date = date(2021, 12, 30)
    leave_reason = LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_description
    computed_start_dates = get_computed_start_dates(earliest_start_date, leave_reason)
    assert computed_start_dates.same_reason == CARING_LEAVE_EARLIEST_START_DATE
    assert computed_start_dates.other_reason == PFML_PROGRAM_LAUNCH_DATE


def test_computed_start_dates_for_leave_with_prior_year_after_launch():
    earliest_start_date = date(2022, 1, 15)
    leave_reason = LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description
    computed_start_dates = get_computed_start_dates(earliest_start_date, leave_reason)
    assert computed_start_dates.same_reason == date(2021, 1, 10)
    assert computed_start_dates.other_reason == date(2021, 1, 10)
    assert computed_start_dates.same_reason.strftime("%A") == "Sunday"
    assert computed_start_dates.other_reason.strftime("%A") == "Sunday"


def test_computed_start_dates_for_caring_leave_with_prior_year_after_launch():
    earliest_start_date = date(2022, 7, 30)
    leave_reason = LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_description
    computed_start_dates = get_computed_start_dates(earliest_start_date, leave_reason)
    assert computed_start_dates.same_reason == date(2021, 7, 25)
    assert computed_start_dates.other_reason == date(2021, 7, 25)
    assert computed_start_dates.same_reason.strftime("%A") == "Sunday"
    assert computed_start_dates.other_reason.strftime("%A") == "Sunday"

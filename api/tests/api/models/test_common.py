from datetime import date

from massgov.pfml.api.constants.application import (
    CARING_LEAVE_EARLIEST_START_DATE,
    PFML_PROGRAM_LAUNCH_DATE,
)
from massgov.pfml.api.models.common import (
    get_computed_start_dates,
    get_earliest_start_date,
    get_latest_end_date,
)
from massgov.pfml.db.models.applications import ContinuousLeavePeriod, LeaveReason
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    IntermittentLeavePeriodFactory,
    ReducedScheduleLeavePeriodFactory,
)


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


def test_get_earliest_start_date(test_db_session, initialize_factories_session):
    application = ApplicationFactory.create()

    leave_periods = [
        IntermittentLeavePeriodFactory.create(
            start_date=date(2021, 1, 8),
            end_date=date(2021, 1, 10),
            application_id=application.application_id,
        ),
        ReducedScheduleLeavePeriodFactory.create(
            start_date=date(2021, 1, 12),
            end_date=date(2021, 1, 15),
            application_id=application.application_id,
        ),
        ContinuousLeavePeriod(
            start_date=date(2021, 1, 1),
            end_date=date(2021, 1, 5),
            application_id=application.application_id,
        ),
    ]
    for leave_period in leave_periods:
        test_db_session.add(leave_period)
    test_db_session.commit()

    earliest_start_date = get_earliest_start_date(application)
    assert earliest_start_date == date(2021, 1, 1)


def test_get_latest_end_date(test_db_session, initialize_factories_session):
    application = ApplicationFactory.create()

    leave_periods = [
        IntermittentLeavePeriodFactory.create(
            start_date=date(2021, 1, 8),
            end_date=date(2021, 1, 10),
            application_id=application.application_id,
        ),
        ReducedScheduleLeavePeriodFactory.create(
            start_date=date(2021, 1, 12),
            end_date=date(2021, 1, 15),
            application_id=application.application_id,
        ),
        ContinuousLeavePeriod(
            start_date=date(2021, 1, 1),
            end_date=date(2021, 1, 5),
            application_id=application.application_id,
        ),
    ]
    for leave_period in leave_periods:
        test_db_session.add(leave_period)
    test_db_session.commit()

    latest_end_date = get_latest_end_date(application)
    assert latest_end_date == date(2021, 1, 15)

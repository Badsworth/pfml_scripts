from datetime import date

import pytest

from massgov.pfml.api.constants.application import (
    CARING_LEAVE_EARLIEST_START_DATE,
    PFML_PROGRAM_LAUNCH_DATE,
)
from massgov.pfml.api.models.applications.common import ComputedStartDates, LeaveReason
from massgov.pfml.api.models.common import MaskedPhoneResponse, Phone, PreviousLeaveQualifyingReason
from massgov.pfml.api.validation.exceptions import ValidationException
from massgov.pfml.db.models.applications import LeaveReason as DBLeaveReason
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    IntermittentLeavePeriodFactory,
)


def test_leave_reason_to_previous_leave_qualifying_reason():
    leave_reasons = [
        LeaveReason.pregnancy,
        LeaveReason.child_bonding,
        LeaveReason.serious_health_condition_employee,
        LeaveReason.caring_leave,
    ]
    expected_previous_leave_reasons = [
        PreviousLeaveQualifyingReason.PREGNANCY_MATERNITY,
        PreviousLeaveQualifyingReason.CHILD_BONDING,
        PreviousLeaveQualifyingReason.AN_ILLNESS_OR_INJURY,
        PreviousLeaveQualifyingReason.CARE_FOR_A_FAMILY_MEMBER,
    ]

    for index, leave_reason in enumerate(leave_reasons):
        assert (
            LeaveReason.to_previous_leave_qualifying_reason(leave_reason)
            == expected_previous_leave_reasons[index]
        )


def test_masked_phone_str_input():
    phone_str = "+15109283075"
    masked = MaskedPhoneResponse.from_orm(phone=phone_str)
    assert masked.int_code == "1"
    assert masked.phone_number == "***-***-3075"


def test_phone_str_input_matches_e164():
    phone_str = "224-705-2345"
    phone = Phone(phone_number=phone_str)
    assert phone.e164 == "+12247052345"

    phone_str = "510-928-3075"
    phone = Phone(phone_number=phone_str, int_code="1")
    assert phone.e164 == "+15109283075"


def test_phone_str_input_does_not_match_e164():
    phone_str = "510-928-3075"
    wrong_e164 = "+15109283076"

    with pytest.raises(ValidationException):
        Phone(phone_number=phone_str, e164=wrong_e164)


def test_computed_start_dates_for_application_with_no_reason():
    test_app = ApplicationFactory.build(
        leave_reason_id=None,
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.build(start_date=date(2021, 1, 15))
        ],
    )
    computed_start_dates = ComputedStartDates.from_orm(test_app)
    assert computed_start_dates.same_reason is None
    assert computed_start_dates.other_reason is None


def test_computed_start_dates_for_application_with_no_leave_periods():
    test_app = ApplicationFactory.build(
        leave_reason_id=DBLeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
    )
    computed_start_dates = ComputedStartDates.from_orm(test_app)
    assert computed_start_dates.same_reason is None
    assert computed_start_dates.other_reason is None


def test_computed_start_dates_for_leave_with_prior_year_before_launch():
    test_app = ApplicationFactory.build(
        leave_reason_id=DBLeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.build(start_date=date(2021, 1, 15))
        ],
    )
    computed_start_dates = ComputedStartDates.from_orm(test_app)
    assert computed_start_dates.same_reason == PFML_PROGRAM_LAUNCH_DATE
    assert computed_start_dates.other_reason == PFML_PROGRAM_LAUNCH_DATE


def test_computed_start_dates_for_caring_leave_with_prior_year_before_launch():
    test_app = ApplicationFactory.build(
        leave_reason_id=DBLeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id,
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(start_date=date(2021, 12, 30))
        ],
    )
    computed_start_dates = ComputedStartDates.from_orm(test_app)
    assert computed_start_dates.same_reason == CARING_LEAVE_EARLIEST_START_DATE
    assert computed_start_dates.other_reason == PFML_PROGRAM_LAUNCH_DATE


def test_computed_start_dates_for_leave_with_prior_year_after_launch():
    test_app = ApplicationFactory.build(
        leave_reason_id=DBLeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(start_date=date(2022, 12, 30))
        ],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.build(start_date=date(2022, 1, 15))
        ],
    )
    computed_start_dates = ComputedStartDates.from_orm(test_app)
    assert computed_start_dates.same_reason == date(2021, 1, 10)
    assert computed_start_dates.other_reason == date(2021, 1, 10)
    assert computed_start_dates.same_reason.strftime("%A") == "Sunday"
    assert computed_start_dates.other_reason.strftime("%A") == "Sunday"


def test_computed_start_dates_for_caring_leave_with_prior_year_after_launch():
    test_app = ApplicationFactory.build(
        leave_reason_id=DBLeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id,
        continuous_leave_periods=[ContinuousLeavePeriodFactory.build(start_date=date(2022, 7, 30))],
    )
    computed_start_dates = ComputedStartDates.from_orm(test_app)
    assert computed_start_dates.same_reason == date(2021, 7, 25)
    assert computed_start_dates.other_reason == date(2021, 7, 25)
    assert computed_start_dates.same_reason.strftime("%A") == "Sunday"
    assert computed_start_dates.other_reason.strftime("%A") == "Sunday"

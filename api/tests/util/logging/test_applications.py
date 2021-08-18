#
# Tests for massgov.pfml.util.logging.applications
#
from datetime import datetime

import pytest

from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    EmployerBenefitFactory,
    IntermittentLeavePeriodFactory,
    OtherIncomeFactory,
    PreviousLeaveOtherReasonFactory,
    ReducedScheduleLeavePeriodFactory,
)
from massgov.pfml.util.logging.applications import get_application_log_attributes

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_get_application_log_attributes(user, test_db_session, initialize_factories_session):
    application = ApplicationFactory.create(user=user, updated_time=datetime.now())
    EmployerBenefitFactory.create(application_id=application.application_id, benefit_type_id=None)
    OtherIncomeFactory.create(application_id=application.application_id)
    PreviousLeaveOtherReasonFactory.create(application_id=application.application_id)

    log_attributes = get_application_log_attributes(application)

    expected_attributes = {
        "application.absence_case_id": None,
        "application.application_id": str(application.application_id),
        "application.completed_time": None,
        "application.completed_time.timestamp": None,
        "application.has_concurrent_leave": "False",
        "application.has_continuous_leave_periods": "False",
        "application.has_employer_benefits": "False",
        "application.has_future_child_date": None,
        "application.has_intermittent_leave_periods": "False",
        "application.has_mailing_address": "False",
        "application.has_other_incomes": "False",
        "application.has_previous_leaves_other_reason": "False",
        "application.has_previous_leaves_same_reason": "False",
        "application.has_reduced_schedule_leave_periods": "False",
        "application.has_state_id": "False",
        "application.has_submitted_payment_preference": None,
        "application.leave_reason": "Serious Health Condition - Employee",
        "application.leave_reason_qualifier": None,
        "application.num_employer_benefits": "1",
        "application.num_other_incomes": "1",
        "application.num_previous_leaves_other_reason": "1",
        "application.num_previous_leaves_same_reason": "0",
        "application.num_employer_benefit_types.Accrued paid leave": "0",
        "application.num_employer_benefit_types.Family or medical leave insurance": "0",
        "application.num_employer_benefit_types.Permanent disability insurance": "0",
        "application.num_employer_benefit_types.Short-term disability insurance": "0",
        "application.num_other_income_types.Disability benefits under Gov't retirement plan": "0",
        "application.num_other_income_types.Earnings from another employment/self-employment": "0",
        "application.num_other_income_types.Jones Act benefits": "0",
        "application.num_other_income_types.Railroad Retirement benefits": "0",
        "application.num_other_income_types.SSDI": "1",
        "application.num_other_income_types.Unemployment Insurance": "0",
        "application.num_other_income_types.Workers Compensation": "0",
        "application.num_previous_leave_other_reason_reasons.Caring for a family member with a serious health condition": "0",
        "application.num_previous_leave_other_reason_reasons.Bonding with my child after birth or placement": "0",
        "application.num_previous_leave_other_reason_reasons.Caring for a family member who serves in the armed forces": "0",
        "application.num_previous_leave_other_reason_reasons.Managing family affairs while a family member is on active duty in the armed forces": "0",
        "application.num_previous_leave_other_reason_reasons.Pregnancy": "1",
        "application.num_previous_leave_other_reason_reasons.An illness or injury": "0",
        "application.num_previous_leave_same_reason_reasons.Caring for a family member with a serious health condition": "0",
        "application.num_previous_leave_same_reason_reasons.Bonding with my child after birth or placement": "0",
        "application.num_previous_leave_same_reason_reasons.Caring for a family member who serves in the armed forces": "0",
        "application.num_previous_leave_same_reason_reasons.Managing family affairs while a family member is on active duty in the armed forces": "0",
        "application.num_previous_leave_same_reason_reasons.Pregnancy": "0",
        "application.num_previous_leave_same_reason_reasons.An illness or injury": "0",
        "application.pregnant_or_recent_birth": "False",
        "application.start_time": str(application.start_time),
        "application.start_time.timestamp": str(application.start_time.timestamp()),
        "application.submitted_time": None,
        "application.submitted_time.timestamp": None,
        "application.updated_time": str(application.updated_time),
        "application.updated_time.timestamp": str(application.updated_time.timestamp()),
        "work_pattern.work_pattern_type": None,
    }
    assert log_attributes == expected_attributes


def test_get_leave_period_log_attributes(user, test_db_session, initialize_factories_session):
    application = ApplicationFactory.create(
        user=user,
        updated_time=datetime.now(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=True,
        has_reduced_schedule_leave_periods=True,
    )
    continuous_leave_1 = ContinuousLeavePeriodFactory.create(
        application_id=application.application_id
    )
    continuous_leave_2 = ContinuousLeavePeriodFactory.create(
        application_id=application.application_id
    )
    intermittent_leave_1 = IntermittentLeavePeriodFactory.create(
        application_id=application.application_id
    )
    intermittent_leave_2 = IntermittentLeavePeriodFactory.create(
        application_id=application.application_id
    )
    reduced_schedule_leave_1 = ReducedScheduleLeavePeriodFactory.create(
        application_id=application.application_id
    )
    reduced_schedule_leave_2 = ReducedScheduleLeavePeriodFactory.create(
        application_id=application.application_id
    )

    log_attributes = get_application_log_attributes(application)

    expected_attributes = {
        "application.continuous_leave[1].start_date": continuous_leave_1.start_date.isoformat(),
        "application.continuous_leave[1].end_date": continuous_leave_1.end_date.isoformat(),
        "application.continuous_leave[2].start_date": continuous_leave_2.start_date.isoformat(),
        "application.continuous_leave[2].end_date": continuous_leave_2.end_date.isoformat(),
        "application.intermittent_leave[1].start_date": intermittent_leave_1.start_date.isoformat(),
        "application.intermittent_leave[1].end_date": intermittent_leave_1.end_date.isoformat(),
        "application.intermittent_leave[2].start_date": intermittent_leave_2.start_date.isoformat(),
        "application.intermittent_leave[2].end_date": intermittent_leave_2.end_date.isoformat(),
        "application.reduced_schedule_leave[1].start_date": reduced_schedule_leave_1.start_date.isoformat(),
        "application.reduced_schedule_leave[1].end_date": reduced_schedule_leave_1.end_date.isoformat(),
        "application.reduced_schedule_leave[2].start_date": reduced_schedule_leave_2.start_date.isoformat(),
        "application.reduced_schedule_leave[2].end_date": reduced_schedule_leave_2.end_date.isoformat(),
    }

    log_atribute_subset = {
        key: value for key, value in log_attributes.items() if key in expected_attributes
    }

    assert log_atribute_subset == expected_attributes

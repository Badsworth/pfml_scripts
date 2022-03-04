#
# Tests for massgov.pfml.util.logging.applications
#
from datetime import datetime

from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    EmployerBenefitFactory,
    IntermittentLeavePeriodFactory,
    OtherIncomeFactory,
    PreviousLeaveOtherReasonFactory,
    ReducedScheduleLeavePeriodFactory,
)
from massgov.pfml.fineos.models.customer_api.spec import AbsencePeriod
from massgov.pfml.util.logging.applications import (
    get_absence_period_log_attributes,
    get_application_log_attributes,
)


def test_get_application_log_attributes(user, test_db_session, initialize_factories_session):
    application = ApplicationFactory.create(user=user, updated_at=datetime.now())
    EmployerBenefitFactory.create(application_id=application.application_id, benefit_type_id=None)
    OtherIncomeFactory.create(application_id=application.application_id)
    PreviousLeaveOtherReasonFactory.create(application_id=application.application_id)

    log_attributes = get_application_log_attributes(application)

    expected_attributes = {
        "absence_case_id": None,
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
        "application.organization_unit_id": None,
        "application.pregnant_or_recent_birth": "False",
        "application.created_at": str(application.created_at),
        "application.created_at.timestamp": str(application.created_at.timestamp()),
        "application.submitted_time": None,
        "application.submitted_time.timestamp": None,
        "application.updated_at": str(application.updated_at),
        "application.updated_at.timestamp": str(application.updated_at.timestamp()),
        "work_pattern.work_pattern_type": None,
        "application.is_withholding_tax": None,
        "application.split_from_application_id": None,
    }
    assert log_attributes == expected_attributes


def test_get_leave_period_log_attributes(user, test_db_session, initialize_factories_session):
    application = ApplicationFactory.create(
        user=user,
        updated_at=datetime.now(),
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


def test_get_absence_period_log_attributes(user, test_db_session):
    absence_details = [
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            absenceType="Episodic",
            requestStatus="Pending",
        ),
        AbsencePeriod(
            id="PL-14449-0000002238",
            reason="Child Bonding",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            absenceType="Episodic",
            requestStatus="Approved",
        ),
    ]
    log_attributes = get_absence_period_log_attributes(absence_details, absence_details[1])

    expected_attributes = {
        "num_absence_periods": str(len(absence_details)),
        "num_pending_leave_request_decision_status": "1",
        "absence_period_0_reason": "Pregnancy/Maternity",
        "absence_period_0_request_status": "Pending",
        "imported_absence_period_1_reason": "Child Bonding",
        "imported_absence_period_1_request_status": "Approved",
    }

    assert log_attributes == expected_attributes

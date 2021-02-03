#
# Tests for massgov.pfml.util.logging.applications
#
from datetime import datetime

from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    EmployerBenefitFactory,
    OtherIncomeFactory,
    PreviousLeaveFactory,
)
from massgov.pfml.util.logging.applications import get_application_log_attributes


def test_get_application_log_attributes(user, test_db_session, initialize_factories_session):
    application = ApplicationFactory.create(user=user, updated_time=datetime.now())
    EmployerBenefitFactory.create(application_id=application.application_id, benefit_type_id=None)
    OtherIncomeFactory.create(application_id=application.application_id)
    PreviousLeaveFactory.create(application_id=application.application_id)

    log_attributes = get_application_log_attributes(application)

    expected_attributes = {
        "application.absence_case_id": None,
        "application.application_id": str(application.application_id),
        "application.completed_time": None,
        "application.completed_time.timestamp": None,
        "application.employer_id": str(application.employer_id),
        "application.has_continuous_leave_periods": "False",
        "application.has_employer_benefits": None,
        "application.has_future_child_date": None,
        "application.has_intermittent_leave_periods": "False",
        "application.has_mailing_address": "False",
        "application.has_other_incomes": None,
        "application.has_other_incomes_awaiting_approval": None,
        "application.has_previous_leaves": None,
        "application.has_reduced_schedule_leave_periods": "False",
        "application.has_state_id": "False",
        "application.has_submitted_payment_preference": None,
        "application.leave_reason": "Serious Health Condition - Employee",
        "application.leave_reason_qualifier": None,
        "application.leave_type": None,
        "application.num_employer_benefits": "1",
        "application.num_other_incomes": "1",
        "application.num_previous_leaves": "1",
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
        "application.num_previous_leave_reasons.Care for a family member": "0",
        "application.num_previous_leave_reasons.Child bonding": "0",
        "application.num_previous_leave_reasons.Military caregiver": "0",
        "application.num_previous_leave_reasons.Military exigency family": "0",
        "application.num_previous_leave_reasons.Pregnancy / Maternity": "1",
        "application.num_previous_leave_reasons.Serious health condition": "0",
        "application.start_time": str(application.start_time),
        "application.start_time.timestamp": str(application.start_time.timestamp()),
        "application.submitted_time": None,
        "application.submitted_time.timestamp": None,
        "application.updated_time": str(application.updated_time),
        "application.updated_time.timestamp": str(application.updated_time.timestamp()),
        "work_pattern.work_pattern_type": None,
    }
    assert log_attributes == expected_attributes

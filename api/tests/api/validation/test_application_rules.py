import datetime
from datetime import date
from unittest import mock

import pytest
from freezegun import freeze_time

from massgov.pfml.api.models.applications.common import (
    DocumentResponse,
    DurationBasis,
    FrequencyIntervalBasis,
)
from massgov.pfml.api.models.applications.requests import ApplicationImportRequestBody
from massgov.pfml.api.validation.application_rules import (
    get_always_required_issues,
    get_application_complete_issues,
    get_concurrent_leave_issues,
    get_conditional_issues,
    get_continuous_leave_issues,
    get_intermittent_leave_issues,
    get_leave_periods_issues,
    get_payments_issues,
    get_reduced_schedule_leave_issues,
    get_work_pattern_issues,
    validate_application_import_request_for_claim,
)
from massgov.pfml.api.validation.exceptions import (
    IssueRule,
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.applications import (
    ConcurrentLeave,
    DocumentType,
    EmployerBenefit,
    EmploymentStatus,
    IntermittentLeavePeriod,
    LeaveReason,
    LeaveReasonQualifier,
    OtherIncome,
    PreviousLeaveOtherReason,
    PreviousLeaveSameReason,
    WorkPatternDay,
)
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ClaimFactory,
    ConcurrentLeaveFactory,
    ContinuousLeavePeriodFactory,
    DocumentFactory,
    EmployerBenefitFactory,
    IntermittentLeavePeriodFactory,
    OtherIncomeFactory,
    PaymentPreferenceFactory,
    PreviousLeaveOtherReasonFactory,
    PreviousLeaveSameReasonFactory,
    ReducedScheduleLeavePeriodFactory,
    TaxIdentifierFactory,
    WorkPatternFixedFactory,
    WorkPatternVariableFactory,
)

PFML_PROGRAM_LAUNCH_DATE = date(2021, 1, 1)


def test_first_name_required():
    test_app = ApplicationFactory.build(
        first_name=None,
        has_state_id=True,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required, message="first_name is required", field="first_name"
        )
    ] == issues


def test_last_name_required():
    test_app = ApplicationFactory.build(
        last_name=None,
        has_state_id=True,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required, message="last_name is required", field="last_name"
        )
    ] == issues


def test_phone_required():
    test_app = ApplicationFactory.build(
        phone=None,
        has_state_id=True,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )

    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="phone.phone_number is required",
            field="phone.phone_number",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="phone.phone_type is required",
            field="phone.phone_type",
        ),
    ] == issues


def test_date_of_birth_required():
    test_app = ApplicationFactory.build(
        date_of_birth=None,
        has_state_id=True,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required, message="date_of_birth is required", field="date_of_birth"
        )
    ] == issues


def test_has_state_id_required():
    test_app = ApplicationFactory.build(
        has_state_id=None,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required, message="has_state_id is required", field="has_state_id"
        )
    ] == issues


def test_tax_identifier_required():
    test_app = ApplicationFactory.build(
        tax_identifier=None,
        tax_identifier_id=None,
        has_state_id=True,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required, message="tax_identifier is required", field="tax_identifier"
        )
    ] == issues


def test_leave_reason_required():
    test_app = ApplicationFactory.build(
        leave_reason_id=None,
        has_state_id=True,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="leave_details.reason is required",
            field="leave_details.reason",
        )
    ] == issues


def test_employment_status_required():
    test_app = ApplicationFactory.build(
        employment_status=None,
        hours_worked_per_week=70,
        has_state_id=True,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="employment_status is required",
            field="employment_status",
        )
    ] == issues


def test_employer_notified_required():
    test_app = ApplicationFactory.build(
        employer_notified=None,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        has_state_id=True,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="leave_details.employer_notified is required",
            field="leave_details.employer_notified",
        )
    ] == issues


@freeze_time("2021-01-01")
def test_employer_notified_date_minimum():
    test_app = ApplicationFactory.build(
        employer_notified=True, employer_notification_date=date(2018, 12, 31)
    )
    issues = get_conditional_issues(test_app)
    assert (
        ValidationErrorDetail(
            type=IssueType.minimum,
            rule=IssueRule.conditional,
            message="employer_notification_date year must be within the past 2 years",
            field="leave_details.employer_notification_date",
        )
        in issues
    )


@freeze_time("2021-01-01")
def test_employer_notified_date_maximum():
    test_app = ApplicationFactory.build(
        employer_notified=True, employer_notification_date=date(2021, 1, 2)
    )
    issues = get_conditional_issues(test_app)
    assert (
        ValidationErrorDetail(
            type=IssueType.maximum,
            rule=IssueRule.conditional,
            message="employer_notification_date must be today or prior",
            field="leave_details.employer_notification_date",
        )
        in issues
    )


def test_hours_worked_per_week_required():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        has_state_id=True,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="hours_worked_per_week is required",
            field="hours_worked_per_week",
        )
    ] == issues


def test_residential_address_required():
    test_app = ApplicationFactory.build(
        residential_address=None,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        has_state_id=True,
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="residential_address is required",
            field="residential_address",
        )
    ] == issues


def test_residential_address_fields_required():
    test_app = ApplicationFactory.build(
        residential_address=AddressFactory.build(
            address_line_one=None, city=None, geo_state_id=None, zip_code=None
        ),
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        employer_notification_date=date(2021, 1, 3),
        employer_notified=True,
    )

    issues = get_conditional_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="residential_address.line_1 is required",
            field="residential_address.line_1",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="residential_address.city is required",
            field="residential_address.city",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="residential_address.state is required",
            field="residential_address.state",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="residential_address.zip is required",
            field="residential_address.zip",
        ),
    ] == issues


def test_mailing_address_fields_required():
    test_app = ApplicationFactory.build(
        mailing_address=AddressFactory.build(
            address_line_one=None, city=None, geo_state_id=None, zip_code=None
        ),
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        employer_notification_date=date(2021, 1, 3),
        employer_notified=True,
    )

    issues = get_conditional_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="mailing_address.line_1 is required",
            field="mailing_address.line_1",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="mailing_address.city is required",
            field="mailing_address.city",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="mailing_address.state is required",
            field="mailing_address.state",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="mailing_address.zip is required",
            field="mailing_address.zip",
        ),
    ] == issues


def test_has_mailing_address_required():
    test_app = ApplicationFactory.build(
        has_mailing_address=None,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        has_state_id=True,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="has_mailing_address is required",
            field="has_mailing_address",
        )
    ] == issues


def test_work_pattern_type_required():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=None,
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="work_pattern.work_pattern_type is required",
            field="work_pattern.work_pattern_type",
        )
    ] == issues


def test_has_leave_periods_required():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        hours_worked_per_week=70,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
        has_continuous_leave_periods=None,
        has_intermittent_leave_periods=None,
        has_reduced_schedule_leave_periods=None,
    )
    issues = get_always_required_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="has_continuous_leave_periods is required",
            field="has_continuous_leave_periods",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="has_intermittent_leave_periods is required",
            field="has_intermittent_leave_periods",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="has_reduced_schedule_leave_periods is required",
            field="has_reduced_schedule_leave_periods",
        ),
    ] == issues


@freeze_time("2021-01-01")
def test_allow_hybrid_leave():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=False,
        has_reduced_schedule_leave_periods=True,
        continuous_leave_periods=[ContinuousLeavePeriodFactory.build(start_date=date(2021, 1, 1))],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.build(start_date=date(2021, 2, 1))
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert not issues


@freeze_time("2021-03-01")
def test_disallow_overlapping_hybrid_leave_dates():
    test_app = ApplicationFactory.build(
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(
                start_date=date(2021, 3, 1), end_date=date(2021, 4, 1)
            )
        ],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.build(
                # Make sure empty dates don't crash things
                start_date=None,
                end_date=None,
            ),
            ReducedScheduleLeavePeriodFactory.build(
                start_date=date(2021, 3, 15), end_date=date(2021, 3, 20)
            ),
            ReducedScheduleLeavePeriodFactory.build(
                start_date=date(2021, 3, 21), end_date=date(2021, 4, 1)
            ),
        ],
    )

    issues = get_leave_periods_issues(test_app)

    # Only one disallow_overlapping_leave_periods is output even if there are several overlapping leave periods
    disallow_overlapping_leave_period_issues = filter(
        lambda issue: issue.rule is IssueRule.disallow_overlapping_leave_periods, issues
    )
    assert [
        ValidationErrorDetail(
            message="Leave period ranges cannot overlap. Received 2021-03-01 ??? 2021-04-01 and 2021-03-15 ??? 2021-03-20.",
            rule=IssueRule.disallow_overlapping_leave_periods,
            type=IssueType.conflicting,
        ),
        ValidationErrorDetail(
            message="Leave period ranges cannot overlap. Received 2021-03-01 ??? 2021-04-01 and 2021-03-21 ??? 2021-04-01.",
            rule=IssueRule.disallow_overlapping_leave_periods,
            type=IssueType.conflicting,
        ),
    ] == list(disallow_overlapping_leave_period_issues)


def test_disallow_hybrid_intermittent_continuous_leave():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=True,
        has_reduced_schedule_leave_periods=False,
        continuous_leave_periods=[ContinuousLeavePeriodFactory.build()],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.build(
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
                frequency=6,
                duration_basis=DurationBasis.days.value,
                duration=3,
            )
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert (
        ValidationErrorDetail(
            message="Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
            rule=IssueRule.disallow_hybrid_intermittent_leave,
            type=IssueType.conflicting,
        )
        in issues
    )


def test_disallow_hybrid_intermittent_reduced_leave():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
        has_continuous_leave_periods=False,
        has_intermittent_leave_periods=True,
        has_reduced_schedule_leave_periods=True,
        reduced_schedule_leave_periods=[ReducedScheduleLeavePeriodFactory.build()],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.build(
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
                frequency=6,
                duration_basis=DurationBasis.days.value,
                duration=3,
            )
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert (
        ValidationErrorDetail(
            message="Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
            rule=IssueRule.disallow_hybrid_intermittent_leave,
            type=IssueType.conflicting,
        )
        in issues
    )


def test_disallow_2020_leave_period_start_dates():
    test_app = ApplicationFactory.build(
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(start_date=date(2020, 12, 30))
        ],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.build(start_date=date(2020, 12, 30))
        ],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.build(start_date=date(2020, 12, 30))
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert (
        ValidationErrorDetail(
            field="leave_details.continuous_leave_periods[0].start_date",
            message="start_date cannot be in a year earlier than 2021",
            type=IssueType.minimum,
        )
        in issues
    )

    assert (
        ValidationErrorDetail(
            field="leave_details.intermittent_leave_periods[0].start_date",
            message="start_date cannot be in a year earlier than 2021",
            type=IssueType.minimum,
        )
        in issues
    )

    assert (
        ValidationErrorDetail(
            field="leave_details.reduced_schedule_leave_periods[0].start_date",
            message="start_date cannot be in a year earlier than 2021",
            type=IssueType.minimum,
        )
        in issues
    )


def test_disallow_caring_leave_before_july():
    test_app = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id,
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(
                start_date=date(2021, 6, 30), end_date=date(2021, 8, 1)
            )
        ],
    )

    disallow_submission_issue = ValidationErrorDetail(
        message="Caring leave start_date cannot be before 2021-07-01",
        rule=IssueRule.disallow_caring_leave_before_july,
        type="",
    )

    issues = get_leave_periods_issues(test_app)
    assert disallow_submission_issue in issues


def test_disallow_submit_over_60_days_before_start_date():
    test_app = ApplicationFactory.build(
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(
                start_date=date(2021, 5, 1), end_date=date(2021, 5, 8)
            )
        ],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.build(
                start_date=date(2021, 7, 17), end_date=date(2021, 7, 28)
            )
        ],
    )

    disallow_submission_issue = ValidationErrorDetail(
        message="Can't submit application more than 60 days in advance of the earliest leave period",
        rule=IssueRule.disallow_submit_over_60_days_before_start_date,
        type="",
    )

    with freeze_time("2021-01-01"):
        issues = get_leave_periods_issues(test_app)
        assert disallow_submission_issue in issues

    with freeze_time("2021-04-01"):
        issues = get_leave_periods_issues(test_app)
        assert disallow_submission_issue not in issues


def test_min_leave_periods():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        residential_address=AddressFactory.build(),
        work_pattern=WorkPatternFixedFactory.build(),
        has_continuous_leave_periods=False,
        has_intermittent_leave_periods=False,
        has_reduced_schedule_leave_periods=False,
        continuous_leave_periods=[],
        intermittent_leave_periods=[],
        reduced_schedule_leave_periods=[],
    )

    issues = get_leave_periods_issues(test_app)

    assert [
        ValidationErrorDetail(
            message="At least one leave period should be entered",
            rule=IssueRule.min_leave_periods,
            type=IssueType.required,
        )
    ] == issues


def test_continuous_leave_period():
    test_leave_periods = [ContinuousLeavePeriodFactory.build(start_date=None, end_date=None)]
    issues = get_continuous_leave_issues(test_leave_periods)

    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="end_date is required",
            field="leave_details.continuous_leave_periods[0].end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.continuous_leave_periods[0].start_date",
        ),
    ] == issues


def test_leave_period_end_date_before_start_date():
    continuous_leave_issues = get_continuous_leave_issues(
        [ContinuousLeavePeriodFactory.build(start_date=date(2021, 2, 1), end_date=date(2021, 1, 1))]
    )
    intermittent_leave_issues = get_intermittent_leave_issues(
        [
            IntermittentLeavePeriodFactory.build(
                start_date=date(2021, 2, 1),
                end_date=date(2021, 1, 1),
                duration=1,
                duration_basis=DurationBasis.days.value,
                frequency=1,
                frequency_interval=1,
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
            )
        ]
    )

    reduced_schedule_leave_issues = get_reduced_schedule_leave_issues(
        ApplicationFactory.build(
            reduced_schedule_leave_periods=[
                ReducedScheduleLeavePeriodFactory.build(
                    start_date=date(2021, 2, 1), end_date=date(2021, 1, 1)
                )
            ]
        )
    )

    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="end_date cannot be earlier than the start_date",
            field="leave_details.continuous_leave_periods[0].end_date",
        )
    ] == continuous_leave_issues

    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="end_date cannot be earlier than the start_date",
            field="leave_details.intermittent_leave_periods[0].end_date",
        )
    ] == intermittent_leave_issues

    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="end_date cannot be earlier than the start_date",
            field="leave_details.reduced_schedule_leave_periods[0].end_date",
        )
    ] == reduced_schedule_leave_issues


@freeze_time("2021-01-01")
def test_leave_period_disallow_12mo_leave_period_per_type():
    continuous_leave_issues = get_continuous_leave_issues(
        [ContinuousLeavePeriodFactory.build(start_date=date(2021, 2, 1), end_date=date(2022, 5, 1))]
    )
    intermittent_leave_issues = get_intermittent_leave_issues(
        [
            IntermittentLeavePeriodFactory.build(
                start_date=date(2021, 2, 1),
                end_date=date(2022, 5, 1),
                duration=1,
                duration_basis=DurationBasis.days.value,
                frequency=1,
                frequency_interval=1,
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
            )
        ]
    )

    reduced_schedule_leave_issues = get_reduced_schedule_leave_issues(
        ApplicationFactory.build(
            reduced_schedule_leave_periods=[
                ReducedScheduleLeavePeriodFactory.build(
                    start_date=date(2021, 2, 1), end_date=date(2022, 5, 1)
                )
            ]
        )
    )

    assert [
        ValidationErrorDetail(
            message="Leave cannot exceed 364 days",
            rule=IssueRule.disallow_12mo_continuous_leave_period,
            type="",
        )
    ] == continuous_leave_issues

    assert [
        ValidationErrorDetail(
            message="Leave cannot exceed 364 days",
            rule=IssueRule.disallow_12mo_intermittent_leave_period,
            type="",
        )
    ] == intermittent_leave_issues

    assert [
        ValidationErrorDetail(
            message="Leave cannot exceed 364 days",
            rule=IssueRule.disallow_12mo_reduced_leave_period,
            type="",
        )
    ] == reduced_schedule_leave_issues


@freeze_time("2021-01-01")
def test_leave_period_disallow_12mo_leave_period():
    test_app = ApplicationFactory.build(
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        work_pattern=WorkPatternFixedFactory.build(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=False,
        has_reduced_schedule_leave_periods=True,
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.build(
                start_date=date(2021, 1, 1), end_date=date(2021, 6, 1)
            )
        ],
        reduced_schedule_leave_periods=[
            # End date is 1 year from the continuous leave period start date
            ReducedScheduleLeavePeriodFactory.build(
                start_date=date(2021, 6, 2), end_date=date(2022, 1, 1)
            )
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert [
        ValidationErrorDetail(
            rule=IssueRule.disallow_12mo_leave_period,
            message="Leave cannot exceed 364 days",
            type="",
        )
    ] == issues


def test_leave_period_allows_same_start_end_date():
    start_end_date = date(2021, 2, 2)
    issues = get_reduced_schedule_leave_issues(
        ApplicationFactory.build(
            reduced_schedule_leave_periods=[
                ReducedScheduleLeavePeriodFactory.build(
                    start_date=start_end_date, end_date=start_end_date
                )
            ]
        )
    )

    assert not issues


def test_intermittent_leave_period():
    test_leave_periods = [
        IntermittentLeavePeriodFactory.build(
            start_date=None,
            end_date=None,
            duration=None,
            duration_basis=None,
            frequency=None,
            frequency_interval_basis=None,
        )
    ]

    issues = get_intermittent_leave_issues(test_leave_periods)

    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="duration is required",
            field="leave_details.intermittent_leave_periods[0].duration",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="duration_basis is required",
            field="leave_details.intermittent_leave_periods[0].duration_basis",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="end_date is required",
            field="leave_details.intermittent_leave_periods[0].end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="frequency is required",
            field="leave_details.intermittent_leave_periods[0].frequency",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="frequency_interval is required",
            field="leave_details.intermittent_leave_periods[0].frequency_interval",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="frequency_interval_basis is required",
            field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.intermittent_leave_periods[0].start_date",
        ),
    ] == issues


@pytest.mark.parametrize(
    "test_leave_periods,expected_issues",
    [
        (
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 15),
                    duration=24,
                    duration_basis="Hours",
                    frequency=1,
                    frequency_interval=1,
                    frequency_interval_basis="Weeks",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_duration_hours_maximum,
                    message="leave_details.intermittent_leave_periods[0].duration must be less than 24 if the duration_basis is hours",
                    field="leave_details.intermittent_leave_periods[0].duration",
                )
            ],
        ),
        (
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 15),
                    duration=30,
                    duration_basis="Hours",
                    frequency=1,
                    frequency_interval=1,
                    frequency_interval_basis="Weeks",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_duration_hours_maximum,
                    message="leave_details.intermittent_leave_periods[0].duration must be less than 24 if the duration_basis is hours",
                    field="leave_details.intermittent_leave_periods[0].duration",
                )
            ],
        ),
    ],
)
def test_intermittent_hours_less_than_24(test_leave_periods, expected_issues):
    issues = get_intermittent_leave_issues(test_leave_periods)
    assert issues == expected_issues


@pytest.mark.parametrize(
    "test_leave_periods, expected_issues",
    [
        (
            # 30 days in period and 30 days (1 month) interval
            # this should pass
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 31),
                    duration=1,
                    duration_basis="Days",
                    frequency=1,
                    frequency_interval=1,
                    frequency_interval_basis="Months",
                )
            ],
            [],
        ),
        (
            # 29 days in period but 30 days in interval
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 29),
                    duration=1,
                    duration_basis="Days",
                    frequency=1,
                    frequency_interval=1,
                    frequency_interval_basis="Months",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_interval_maximum,
                    message="the total days in the interval (frequency_interval * the number of days in frequency_interval_basis) cannot exceed the total days between the start and end dates of the leave period",
                    field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
                )
            ],
        ),
        (
            # 13 days in period but 14 days in interval
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 13),
                    duration=1,
                    duration_basis="Days",
                    frequency=1,
                    frequency_interval=2,
                    frequency_interval_basis="Weeks",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_interval_maximum,
                    message="the total days in the interval (frequency_interval * the number of days in frequency_interval_basis) cannot exceed the total days between the start and end dates of the leave period",
                    field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
                )
            ],
        ),
        (
            # 59 days in period but 180 days in interval
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 2, 28),
                    duration=1,
                    duration_basis="Days",
                    frequency=1,
                    frequency_interval=6,
                    frequency_interval_basis="Months",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_interval_maximum,
                    message="the total days in the interval (frequency_interval * the number of days in frequency_interval_basis) cannot exceed the total days between the start and end dates of the leave period",
                    field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
                )
            ],
        ),
        (
            # 5 days in period but 7 days in interval
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 5),
                    duration=1,
                    duration_basis="Days",
                    frequency=1,
                    frequency_interval=1,
                    frequency_interval_basis="Weeks",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_interval_maximum,
                    message="the total days in the interval (frequency_interval * the number of days in frequency_interval_basis) cannot exceed the total days between the start and end dates of the leave period",
                    field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
                )
            ],
        ),
        (
            # 5 days in period but 10 days in interval
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 1, 5),
                    duration=1,
                    duration_basis="Days",
                    frequency=1,
                    frequency_interval=10,
                    frequency_interval_basis="Days",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.intermittent_interval_maximum,
                    message="the total days in the interval (frequency_interval * the number of days in frequency_interval_basis) cannot exceed the total days between the start and end dates of the leave period",
                    field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
                )
            ],
        ),
    ],
)
def test_intermittent_interval_less_than_leave_period_length(test_leave_periods, expected_issues):
    issues = get_intermittent_leave_issues(test_leave_periods)
    assert issues == expected_issues


@pytest.mark.parametrize(
    "test_leave_periods,expected_issues",
    [
        (
            # 5 days twice a week is less than 2 weeks
            # this should pass
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 3, 1),
                    duration=5,
                    duration_basis="Days",
                    frequency=2,
                    frequency_interval=2,
                    frequency_interval_basis="Weeks",
                )
            ],
            [],
        ),
        (
            # 5 days twice a week exceeds 1 week
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 3, 1),
                    duration=5,
                    duration_basis="Days",
                    frequency=2,
                    frequency_interval=1,
                    frequency_interval_basis="Weeks",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.days_absent_per_intermittent_interval_maximum,
                    message="The total days absent per interval (frequency * duration) cannot exceed the total days in the interval",
                    field="leave_details.intermittent_leave_periods[0].duration",
                )
            ],
        ),
        (
            # 100 days 3 times over 6 months exceeds 6 months
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 8, 1),
                    duration=100,
                    duration_basis="Days",
                    frequency=3,
                    frequency_interval=6,
                    frequency_interval_basis="Months",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.days_absent_per_intermittent_interval_maximum,
                    message="The total days absent per interval (frequency * duration) cannot exceed the total days in the interval",
                    field="leave_details.intermittent_leave_periods[0].duration",
                )
            ],
        ),
        (
            # 2 days three times exceeds 3 days
            [
                IntermittentLeavePeriod(
                    start_date=date(2021, 1, 1),
                    end_date=date(2021, 3, 1),
                    duration=2,
                    duration_basis="Days",
                    frequency=3,
                    frequency_interval=3,
                    frequency_interval_basis="Days",
                )
            ],
            [
                ValidationErrorDetail(
                    type=IssueType.days_absent_per_intermittent_interval_maximum,
                    message="The total days absent per interval (frequency * duration) cannot exceed the total days in the interval",
                    field="leave_details.intermittent_leave_periods[0].duration",
                )
            ],
        ),
    ],
)
def test_intermittent_absence_days_less_than_interval_length(test_leave_periods, expected_issues):
    issues = get_intermittent_leave_issues(test_leave_periods)
    assert issues == expected_issues


def test_reduced_leave_period_required_fields():
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            start_date=None,
            end_date=None,
            sunday_off_minutes=None,
            monday_off_minutes=None,
            tuesday_off_minutes=None,
            wednesday_off_minutes=None,
            thursday_off_minutes=None,
            friday_off_minutes=None,
            saturday_off_minutes=None,
        )
    ]
    test_app = ApplicationFactory.build(reduced_schedule_leave_periods=test_leave_periods)

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="Reduced leave minutes must be greater than 0",
            rule=IssueRule.min_reduced_leave_minutes,
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="end_date is required",
            field="leave_details.reduced_schedule_leave_periods[0].end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.reduced_schedule_leave_periods[0].start_date",
        ),
    ] == issues


@freeze_time("2021-01-01")
def test_reduced_leave_period_required_minutes_fields():
    # Minutes fields are reported as missing when at least one is not None or 0
    #

    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            start_date=date(2021, 2, 1),
            end_date=date(2021, 2, 15),
            sunday_off_minutes=15,
            monday_off_minutes=None,
            tuesday_off_minutes=None,
            wednesday_off_minutes=None,
            thursday_off_minutes=None,
            friday_off_minutes=None,
            saturday_off_minutes=None,
        )
    ]
    test_app = ApplicationFactory.build(reduced_schedule_leave_periods=test_leave_periods)

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="monday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].monday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="tuesday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].tuesday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="wednesday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].wednesday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="thursday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].thursday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="friday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].friday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="saturday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].saturday_off_minutes",
        ),
    ] == issues


def test_reduced_leave_period_maximum_minutes():
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            sunday_off_minutes=8,
            monday_off_minutes=8,
            tuesday_off_minutes=8,
            wednesday_off_minutes=8,
            thursday_off_minutes=8,
            friday_off_minutes=8,
            saturday_off_minutes=8,
        )
    ]

    test_app = ApplicationFactory.build(
        reduced_schedule_leave_periods=test_leave_periods,
        work_pattern=WorkPatternFixedFactory.build(
            work_pattern_days=[
                # Use different minutes so the error messages are unique per day, helping
                # us assert that the minutes were compared against each day, rather than
                # the same day over and and over
                WorkPatternDay(day_of_week_id=i + 1, minutes=i + 1)
                for i in range(7)
            ]
        ),
    )

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="sunday_off_minutes cannot exceed the work pattern minutes for the same day, which is 1",
            field="leave_details.reduced_schedule_leave_periods[0].sunday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="monday_off_minutes cannot exceed the work pattern minutes for the same day, which is 2",
            field="leave_details.reduced_schedule_leave_periods[0].monday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="tuesday_off_minutes cannot exceed the work pattern minutes for the same day, which is 3",
            field="leave_details.reduced_schedule_leave_periods[0].tuesday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="wednesday_off_minutes cannot exceed the work pattern minutes for the same day, which is 4",
            field="leave_details.reduced_schedule_leave_periods[0].wednesday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="thursday_off_minutes cannot exceed the work pattern minutes for the same day, which is 5",
            field="leave_details.reduced_schedule_leave_periods[0].thursday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="friday_off_minutes cannot exceed the work pattern minutes for the same day, which is 6",
            field="leave_details.reduced_schedule_leave_periods[0].friday_off_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="saturday_off_minutes cannot exceed the work pattern minutes for the same day, which is 7",
            field="leave_details.reduced_schedule_leave_periods[0].saturday_off_minutes",
        ),
    ] == issues


def test_reduced_leave_period_maximum_minutes_empty_work_pattern_days():
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            sunday_off_minutes=8,
            monday_off_minutes=8,
            tuesday_off_minutes=8,
            wednesday_off_minutes=8,
            thursday_off_minutes=8,
            friday_off_minutes=8,
            saturday_off_minutes=8,
        )
    ]

    test_app = ApplicationFactory.build(
        reduced_schedule_leave_periods=test_leave_periods,
        work_pattern=WorkPatternFixedFactory.build(work_pattern_days=[]),
    )

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [] == issues


def test_reduced_leave_period_minimum_total_minutes():
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            sunday_off_minutes=0,
            monday_off_minutes=0,
            tuesday_off_minutes=0,
            wednesday_off_minutes=0,
            thursday_off_minutes=0,
            friday_off_minutes=0,
            saturday_off_minutes=0,
        )
    ]
    test_app = ApplicationFactory.build(reduced_schedule_leave_periods=test_leave_periods)

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="Reduced leave minutes must be greater than 0",
            rule=IssueRule.min_reduced_leave_minutes,
        )
    ] == issues


def test_mass_id_required_if_has_mass_id():
    test_app = ApplicationFactory.build(has_state_id=True, mass_id=None)
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="mass_id is required if has_mass_id is set",
            field="mass_id",
        )
    ] == issues


def test_mailing_addr_required_if_has_mailing_addr():
    test_app = ApplicationFactory.build(has_mailing_address=True, mailing_address=None)
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="mailing_address is required if has_mailing_address is set",
            field="mailing_address",
        )
    ] == issues


def test_pregnant_required_medical_leave():
    test_app = ApplicationFactory.build(
        leave_reason_id=LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
        pregnant_or_recent_birth=None,
    )
    assert test_app.pregnant_or_recent_birth is None
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="It is required to indicate if there has been a recent pregnancy or birth when medical leave is requested, regardless of if it is related to the leave request",
            field="leave_details.pregnant_or_recent_birth",
        )
    ] == issues


def test_reason_qualifers_required_for_bonding():
    test_app = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.SERIOUS_HEALTH_CONDITION.leave_reason_qualifier_id,
    )
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Invalid leave reason qualifier for bonding leave type",
            field="leave_details.reason_qualifier",
        )
    ] == issues


def test_child_birth_date_required_for_newborn_bonding():
    test_app = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id,
        child_birth_date=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Child birth date is required for newborn bonding leave",
            field="leave_details.child_birth_date",
        )
    ] == issues


def test_child_placement_date_required_for_adoption_bonding():
    test_app = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
        child_placement_date=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Child placement date is required for foster or adoption bonding leave",
            field="leave_details.child_placement_date",
        )
    ] == issues


def test_child_placement_date_required_for_fostercare_bonding():
    test_app = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
        child_placement_date=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Child placement date is required for foster or adoption bonding leave",
            field="leave_details.child_placement_date",
        )
    ] == issues


def test_account_number_required_for_ACH():
    test_app = ApplicationFactory.build(
        payment_preference=PaymentPreferenceFactory.build(
            payment_method_id=PaymentMethod.ACH.payment_method_id, account_number=None
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Account number is required for direct deposit",
            field="payment_preference.account_number",
        )
    ] == issues


def test_routing_number_required_for_ACH():
    test_app = ApplicationFactory.build(
        payment_preference=PaymentPreferenceFactory.build(
            payment_method_id=PaymentMethod.ACH.payment_method_id, routing_number=None
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Routing number is required for direct deposit",
            field="payment_preference.routing_number",
        )
    ] == issues


def test_bank_account_type_required_for_ACH():
    test_app = ApplicationFactory.build(
        payment_preference=PaymentPreferenceFactory.build(
            payment_method_id=PaymentMethod.ACH.payment_method_id, bank_account_type_id=None
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule="conditional",
            message="Account type is required for direct deposit",
            field="payment_preference.bank_account_type",
        )
    ] == issues


def test_valid_routing_number():
    test_app = ApplicationFactory.build(
        payment_preference=PaymentPreferenceFactory.build(
            payment_method_id=PaymentMethod.ACH.payment_method_id, routing_number="123456789"
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.checksum,
            message="Routing number is invalid",
            field="payment_preference.routing_number",
        )
    ] == issues


def test_payment_method_required_for_payment_preference():
    test_app = ApplicationFactory.build(
        payment_preference=PaymentPreferenceFactory.build(payment_method_id=None)
    )
    issues = get_payments_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="Payment method is required",
            field="payment_preference.payment_method",
        )
    ] == issues


def test_min_work_pattern_total_minutes_worked():
    test_app = ApplicationFactory.build(
        work_pattern=WorkPatternFixedFactory.build(
            work_pattern_days=[WorkPatternDay(day_of_week_id=i + 1, minutes=0) for i in range(7)]
        )
    )

    issues = get_work_pattern_issues(test_app)

    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            field="work_pattern.work_pattern_days",
            message="Total minutes for a work pattern must be greater than 0",
        )
    ] == issues


def test_required_work_pattern_minutes():
    test_app = ApplicationFactory.build(
        work_pattern=WorkPatternVariableFactory.build(
            work_pattern_days=[
                # index 0 will have 60 minutes, so work_pattern should pass minimum total minutes for work pattern
                WorkPatternDay(day_of_week_id=i + 1, minutes=60 if i == 0 else None)
                for i in range(7)
            ]
        )
    )

    issues = get_work_pattern_issues(test_app)

    expected_issues = []

    for i in range(6):
        expected_issues.append(
            ValidationErrorDetail(
                type=IssueType.required,
                message=f"work_pattern.work_pattern_days[{i + 1}].minutes is required",
                field=f"work_pattern.work_pattern_days[{i + 1}].minutes",
            )
        )

    assert expected_issues == issues


def test_max_work_pattern_minutes():
    test_app = ApplicationFactory.build(
        work_pattern=WorkPatternVariableFactory.build(
            work_pattern_days=[
                # index 0 will be 24 hours and should be valid
                WorkPatternDay(day_of_week_id=i + 1, minutes=24 * 60 + i)
                for i in range(7)
            ]
        )
    )

    issues = get_work_pattern_issues(test_app)

    expected_issues = []

    for i in range(6):
        expected_issues.append(
            ValidationErrorDetail(
                type=IssueType.maximum,
                message="Total minutes in a work pattern week must be less than a day (1440 minutes)",
                field=f"work_pattern.work_pattern_days[{i + 1}].minutes",
            )
        )

    assert expected_issues == issues


def test_employer_fein_required_for_employed_claimants():
    test_app = ApplicationFactory.build(
        employer_fein=None,
        employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id,
        employer_notification_date=date(2021, 1, 3),
        employer_notified=True,
    )
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="employer_fein is required if employment_status is Employed",
            field="employer_fein",
        )
    ] == issues


def test_employer_fein_not_required_for_self_employed_claimants():
    test_app = ApplicationFactory.build(
        employer_fein=None, employment_status_id=EmploymentStatus.SELF_EMPLOYED.employment_status_id
    )
    issues = get_conditional_issues(test_app)
    assert not issues


def test_employer_notification_date_required():
    test_app = ApplicationFactory.build(employer_notified=True, employer_notification_date=None)
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="employer_notification_date is required for leave_details if employer_notified is set",
            field="leave_details.employer_notification_date",
        )
    ] == issues


def test_employer_notification_date_required_when_employed():
    test_app = ApplicationFactory.build(
        employer_notified=False, employment_status_id=EmploymentStatus.EMPLOYED.employment_status_id
    )
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.require_employer_notified,
            message="employer_notified must be True if employment_status is Employed",
        )
    ] == issues


def test_employer_notification_date_not_required_when_unemployed():
    test_app = ApplicationFactory.build(
        employer_notified=False,
        employment_status_id=EmploymentStatus.UNEMPLOYED.employment_status_id,
    )
    issues = get_conditional_issues(test_app)
    assert [] == issues


def test_employer_notification_date_not_required_when_self_employed():
    test_app = ApplicationFactory.build(
        employer_notified=False,
        employment_status_id=EmploymentStatus.SELF_EMPLOYED.employment_status_id,
    )
    issues = get_conditional_issues(test_app)
    assert [] == issues


def test_has_employer_benefits_true_no_benefit():
    application = ApplicationFactory.build()
    application.has_employer_benefits = True

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="when has_employer_benefits is true, employer_benefits cannot be empty",
            field="employer_benefits",
        )
    ] == issues


def test_employer_benefit_no_issues():
    application = ApplicationFactory.build()
    benefits = [EmployerBenefitFactory.build(application_id=application.application_id)]
    application.employer_benefits = benefits

    issues = get_conditional_issues(application)
    assert [] == issues


def test_employer_benefit_missing_fields():
    test_app = ApplicationFactory.build(employer_benefits=[EmployerBenefit()])
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="employer_benefits[0].benefit_type is required",
            field="employer_benefits[0].benefit_type",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="employer_benefits[0].is_full_salary_continuous is required",
            field="employer_benefits[0].is_full_salary_continuous",
        ),
    ] == issues


def test_employer_benefit_start_date_must_be_after_2020():
    application = ApplicationFactory.build()
    benefits = [
        EmployerBenefitFactory.build(
            application_id=application.application_id, benefit_start_date=date(2020, 12, 31)
        )
    ]
    application.employer_benefits = benefits

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="employer_benefits[0].benefit_start_date cannot be earlier than 2021-01-01",
            field="employer_benefits[0].benefit_start_date",
        )
    ] == issues


def test_employer_benefit_end_date_must_be_after_2020():
    application = ApplicationFactory.build()
    benefits = [
        EmployerBenefitFactory.build(
            application_id=application.application_id, benefit_end_date=date(2020, 12, 31)
        )
    ]
    application.employer_benefits = benefits

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="employer_benefits[0].benefit_end_date cannot be earlier than 2021-01-01",
            field="employer_benefits[0].benefit_end_date",
        )
    ] == issues


def test_employer_benefit_end_date_must_be_after_start_date():
    application = ApplicationFactory.build()
    benefits = [
        EmployerBenefitFactory.build(
            application_id=application.application_id,
            benefit_start_date=date(2021, 1, 2),
            benefit_end_date=date(2021, 1, 1),
        )
    ]
    application.employer_benefits = benefits

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.invalid_date_range,
            message="employer_benefits[0].benefit_end_date cannot be earlier than employer_benefits[0].benefit_start_date",
            field="employer_benefits[0].benefit_end_date",
        )
    ] == issues


def test_employer_benefit_requires_start_date_when_is_full_salary_continuous_is_true():
    application = ApplicationFactory.build()
    benefits = [
        EmployerBenefitFactory.build(
            application_id=application.application_id,
            is_full_salary_continuous=True,
            benefit_start_date=None,
        )
    ]
    application.employer_benefits = benefits

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="employer_benefits[0].benefit_start_date is required",
            field="employer_benefits[0].benefit_start_date",
        )
    ] == issues


def test_other_leave_rules():
    application = ApplicationFactory.build(
        has_concurrent_leave=None,
        has_employer_benefits=None,
        has_other_incomes=None,
        has_previous_leaves_other_reason=None,
        has_previous_leaves_same_reason=None,
    )
    issues = get_conditional_issues(application)

    assert (
        ValidationErrorDetail(
            field="has_concurrent_leave",
            message="has_concurrent_leave is required",
            type=IssueType.required,
        )
        in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_employer_benefits",
            message="has_employer_benefits is required",
            type=IssueType.required,
        )
        in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_other_incomes",
            message="has_other_incomes is required",
            type=IssueType.required,
        )
        in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_previous_leaves_other_reason",
            message="has_previous_leaves_other_reason is required",
            type=IssueType.required,
        )
        in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_previous_leaves_same_reason",
            message="has_previous_leaves_same_reason is required",
            type=IssueType.required,
        )
        in issues
    )


def test_other_leave_submitted_rules():
    # TODO (CP-2455): Remove this test once we always require other leaves be present, even on submitted applications
    application = ApplicationFactory.build(submitted_time=datetime.datetime.now())
    issues = get_conditional_issues(application)

    assert (
        ValidationErrorDetail(
            field="has_employer_benefits",
            message="has_employer_benefits is required",
            type=IssueType.required,
        )
        not in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_other_incomes",
            message="has_other_incomes is required",
            type=IssueType.required,
        )
        not in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_previous_leaves_other_reason",
            message="has_previous_leaves_other_reason is required",
            type=IssueType.required,
        )
        not in issues
    )
    assert (
        ValidationErrorDetail(
            field="has_previous_leaves_same_reason",
            message="has_previous_leaves_same_reason is required",
            type=IssueType.required,
        )
        not in issues
    )


def test_has_other_incomes_true_no_income():
    application = ApplicationFactory.build()
    application.has_other_incomes = True

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="when has_other_incomes is true, other_incomes cannot be empty",
            field="other_incomes",
        )
    ] == issues


def test_has_other_incomes_true_zero_income():
    application = ApplicationFactory.build()
    application.has_other_incomes = True

    incomes = [
        OtherIncomeFactory.build(application_id=application.application_id, income_amount_dollars=0)
    ]
    application.other_incomes = incomes

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="income_amount_dollars must be greater than zero",
            field="other_incomes[0].income_amount_dollars",
        )
    ] == issues


def test_other_income_no_issues():
    application = ApplicationFactory.build()
    incomes = [OtherIncomeFactory.build(application_id=application.application_id)]
    application.other_incomes = incomes

    issues = get_conditional_issues(application)
    assert [] == issues


def test_other_income_missing_fields():
    test_app = ApplicationFactory.build(other_incomes=[OtherIncome()])
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="other_incomes[0].income_end_date is required",
            field="other_incomes[0].income_end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="other_incomes[0].income_start_date is required",
            field="other_incomes[0].income_start_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="other_incomes[0].income_type is required",
            field="other_incomes[0].income_type",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="other_incomes[0].income_amount_dollars is required",
            field="other_incomes[0].income_amount_dollars",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="other_incomes[0].income_amount_frequency is required",
            field="other_incomes[0].income_amount_frequency",
        ),
    ] == issues


def test_other_income_start_date_must_be_after_2020():
    application = ApplicationFactory.build()
    incomes = [
        OtherIncomeFactory.build(
            application_id=application.application_id, income_start_date=date(2020, 12, 31)
        )
    ]
    application.other_incomes = incomes

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="other_incomes[0].income_start_date cannot be earlier than 2021-01-01",
            field="other_incomes[0].income_start_date",
        )
    ] == issues


def test_other_income_end_date_must_be_after_2020():
    application = ApplicationFactory.build()
    incomes = [
        OtherIncomeFactory.build(
            application_id=application.application_id, income_end_date=date(2020, 12, 31)
        )
    ]
    application.other_incomes = incomes

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="other_incomes[0].income_end_date cannot be earlier than 2021-01-01",
            field="other_incomes[0].income_end_date",
        )
    ] == issues


def test_other_income_end_date_must_be_after_start_date():
    application = ApplicationFactory.build()
    incomes = [
        OtherIncomeFactory.build(
            application_id=application.application_id,
            income_start_date=date(2021, 1, 2),
            income_end_date=date(2021, 1, 1),
        )
    ]
    application.other_incomes = incomes

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.invalid_date_range,
            message="other_incomes[0].income_end_date cannot be earlier than other_incomes[0].income_start_date",
            field="other_incomes[0].income_end_date",
        )
    ] == issues


def test_has_previous_leaves_true_no_leave():
    application = ApplicationFactory.build()
    application.has_previous_leaves_other_reason = True
    application.has_previous_leaves_same_reason = True

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="when has_previous_leaves_other_reason is true, previous_leaves_other_reason cannot be empty",
            field="previous_leaves_other_reason",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="when has_previous_leaves_same_reason is true, previous_leaves_same_reason cannot be empty",
            field="previous_leaves_same_reason",
        ),
    ] == issues


def test_concurrent_leave_no_issues():
    application = ApplicationFactory.build()
    application.has_concurrent_leave = True
    application.concurrent_leave = ConcurrentLeaveFactory.build(
        application_id=application.application_id,
        is_for_current_employer=True,
        leave_start_date=date(2021, 1, 1),
        leave_end_date=date(2021, 3, 1),
    )

    issues = get_conditional_issues(application)
    assert [] == issues


def test_concurrent_leave_required_fields():
    application = ApplicationFactory.build()
    application.has_concurrent_leave = True
    application.concurrent_leave = ConcurrentLeaveFactory.build(
        application_id=application.application_id,
        is_for_current_employer=None,
        leave_start_date=None,
        leave_end_date=None,
    )

    issues = get_conditional_issues(application)

    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="concurrent_leave.leave_start_date is required",
            field="concurrent_leave.leave_start_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="concurrent_leave.leave_end_date is required",
            field="concurrent_leave.leave_end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="concurrent_leave.is_for_current_employer is required",
            field="concurrent_leave.is_for_current_employer",
        ),
    ] == issues


@pytest.mark.parametrize(
    "test_concurrent_leave,expected_issues",
    [
        (
            ConcurrentLeave(
                is_for_current_employer=True,
                leave_start_date=date(2020, 1, 1),
                leave_end_date=date(2020, 4, 1),
            ),
            [
                ValidationErrorDetail(
                    type=IssueType.minimum,
                    message=f"concurrent_leave.leave_start_date cannot be earlier than {PFML_PROGRAM_LAUNCH_DATE}",
                    field="concurrent_leave.leave_start_date",
                ),
                ValidationErrorDetail(
                    type=IssueType.minimum,
                    message=f"concurrent_leave.leave_end_date cannot be earlier than {PFML_PROGRAM_LAUNCH_DATE}",
                    field="concurrent_leave.leave_end_date",
                ),
            ],
        ),
        (
            ConcurrentLeave(
                is_for_current_employer=True,
                leave_start_date=date(2021, 5, 1),
                leave_end_date=date(2021, 4, 1),
            ),
            [
                ValidationErrorDetail(
                    type=IssueType.invalid_date_range,
                    message="concurrent_leave.leave_end_date cannot be earlier than concurrent_leave.leave_start_date",
                    field="concurrent_leave.leave_end_date",
                )
            ],
        ),
    ],
)
def test_concurrent_leave_date_range_issues(test_concurrent_leave, expected_issues):
    application = ApplicationFactory.build()
    application.has_concurrent_leave = True
    application.concurrent_leave = test_concurrent_leave

    issues = get_conditional_issues(application)

    assert expected_issues == issues


def test_previous_leave_no_issues():
    application = ApplicationFactory.build()
    application.has_previous_leaves_other_reason = True
    application.has_previous_leaves_same_reason = False
    leaves_other_reason = [
        PreviousLeaveOtherReasonFactory.build(application_id=application.application_id)
    ]
    application.previous_leaves_other_reason = leaves_other_reason

    issues = get_conditional_issues(application)
    assert [] == issues


def test_previous_leave_missing_fields():
    test_app = ApplicationFactory.build(previous_leaves_same_reason=[PreviousLeaveSameReason()])
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_same_reason[0].leave_start_date is required",
            field="previous_leaves_same_reason[0].leave_start_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_same_reason[0].leave_end_date is required",
            field="previous_leaves_same_reason[0].leave_end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_same_reason[0].is_for_current_employer is required",
            field="previous_leaves_same_reason[0].is_for_current_employer",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_same_reason[0].leave_minutes is required",
            field="previous_leaves_same_reason[0].leave_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_same_reason[0].worked_per_week_minutes is required",
            field="previous_leaves_same_reason[0].worked_per_week_minutes",
        ),
    ] == issues

    test_app = ApplicationFactory.build(previous_leaves_other_reason=[PreviousLeaveOtherReason()])
    issues = get_conditional_issues(test_app)
    assert [
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_other_reason[0].leave_start_date is required",
            field="previous_leaves_other_reason[0].leave_start_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_other_reason[0].leave_end_date is required",
            field="previous_leaves_other_reason[0].leave_end_date",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_other_reason[0].is_for_current_employer is required",
            field="previous_leaves_other_reason[0].is_for_current_employer",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_other_reason[0].leave_minutes is required",
            field="previous_leaves_other_reason[0].leave_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_other_reason[0].worked_per_week_minutes is required",
            field="previous_leaves_other_reason[0].worked_per_week_minutes",
        ),
        ValidationErrorDetail(
            type=IssueType.required,
            message="previous_leaves_other_reason[0].leave_reason is required",
            field="previous_leaves_other_reason[0].leave_reason",
        ),
    ] == issues


def test_previous_leave_start_date_must_be_after_2020():
    application = ApplicationFactory.build()
    leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id, leave_start_date=date(2020, 12, 31)
        )
    ]
    application.previous_leaves_same_reason = leaves

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="previous_leaves_same_reason[0].leave_start_date cannot be earlier than 2021-01-01",
            field="previous_leaves_same_reason[0].leave_start_date",
        )
    ] == issues


def test_previous_leave_end_date_must_be_after_2020():
    application = ApplicationFactory.build()
    leaves = [
        PreviousLeaveOtherReasonFactory.build(
            application_id=application.application_id, leave_end_date=date(2020, 12, 31)
        )
    ]
    application.previous_leaves_other_reason = leaves

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="previous_leaves_other_reason[0].leave_end_date cannot be earlier than 2021-01-01",
            field="previous_leaves_other_reason[0].leave_end_date",
        )
    ] == issues


def test_previous_leave_start_dates_for_caring_leave_with_prior_year_before_launch():
    application = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id,
    )
    leave_periods = [
        ContinuousLeavePeriodFactory.build(
            application_id=application.application_id,
            start_date=date(2021, 8, 1),
            end_date=date(2021, 8, 15),
        )
    ]
    application.continuous_leave_periods = leave_periods
    leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 4, 1),
            leave_end_date=date(2021, 4, 15),
        )
    ]
    application.previous_leaves_same_reason = leaves

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="previous_leaves_same_reason[0].leave_start_date cannot be earlier than 2021-07-01",
            field="previous_leaves_same_reason[0].leave_start_date",
        ),
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="previous_leaves_same_reason[0].leave_end_date cannot be earlier than 2021-07-01",
            field="previous_leaves_same_reason[0].leave_end_date",
        ),
    ] == issues


def test_previous_leave_start_dates_for_caring_leave_with_prior_year_after_launch():
    application = ApplicationFactory.build(
        leave_reason_id=LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id,
    )
    leave_periods = [
        ContinuousLeavePeriodFactory.build(
            application_id=application.application_id,
            start_date=date(2022, 8, 1),
            end_date=date(2022, 8, 15),
        )
    ]
    application.continuous_leave_periods = leave_periods
    leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 7, 30),
            leave_end_date=date(2021, 8, 15),
        )
    ]
    application.previous_leaves_same_reason = leaves

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.minimum,
            message="previous_leaves_same_reason[0].leave_start_date cannot be earlier than 2021-08-01",
            field="previous_leaves_same_reason[0].leave_start_date",
        ),
    ] == issues


def test_previous_leave_end_date_must_be_after_start_date():
    application = ApplicationFactory.build()
    leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 1, 2),
            leave_end_date=date(2021, 1, 1),
        )
    ]
    application.previous_leaves_same_reason = leaves

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.invalid_date_range,
            message="previous_leaves_same_reason[0].leave_end_date cannot be earlier than previous_leaves_same_reason[0].leave_start_date",
            field="previous_leaves_same_reason[0].leave_end_date",
        )
    ] == issues


def test_previous_leave_worked_per_week_minutes_must_be_less_than_10080():
    application = ApplicationFactory.build()
    leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 1, 2),
            leave_end_date=date(2021, 2, 3),
            leave_minutes=1464,
            worked_per_week_minutes=60000,
        )
    ]
    application.previous_leaves_same_reason = leaves

    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.maximum,
            message="Minutes worked per week cannot exceed 10080",
            field="previous_leaves_same_reason[0].worked_per_week_minutes",
        )
    ] == issues


def test_previous_leaves_cannot_overlap_leave_periods():
    application = ApplicationFactory.build()

    # Previous leaves for the same reason; continuous leave; previous leave overlapping with the tail of the leave period
    leave_periods = [
        ContinuousLeavePeriodFactory.build(
            application_id=application.application_id,
            start_date=date(2021, 1, 1),
            end_date=date(2021, 2, 28),
        )
    ]
    previous_leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 2, 28),
            leave_end_date=date(2021, 3, 12),
        )
    ]
    application.has_continuous_leave_periods = True
    application.continuous_leave_periods = leave_periods
    application.previous_leaves_same_reason = previous_leaves
    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.conflicting,
            rule=IssueRule.disallow_overlapping_leave_period_with_previous_leave,
            message="Previous leaves cannot overlap with leave periods. Received leave period 2021-01-01 ??? 2021-02-28 and previous leave 2021-02-28 ??? 2021-03-12.",
        )
    ] == issues

    # Previous leaves for the same reason; reduced leave; previous leave overlapping with the beginning of the leave period
    leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            application_id=application.application_id,
            start_date=date(2021, 1, 5),
            end_date=date(2021, 2, 28),
        )
    ]
    previous_leaves = [
        PreviousLeaveSameReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 1, 1),
            leave_end_date=date(2021, 1, 5),
        )
    ]
    application.has_continuous_leave_periods = False
    application.continuous_leave_periods = []
    application.has_reduced_schedule_leave_periods = True
    application.reduced_schedule_leave_periods = leave_periods
    application.previous_leaves_same_reason = previous_leaves
    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.conflicting,
            rule=IssueRule.disallow_overlapping_leave_period_with_previous_leave,
            message="Previous leaves cannot overlap with leave periods. Received leave period 2021-01-05 ??? 2021-02-28 and previous leave 2021-01-01 ??? 2021-01-05.",
        )
    ] == issues

    # Previous leaves for another reason; reduced leave; previous leave contained within the leave period
    leave_periods = [
        ReducedScheduleLeavePeriodFactory.build(
            application_id=application.application_id,
            start_date=date(2021, 1, 5),
            end_date=date(2021, 2, 28),
        )
    ]
    previous_leaves = [
        PreviousLeaveOtherReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 1, 7),
            leave_end_date=date(2021, 1, 24),
        )
    ]
    application.reduced_schedule_leave_periods = leave_periods
    application.previous_leaves_same_reason = []
    application.previous_leaves_other_reason = previous_leaves
    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.conflicting,
            rule=IssueRule.disallow_overlapping_leave_period_with_previous_leave,
            message="Previous leaves cannot overlap with leave periods. Received leave period 2021-01-05 ??? 2021-02-28 and previous leave 2021-01-07 ??? 2021-01-24.",
        )
    ] == issues

    # Previous leaves for another reason; intermittent leave; previous leave contain the entire leave period
    leave_periods = [
        IntermittentLeavePeriodFactory.build(
            application_id=application.application_id,
            start_date=date(2021, 1, 5),
            end_date=date(2021, 2, 28),
        )
    ]
    previous_leaves = [
        PreviousLeaveOtherReasonFactory.build(
            application_id=application.application_id,
            leave_start_date=date(2021, 1, 3),
            leave_end_date=date(2021, 3, 1),
        )
    ]
    application.has_reduced_schedule_leave_periods = False
    application.has_intermittent_leave_periods = True
    application.reduced_schedule_leave_periods = []
    application.intermittent_leave_periods = leave_periods
    application.previous_leaves_other_reason = previous_leaves
    issues = get_conditional_issues(application)
    assert [
        ValidationErrorDetail(
            type=IssueType.conflicting,
            rule=IssueRule.disallow_overlapping_leave_period_with_previous_leave,
            message="Previous leaves cannot overlap with leave periods. Received leave period 2021-01-05 ??? 2021-02-28 and previous leave 2021-01-03 ??? 2021-03-01.",
        )
    ] == issues


@pytest.mark.parametrize(
    "is_withholding_tax, has_submitted_payment_preference, include_id_document, expected_issues",
    [
        (
            None,
            True,
            True,
            [
                ValidationErrorDetail(
                    type=IssueType.required,
                    message="Tax withholding preference is required",
                    field="is_withholding_tax",
                )
            ],
        ),
        (False, True, True, []),
        (True, True, True, []),
        (
            False,
            False,
            True,
            [
                ValidationErrorDetail(
                    message="Payment preference is required",
                    type=IssueType.required,
                    field="payment_method",
                )
            ],
        ),
        (
            True,
            True,
            False,
            [
                ValidationErrorDetail(
                    type=IssueType.required, message="An identification document is required"
                )
            ],
        ),
    ],
)
@mock.patch("massgov.pfml.api.validation.application_rules.get_documents")
def test_get_application_complete_issues(
    mock_get_docs,
    is_withholding_tax,
    has_submitted_payment_preference,
    include_id_document,
    expected_issues,
    test_db_session,
    user,
    initialize_factories_session,
):
    application = ApplicationFactory.create(
        is_withholding_tax=is_withholding_tax,
        has_submitted_payment_preference=has_submitted_payment_preference,
        claim=ClaimFactory.build(),
        user_id=user.user_id,
        leave_reason_id=LeaveReason.PREGNANCY_MATERNITY.leave_reason_id,
    )
    mock_get_docs.return_value = []
    if include_id_document:
        DocumentFactory.create(
            user_id=application.user_id,
            application_id=application.application_id,
            document_type_id=DocumentType.PASSPORT.document_type_id,
        )

    issues = get_application_complete_issues(application, test_db_session)

    assert issues == expected_issues


def test_get_application_complete_issues_certification_validation(
    initialize_factories_session, user, test_db_session
):
    application = ApplicationFactory.create(
        is_withholding_tax=True,
        has_submitted_payment_preference=True,
        claim=ClaimFactory.build(),
        user_id=user.user_id,
        leave_reason_id=LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
    )
    DocumentFactory.create(
        user_id=application.user_id,
        application_id=application.application_id,
        document_type_id=DocumentType.PASSPORT.document_type_id,
    )

    issues = get_application_complete_issues(application, test_db_session)

    assert issues == [
        ValidationErrorDetail(
            type=IssueType.required, message="A certification document is required"
        )
    ]


@pytest.mark.parametrize(
    "document_type, expected_issues",
    [
        (
            DocumentType.PASSPORT.document_type_description,
            [
                ValidationErrorDetail(
                    type=IssueType.required, message="A certification document is required"
                )
            ],
        ),
        (
            DocumentType.CHILD_BONDING_EVIDENCE_FORM.document_type_description,
            [
                ValidationErrorDetail(
                    type=IssueType.required, message="An identification document is required"
                )
            ],
        ),
    ],
)
@mock.patch("massgov.pfml.api.validation.application_rules.get_documents")
def test_get_application_complete_issues_fineos_fallback(
    mock_get_documents,
    document_type,
    expected_issues,
    initialize_factories_session,
    user,
    test_db_session,
):
    application = ApplicationFactory.create(
        is_withholding_tax=True,
        has_submitted_payment_preference=True,
        claim=ClaimFactory.build(),
        user_id=user.user_id,
        leave_reason_id=LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
    )

    mock_get_documents.return_value = [
        DocumentResponse(
            user_id=user.user_id,
            application_id=application.application_id,
            document_type=document_type,
            name="File.pdf",
            description="my file",
        )
    ]

    issues = get_application_complete_issues(application, test_db_session)

    assert issues == expected_issues


@mock.patch("massgov.pfml.api.validation.application_rules.get_documents_issues", return_value=[])
def test_get_application_complete_issues_missing_absence_id(test_db_session):
    claim = ClaimFactory.build(fineos_absence_id=None)
    application = ApplicationFactory.build(
        is_withholding_tax=False, claim=claim, has_submitted_payment_preference=True
    )

    issues = get_application_complete_issues(application, test_db_session)

    assert issues == [
        ValidationErrorDetail(
            type=IssueType.object_not_found,
            message="A case must exist before it can be marked as complete.",
        )
    ]


@mock.patch("massgov.pfml.api.validation.application_rules.get_documents_issues", return_value=[])
def test_get_application_complete_issues_missing_part1_field(test_db_session):
    # This validation doesn't care if a new "Submit" rule isn't fulfilled, as long as a claim
    # with a Fineos absence ID exists.
    application = ApplicationFactory.build(
        is_withholding_tax=False,
        claim=ClaimFactory.build(),
        first_name=None,
        has_submitted_payment_preference=True,
    )
    issues = get_application_complete_issues(application, test_db_session)

    assert not issues


class TestGetConcurrentLeaveIssues:
    @pytest.fixture
    def application(self, concurrent_leave):
        application = ApplicationFactory.build()
        application.concurrent_leave = concurrent_leave
        application.has_concurrent_leave = True
        return application

    @pytest.fixture
    def continuous_leave_periods(self, application):
        return [
            ContinuousLeavePeriodFactory.build(
                start_date=date(2021, 11, 20), end_date=date(2021, 12, 28)
            )
        ]

    @pytest.fixture
    def reduced_leave_periods(self):
        return [
            ReducedScheduleLeavePeriodFactory.build(
                start_date=date(2021, 11, 20), end_date=date(2021, 12, 28)
            )
        ]

    @pytest.fixture
    def concurrent_leave(self):
        return ConcurrentLeaveFactory.build(
            is_for_current_employer=True,
            leave_start_date=date(2021, 11, 19),
            leave_end_date=date(2021, 11, 27),
        )

    @pytest.fixture
    def concurrent_leave_start_issue(self):
        return ValidationErrorDetail(
            type=IssueType.conflicting,
            message="Concurrent leaves cannot overlap with waiting period.",
            rule=IssueRule.disallow_overlapping_waiting_period_and_concurrent_leave_start_date,
            field="concurrent_leave.leave_start_date",
        )

    @pytest.fixture
    def concurrent_leave_end_issue(self):
        return ValidationErrorDetail(
            type=IssueType.conflicting,
            message="Concurrent leaves cannot overlap with waiting period.",
            rule=IssueRule.disallow_overlapping_waiting_period_and_concurrent_leave_end_date,
            field="concurrent_leave.leave_end_date",
        )

    @pytest.fixture
    def intermittent_leave(self):
        return [
            IntermittentLeavePeriodFactory.build(
                start_date=date(2021, 11, 20), end_date=date(2021, 12, 20)
            )
        ]

    def test_concurrent_leave_start_date_cannot_overlap_continuous_leave_waiting_period(
        self, application, continuous_leave_periods, concurrent_leave_start_issue
    ):
        application.has_continuous_leave_periods = True
        application.continuous_leave_periods = continuous_leave_periods
        application.concurrent_leave.leave_start_date = continuous_leave_periods[0].start_date

        issues = get_concurrent_leave_issues(application)
        assert concurrent_leave_start_issue in issues

    def test_concurrent_leave_end_date_cannot_overlap_continuous_leave_waiting_period(
        self, application, continuous_leave_periods, concurrent_leave_end_issue
    ):
        application.has_continuous_leave_periods = True
        application.continuous_leave_periods = continuous_leave_periods
        application.concurrent_leave.leave_end_date = continuous_leave_periods[
            0
        ].start_date + datetime.timedelta(days=1)

        issues = get_concurrent_leave_issues(application)
        assert concurrent_leave_end_issue in issues

    def test_concurrent_leave_start_and_end_dates_cannot_overlap_continuous_leave_waiting_period(
        self,
        application,
        continuous_leave_periods,
        concurrent_leave_start_issue,
        concurrent_leave_end_issue,
    ):
        application.has_continuous_leave_periods = True
        application.continuous_leave_periods = continuous_leave_periods
        application.concurrent_leave.leave_start_date = continuous_leave_periods[0].start_date
        application.concurrent_leave.leave_end_date = continuous_leave_periods[
            0
        ].start_date + datetime.timedelta(days=1)

        issues = get_concurrent_leave_issues(application)
        assert concurrent_leave_start_issue in issues
        assert concurrent_leave_end_issue in issues

    def test_concurrent_leave_start_date_cannot_overlap_reduced_leave_waiting_period(
        self, application, reduced_leave_periods, concurrent_leave_start_issue
    ):
        application.has_reduced_schedule_leave_periods = True
        application.reduced_schedule_leave_periods = reduced_leave_periods
        application.concurrent_leave.leave_start_date = reduced_leave_periods[0].start_date

        issues = get_concurrent_leave_issues(application)
        assert concurrent_leave_start_issue in issues

    def test_concurrent_leave_dates_not_validated_for_intermittent_leave(
        self, application, intermittent_leave
    ):
        application.has_intermittent_leave_periods = True
        application.intermittent_leave_periods = intermittent_leave
        application.concurrent_leave.leave_start_date = intermittent_leave[0].start_date
        application.concurrent_leave.leave_end_date = intermittent_leave[
            0
        ].start_date + datetime.timedelta(days=1)

        issues = get_concurrent_leave_issues(application)
        assert [] == issues

    def test_no_issues_returned_if_no_concurrent_leave(self, application, continuous_leave_periods):
        application.has_continuous_leave_periods = True
        application.continuous_leave_periods = continuous_leave_periods
        application.has_concurrent_leave = False
        application.concurrent_leave = None

        issues = get_concurrent_leave_issues(application)
        assert [] == issues

    def test_no_issues_for_non_overlapping_leaves(self, application, continuous_leave_periods):
        application.has_continuous_leave_periods = True
        application.continuous_leave_periods = continuous_leave_periods
        application.concurrent_leave.leave_start_date = continuous_leave_periods[
            0
        ].start_date + datetime.timedelta(days=7)
        application.concurrent_leave.leave_end_date = continuous_leave_periods[
            0
        ].start_date + datetime.timedelta(days=8)

        issues = get_concurrent_leave_issues(application)
        assert [] == issues

    def test_correct_calculation_of_waiting_period_dates(
        self,
        application,
        continuous_leave_periods,
        reduced_leave_periods,
        concurrent_leave_start_issue,
    ):
        application.has_continuous_leave_periods = True
        application.has_reduced_schedule_leave_periods = True

        application.continuous_leave_periods = continuous_leave_periods
        application.continuous_leave_periods[0].start_date = date(2021, 11, 20)
        application.continuous_leave_periods[0].end_date = date(2021, 12, 28)

        # This is the earliest leave start date
        # we should receive an error if concurrent start or end dates land between 10/28/21 and 11/3/21
        application.reduced_schedule_leave_periods = reduced_leave_periods
        application.reduced_schedule_leave_periods[0].start_date = date(2021, 10, 28)
        application.reduced_schedule_leave_periods[0].end_date = date(2021, 11, 19)

        application.concurrent_leave.leave_start_date = date(2021, 10, 29)
        application.concurrent_leave.leave_end_date = date(2021, 11, 10)

        issues = get_concurrent_leave_issues(application)
        assert concurrent_leave_start_issue in issues

    def test_with_no_concurrent_leave_start_date_no_errors(
        self, application, continuous_leave_periods
    ):
        application.has_continuous_leave_periods = True
        application.continuous_leave_periods = continuous_leave_periods

        application.concurrent_leave.leave_start_date = None

        # should resolve without errors
        get_concurrent_leave_issues(application)


class TestValidateApplicationImportRequestForClaim:
    def test_tax_id_should_match_claim_tax_id(self):
        claim = ClaimFactory.build()
        claim.employee.tax_identifier = TaxIdentifierFactory.build(tax_identifier="000000000")

        with pytest.raises(ValidationException) as exc:
            validate_application_import_request_for_claim(
                ApplicationImportRequestBody(
                    tax_identifier="123456789",  # different SSN as on the claim
                    absence_case_id=claim.fineos_absence_id,
                ),
                claim,
            )

        assert exc.value.errors == [
            ValidationErrorDetail(
                type=IssueType.incorrect,
                message="Code 2: An issue occurred while trying to import the application.",
            )
        ]

    def test_skips_tax_id_match_when_claim_has_no_tax_id(self):
        claim = ClaimFactory.build()
        claim.employee.tax_identifier = None

        res = validate_application_import_request_for_claim(
            ApplicationImportRequestBody(
                tax_identifier="123456789", absence_case_id=claim.fineos_absence_id
            ),
            claim,
        )

        # No exception raised, so a success
        assert res is None

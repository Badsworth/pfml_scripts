from datetime import date

from freezegun import freeze_time

from massgov.pfml.api.models.applications.common import DurationBasis, FrequencyIntervalBasis
from massgov.pfml.api.services.application_rules import (
    get_always_required_issues,
    get_conditional_issues,
    get_continuous_leave_issues,
    get_intermittent_leave_issues,
    get_leave_periods_issues,
    get_payments_issues,
    get_reduced_schedule_leave_issues,
    get_work_pattern_issues,
)
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType
from massgov.pfml.db.models.applications import (
    EmployerBenefit,
    EmploymentStatus,
    LeaveReason,
    LeaveReasonQualifier,
    OtherIncome,
    WorkPatternDay,
)
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    IntermittentLeavePeriodFactory,
    PaymentPreferenceFactory,
    ReducedScheduleLeavePeriodFactory,
    WorkPatternFixedFactory,
    WorkPatternVariableFactory,
)


def test_first_name_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        first_name=None,
        has_state_id=True,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(type=IssueType.required, message="first_name is required", field="first_name")
    ] == issues


def test_last_name_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        last_name=None,
        has_state_id=True,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(type=IssueType.required, message="last_name is required", field="last_name")
    ] == issues


def test_date_of_birth_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        date_of_birth=None,
        has_state_id=True,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(type=IssueType.required, message="date_of_birth is required", field="date_of_birth")
    ] == issues


def test_has_state_id_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        has_state_id=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(type=IssueType.required, message="has_state_id is required", field="has_state_id")
    ] == issues


def test_tax_identifier_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        tax_identifier=None,
        tax_identifier_id=None,
        has_state_id=True,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(type=IssueType.required, message="tax_identifier is required", field="tax_identifier")
    ] == issues


def test_leave_reason_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        leave_reason=None,
        has_state_id=True,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="leave_details.reason is required",
            field="leave_details.reason",
        )
    ] == issues


def test_employment_status_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=None,
        hours_worked_per_week=70,
        has_state_id=True,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="employment_status is required",
            field="employment_status",
        )
    ] == issues


def test_employer_notified_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employer_notified=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        has_state_id=True,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="leave_details.employer_notified is required",
            field="leave_details.employer_notified",
        )
    ] == issues


def test_hours_worked_per_week_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        has_state_id=True,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="hours_worked_per_week is required",
            field="hours_worked_per_week",
        )
    ] == issues


def test_residential_address_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        residential_address=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        has_state_id=True,
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="residential_address is required",
            field="residential_address",
        )
    ] == issues


def test_residential_address_fields_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        residential_address=AddressFactory.create(
            address_line_one=None, city=None, geo_state_id=None, zip_code=None,
        ),
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        employer_notification_date="2021-01-03",
        employer_notified=True,
    )

    issues = get_conditional_issues(test_app)

    assert [
        Issue(
            type=IssueType.required,
            message="residential_address.line_1 is required",
            field="residential_address.line_1",
        ),
        Issue(
            type=IssueType.required,
            message="residential_address.city is required",
            field="residential_address.city",
        ),
        Issue(
            type=IssueType.required,
            message="residential_address.state is required",
            field="residential_address.state",
        ),
        Issue(
            type=IssueType.required,
            message="residential_address.zip is required",
            field="residential_address.zip",
        ),
    ] == issues


def test_mailing_address_fields_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        mailing_address=AddressFactory.create(
            address_line_one=None, city=None, geo_state_id=None, zip_code=None,
        ),
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        employer_notification_date="2021-01-03",
        employer_notified=True,
    )

    issues = get_conditional_issues(test_app)

    assert [
        Issue(
            type=IssueType.required,
            message="mailing_address.line_1 is required",
            field="mailing_address.line_1",
        ),
        Issue(
            type=IssueType.required,
            message="mailing_address.city is required",
            field="mailing_address.city",
        ),
        Issue(
            type=IssueType.required,
            message="mailing_address.state is required",
            field="mailing_address.state",
        ),
        Issue(
            type=IssueType.required,
            message="mailing_address.zip is required",
            field="mailing_address.zip",
        ),
    ] == issues


def test_has_mailing_address_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        has_mailing_address=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        has_state_id=True,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="has_mailing_address is required",
            field="has_mailing_address",
        )
    ] == issues


def test_work_pattern_type_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=None,
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="work_pattern.work_pattern_type is required",
            field="work_pattern.work_pattern_type",
        )
    ] == issues


def test_has_leave_periods_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
        has_continuous_leave_periods=None,
        has_intermittent_leave_periods=None,
        has_reduced_schedule_leave_periods=None,
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="has_continuous_leave_periods is required",
            field="has_continuous_leave_periods",
        ),
        Issue(
            type=IssueType.required,
            message="has_intermittent_leave_periods is required",
            field="has_intermittent_leave_periods",
        ),
        Issue(
            type=IssueType.required,
            message="has_reduced_schedule_leave_periods is required",
            field="has_reduced_schedule_leave_periods",
        ),
    ] == issues


@freeze_time("2021-01-01")
def test_allow_hybrid_leave(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=False,
        has_reduced_schedule_leave_periods=True,
        continuous_leave_periods=[ContinuousLeavePeriodFactory.create(start_date=date(2021, 1, 1))],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.create(start_date=date(2021, 2, 1))
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert not issues


@freeze_time("2021-03-01")
def test_disallow_overlapping_hybrid_leave_dates(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.create(
                start_date=date(2021, 3, 1), end_date=date(2021, 4, 1)
            )
        ],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.create(
                # Make sure empty dates don't crash things
                start_date=None,
                end_date=None,
            ),
            ReducedScheduleLeavePeriodFactory.create(
                start_date=date(2021, 3, 15), end_date=date(2021, 3, 20)
            ),
            ReducedScheduleLeavePeriodFactory.create(
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
        Issue(
            message="Leave period ranges cannot overlap. Received 2021-03-01 – 2021-04-01 and 2021-03-15 – 2021-03-20.",
            rule=IssueRule.disallow_overlapping_leave_periods,
            type=IssueType.conflicting,
        ),
        Issue(
            message="Leave period ranges cannot overlap. Received 2021-03-01 – 2021-04-01 and 2021-03-21 – 2021-04-01.",
            rule=IssueRule.disallow_overlapping_leave_periods,
            type=IssueType.conflicting,
        ),
    ] == list(disallow_overlapping_leave_period_issues)


def test_disallow_hybrid_intermittent_continuous_leave(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=True,
        has_reduced_schedule_leave_periods=False,
        continuous_leave_periods=[ContinuousLeavePeriodFactory.create()],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.create(
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
                frequency=6,
                duration_basis=DurationBasis.days.value,
                duration=3,
            )
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert (
        Issue(
            message="Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
            rule=IssueRule.disallow_hybrid_intermittent_leave,
            type=IssueType.conflicting,
        )
        in issues
    )


def test_disallow_hybrid_intermittent_reduced_leave(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
        has_continuous_leave_periods=False,
        has_intermittent_leave_periods=True,
        has_reduced_schedule_leave_periods=True,
        reduced_schedule_leave_periods=[ReducedScheduleLeavePeriodFactory.create()],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.create(
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
                frequency=6,
                duration_basis=DurationBasis.days.value,
                duration=3,
            )
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert (
        Issue(
            message="Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
            rule=IssueRule.disallow_hybrid_intermittent_leave,
            type=IssueType.conflicting,
        )
        in issues
    )


def test_disallow_2020_leave_period_start_dates(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.create(start_date=date(2020, 12, 30))
        ],
        intermittent_leave_periods=[
            IntermittentLeavePeriodFactory.create(start_date=date(2020, 12, 30))
        ],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.create(start_date=date(2020, 12, 30))
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert (
        Issue(
            field="leave_details.continuous_leave_periods[0].start_date",
            message="start_date cannot be in a year earlier than 2021",
            type=IssueType.minimum,
        )
        in issues
    )

    assert (
        Issue(
            field="leave_details.intermittent_leave_periods[0].start_date",
            message="start_date cannot be in a year earlier than 2021",
            type=IssueType.minimum,
        )
        in issues
    )

    assert (
        Issue(
            field="leave_details.reduced_schedule_leave_periods[0].start_date",
            message="start_date cannot be in a year earlier than 2021",
            type=IssueType.minimum,
        )
        in issues
    )


def test_disallow_submit_over_60_days_before_start_date(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.create(
                start_date=date(2021, 5, 1), end_date=date(2021, 5, 8)
            )
        ],
        reduced_schedule_leave_periods=[
            ReducedScheduleLeavePeriodFactory.create(
                start_date=date(2021, 7, 17), end_date=date(2021, 7, 28)
            )
        ],
    )

    disallow_submission_issue = Issue(
        message="Can't submit application more than 60 days in advance of the earliest leave period",
        rule=IssueRule.disallow_submit_over_60_days_before_start_date,
    )

    with freeze_time("2021-01-01"):
        issues = get_leave_periods_issues(test_app)
        assert disallow_submission_issue in issues

    with freeze_time("2021-04-01"):
        issues = get_leave_periods_issues(test_app)
        assert disallow_submission_issue not in issues


def test_min_leave_periods(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        residential_address=AddressFactory.create(),
        work_pattern=WorkPatternFixedFactory.create(),
        has_continuous_leave_periods=False,
        has_intermittent_leave_periods=False,
        has_reduced_schedule_leave_periods=False,
        continuous_leave_periods=[],
        intermittent_leave_periods=[],
        reduced_schedule_leave_periods=[],
    )

    issues = get_leave_periods_issues(test_app)

    assert [
        Issue(
            message="At least one leave period should be entered",
            rule=IssueRule.min_leave_periods,
            type=IssueType.required,
        ),
    ] == issues


def test_continuous_leave_period(test_db_session, initialize_factories_session):
    test_leave_periods = [ContinuousLeavePeriodFactory.create(start_date=None, end_date=None)]
    issues = get_continuous_leave_issues(test_leave_periods)

    assert [
        Issue(
            type=IssueType.required,
            message="end_date is required",
            field="leave_details.continuous_leave_periods[0].end_date",
        ),
        Issue(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.continuous_leave_periods[0].start_date",
        ),
    ] == issues


def test_leave_period_end_date_before_start_date(test_db_session, initialize_factories_session):
    continuous_leave_issues = get_continuous_leave_issues(
        [
            ContinuousLeavePeriodFactory.create(
                start_date=date(2021, 2, 1), end_date=date(2021, 1, 1)
            )
        ]
    )
    intermittent_leave_issues = get_intermittent_leave_issues(
        [
            IntermittentLeavePeriodFactory.create(
                start_date=date(2021, 2, 1),
                end_date=date(2021, 1, 1),
                frequency_interval=1,
                frequency_interval_basis=FrequencyIntervalBasis.months.value,
                frequency=6,
                duration_basis=DurationBasis.days.value,
                duration=3,
            )
        ]
    )

    reduced_schedule_leave_issues = get_reduced_schedule_leave_issues(
        ApplicationFactory.create(
            reduced_schedule_leave_periods=[
                ReducedScheduleLeavePeriodFactory.create(
                    start_date=date(2021, 2, 1), end_date=date(2021, 1, 1)
                )
            ]
        )
    )

    assert [
        Issue(
            type=IssueType.minimum,
            message="end_date cannot be earlier than the start_date",
            field="leave_details.continuous_leave_periods[0].end_date",
        ),
    ] == continuous_leave_issues

    assert [
        Issue(
            type=IssueType.minimum,
            message="end_date cannot be earlier than the start_date",
            field="leave_details.intermittent_leave_periods[0].end_date",
        ),
    ] == intermittent_leave_issues

    assert [
        Issue(
            type=IssueType.minimum,
            message="end_date cannot be earlier than the start_date",
            field="leave_details.reduced_schedule_leave_periods[0].end_date",
        ),
    ] == reduced_schedule_leave_issues


@freeze_time("2021-01-01")
def test_leave_period_disallow_12mo_leave_period(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        work_pattern=WorkPatternFixedFactory.create(),
        has_continuous_leave_periods=True,
        has_intermittent_leave_periods=False,
        has_reduced_schedule_leave_periods=True,
        continuous_leave_periods=[
            ContinuousLeavePeriodFactory.create(
                start_date=date(2021, 1, 1), end_date=date(2021, 6, 1)
            )
        ],
        reduced_schedule_leave_periods=[
            # End date is 1 year from the continuous leave period start date
            ReducedScheduleLeavePeriodFactory.create(
                start_date=date(2021, 6, 2), end_date=date(2022, 1, 1)
            )
        ],
    )

    issues = get_leave_periods_issues(test_app)

    assert [
        Issue(rule=IssueRule.disallow_12mo_leave_period, message="Leave cannot exceed 364 days",),
    ] == issues


def test_leave_period_allows_same_start_end_date(test_db_session, initialize_factories_session):
    start_end_date = date(2021, 2, 2)
    issues = get_reduced_schedule_leave_issues(
        ApplicationFactory.create(
            reduced_schedule_leave_periods=[
                ReducedScheduleLeavePeriodFactory.create(
                    start_date=start_end_date, end_date=start_end_date
                ),
            ]
        )
    )

    assert not issues


def test_intermittent_leave_period(test_db_session, initialize_factories_session):
    test_leave_periods = (
        [
            IntermittentLeavePeriodFactory.create(
                start_date=None,
                end_date=None,
                duration=None,
                duration_basis=None,
                frequency=None,
                frequency_interval_basis=None,
            )
        ],
    )
    issues = get_intermittent_leave_issues(test_leave_periods)

    assert [
        Issue(
            type=IssueType.required,
            message="duration is required",
            field="leave_details.intermittent_leave_periods[0].duration",
        ),
        Issue(
            type=IssueType.required,
            message="duration_basis is required",
            field="leave_details.intermittent_leave_periods[0].duration_basis",
        ),
        Issue(
            type=IssueType.required,
            message="end_date is required",
            field="leave_details.intermittent_leave_periods[0].end_date",
        ),
        Issue(
            type=IssueType.required,
            message="frequency is required",
            field="leave_details.intermittent_leave_periods[0].frequency",
        ),
        Issue(
            type=IssueType.required,
            message="frequency_interval is required",
            field="leave_details.intermittent_leave_periods[0].frequency_interval",
        ),
        Issue(
            type=IssueType.required,
            message="frequency_interval_basis is required",
            field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
        ),
        Issue(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.intermittent_leave_periods[0].start_date",
        ),
    ] == issues


def test_reduced_leave_period_required_fields(test_db_session, initialize_factories_session):
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.create(
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
    test_app = ApplicationFactory.create(reduced_schedule_leave_periods=test_leave_periods)

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        Issue(
            type=IssueType.minimum,
            message="Reduced leave minutes must be greater than 0",
            rule=IssueRule.min_reduced_leave_minutes,
        ),
        Issue(
            type=IssueType.required,
            message="end_date is required",
            field="leave_details.reduced_schedule_leave_periods[0].end_date",
        ),
        Issue(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.reduced_schedule_leave_periods[0].start_date",
        ),
    ] == issues


@freeze_time("2021-01-01")
def test_reduced_leave_period_required_minutes_fields(
    test_db_session, initialize_factories_session
):
    """Minutes fields are reported as missing when at least one is not None or 0
    """

    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.create(
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
    test_app = ApplicationFactory.create(reduced_schedule_leave_periods=test_leave_periods)

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        Issue(
            type=IssueType.required,
            message="monday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].monday_off_minutes",
        ),
        Issue(
            type=IssueType.required,
            message="tuesday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].tuesday_off_minutes",
        ),
        Issue(
            type=IssueType.required,
            message="wednesday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].wednesday_off_minutes",
        ),
        Issue(
            type=IssueType.required,
            message="thursday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].thursday_off_minutes",
        ),
        Issue(
            type=IssueType.required,
            message="friday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].friday_off_minutes",
        ),
        Issue(
            type=IssueType.required,
            message="saturday_off_minutes is required",
            field="leave_details.reduced_schedule_leave_periods[0].saturday_off_minutes",
        ),
    ] == issues


def test_reduced_leave_period_maximum_minutes(test_db_session, initialize_factories_session):
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.create(
            sunday_off_minutes=8,
            monday_off_minutes=8,
            tuesday_off_minutes=8,
            wednesday_off_minutes=8,
            thursday_off_minutes=8,
            friday_off_minutes=8,
            saturday_off_minutes=8,
        )
    ]

    test_app = ApplicationFactory.create(
        reduced_schedule_leave_periods=test_leave_periods,
        work_pattern=WorkPatternFixedFactory.create(
            work_pattern_days=[
                # Use different minutes so the error messages are unique per day, helping
                # us assert that the minutes were compared against each day, rather than
                # the same day over and and over
                WorkPatternDay(week_number=1, day_of_week_id=i + 1, minutes=i + 1)
                for i in range(7)
            ]
        ),
    )

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        Issue(
            type=IssueType.maximum,
            message="monday_off_minutes cannot exceed the work pattern minutes for the same day, which is 1",
            field="leave_details.reduced_schedule_leave_periods[0].monday_off_minutes",
        ),
        Issue(
            type=IssueType.maximum,
            message="tuesday_off_minutes cannot exceed the work pattern minutes for the same day, which is 2",
            field="leave_details.reduced_schedule_leave_periods[0].tuesday_off_minutes",
        ),
        Issue(
            type=IssueType.maximum,
            message="wednesday_off_minutes cannot exceed the work pattern minutes for the same day, which is 3",
            field="leave_details.reduced_schedule_leave_periods[0].wednesday_off_minutes",
        ),
        Issue(
            type=IssueType.maximum,
            message="thursday_off_minutes cannot exceed the work pattern minutes for the same day, which is 4",
            field="leave_details.reduced_schedule_leave_periods[0].thursday_off_minutes",
        ),
        Issue(
            type=IssueType.maximum,
            message="friday_off_minutes cannot exceed the work pattern minutes for the same day, which is 5",
            field="leave_details.reduced_schedule_leave_periods[0].friday_off_minutes",
        ),
        Issue(
            type=IssueType.maximum,
            message="saturday_off_minutes cannot exceed the work pattern minutes for the same day, which is 6",
            field="leave_details.reduced_schedule_leave_periods[0].saturday_off_minutes",
        ),
        Issue(
            type=IssueType.maximum,
            message="sunday_off_minutes cannot exceed the work pattern minutes for the same day, which is 7",
            field="leave_details.reduced_schedule_leave_periods[0].sunday_off_minutes",
        ),
    ] == issues


def test_reduced_leave_period_maximum_minutes_empty_work_pattern_days(
    test_db_session, initialize_factories_session
):
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.create(
            sunday_off_minutes=8,
            monday_off_minutes=8,
            tuesday_off_minutes=8,
            wednesday_off_minutes=8,
            thursday_off_minutes=8,
            friday_off_minutes=8,
            saturday_off_minutes=8,
        )
    ]

    test_app = ApplicationFactory.create(
        reduced_schedule_leave_periods=test_leave_periods,
        work_pattern=WorkPatternFixedFactory.create(work_pattern_days=[]),
    )

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [] == issues


def test_reduced_leave_period_minimum_total_minutes(test_db_session, initialize_factories_session):
    test_leave_periods = [
        ReducedScheduleLeavePeriodFactory.create(
            sunday_off_minutes=0,
            monday_off_minutes=0,
            tuesday_off_minutes=0,
            wednesday_off_minutes=0,
            thursday_off_minutes=0,
            friday_off_minutes=0,
            saturday_off_minutes=0,
        )
    ]
    test_app = ApplicationFactory.create(reduced_schedule_leave_periods=test_leave_periods)

    issues = get_reduced_schedule_leave_issues(test_app)

    assert [
        Issue(
            type=IssueType.minimum,
            message="Reduced leave minutes must be greater than 0",
            rule=IssueRule.min_reduced_leave_minutes,
        )
    ] == issues


def test_mass_id_required_if_has_mass_id(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(has_state_id=True, mass_id=None)
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="mass_id is required if has_mass_id is set",
            field="mass_id",
        )
    ] == issues


def test_mailing_addr_required_if_has_mailing_addr(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(has_mailing_address=True, mailing_address=None)
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="mailing_address is required if has_mailing_address is set",
            field="mailing_address",
        )
    ] == issues


def test_pregnant_required_medical_leave(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        leave_reason_id=LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
        pregnant_or_recent_birth=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="It is required to indicate if there has been a recent pregnancy or birth when medical leave is requested, regardless of if it is related to the leave request",
            field="leave_details.pregnant_or_recent_birth",
        )
    ] == issues


def test_reason_qualifers_required_for_bonding(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.SERIOUS_HEALTH_CONDITION.leave_reason_qualifier_id,
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Invalid leave reason qualifier for bonding leave type",
            field="leave_details.reason_qualifier",
        )
    ] == issues


def test_child_birth_date_required_for_newborn_bonding(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id,
        child_birth_date=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Child birth date is required for newborn bonding leave",
            field="leave_details.child_birth_date",
        )
    ] == issues


def test_child_placement_date_required_for_adoption_bonding(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
        child_placement_date=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Child placement date is required for foster or adoption bonding leave",
            field="leave_details.child_placement_date",
        )
    ] == issues


def test_child_placement_date_required_for_fostercare_bonding(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        leave_reason_id=LeaveReason.CHILD_BONDING.leave_reason_id,
        leave_reason_qualifier_id=LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
        child_placement_date=None,
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Child placement date is required for foster or adoption bonding leave",
            field="leave_details.child_placement_date",
        )
    ] == issues


def test_account_number_required_for_ACH(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        payment_preference=PaymentPreferenceFactory.create(
            payment_method_id=PaymentMethod.ACH.payment_method_id, account_number=None
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Account number is required for direct deposit",
            field="payment_preference.account_number",
        )
    ] == issues


def test_routing_number_required_for_ACH(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        payment_preference=PaymentPreferenceFactory.create(
            payment_method_id=PaymentMethod.ACH.payment_method_id, routing_number=None
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Routing number is required for direct deposit",
            field="payment_preference.routing_number",
        )
    ] == issues


def test_bank_account_type_required_for_ACH(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        payment_preference=PaymentPreferenceFactory.create(
            payment_method_id=PaymentMethod.ACH.payment_method_id, bank_account_type_id=None
        )
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Account type is required for direct deposit",
            field="payment_preference.bank_account_type",
        )
    ] == issues


def test_min_work_pattern_total_minutes_worked(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        work_pattern=WorkPatternFixedFactory(
            work_pattern_days=[
                WorkPatternDay(week_number=1, day_of_week_id=i + 1, minutes=0) for i in range(7)
            ]
        )
    )

    issues = get_work_pattern_issues(test_app)

    assert [
        Issue(
            type=IssueType.minimum,
            field="work_pattern.work_pattern_days",
            message="Total minutes for a work pattern must be greater than 0",
        )
    ] == issues


def test_required_work_pattern_minutes(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        work_pattern=WorkPatternVariableFactory(
            work_pattern_days=[
                # index 0 will have 60 minutes, so work_pattern should pass minimum total minutes for work pattern
                WorkPatternDay(week_number=1, day_of_week_id=i + 1, minutes=60 if i == 0 else None)
                for i in range(7)
            ]
        )
    )

    issues = get_work_pattern_issues(test_app)

    expected_issues = []

    for i in range(6):
        expected_issues.append(
            Issue(
                type=IssueType.required,
                message=f"work_pattern.work_pattern_days[{i + 1}].minutes is required",
                field=f"work_pattern.work_pattern_days[{i + 1}].minutes",
            )
        )

    assert expected_issues == issues


def test_max_work_pattern_minutes(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        work_pattern=WorkPatternVariableFactory(
            work_pattern_days=[
                # index 0 will be 24 hours and should be valid
                WorkPatternDay(week_number=1, day_of_week_id=i + 1, minutes=24 * 60 + i)
                for i in range(7)
            ]
        )
    )

    issues = get_work_pattern_issues(test_app)

    expected_issues = []

    for i in range(6):
        expected_issues.append(
            Issue(
                type=IssueType.maximum,
                message="Total minutes in a work pattern week must be less than a day (1440 minutes)",
                field=f"work_pattern.work_pattern_days[{i + 1}].minutes",
            )
        )

    assert expected_issues == issues


def test_employer_fein_required_for_employed_claimants(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_fein=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        employer_notification_date="2021-01-03",
        employer_notified=True,
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="employer_fein is required if employment_status is Employed",
            field="employer_fein",
        )
    ] == issues


def test_employer_fein_not_required_for_self_employed_claimants(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_fein=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.SELF_EMPLOYED
        ),
    )
    issues = get_conditional_issues(test_app)
    assert not issues


def test_employer_notification_date_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(employer_notified=True, employer_notification_date=None)
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="employer_notification_date is required for leave_details if employer_notified is set",
            field="leave_details.employer_notification_date",
        )
    ] == issues


def test_employer_notification_date_required_when_employed(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_notified=False,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule=IssueRule.require_employer_notified,
            message="employer_notified must be True if employment_status is Employed",
        )
    ] == issues


def test_employer_notification_date_not_required_when_unemployed(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_notified=False,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.UNEMPLOYED
        ),
    )
    issues = get_conditional_issues(test_app)
    assert [] == issues


def test_employer_notification_date_not_required_when_self_employed(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_notified=False,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.SELF_EMPLOYED
        ),
    )
    issues = get_conditional_issues(test_app)
    assert [] == issues


def test_employer_benefit_missing_fields(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(employer_benefits=[EmployerBenefit()])
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="employer_benefits[0].benefit_amount_dollars is required",
            field="employer_benefits[0].benefit_amount_dollars",
        ),
        Issue(
            type=IssueType.required,
            message="employer_benefits[0].benefit_amount_frequency is required",
            field="employer_benefits[0].benefit_amount_frequency",
        ),
        Issue(
            type=IssueType.required,
            message="employer_benefits[0].benefit_end_date is required",
            field="employer_benefits[0].benefit_end_date",
        ),
        Issue(
            type=IssueType.required,
            message="employer_benefits[0].benefit_start_date is required",
            field="employer_benefits[0].benefit_start_date",
        ),
        Issue(
            type=IssueType.required,
            message="employer_benefits[0].benefit_type is required",
            field="employer_benefits[0].benefit_type",
        ),
    ] == issues


def test_other_income_missing_fields(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(other_incomes=[OtherIncome()])
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="other_incomes[0].income_amount_dollars is required",
            field="other_incomes[0].income_amount_dollars",
        ),
        Issue(
            type=IssueType.required,
            message="other_incomes[0].income_amount_frequency is required",
            field="other_incomes[0].income_amount_frequency",
        ),
        Issue(
            type=IssueType.required,
            message="other_incomes[0].income_end_date is required",
            field="other_incomes[0].income_end_date",
        ),
        Issue(
            type=IssueType.required,
            message="other_incomes[0].income_start_date is required",
            field="other_incomes[0].income_start_date",
        ),
        Issue(
            type=IssueType.required,
            message="other_incomes[0].income_type is required",
            field="other_incomes[0].income_type",
        ),
    ] == issues


def test_has_other_incomes_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        other_incomes_awaiting_approval=True, has_other_incomes=False
    )
    issues = get_conditional_issues(test_app)
    assert [] == issues

    test_app = ApplicationFactory.create(
        other_incomes_awaiting_approval=True, has_other_incomes=None
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="has_other_incomes must be set if other_incomes_awaiting_approval is set",
            field="has_other_incomes",
        )
    ] == issues

    test_app = ApplicationFactory.create(
        other_incomes_awaiting_approval=True, has_other_incomes=True
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.conflicting,
            rule=IssueRule.disallow_has_other_incomes_when_awaiting_approval,
            message="has_other_incomes must be false if other_incomes_awaiting_approval is set",
            field="has_other_incomes",
        )
    ] == issues

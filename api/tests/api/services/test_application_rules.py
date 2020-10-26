from datetime import date

from massgov.pfml.api.models.applications.common import DurationBasis, FrequencyIntervalBasis
from massgov.pfml.api.models.applications.responses import ApplicationResponse
from massgov.pfml.api.services.application_rules import (
    get_always_required_issues,
    get_application_issues,
    get_conditional_issues,
    get_continuous_leave_issues,
    get_intermittent_leave_issues,
    get_leave_periods_issues,
    get_payments_issues,
    get_reduced_schedule_leave_issues,
    get_work_pattern_issues,
)
from massgov.pfml.api.util.response import Issue, IssueRule, IssueType, success_response
from massgov.pfml.db.models.applications import (
    EmploymentStatus,
    LeaveReasonQualifier,
    LeaveType,
    WorkPattern,
    WorkPatternDay,
    WorkPatternType,
)
from massgov.pfml.db.models.employees import PaymentType
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    IntermittentLeavePeriodFactory,
    PaymentPreferenceFactory,
    ReducedScheduleLeavePeriodFactory,
    WorkPatternFixedFactory,
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
        continuous_leave_periods=[ContinuousLeavePeriodFactory.create()],
        reduced_schedule_leave_periods=[ReducedScheduleLeavePeriodFactory.create()],
    )

    issues = get_leave_periods_issues(test_app)

    assert not issues


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
            message="frequency_interval_basis is required",
            field="leave_details.intermittent_leave_periods[0].frequency_interval_basis",
        ),
        Issue(
            type=IssueType.required,
            message="start_date is required",
            field="leave_details.intermittent_leave_periods[0].start_date",
        ),
    ] == issues


def test_reduced_leave_period(test_db_session, initialize_factories_session):
    test_leave_periods = [ReducedScheduleLeavePeriodFactory.create(start_date=None, end_date=None)]
    issues = get_reduced_schedule_leave_issues(test_leave_periods)

    assert [
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
        leave_type_id=LeaveType.MEDICAL_LEAVE.leave_type_id, pregnant_or_recent_birth=None
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
        leave_type_id=LeaveType.BONDING_LEAVE.leave_type_id,
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
        leave_type_id=LeaveType.BONDING_LEAVE.leave_type_id,
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
        leave_type_id=LeaveType.BONDING_LEAVE.leave_type_id,
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
        leave_type_id=LeaveType.BONDING_LEAVE.leave_type_id,
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
        payment_preferences=[
            PaymentPreferenceFactory.create(
                payment_type_id=PaymentType.ACH.payment_type_id, account_number=None
            )
        ]
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Account number is required for direct deposit",
            field="payment_preferences[0].account_details.account_number",
        )
    ] == issues


def test_routing_number_required_for_ACH(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        payment_preferences=[
            PaymentPreferenceFactory.create(
                payment_type_id=PaymentType.ACH.payment_type_id, routing_number=None
            )
        ]
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Routing number is required for direct deposit",
            field="payment_preferences[0].account_details.routing_number",
        )
    ] == issues


def test_account_type_required_for_ACH(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        payment_preferences=[
            PaymentPreferenceFactory.create(
                payment_type_id=PaymentType.ACH.payment_type_id, type_of_account=None
            )
        ]
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Account type is required for direct deposit",
            field="payment_preferences[0].account_details.account_type",
        )
    ] == issues


def test_payment_preferences_same_order(test_db_session, initialize_factories_session, app):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        hours_worked_per_week=70,
        has_continuous_leave_periods=True,
        continuous_leave_periods=[ContinuousLeavePeriodFactory.create()],
        payment_preferences=[
            PaymentPreferenceFactory.create(payment_type_id=PaymentType.DEBIT.payment_type_id),
            PaymentPreferenceFactory.create(
                payment_type_id=PaymentType.ACH.payment_type_id, account_number=None
            ),
        ],
        mailing_address=None,
        residential_address=None,
        work_pattern=WorkPatternFixedFactory.create(),
    )
    issues = get_application_issues(test_app)

    with app.app.test_request_context(
        path=f"/v1/applications/{test_app.application_id}", method="PATCH"
    ):
        response = success_response(
            message="Application updated without errors.",
            data=ApplicationResponse.from_orm(test_app).dict(exclude_none=True),
            warnings=issues,
        ).to_api_response()
    assert response.json["warnings"] == [
        {
            "field": "residential_address",
            "message": "residential_address is required",
            "type": "required",
        },
        {
            "field": "payment_preferences[1].account_details.account_number",
            "message": "Account number is required for direct deposit",
            "rule": "conditional",
            "type": "required",
        },
    ]


def test_employer_notified_required_for_employed_claimants(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_notified=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
    )
    issues = get_conditional_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule=IssueRule.conditional,
            message="leave_details.employer_notified is required if employment_status is set to Employed",
            field="leave_details.employer_notified",
        )
    ] == issues


def test_allow_false_employer_notified_for_employed_claimants(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_notified=False,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
    )
    issues = get_conditional_issues(test_app)
    assert not issues


def test_pattern_start_date_required_if_rotating(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        work_pattern=WorkPattern(
            work_pattern_type=WorkPatternType.get_instance(
                test_db_session, template=WorkPatternType.ROTATING
            ),
            work_pattern_days=[
                WorkPatternDay(week_number=1, day_of_week_id=i + 1, hours=1) for i in range(7)
            ],
            work_week_starts_id=7,
        )
    )

    issues = get_work_pattern_issues(test_app)

    assert [
        Issue(
            type=IssueType.required,
            message="Pattern start date is required for rotating work patterns",
            field="work_pattern.pattern_start_date",
        )
    ] == issues


def test_pattern_start_date_is_not_expected_if_not_rotating(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        work_pattern=WorkPattern(
            work_pattern_type=WorkPatternType.get_instance(
                test_db_session, template=WorkPatternType.FIXED
            ),
            work_pattern_days=[
                WorkPatternDay(week_number=1, day_of_week_id=i + 1) for i in range(7)
            ],
            work_week_starts_id=7,
            pattern_start_date="2021-01-03",
        )
    )

    issues = get_work_pattern_issues(test_app)

    assert [
        Issue(
            type=IssueType.conflicting,
            message="Pattern start date is not expected for fixed or variable work patterns.",
            field="work_pattern.pattern_start_date",
        )
    ] == issues


def test_work_pattern_days_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        work_pattern=WorkPattern(
            work_pattern_type=WorkPatternType.get_instance(
                test_db_session, template=WorkPatternType.FIXED
            ),
            work_week_starts_id=7,
        )
    )

    issues = get_work_pattern_issues(test_app)

    assert [
        Issue(
            type=IssueType.required,
            message="Work patterns days are required",
            field="work_pattern.work_pattern_days",
        )
    ] == issues


def test_employer_fein_required_for_employed_claimants(
    test_db_session, initialize_factories_session
):
    test_app = ApplicationFactory.create(
        employer_fein=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
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

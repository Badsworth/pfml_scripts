from massgov.pfml.api.models.applications.responses import ApplicationResponse
from massgov.pfml.api.services.application_rules import (
    get_always_required_issues,
    get_application_issues,
    get_conditional_issues,
    get_continuous_leave_issues,
    get_intermittent_leave_issues,
    get_payments_issues,
    get_reduced_schedule_leave_issues,
)
from massgov.pfml.api.util.response import Issue, IssueType, success_response
from massgov.pfml.db.models.applications import EmploymentStatus, LeaveReasonQualifier, LeaveType
from massgov.pfml.db.models.employees import PaymentType
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ContinuousLeavePeriodFactory,
    IntermittentLeavePeriodFactory,
    PaymentPreferenceFactory,
    ReducedScheduleLeavePeriod,
)


def test_first_name_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        first_name=None,
        has_state_id=True,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        residential_address=AddressFactory.create(),
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
        residential_address=AddressFactory.create(),
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
        residential_address=AddressFactory.create(),
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
        residential_address=AddressFactory.create(),
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
        residential_address=AddressFactory.create(),
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
        residential_address=AddressFactory.create(),
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="leave_reason is required",
            field="leave_details.reason",
        )
    ] == issues


def test_employment_status_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=None, has_state_id=True, residential_address=AddressFactory.create()
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="employment_status is required",
            field="employment_status",
        )
    ] == issues


def test_residential_address_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        residential_address=None,
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        has_state_id=True,
    )
    issues = get_always_required_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            message="residential_address is required",
            field="residential_address",
        )
    ] == issues


def test_has_leave_periods_required(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        residential_address=AddressFactory.create(),
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


def test_continuous_leave_period(test_db_session, initialize_factories_session):
    test_leave_periods = [ContinuousLeavePeriodFactory.create(start_date=None, end_date=None)]
    issues = get_continuous_leave_issues(test_leave_periods)

    assert [
        Issue(
            type=IssueType.required,
            message="Start date is required for continuous_leave_periods[0]",
            field="leave_details.continuous_leave_periods[0].start_date",
        ),
        Issue(
            type=IssueType.required,
            message="End date is required for continuous_leave_periods[0]",
            field="leave_details.continuous_leave_periods[0].end_date",
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
    test_leave_periods = [ReducedScheduleLeavePeriod.create(start_date=None, end_date=None)]
    issues = get_reduced_schedule_leave_issues(test_leave_periods)

    assert [
        Issue(
            type=IssueType.required,
            message="Start date is required for reduced_schedule_leave_periods[0]",
            field="leave_details.reduced_schedule_leave_periods[0].start_date",
        ),
        Issue(
            type=IssueType.required,
            message="End date is required for reduced_schedule_leave_periods[0]",
            field="leave_details.reduced_schedule_leave_periods[0].end_date",
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


def test_mailing_address_required_for_debit(test_db_session, initialize_factories_session):
    test_app = ApplicationFactory.create(
        payment_preferences=[
            PaymentPreferenceFactory.create(payment_type_id=PaymentType.DEBIT.payment_type_id)
        ],
        mailing_address=None,
        residential_address=None,
    )
    issues = get_payments_issues(test_app)
    assert [
        Issue(
            type=IssueType.required,
            rule="conditional",
            message="Address is required for debit card for payment_preference[0]",
            field="residential_address",
        )
    ] == issues


def test_payment_preferences_same_order(test_db_session, initialize_factories_session, app):
    test_app = ApplicationFactory.create(
        employment_status=EmploymentStatus.get_instance(
            test_db_session, template=EmploymentStatus.EMPLOYED
        ),
        payment_preferences=[
            PaymentPreferenceFactory.create(payment_type_id=PaymentType.DEBIT.payment_type_id),
            PaymentPreferenceFactory.create(
                payment_type_id=PaymentType.ACH.payment_type_id, account_number=None
            ),
        ],
        mailing_address=None,
        residential_address=None,
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
            "field": "residential_address",
            "message": "Address is required for debit card for payment_preference[0]",
            "rule": "conditional",
            "type": "required",
        },
        {
            "field": "payment_preferences[1].account_details.account_number",
            "message": "Account number is required for direct deposit",
            "rule": "conditional",
            "type": "required",
        },
    ]

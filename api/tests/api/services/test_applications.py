import unittest.mock as mock
from datetime import date, datetime, timedelta

import pytest
from freezegun import freeze_time

import massgov
from massgov.pfml.api.services.administrator_fineos_actions import EformTypes
from massgov.pfml.api.services.applications import (
    set_application_absence_and_leave_period,
    set_customer_contact_detail_fields,
    set_customer_detail_fields,
    set_employer_benefits_from_fineos,
    set_employment_status_and_occupations,
    set_other_incomes_from_fineos,
    set_other_leaves,
    set_payment_preference_fields,
    split_application_by_date,
    split_start_end_dates,
)
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.absences import AbsenceReason
from massgov.pfml.db.models.applications import (
    AmountFrequency,
    ConcurrentLeave,
    ContinuousLeavePeriod,
    DayOfWeek,
    EmployerBenefit,
    EmploymentStatus,
    LeaveReason,
    LeaveReasonQualifier,
    OtherIncomeType,
)
from massgov.pfml.db.models.employees import BankAccountType, Gender, PaymentMethod
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ConcurrentLeaveFactory,
    ContinuousLeavePeriodFactory,
    EmployerBenefitFactory,
    IntermittentLeavePeriodFactory,
    OtherIncomeFactory,
    ReducedScheduleLeavePeriodFactory,
)
from massgov.pfml.fineos import exception
from massgov.pfml.fineos.mock.eform import (
    MOCK_EFORM_EMPLOYER_RESPONSE_V2,
    MOCK_EFORM_OTHER_INCOME_V1,
)
from massgov.pfml.fineos.models.customer_api import EForm, EFormAttribute, ModelEnum
from massgov.pfml.fineos.models.customer_api.spec import (
    AbsenceDay,
    AbsenceDetails,
    AbsencePeriod,
    EFormSummary,
    EpisodicLeavePeriodDetail,
    WeekBasedWorkPattern,
    WorkPatternDay,
)


@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


@pytest.fixture
def absence_case_id():
    return ""


@pytest.fixture
def fineos_web_id():
    return ""


@pytest.fixture
def fineos_client():
    return massgov.pfml.fineos.create_client()


@pytest.fixture
def application():
    return ApplicationFactory.create(leave_reason_id=None, phone=None)


@pytest.fixture
def continuous_leave_periods():
    return [
        AbsencePeriod(
            id="PL-14449-0000002238",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 1, 1),
            endDate=date(2021, 2, 9),
            absenceType="Continuous",
            requestStatus="Pending",
        )
    ]


@pytest.fixture
def continuous_leave_periods_not_open():
    return [
        AbsencePeriod(
            id="PL-14449-0000002238",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 1, 1),
            endDate=date(2021, 2, 9),
            absenceType="Continuous",
            requestStatus="Approved",
        )
    ]


@pytest.fixture
def intermittent_leave_periods():
    episodic_leave_period_detail = EpisodicLeavePeriodDetail(
        frequency=5,
        frequencyInterval=5,
        frequencyIntervalBasis="Month",
        duration=10,
        durationBasis="week",
    )
    return [
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 1, 29),
            endDate=date(2021, 1, 30),
            absenceType="Episodic",
            episodicLeavePeriodDetail=episodic_leave_period_detail,
            requestStatus="Pending",
        )
    ]


@pytest.fixture
def intermittent_leave_periods_not_open():
    episodic_leave_period_detail = EpisodicLeavePeriodDetail(
        frequency=5,
        frequencyInterval=5,
        frequencyIntervalBasis="Month",
        duration=10,
        durationBasis="week",
    )
    return [
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="Child Bonding",
            reasonQualifier1="Not Work Related",
            reasonQualifier2="",
            startDate=date(2021, 1, 29),
            endDate=date(2021, 1, 30),
            absenceType="Episodic",
            episodicLeavePeriodDetail=episodic_leave_period_detail,
            requestStatus="Approved",
        ),
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 2, 1),
            endDate=date(2021, 2, 15),
            absenceType="Episodic",
            episodicLeavePeriodDetail=episodic_leave_period_detail,
            requestStatus="Approved",
        ),
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="Care for a Family Member",
            reasonQualifier1="Adoption",
            reasonQualifier2="",
            startDate=date(2021, 1, 30),
            endDate=date(2021, 2, 12),
            absenceType="Episodic",
            episodicLeavePeriodDetail=episodic_leave_period_detail,
            requestStatus="Approved",
        ),
    ]


@pytest.fixture
def intermittent_leave_periods_invalid_leave_reason():
    episodic_leave_period_detail = EpisodicLeavePeriodDetail(
        frequency=5,
        frequencyInterval=5,
        frequencyIntervalBasis="Month",
        duration=10,
        durationBasis="week",
    )
    return [
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="invalid",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 1, 29),
            endDate=date(2021, 1, 30),
            absenceType="Episodic",
            episodicLeavePeriodDetail=episodic_leave_period_detail,
            requestStatus="Pending",
        )
    ]


@pytest.fixture
def intermittent_leave_periods_invalid_leave_reason_qualifier():
    episodic_leave_period_detail = EpisodicLeavePeriodDetail(
        frequency=5,
        frequencyInterval=5,
        frequencyIntervalBasis="Month",
        duration=10,
        durationBasis="week",
    )
    return [
        AbsencePeriod(
            id="PL-14449-0000002237",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Invalid",
            reasonQualifier2="",
            startDate=date(2021, 1, 29),
            endDate=date(2021, 1, 30),
            absenceType="Episodic",
            episodicLeavePeriodDetail=episodic_leave_period_detail,
            requestStatus="Pending",
        )
    ]


@pytest.fixture
def reduced_leave_periods():
    return [
        AbsencePeriod(
            id="PL-14449-0000002239",
            reason="Pregnancy/Maternity",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 1, 29),
            endDate=date(2021, 3, 29),
            absenceType="Reduced Schedule",
            requestStatus="Pending",
        )
    ]


@pytest.fixture
def absence_details(continuous_leave_periods, intermittent_leave_periods, reduced_leave_periods):
    return AbsenceDetails(
        creationDate=datetime(2020, 10, 10),
        notificationDate=date(2020, 10, 20),
        reportedTimeOff=[],
        absencePeriods=continuous_leave_periods
        + intermittent_leave_periods
        + reduced_leave_periods,
        absenceDays=[
            # friday, not in the reduced schedule leave range
            AbsenceDay(date=datetime(2021, 1, 15), timeRequested="3.25"),
            # monday
            AbsenceDay(date=datetime(2021, 2, 1), timeRequested="4.25"),
            # tuesday
            AbsenceDay(date=datetime(2021, 2, 2), timeRequested="3.00"),
        ],
        reportedReducedSchedule=[],
    )


@pytest.fixture
def absence_details_without_open_absence_period(
    continuous_leave_periods_not_open, intermittent_leave_periods_not_open
):
    return AbsenceDetails(
        creationDate=datetime(2020, 10, 10),
        notificationDate=date(2020, 10, 20),
        reportedTimeOff=[],
        absencePeriods=continuous_leave_periods_not_open + intermittent_leave_periods_not_open,
        reportedReducedSchedule=[],
    )


@pytest.fixture
def absence_details_invalid_leave_reason(intermittent_leave_periods_invalid_leave_reason):
    return AbsenceDetails(
        creationDate=datetime(2020, 10, 10),
        notificationDate=date(2020, 10, 20),
        reportedTimeOff=[],
        absencePeriods=intermittent_leave_periods_invalid_leave_reason,
        reportedReducedSchedule=[],
    )


@pytest.fixture
def absence_details_invalid_leave_reason_qualifier(
    intermittent_leave_periods_invalid_leave_reason_qualifier,
):
    return AbsenceDetails(
        creationDate=datetime(2020, 10, 10),
        notificationDate=date(2020, 10, 20),
        reportedTimeOff=[],
        absencePeriods=intermittent_leave_periods_invalid_leave_reason_qualifier,
        reportedReducedSchedule=[],
    )


def _compare_continuous_leave(
    application,
    continuous_leave: ContinuousLeavePeriod,
    fineos_continuous_leave: AbsencePeriod,
):
    assert continuous_leave.application_id == application.application_id
    assert continuous_leave.start_date == fineos_continuous_leave.startDate
    assert continuous_leave.end_date == fineos_continuous_leave.endDate


def _compare_intermittent_leave(application, intermittent_leave, fineos_intermittent_leave):
    assert intermittent_leave.application_id == application.application_id
    assert intermittent_leave.start_date == fineos_intermittent_leave.startDate
    assert intermittent_leave.end_date == fineos_intermittent_leave.endDate

    episodic_detail = fineos_intermittent_leave.episodicLeavePeriodDetail
    assert intermittent_leave.frequency == episodic_detail.frequency
    assert intermittent_leave.frequency_interval == episodic_detail.frequencyInterval
    assert intermittent_leave.frequency_interval_basis == episodic_detail.frequencyIntervalBasis
    assert intermittent_leave.duration == episodic_detail.duration
    assert intermittent_leave.duration_basis == episodic_detail.durationBasis


def _compare_reduced_leave(application, reduced_leave, fineos_reduced_leave):
    assert reduced_leave.application_id == application.application_id
    assert reduced_leave.start_date == fineos_reduced_leave.startDate
    assert reduced_leave.end_date == fineos_reduced_leave.endDate
    assert reduced_leave.monday_off_minutes == 255
    assert reduced_leave.tuesday_off_minutes == 180
    assert reduced_leave.wednesday_off_minutes == 0
    assert reduced_leave.thursday_off_minutes == 0
    assert reduced_leave.friday_off_minutes == 0
    assert reduced_leave.saturday_off_minutes == 0
    assert reduced_leave.sunday_off_minutes == 0


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
def test_set_application_absence_and_leave_period(
    mock_get_absence, fineos_client, fineos_web_id, absence_case_id, application, absence_details
):
    mock_get_absence.return_value = absence_details
    set_application_absence_and_leave_period(
        fineos_client, fineos_web_id, application, absence_case_id
    )

    assert len(application.continuous_leave_periods) == 1
    assert application.has_continuous_leave_periods
    continuous_leave = application.continuous_leave_periods[0]
    fineos_continuous_leave = absence_details.absencePeriods[0]
    _compare_continuous_leave(application, continuous_leave, fineos_continuous_leave)

    assert len(application.intermittent_leave_periods) == 1
    assert application.has_intermittent_leave_periods
    intermittent_leave = application.intermittent_leave_periods[0]
    fineos_intermittent_leave = absence_details.absencePeriods[1]
    _compare_intermittent_leave(application, intermittent_leave, fineos_intermittent_leave)

    assert len(application.reduced_schedule_leave_periods) == 1
    assert application.has_reduced_schedule_leave_periods
    reduced_leave = application.reduced_schedule_leave_periods[0]
    fineos_reduced_leave = absence_details.absencePeriods[2]
    _compare_reduced_leave(application, reduced_leave, fineos_reduced_leave)

    assert application.leave_reason_id == LeaveReason.get_id(
        absence_details.absencePeriods[0].reason
    )
    assert application.leave_reason_qualifier_id == LeaveReasonQualifier.get_id(
        absence_details.absencePeriods[0].reasonQualifier1
    )
    assert application.pregnant_or_recent_birth
    assert application.completed_time is None

    assert application.submitted_time == absence_details.creationDate
    assert application.has_future_child_date is False

    absence_details.absencePeriods[0].reason = "Child Bonding"
    absence_details.absencePeriods[0].status = "estimated"
    mock_get_absence.return_value = absence_details
    set_application_absence_and_leave_period(
        fineos_client, fineos_web_id, application, absence_case_id
    )
    assert application.has_future_child_date is True


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
def test_set_application_absence_and_leave_period_without_open_absence_period(
    mock_get_absence,
    fineos_client,
    fineos_web_id,
    absence_case_id,
    application,
    absence_details_without_open_absence_period,
):
    mock_get_absence.return_value = absence_details_without_open_absence_period
    set_application_absence_and_leave_period(
        fineos_client, fineos_web_id, application, absence_case_id
    )

    assert len(application.continuous_leave_periods) == 1
    assert application.has_continuous_leave_periods
    continuous_leave = application.continuous_leave_periods[0]
    fineos_continuous_leave = absence_details_without_open_absence_period.absencePeriods[0]
    _compare_continuous_leave(application, continuous_leave, fineos_continuous_leave)

    assert len(application.intermittent_leave_periods) == 3
    assert application.has_intermittent_leave_periods

    intermittent_leave = application.intermittent_leave_periods[0]
    fineos_intermittent_leave = absence_details_without_open_absence_period.absencePeriods[1]
    _compare_intermittent_leave(application, intermittent_leave, fineos_intermittent_leave)

    assert application.leave_reason_id == LeaveReason.get_id(
        absence_details_without_open_absence_period.absencePeriods[2].reason
    )
    assert application.leave_reason_qualifier_id == LeaveReasonQualifier.get_id(
        absence_details_without_open_absence_period.absencePeriods[2].reasonQualifier1
    )

    assert application.pregnant_or_recent_birth is True
    assert application.completed_time is not None

    assert application.submitted_time == absence_details_without_open_absence_period.creationDate


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
def test_set_application_absence_and_leave_period_invalid_leave_reason(
    mock_get_absence,
    fineos_client,
    fineos_web_id,
    absence_case_id,
    application,
    absence_details_invalid_leave_reason,
):
    mock_get_absence.return_value = absence_details_invalid_leave_reason
    with pytest.raises(ValidationException) as exc:
        set_application_absence_and_leave_period(
            fineos_client, fineos_web_id, application, absence_case_id
        )
    assert exc.value.errors == [
        ValidationErrorDetail(
            type=IssueType.invalid,
            message="Absence period reason is not supported.",
            field="leave_details.reason",
        )
    ]


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
def test_set_application_absence_and_leave_period_valid_but_unsupported_leave_reason(
    mock_get_absence, fineos_client, fineos_web_id, absence_case_id, application, absence_details
):
    valid_reason = AbsenceReason.MILITARY_CAREGIVER.absence_reason_description
    absence_details.absencePeriods[0].reason = valid_reason
    mock_get_absence.return_value = absence_details
    with pytest.raises(ValidationException) as exc:
        set_application_absence_and_leave_period(
            fineos_client, fineos_web_id, application, absence_case_id
        )
    assert exc.value.errors == [
        ValidationErrorDetail(
            type=IssueType.invalid,
            message="Absence period reason is not supported.",
            field="leave_details.reason",
        )
    ]


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
def test_set_application_absence_and_leave_period_invalid_leave_reason_qualifier(
    mock_get_absence,
    fineos_client,
    fineos_web_id,
    absence_case_id,
    application,
    absence_details_invalid_leave_reason_qualifier,
):
    mock_get_absence.return_value = absence_details_invalid_leave_reason_qualifier
    with pytest.raises(KeyError):
        set_application_absence_and_leave_period(
            fineos_client, fineos_web_id, application, absence_case_id
        )


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.first_name == "Samantha"
    assert application.last_name == "Jorgenson"
    assert application.gender_id == Gender.NONBINARY.gender_id
    assert application.mass_id == "123456789"
    assert application.has_state_id is True
    assert application.residential_address.address_line_one == "37 Mather Drive"


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields_with_invalid_gender(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    customer_details.gender = "Any"
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.gender is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields_with_no_gender(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    customer_details.gender = None
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.gender is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields_with_no_mass_id(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    customer_details.classExtensionInformation = []
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.mass_id is None
    assert application.has_state_id is False


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields_with_blank_mass_id(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    customer_details.classExtensionInformation = [
        massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
            name="MassachusettsID", stringValue=""
        )
    ]
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.mass_id is None
    assert application.has_state_id is False


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields_with_invalid_address(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    customer_details.customerAddress = "1234 SE Main"
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.residential_address is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
def test_set_customer_detail_fields_with_blank_address(
    mock_read_customer_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
    customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
        customer_details_json
    )
    customer_details.customerAddress = None
    mock_read_customer_details.return_value = customer_details
    set_customer_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.residential_address is None


def test_set_employment_status_and_occupations(fineos_client, fineos_web_id, application, user):
    set_employment_status_and_occupations(fineos_client, fineos_web_id, application)
    assert application.employment_status_id == EmploymentStatus.EMPLOYED.employment_status_id
    assert application.hours_worked_per_week == 37.5
    assert (
        application.work_pattern.work_pattern_days[0].day_of_week_id
        == DayOfWeek.MONDAY.day_of_week_id
    )
    assert application.work_pattern.work_pattern_days[0].minutes == 5 + 4 * 60


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_week_based_work_pattern")
def test_set_employment_status_and_occupations_work_pattern_not_fixed(
    mock_get_week_based_work_pattern, fineos_client, fineos_web_id, application, user
):
    mock_get_week_based_work_pattern.return_value = WeekBasedWorkPattern(
        workPatternType="2 weeks Rotating",
        workPatternDays=[WorkPatternDay(dayOfWeek="Monday", weekNumber=12, hours=4, minutes=5)],
    )
    set_employment_status_and_occupations(fineos_client, fineos_web_id, application)
    assert application.employment_status_id == EmploymentStatus.EMPLOYED.employment_status_id
    assert application.hours_worked_per_week == 37.5
    assert application.work_pattern is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_week_based_work_pattern")
def test_set_employment_status_and_occupations_work_pattern_fineos_error(
    mock_get_week_based_work_pattern, fineos_client, fineos_web_id, application, user
):
    # FINEOS returns a 403 Forbidden error for Variable work patterns
    error_msg = """{
        "error" : "User does not have permission to access the resource or the instance data",
        "correlationId" : "1234"
    }"""
    error = exception.FINEOSForbidden("get_week_based_work_pattern", 200, 403, error_msg)
    mock_get_week_based_work_pattern.side_effect = error
    set_employment_status_and_occupations(fineos_client, fineos_web_id, application)
    # data from the get_customer_occupations_customer_api() call is unaffected
    assert application.employment_status_id == EmploymentStatus.EMPLOYED.employment_status_id
    assert application.hours_worked_per_week == 37.5
    # due to 403 error, no work_pattern is set
    assert application.work_pattern is None


@mock.patch(
    "massgov.pfml.fineos.mock_client.MockFINEOSClient.get_customer_occupations_customer_api"
)
@pytest.mark.parametrize("status", ("Terminated", "Self-Employed", "Retired", "Unknown"))
def test_set_invalid_status_returns_error(
    mock_get_customer_occupations_customer_api,
    fineos_client,
    fineos_web_id,
    application,
    user,
    status,
):
    mock_get_customer_occupations_customer_api.return_value = [
        massgov.pfml.fineos.models.customer_api.ReadCustomerOccupation(
            occupationId=12345, hoursWorkedPerWeek=37.5, employmentStatus=status
        )
    ]
    with pytest.raises(ValidationException) as exc:
        set_employment_status_and_occupations(fineos_client, fineos_web_id, application)
        assert exc.value.errors == [
            ValidationErrorDetail(
                type=IssueType.invalid,
                message="Employment Status must be Active",
                field="employment_status",
            )
        ]


def test_set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session):
    set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.has_submitted_payment_preference is True
    assert (
        application.payment_preference.payment_method.payment_method_id
        == PaymentMethod.ACH.payment_method_id
    )
    assert application.payment_preference.account_number == "1234565555"
    assert application.payment_preference.routing_number == "011222333"
    assert (
        application.payment_preference.bank_account_type.bank_account_type_id
        == BankAccountType.CHECKING.bank_account_type_id
    )
    assert application.has_mailing_address is True
    assert application.mailing_address.address_line_one == "44324 Nayeli Stream"


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
def test_set_payment_preference_fields_without_a_default_preference(
    mock_get_payment_preferences, fineos_client, fineos_web_id, application, test_db_session
):
    mock_get_payment_preferences.return_value = [
        massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
            paymentMethod="Elec Funds Transfer",
            paymentPreferenceId="96166",
            accountDetails=massgov.pfml.fineos.models.customer_api.AccountDetails(
                accountNo="0987654321",
                accountName="Constance Griffin",
                routingNumber="011222333",
                accountType="Checking",
            ),
        ),
        massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
            paymentMethod="Elec Funds Transfer",
            paymentPreferenceId="1234",
            accountDetails=massgov.pfml.fineos.models.customer_api.AccountDetails(
                accountNo="1234565555",
                accountName="Constance Griffin",
                routingNumber="011222333",
                accountType="Checking",
            ),
        ),
    ]
    set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session)
    # takes first payment pref, if none is set to default
    assert application.payment_preference.account_number == "0987654321"
    assert application.has_submitted_payment_preference is True


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
def test_set_payment_preference_fields_with_check_as_default_preference(
    mock_get_payment_preferences, fineos_client, fineos_web_id, application, test_db_session
):
    mock_get_payment_preferences.return_value = [
        massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
            paymentMethod="Check",
            paymentPreferenceId="96166",
            isDefault=True,
            chequeDetails=massgov.pfml.fineos.models.customer_api.ChequeDetails(
                nameToPrintOnCheck=""
            ),
            customerAddress=massgov.pfml.fineos.models.customer_api.CustomerAddress(
                address=massgov.pfml.fineos.models.customer_api.Address(
                    addressLine1="1234 SE Elm",
                    addressLine2="",
                    addressLine3="",
                    addressLine4="Amherst",
                    addressLine5="",
                    addressLine6="MA",
                    addressLine7="",
                    postCode="01002",
                    country="USA",
                    classExtensionInformation=[],
                )
            ),
        ),
    ]
    set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert (
        application.payment_preference.payment_method.payment_method_id
        == PaymentMethod.CHECK.payment_method_id
    )
    assert application.has_submitted_payment_preference is True
    assert application.has_mailing_address is True
    assert application.mailing_address.address_line_one == "1234 SE Elm"


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
def test_set_payment_preference_fields_with_blank_payment_method(
    mock_get_payment_preferences, fineos_client, fineos_web_id, application, test_db_session
):
    mock_get_payment_preferences.return_value = [
        massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
            paymentMethod="", paymentPreferenceId="1234", isDefault=True
        )
    ]
    set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.payment_preference is None
    assert application.has_submitted_payment_preference is False


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
def test_set_payment_preference_fields_without_address(
    mock_get_payment_preferences, fineos_client, fineos_web_id, application, test_db_session
):
    mock_get_payment_preferences.return_value = [
        massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
            paymentMethod="Elec Funds Transfer",
            paymentPreferenceId="85622",
            isDefault=True,
            accountDetails=massgov.pfml.fineos.models.customer_api.AccountDetails(
                accountNo="1234565555",
                accountName="Constance Griffin",
                routingNumber="011222333",
                accountType="Checking",
            ),
        )
    ]
    set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.has_mailing_address is False
    assert application.mailing_address is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
def test_set_customer_contact_detail_fields(
    mock_read_customer_contact_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_contact_details_json = massgov.pfml.fineos.mock_client.mock_customer_contact_details()
    customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
        customer_contact_details_json
    )

    application.user.mfa_phone_number = "+13214567890"
    application.user.mfa_delivery_preference_id = 1  # 'SMS' for MFA
    mock_read_customer_contact_details.return_value = customer_contact_details
    set_customer_contact_detail_fields(fineos_client, fineos_web_id, application, test_db_session)

    # This also asserts that the preferred phone number gets returned in this case
    # since the phone number being set is the 2nd element in the phoneNumbers array
    assert application.phone.phone_number == "+13214567890"
    assert application.phone_id == application.phone.phone_id


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
def test_set_customer_contact_detail_fields_missing_country_code(
    mock_read_customer_contact_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_contact_details_json = massgov.pfml.fineos.mock_client.mock_customer_contact_details()
    # country code missing
    for phone_num in customer_contact_details_json["phoneNumbers"]:
        phone_num["intCode"] = None
    customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
        customer_contact_details_json
    )

    application.user.mfa_phone_number = "+13214567890"
    application.user.mfa_delivery_preference_id = 1
    mock_read_customer_contact_details.return_value = customer_contact_details
    set_customer_contact_detail_fields(fineos_client, fineos_web_id, application, test_db_session)

    # We still get a match, country code added
    assert application.phone.phone_number == "+13214567890"
    assert application.phone_id == application.phone.phone_id


def test_set_customer_contact_detail_fields_without_mfa_enabled(
    fineos_client, fineos_web_id, application, test_db_session
):
    application.user.mfa_phone_number = None
    application.user.mfa_delivery_preference_id = 2  # 'opt-out' of MFA
    with pytest.raises(ValidationException) as exc:
        set_customer_contact_detail_fields(
            fineos_client, fineos_web_id, application, test_db_session
        )

    assert exc.value.errors == [
        ValidationErrorDetail(
            type=IssueType.incorrect,
            message="Code 3: An issue occurred while trying to import the application.",
        )
    ]
    assert application.phone is None


def test_set_customer_contact_detail_fields_without_matching_mfa_phone_number(
    fineos_client, fineos_web_id, application, test_db_session
):
    application.user.mfa_phone_number = "+12341456789"
    application.user.mfa_delivery_preference_id = 1
    with pytest.raises(ValidationException) as exc:
        set_customer_contact_detail_fields(
            fineos_client, fineos_web_id, application, test_db_session
        )

    assert exc.value.errors == [
        ValidationErrorDetail(
            type=IssueType.incorrect,
            message="Code 3: An issue occurred while trying to import the application.",
        )
    ]

    assert application.phone is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
def test_set_customer_contact_detail_fields_with_invalid_phone_number(
    mock_read_customer_contact_details, fineos_client, fineos_web_id, application, test_db_session
):
    customer_contact_details_json = massgov.pfml.fineos.mock_client.mock_customer_contact_details()
    customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
        customer_contact_details_json
    )
    # Reset phone fields that get auto generated from the application factory
    application.phone_id = None
    application.phone = None
    customer_contact_details.phoneNumbers = None

    mock_read_customer_contact_details.return_value = customer_contact_details
    set_customer_contact_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.phone is None
    assert application.phone_id is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
def test_set_customer_contact_detail_fields_with_no_contact_details_returned_from_fineos(
    mock_read_customer_contact_details, fineos_client, fineos_web_id, application, test_db_session
):
    # Reset phone fields that get auto generated from the application factory
    application.phone_id = None
    application.phone = None

    # Checks to assert that if FINEOS returns no data, we don't update the applications phone record
    mock_read_customer_contact_details.return_value = None
    set_customer_contact_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.phone is None
    assert application.phone_id is None

    # Checks to assert that if FINEOS returns contact details, but no phone numbers,
    # we don't update the application phone record
    customer_contact_details_json = massgov.pfml.fineos.mock_client.mock_customer_contact_details()
    customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
        customer_contact_details_json
    )
    customer_contact_details.phoneNumbers = None
    mock_read_customer_contact_details.return_value = customer_contact_details
    set_customer_contact_detail_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.phone is None
    assert application.phone_id is None


def test_set_other_leaves(
    fineos_client, fineos_web_id, application, test_db_session, absence_case_id
):
    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is True
    assert application.has_previous_leaves_same_reason is False
    assert application.has_concurrent_leave is True


def test_set_other_leaves_includes_minutes(
    fineos_client, fineos_web_id, application, test_db_session, absence_case_id
):
    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is True
    test_db_session.refresh(application)
    # values from MOCK_CUSTOMER_EFORM_OTHER_LEAVES
    assert application.previous_leaves_other_reason[0].leave_minutes == 2400
    assert application.previous_leaves_other_reason[0].worked_per_week_minutes == 1245


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform_summary")
def test_set_other_leaves_with_no_leaves(
    mock_customer_get_eform_summary,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    mock_customer_get_eform_summary.return_value = []
    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is False
    assert application.has_previous_leaves_same_reason is False
    assert application.has_concurrent_leave is False
    assert application.concurrent_leave is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_leaves_with_only_concurrent_leave(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Leaves - current version",
        eformAttributes=[
            # Minimum info needed to create Concurrent Leave:
            EFormAttribute(
                name="V2AccruedPLEmployer1",  # is_for_current_employer
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            )
        ],
    )
    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is False
    assert application.has_previous_leaves_same_reason is False
    assert application.has_concurrent_leave is True


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_leaves_with_only_previous_leave_same_reason(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Leaves - current version",
        eformAttributes=[
            # Minimum info needed to create Previous Leave, same reason:
            EFormAttribute(
                name="V2Leave1",  # is_for_same_reason
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="V2LeaveFromEmployer1",  # is_for_current_employer
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
        ],
    )

    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is False
    assert application.has_previous_leaves_same_reason is True
    assert application.has_concurrent_leave is False
    assert application.concurrent_leave is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_leaves_with_only_previous_leave_other_reason(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Leaves - current version",
        eformAttributes=[
            # Minimum info needed to create Previous Leave, other reason:
            EFormAttribute(
                name="V2Leave1",  # is_for_same_reason
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
            ),
            EFormAttribute(
                name="V2LeaveFromEmployer1",  # is_for_current_employer
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
        ],
    )

    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is True
    assert application.has_previous_leaves_same_reason is False
    assert application.has_concurrent_leave is False
    assert application.concurrent_leave is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_leaves_with_both_types_of_previous_leave(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Leaves - current version",
        eformAttributes=[
            # Minimum info needed to create Previous Leaves, both other and same reason:
            EFormAttribute(
                name="V2Leave1",  # is_for_same_reason
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="No"),
            ),
            EFormAttribute(
                name="V2LeaveFromEmployer1",  # is_for_current_employer
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="V2Leave2",  # is_for_same_reason
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
            EFormAttribute(
                name="V2LeaveFromEmployer2",  # is_for_current_employer
                enumValue=ModelEnum(domainName="PleaseSelectYesNo", instanceValue="Yes"),
            ),
        ],
    )

    set_other_leaves(fineos_client, fineos_web_id, application, test_db_session, absence_case_id)
    assert application.has_previous_leaves_other_reason is True
    assert application.has_previous_leaves_same_reason is True
    assert application.has_concurrent_leave is False
    assert application.concurrent_leave is None


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_employer_benefits_from_fineos_v1(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    eform_summaries = [
        EFormSummary(eformId=211714, eformType=EformTypes.OTHER_INCOME),
        EFormSummary(eformId=211714, eformType=EformTypes.OTHER_LEAVES),  # should not be parsed
    ]

    mock_customer_get_eform.return_value = MOCK_EFORM_OTHER_INCOME_V1

    set_employer_benefits_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=eform_summaries,
    )
    assert application.has_employer_benefits is True
    assert len(application.employer_benefits) == 1


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_employer_benefits_from_fineos_v2(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    eform_summaries = [
        EFormSummary(eformId=211714, eformType=EformTypes.OTHER_INCOME_V2),
    ]

    mock_customer_get_eform.return_value = MOCK_EFORM_EMPLOYER_RESPONSE_V2

    set_employer_benefits_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=eform_summaries,
    )
    assert application.has_employer_benefits is True
    assert len(application.employer_benefits) == 1


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_employer_benefits_from_fineos_v2_does_not_insert_duplicate_other_income(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    eform_summaries = [
        EFormSummary(eformId=211714, eformType=EformTypes.OTHER_INCOME_V2),
    ]

    mock_customer_get_eform.return_value = MOCK_EFORM_EMPLOYER_RESPONSE_V2

    set_employer_benefits_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=eform_summaries,
    )
    set_other_incomes_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=eform_summaries,
    )
    assert application.has_employer_benefits is True
    assert len(application.employer_benefits) == 1
    assert application.has_other_incomes is False
    assert len(application.other_incomes) == 0


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_incomes_from_fineos(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    eform_summaries = [
        EFormSummary(eformId=1, eformType=EformTypes.OTHER_INCOME_V2),
        EFormSummary(eformId=2, eformType=EformTypes.OTHER_INCOME),  # should not be parsed
        EFormSummary(eformId=3, eformType=EformTypes.OTHER_LEAVES),  # should not be parsed
    ]

    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Income - current version",
        eformAttributes=[
            # Minimum info needed to create Previous Leaves, both other and same reason:
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitStartDate",
                dateValue="2021-05-04",
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitEndDate",
                dateValue="2021-05-05",
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitFrequency",
                enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per Month"),
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitWRT",
                enumValue=ModelEnum(
                    domainName="WageReplacementType2",
                    instanceValue="Earnings from another employer or through self-employment",
                ),
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement",
                enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Yes"),
            ),
            EFormAttribute(name="V2OtherIncomeNonEmployerBenefitAmount1", decimalValue=100.0),
        ],
    )
    set_other_incomes_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=eform_summaries,
    )

    assert application.has_other_incomes is True
    assert application.other_incomes[0].income_amount_dollars == 100
    assert (
        application.other_incomes[0].income_type_id == 7
    )  # OTHER EMPLOYER INCOME TYPE (lk_other_income_type)
    assert len(application.other_incomes) == 1


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_incomes_with_multiple_different_income_types(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):

    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Income - current version",
        eformAttributes=[
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitStartDate",
                dateValue="2021-05-04",
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitEndDate",
                dateValue="2021-05-05",
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitFrequency",
                enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Per Month"),
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitWRT1",
                enumValue=ModelEnum(
                    domainName="WageReplacementType2", instanceValue="Jones Act benefits"
                ),
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitWRT2",
                enumValue=ModelEnum(
                    domainName="WageReplacementType2",
                    instanceValue="Disability benefits under a governmental retirement plan such as STRS or PERS",
                ),
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement",
                enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Yes"),
            ),
            EFormAttribute(name="V2OtherIncomeNonEmployerBenefitAmount1", decimalValue=100.0),
            EFormAttribute(name="V2OtherIncomeNonEmployerBenefitAmount2", decimalValue=200.0),
        ],
    )
    set_other_incomes_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=[EFormSummary(eformId=1, eformType=EformTypes.OTHER_INCOME_V2)],
    )
    assert application.has_other_incomes is True

    assert application.other_incomes[0].income_amount_dollars == 100
    assert application.other_incomes[0].income_type_id == 5  # (lk_other_income_type)

    assert application.other_incomes[1].income_amount_dollars == 200
    assert application.other_incomes[1].income_type_id == 4  # (lk_other_income_type)

    assert len(application.other_incomes) == 2


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
def test_set_other_incomes_from_fineos_without_frequency_or_type(
    mock_customer_get_eform,
    fineos_client,
    fineos_web_id,
    application,
    test_db_session,
    absence_case_id,
):
    eform_summaries = [
        EFormSummary(eformId=1, eformType=EformTypes.OTHER_INCOME_V2),
    ]

    mock_customer_get_eform.return_value = EForm(
        eformId=211714,
        eformType="Other Income - current version",
        eformAttributes=[
            # Minimum info needed to create Previous Leaves, both other and same reason:
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitStartDate",
                dateValue="2021-05-04",
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitEndDate",
                dateValue="2021-05-05",
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitFrequency",
                enumValue=ModelEnum(domainName="FrequencyEforms", instanceValue="Not Provided"),
            ),
            EFormAttribute(
                name="V2OtherIncomeNonEmployerBenefitWRT",
                enumValue=ModelEnum(
                    domainName="WageReplacementType2",
                    instanceValue="Please Select",
                ),
            ),
            EFormAttribute(
                name="V2ReceiveWageReplacement",
                enumValue=ModelEnum(domainName="YesNoI'veApplied", instanceValue="Yes"),
            ),
            EFormAttribute(name="V2OtherIncomeNonEmployerBenefitAmount1", decimalValue=100.0),
        ],
    )
    set_other_incomes_from_fineos(
        fineos_client,
        fineos_web_id,
        application,
        test_db_session,
        absence_case_id,
        eform_summaries=eform_summaries,
    )

    assert application.has_other_incomes is True
    assert application.other_incomes[0].income_amount_dollars == 100
    assert (
        application.other_incomes[0].income_amount_frequency_id
        == AmountFrequency.UNKNOWN.amount_frequency_id
    )
    assert (
        application.other_incomes[0].income_type_id == OtherIncomeType.UNKNOWN.other_income_type_id
    )
    assert len(application.other_incomes) == 1


class TestSplitApplicationByDate:
    class TestSplitStartEndDates:
        def test_dates_exclusively_after_split(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date + timedelta(days=10)
                end_date = split_on_date + timedelta(days=20)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )
                assert dates_before is None
                assert dates_after is not None
                assert dates_after.start_date == start_date
                assert dates_after.end_date == end_date

        def test_dates_exclusively_before_split(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=20)
                end_date = split_on_date - timedelta(days=10)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_after is None
                assert dates_before is not None
                assert dates_before.start_date == start_date
                assert dates_before.end_date == end_date

        def test_start_date_equals_split_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date
                end_date = split_on_date + timedelta(days=20)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before is not None
                assert dates_before.start_date == start_date
                assert dates_before.end_date == start_date
                assert dates_after is not None
                assert dates_after.start_date == split_on_date + timedelta(days=1)
                assert dates_after.end_date == end_date

        def test_end_date_equals_split_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=10)
                end_date = split_on_date
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before is not None
                assert dates_before.start_date == start_date
                assert dates_before.end_date == end_date
                assert dates_after is None

        def test_end_date_before_start_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=10)
                end_date = start_date - timedelta(days=1)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before is None
                assert dates_after is None

        def test_split_date(self):
            with freeze_time("2021-06-14"):
                split_on_date = date.today()
                start_date = split_on_date - timedelta(days=10)
                end_date = split_on_date + timedelta(days=10)
                dates_before, dates_after = split_start_end_dates(
                    start_date, end_date, split_on_date
                )

                assert dates_before.start_date == start_date
                assert dates_before.end_date == split_on_date
                assert dates_after.start_date == split_on_date + timedelta(1)
                assert dates_after.end_date == end_date

    def _verify_leave_period(self, leave_period, start_date, end_date, application_id):
        assert leave_period.application_id == application_id
        if isinstance(leave_period, ConcurrentLeave):
            assert leave_period.leave_start_date == start_date
            assert leave_period.leave_end_date == end_date
        else:
            assert leave_period.start_date == start_date
            assert leave_period.end_date == end_date

    def _verify_benefit(self, benefit, start_date, end_date, amount, application_id):
        assert benefit.application_id == application_id
        if isinstance(benefit, EmployerBenefit):
            assert benefit.benefit_start_date == start_date
            assert benefit.benefit_end_date == end_date
            assert benefit.benefit_amount_dollars == amount
        else:
            assert benefit.income_start_date == start_date
            assert benefit.income_end_date == end_date
            assert benefit.income_amount_dollars == amount

    def test_split_no_leave_periods_or_benefits(self, application, test_db_session):
        split_on_date = date.today()
        split_app_1, split_app_2 = split_application_by_date(
            test_db_session, application, split_on_date
        )
        test_db_session.refresh(split_app_1)
        test_db_session.refresh(split_app_2)

        assert split_app_1.application_id == application.application_id
        assert split_app_2.application_id != application.application_id
        assert split_app_1.application_id != split_app_2.application_id
        assert split_app_1.split_into_application_id == split_app_2.application_id
        assert split_app_2.split_from_application_id == split_app_1.application_id
        assert split_app_1.claim_id is None
        assert split_app_2.claim_id is None

    def test_leave_periods_multiple_dates(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date_1 = split_on_date - timedelta(days=20)
            end_date_1 = split_on_date - timedelta(days=10)

            start_date_2 = split_on_date - timedelta(days=10)
            end_date_2 = split_on_date + timedelta(days=10)

            start_date_3 = split_on_date + timedelta(days=10)
            end_date_3 = split_on_date + timedelta(days=20)

            application.continuous_leave_periods = [
                ContinuousLeavePeriodFactory.create(
                    start_date=start_date_1,
                    end_date=end_date_1,
                ),
                ContinuousLeavePeriodFactory.create(
                    start_date=start_date_2,
                    end_date=end_date_2,
                ),
                ContinuousLeavePeriodFactory.create(
                    start_date=start_date_3,
                    end_date=end_date_3,
                ),
            ]

            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            # Apply a consistent ordering to the leave periods before validating
            split_app_1_leave_periods = split_app_1.continuous_leave_periods
            split_app_1_leave_periods.sort(key=lambda lp: lp.start_date)
            split_app_2_leave_periods = split_app_2.continuous_leave_periods
            split_app_2_leave_periods.sort(key=lambda lp: lp.start_date)

            assert len(split_app_1.continuous_leave_periods) == 2
            assert len(split_app_2.continuous_leave_periods) == 2
            self._verify_leave_period(
                split_app_1_leave_periods[0], start_date_1, end_date_1, split_app_1.application_id
            )
            self._verify_leave_period(
                split_app_1_leave_periods[1],
                start_date_2,
                split_on_date,
                split_app_1.application_id,
            )
            self._verify_leave_period(
                split_app_2_leave_periods[0],
                split_on_date + timedelta(days=1),
                end_date_2,
                split_app_2.application_id,
            )
            self._verify_leave_period(
                split_app_2_leave_periods[1], start_date_3, end_date_3, split_app_2.application_id
            )

    def test_split_multiple_type_of_leave_periods(self, application, test_db_session):
        split_on_date = date.today()
        application.continuous_leave_periods = [
            ContinuousLeavePeriodFactory.create(
                start_date=split_on_date - timedelta(days=10),
                end_date=split_on_date + timedelta(days=10),
            )
        ]
        application.intermittent_leave_periods = [
            IntermittentLeavePeriodFactory.create(
                start_date=split_on_date - timedelta(days=10),
                end_date=split_on_date + timedelta(days=10),
            )
        ]
        application.reduced_schedule_leave_periods = [
            ReducedScheduleLeavePeriodFactory.create(
                start_date=split_on_date - timedelta(days=10),
                end_date=split_on_date + timedelta(days=10),
            )
        ]
        application.concurrent_leave = ConcurrentLeaveFactory.create(
            leave_start_date=split_on_date - timedelta(days=10),
            leave_end_date=split_on_date + timedelta(days=10),
            application=application,
        )
        application.has_concurrent_leave = True

        split_app_1, split_app_2 = split_application_by_date(
            test_db_session, application, split_on_date
        )
        test_db_session.refresh(split_app_1)
        test_db_session.refresh(split_app_2)

        assert len(split_app_1.all_leave_periods) == 3
        assert len(split_app_2.all_leave_periods) == 3
        for leave_period in split_app_1.all_leave_periods:
            self._verify_leave_period(
                leave_period,
                split_on_date - timedelta(days=10),
                split_on_date,
                split_app_1.application_id,
            )

        for leave_period in split_app_2.all_leave_periods:
            self._verify_leave_period(
                leave_period,
                split_on_date + timedelta(days=1),
                split_on_date + timedelta(days=10),
                split_app_2.application_id,
            )

        self._verify_leave_period(
            split_app_1.concurrent_leave,
            split_on_date - timedelta(days=10),
            split_on_date,
            split_app_1.application_id,
        )
        self._verify_leave_period(
            split_app_2.concurrent_leave,
            split_on_date + timedelta(days=1),
            split_on_date + timedelta(days=10),
            split_app_2.application_id,
        )

    def test_multiple_benefits(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=10)
            end_date = split_on_date + timedelta(days=20)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=100,
                )
            ]
            application.other_incomes = [
                OtherIncomeFactory.create(
                    application_id=application.application_id,
                    income_start_date=start_date,
                    income_end_date=end_date,
                    income_amount_dollars=200,
                )
            ]

            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 1
            assert len(split_app_2.employer_benefits) == 1
            assert len(split_app_1.other_incomes) == 1
            assert len(split_app_2.other_incomes) == 1
            for benefit in split_app_1.employer_benefits:
                self._verify_benefit(
                    benefit, start_date, split_on_date, 100, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                self._verify_benefit(
                    benefit, split_on_date + timedelta(1), end_date, 100, split_app_2.application_id
                )
            for income in split_app_1.other_incomes:
                self._verify_benefit(
                    income, start_date, split_on_date, 200, split_app_1.application_id
                )
            for income in split_app_2.other_incomes:
                self._verify_benefit(
                    income, split_on_date + timedelta(1), end_date, 200, split_app_2.application_id
                )

    def test_benefit_all_at_once_frequency_scenario_uneven_split(
        self, application, test_db_session
    ):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=20)
            end_date = split_on_date + timedelta(days=14)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 1
            assert len(split_app_2.employer_benefits) == 1
            for benefit in split_app_1.employer_benefits:
                self._verify_benefit(
                    benefit, start_date, split_on_date, 600, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                self._verify_benefit(
                    benefit, split_on_date + timedelta(1), end_date, 400, split_app_2.application_id
                )

    def test_benefit_all_at_once_frequency_scenario_even_split(self, application, test_db_session):
        with freeze_time("2022-03-05"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=4)
            end_date = split_on_date + timedelta(days=5)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 1
            assert len(split_app_2.employer_benefits) == 1
            for benefit in split_app_1.employer_benefits:
                self._verify_benefit(
                    benefit, start_date, split_on_date, 500, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                self._verify_benefit(
                    benefit, split_on_date + timedelta(1), end_date, 500, split_app_2.application_id
                )

    def test_benefit_multiple_types_and_frequency(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=20)
            end_date = split_on_date + timedelta(days=14)

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                ),
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=300,
                    benefit_amount_frequency_id=AmountFrequency.PER_MONTH.amount_frequency_id,
                ),
            ]
            application.other_incomes = [
                OtherIncomeFactory.create(
                    application_id=application.application_id,
                    income_start_date=start_date,
                    income_end_date=end_date,
                    income_amount_dollars=200,
                    income_amount_frequency_id=AmountFrequency.PER_DAY.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.employer_benefits) == 2
            assert len(split_app_2.employer_benefits) == 2
            assert len(split_app_1.other_incomes) == 1
            assert len(split_app_2.other_incomes) == 1
            for benefit in split_app_1.employer_benefits:
                amount = (
                    600
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit, start_date, split_on_date, amount, split_app_1.application_id
                )
            for benefit in split_app_2.employer_benefits:
                amount = (
                    400
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit,
                    split_on_date + timedelta(1),
                    end_date,
                    amount,
                    split_app_2.application_id,
                )
            for income in split_app_1.other_incomes:
                self._verify_benefit(
                    income, start_date, split_on_date, 200, split_app_1.application_id
                )
            for income in split_app_2.other_incomes:
                self._verify_benefit(
                    income, split_on_date + timedelta(1), end_date, 200, split_app_2.application_id
                )

    def test_split_app_leave_periods_and_benefits(self, application, test_db_session):
        with freeze_time("2021-06-14"):
            split_on_date = date.today()
            start_date = split_on_date - timedelta(days=20)
            end_date = split_on_date + timedelta(days=14)

            application.continuous_leave_periods = [
                ContinuousLeavePeriodFactory.create(
                    start_date=split_on_date - timedelta(days=10),
                    end_date=split_on_date + timedelta(days=10),
                )
            ]
            application.intermittent_leave_periods = [
                IntermittentLeavePeriodFactory.create(
                    start_date=split_on_date - timedelta(days=10),
                    end_date=split_on_date + timedelta(days=10),
                )
            ]
            application.reduced_schedule_leave_periods = [
                ReducedScheduleLeavePeriodFactory.create(
                    start_date=split_on_date - timedelta(days=10),
                    end_date=split_on_date + timedelta(days=10),
                )
            ]
            application.concurrent_leave = ConcurrentLeaveFactory.create(
                leave_start_date=split_on_date - timedelta(days=10),
                leave_end_date=split_on_date + timedelta(days=10),
                application=application,
            )
            application.has_concurrent_leave = True

            application.employer_benefits = [
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=1000,
                    benefit_amount_frequency_id=AmountFrequency.ALL_AT_ONCE.amount_frequency_id,
                ),
                EmployerBenefitFactory.create(
                    application_id=application.application_id,
                    benefit_start_date=start_date,
                    benefit_end_date=end_date,
                    benefit_amount_dollars=300,
                    benefit_amount_frequency_id=AmountFrequency.PER_MONTH.amount_frequency_id,
                ),
            ]
            application.other_incomes = [
                OtherIncomeFactory.create(
                    application_id=application.application_id,
                    income_start_date=start_date,
                    income_end_date=end_date,
                    income_amount_dollars=200,
                    income_amount_frequency_id=AmountFrequency.PER_DAY.amount_frequency_id,
                )
            ]
            split_app_1, split_app_2 = split_application_by_date(
                test_db_session, application, split_on_date
            )
            test_db_session.commit()
            test_db_session.refresh(split_app_1)
            test_db_session.refresh(split_app_2)

            assert len(split_app_1.all_leave_periods) == 3
            assert split_app_1.has_continuous_leave_periods is True
            assert split_app_1.has_intermittent_leave_periods is True
            assert split_app_1.has_reduced_schedule_leave_periods is True
            assert split_app_1.has_employer_benefits is True
            assert split_app_1.has_other_incomes is True
            assert len(split_app_2.all_leave_periods) == 3
            assert split_app_2.has_continuous_leave_periods is True
            assert split_app_2.has_intermittent_leave_periods is True
            assert split_app_2.has_reduced_schedule_leave_periods is True
            assert split_app_2.has_employer_benefits is True
            assert split_app_2.has_other_incomes is True
            for leave_period in split_app_1.all_leave_periods:
                self._verify_leave_period(
                    leave_period,
                    split_on_date - timedelta(days=10),
                    split_on_date,
                    split_app_1.application_id,
                )

            for leave_period in split_app_2.all_leave_periods:
                self._verify_leave_period(
                    leave_period,
                    split_on_date + timedelta(days=1),
                    split_on_date + timedelta(days=10),
                    split_app_2.application_id,
                )

            self._verify_leave_period(
                split_app_1.concurrent_leave,
                split_on_date - timedelta(days=10),
                split_on_date,
                split_app_1.application_id,
            )
            self._verify_leave_period(
                split_app_2.concurrent_leave,
                split_on_date + timedelta(days=1),
                split_on_date + timedelta(days=10),
                split_app_2.application_id,
            )
            for benefit in split_app_1.employer_benefits:
                amount = (
                    600
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit,
                    start_date,
                    split_on_date,
                    amount,
                    split_app_1.application_id,
                )
            for benefit in split_app_2.employer_benefits:
                amount = (
                    400
                    if benefit.benefit_amount_frequency_id
                    == AmountFrequency.ALL_AT_ONCE.amount_frequency_id
                    else 300
                )
                self._verify_benefit(
                    benefit,
                    split_on_date + timedelta(1),
                    end_date,
                    amount,
                    split_app_2.application_id,
                )
            for income in split_app_1.other_incomes:
                self._verify_benefit(
                    income, start_date, split_on_date, 200, split_app_1.application_id
                )
            for income in split_app_2.other_incomes:
                self._verify_benefit(
                    income, split_on_date + timedelta(1), end_date, 200, split_app_2.application_id
                )

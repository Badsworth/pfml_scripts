from datetime import date, datetime
from unittest import mock

import pytest

import massgov
from massgov.pfml.api.services.administrator_fineos_actions import EformTypes
from massgov.pfml.api.services.application_import import ApplicationImportService
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.absences import AbsenceReason
from massgov.pfml.db.models.applications import (
    AmountFrequency,
    ContinuousLeavePeriod,
    DayOfWeek,
    EmploymentStatus,
    LeaveReason,
    LeaveReasonQualifier,
    OtherIncomeType,
)
from massgov.pfml.db.models.employees import BankAccountType, Gender, PaymentMethod
from massgov.pfml.db.models.factories import ApplicationFactory, ClaimFactory
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


@pytest.fixture
def claim(employer, employee):
    return ClaimFactory.create(
        employer=employer,
        employee=employee,
        fineos_absence_status_id=1,
        claim_type_id=1,
        fineos_absence_id="foo",
    )


@pytest.fixture
def application(user, claim):
    return ApplicationFactory.create(leave_reason_id=None, phone=None)


@pytest.fixture
def fineos_web_id():
    return ""


@pytest.fixture
def absence_case_id():
    return ""


@pytest.fixture
def fineos_client():
    return massgov.pfml.fineos.create_client()


@pytest.fixture
def test_db_session(test_db_session):
    return test_db_session


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


@pytest.fixture
def import_service(
    fineos_client, fineos_web_id, application, test_db_session, claim, absence_case_id
):
    return ApplicationImportService(
        fineos_client, fineos_web_id, application, test_db_session, claim, absence_case_id
    )


class TestApplicationImportService:
    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_set_application_absence_and_leave_period(
        self, mock_get_absence, application, absence_details, import_service
    ):
        mock_get_absence.return_value = absence_details
        import_service._set_application_absence_and_leave_period()

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
        import_service._set_application_absence_and_leave_period()
        assert application.has_future_child_date is True

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_set_application_absence_and_leave_period_without_open_absence_period(
        self,
        mock_get_absence,
        import_service,
        application,
        absence_details_without_open_absence_period,
    ):
        mock_get_absence.return_value = absence_details_without_open_absence_period
        import_service._set_application_absence_and_leave_period()

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

        assert (
            application.submitted_time == absence_details_without_open_absence_period.creationDate
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_set_application_absence_and_leave_period_invalid_leave_reason(
        self,
        mock_get_absence,
        import_service,
        absence_details_invalid_leave_reason,
    ):
        mock_get_absence.return_value = absence_details_invalid_leave_reason
        with pytest.raises(ValidationException) as exc:
            import_service._set_application_absence_and_leave_period()
        assert exc.value.errors == [
            ValidationErrorDetail(
                type=IssueType.invalid,
                message="Absence period reason is not supported.",
                field="leave_details.reason",
            )
        ]

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_set_application_absence_and_leave_period_valid_but_unsupported_leave_reason(
        self, mock_get_absence, import_service, application, absence_details
    ):
        valid_reason = AbsenceReason.MILITARY_CAREGIVER.absence_reason_description
        absence_details.absencePeriods[0].reason = valid_reason
        mock_get_absence.return_value = absence_details
        with pytest.raises(ValidationException) as exc:
            import_service._set_application_absence_and_leave_period()
        assert exc.value.errors == [
            ValidationErrorDetail(
                type=IssueType.invalid,
                message="Absence period reason is not supported.",
                field="leave_details.reason",
            )
        ]

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_set_application_absence_and_leave_period_invalid_leave_reason_qualifier(
        self,
        mock_get_absence,
        application,
        import_service,
        absence_details_invalid_leave_reason_qualifier,
    ):
        mock_get_absence.return_value = absence_details_invalid_leave_reason_qualifier
        with pytest.raises(KeyError):
            import_service._set_application_absence_and_leave_period()

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
    def test_set_customer_contact_detail_fields(
        self, mock_read_customer_contact_details, import_service, application, test_db_session
    ):
        customer_contact_details_json = (
            massgov.pfml.fineos.mock_client.mock_customer_contact_details()
        )
        customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
            customer_contact_details_json
        )

        application.user.mfa_phone_number = "+13214567890"
        application.user.mfa_delivery_preference_id = 1  # 'SMS' for MFA
        mock_read_customer_contact_details.return_value = customer_contact_details
        import_service._set_customer_contact_detail_fields()

        # This also asserts that the preferred phone number gets returned in this case
        # since the phone number being set is the 2nd element in the phoneNumbers array
        assert application.phone.phone_number == "+13214567890"
        assert application.phone_id == application.phone.phone_id

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
    def test_set_customer_contact_detail_fields_missing_country_code(
        self, mock_read_customer_contact_details, import_service, application, test_db_session
    ):
        customer_contact_details_json = (
            massgov.pfml.fineos.mock_client.mock_customer_contact_details()
        )
        # country code missing
        for phone_num in customer_contact_details_json["phoneNumbers"]:
            phone_num["intCode"] = None
        customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
            customer_contact_details_json
        )

        application.user.mfa_phone_number = "+13214567890"
        application.user.mfa_delivery_preference_id = 1
        mock_read_customer_contact_details.return_value = customer_contact_details
        import_service._set_customer_contact_detail_fields()

        # We still get a match, country code added
        assert application.phone.phone_number == "+13214567890"
        assert application.phone_id == application.phone.phone_id

    def test_set_customer_contact_detail_fields_without_mfa_enabled(
        self, import_service, application
    ):
        application.user.mfa_phone_number = None
        application.user.mfa_delivery_preference_id = 2  # 'opt-out' of MFA

        with pytest.raises(ValidationException) as exc:
            import_service._set_customer_contact_detail_fields()

        assert exc.value.errors == [
            ValidationErrorDetail(
                type=IssueType.incorrect,
                message="Code 3: An issue occurred while trying to import the application.",
            )
        ]
        assert application.phone is None

    def test_set_customer_contact_detail_fields_without_matching_mfa_phone_number(
        self, import_service, application
    ):
        application.user.mfa_phone_number = "+12341456789"
        application.user.mfa_delivery_preference_id = 1
        with pytest.raises(ValidationException) as exc:
            import_service._set_customer_contact_detail_fields()

        assert exc.value.errors == [
            ValidationErrorDetail(
                type=IssueType.incorrect,
                message="Code 3: An issue occurred while trying to import the application.",
            )
        ]
        assert application.phone is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
    def test_set_customer_contact_detail_fields_with_invalid_phone_number(
        self, mock_read_customer_contact_details, import_service, application, test_db_session
    ):
        customer_contact_details_json = (
            massgov.pfml.fineos.mock_client.mock_customer_contact_details()
        )
        customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
            customer_contact_details_json
        )
        # Reset phone fields that get auto generated from the application factory
        application.phone_id = None
        application.phone = None
        customer_contact_details.phoneNumbers = None

        mock_read_customer_contact_details.return_value = customer_contact_details
        import_service._set_customer_contact_detail_fields()
        assert application.phone is None
        assert application.phone_id is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_contact_details")
    def test_set_customer_contact_detail_fields_with_no_contact_details_returned_from_fineos(
        self, mock_read_customer_contact_details, import_service, application, test_db_session
    ):
        # Reset phone fields that get auto generated from the application factory
        application.phone_id = None
        application.phone = None

        # Checks to assert that if FINEOS returns no data, we don't update the applications phone record
        mock_read_customer_contact_details.return_value = None
        import_service._set_customer_contact_detail_fields()
        assert application.phone is None
        assert application.phone_id is None

        # Checks to assert that if FINEOS returns contact details, but no phone numbers,
        # we don't update the application phone record
        customer_contact_details_json = (
            massgov.pfml.fineos.mock_client.mock_customer_contact_details()
        )
        customer_contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails.parse_obj(
            customer_contact_details_json
        )
        customer_contact_details.phoneNumbers = None
        mock_read_customer_contact_details.return_value = customer_contact_details
        import_service._set_customer_contact_detail_fields()
        assert application.phone is None
        assert application.phone_id is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields(
        self, mock_read_customer_details, application, import_service
    ):
        customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
        customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
            customer_details_json
        )
        mock_read_customer_details.return_value = customer_details
        import_service._set_customer_detail_fields()
        assert application.first_name == "Samantha"
        assert application.last_name == "Jorgenson"
        assert application.gender_id == Gender.NONBINARY.gender_id
        assert application.mass_id == "123456789"
        assert application.has_state_id is True
        assert application.residential_address.address_line_one == "37 Mather Drive"

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields_with_invalid_gender(
        self, mock_read_customer_details, application, import_service
    ):
        customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
        customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
            customer_details_json
        )
        customer_details.gender = "Any"
        mock_read_customer_details.return_value = customer_details
        import_service._set_customer_detail_fields()
        assert application.gender is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields_with_no_gender(
        self, mock_read_customer_details, application, import_service
    ):
        customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
        customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
            customer_details_json
        )
        customer_details.gender = None
        mock_read_customer_details.return_value = customer_details
        import_service._set_customer_detail_fields()
        assert application.gender is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields_with_no_mass_id(
        self, mock_read_customer_details, application, import_service
    ):
        customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
        customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
            customer_details_json
        )
        customer_details.classExtensionInformation = []
        mock_read_customer_details.return_value = customer_details
        import_service._set_customer_detail_fields()
        assert application.mass_id is None
        assert application.has_state_id is False

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields_with_blank_mass_id(
        self, mock_read_customer_details, application, import_service
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
        import_service._set_customer_detail_fields()
        assert application.mass_id is None
        assert application.has_state_id is False

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields_with_invalid_address(
        self, mock_read_customer_details, import_service, application
    ):
        customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
        customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
            customer_details_json
        )
        customer_details.customerAddress = "1234 SE Main"
        mock_read_customer_details.return_value = customer_details
        import_service._set_customer_detail_fields()
        assert application.residential_address is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.read_customer_details")
    def test_set_customer_detail_fields_with_blank_address(
        self, mock_read_customer_details, import_service, application
    ):
        customer_details_json = massgov.pfml.fineos.mock_client.mock_customer_details()
        customer_details = massgov.pfml.fineos.models.customer_api.Customer.parse_obj(
            customer_details_json
        )
        customer_details.customerAddress = None
        mock_read_customer_details.return_value = customer_details
        import_service._set_customer_detail_fields()
        assert application.residential_address is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_employer_benefits_from_fineos_v1(
        self, mock_customer_get_eform, application, import_service
    ):
        eform_summaries = [
            EFormSummary(eformId=211714, eformType=EformTypes.OTHER_INCOME),
            EFormSummary(eformId=211714, eformType=EformTypes.OTHER_LEAVES),  # should not be parsed
        ]

        mock_customer_get_eform.return_value = MOCK_EFORM_OTHER_INCOME_V1

        import_service._set_employer_benefits_from_fineos(
            eform_summaries=eform_summaries,
        )
        assert application.has_employer_benefits is True
        assert len(application.employer_benefits) == 1

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_employer_benefits_from_fineos_v2(
        self, mock_customer_get_eform, application, import_service
    ):
        eform_summaries = [
            EFormSummary(eformId=211714, eformType=EformTypes.OTHER_INCOME_V2),
        ]

        mock_customer_get_eform.return_value = MOCK_EFORM_EMPLOYER_RESPONSE_V2

        import_service._set_employer_benefits_from_fineos(
            eform_summaries=eform_summaries,
        )
        assert application.has_employer_benefits is True
        assert len(application.employer_benefits) == 1

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_employer_benefits_from_fineos_v2_does_not_insert_duplicate_other_income(
        self, mock_customer_get_eform, application, import_service
    ):
        eform_summaries = [
            EFormSummary(eformId=211714, eformType=EformTypes.OTHER_INCOME_V2),
        ]

        mock_customer_get_eform.return_value = MOCK_EFORM_EMPLOYER_RESPONSE_V2

        import_service._set_employer_benefits_from_fineos(
            eform_summaries=eform_summaries,
        )
        import_service._set_other_incomes_from_fineos(
            eform_summaries=eform_summaries,
        )
        assert application.has_employer_benefits is True
        assert len(application.employer_benefits) == 1
        assert application.has_other_incomes is False
        assert len(application.other_incomes) == 0

    def test_set_employment_status_and_occupations(self, import_service, application):
        import_service._set_employment_status_and_occupations()
        assert application.employment_status_id == EmploymentStatus.EMPLOYED.employment_status_id
        assert application.hours_worked_per_week == 37.5
        assert (
            application.work_pattern.work_pattern_days[0].day_of_week_id
            == DayOfWeek.MONDAY.day_of_week_id
        )
        assert application.work_pattern.work_pattern_days[0].minutes == 5 + 4 * 60

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_week_based_work_pattern")
    def test_set_employment_status_and_occupations_work_pattern_not_fixed(
        self, mock_get_week_based_work_pattern, import_service, application
    ):
        mock_get_week_based_work_pattern.return_value = WeekBasedWorkPattern(
            workPatternType="2 weeks Rotating",
            workPatternDays=[WorkPatternDay(dayOfWeek="Monday", weekNumber=12, hours=4, minutes=5)],
        )
        import_service._set_employment_status_and_occupations()
        assert application.employment_status_id == EmploymentStatus.EMPLOYED.employment_status_id
        assert application.hours_worked_per_week == 37.5
        assert application.work_pattern is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_week_based_work_pattern")
    def test_set_employment_status_and_occupations_work_pattern_fineos_error(
        self, mock_get_week_based_work_pattern, import_service, application
    ):
        # FINEOS returns a 403 Forbidden error for Variable work patterns
        error_msg = """{
            "error" : "User does not have permission to access the resource or the instance data",
            "correlationId" : "1234"
        }"""
        error = exception.FINEOSForbidden("get_week_based_work_pattern", 200, 403, error_msg)
        mock_get_week_based_work_pattern.side_effect = error
        import_service._set_employment_status_and_occupations()
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
        self,
        mock_get_customer_occupations_customer_api,
        application,
        import_service,
        status,
    ):
        mock_get_customer_occupations_customer_api.return_value = [
            massgov.pfml.fineos.models.customer_api.ReadCustomerOccupation(
                occupationId=12345, hoursWorkedPerWeek=37.5, employmentStatus=status
            )
        ]
        with pytest.raises(ValidationException) as exc:
            import_service._set_employment_status_and_occupations()
            assert exc.value.errors == [
                ValidationErrorDetail(
                    type=IssueType.invalid,
                    message="Employment Status must be Active",
                    field="employment_status",
                )
            ]

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_other_incomes_from_fineos(
        self, mock_customer_get_eform, application, import_service
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
        import_service._set_other_incomes_from_fineos(
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
        self, mock_customer_get_eform, application, import_service
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
        import_service._set_other_incomes_from_fineos(
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
        self, mock_customer_get_eform, application, import_service
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
        import_service._set_other_incomes_from_fineos(
            eform_summaries=eform_summaries,
        )

        assert application.has_other_incomes is True
        assert application.other_incomes[0].income_amount_dollars == 100
        assert (
            application.other_incomes[0].income_amount_frequency_id
            == AmountFrequency.UNKNOWN.amount_frequency_id
        )
        assert (
            application.other_incomes[0].income_type_id
            == OtherIncomeType.UNKNOWN.other_income_type_id
        )
        assert len(application.other_incomes) == 1

    def test_set_other_leaves(self, application, import_service):
        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is True
        assert application.has_previous_leaves_same_reason is False
        assert application.has_concurrent_leave is True

    def test_set_other_leaves_includes_minutes(self, application, import_service, test_db_session):
        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is True
        test_db_session.refresh(application)
        # values from MOCK_CUSTOMER_EFORM_OTHER_LEAVES
        assert application.previous_leaves_other_reason[0].leave_minutes == 2400
        assert application.previous_leaves_other_reason[0].worked_per_week_minutes == 1245

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform_summary")
    def test_set_other_leaves_with_no_leaves(
        self, mock_customer_get_eform_summary, application, import_service
    ):
        mock_customer_get_eform_summary.return_value = []
        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is False
        assert application.has_previous_leaves_same_reason is False
        assert application.has_concurrent_leave is False
        assert application.concurrent_leave is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_other_leaves_with_only_concurrent_leave(
        self, mock_customer_get_eform, application, import_service
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
        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is False
        assert application.has_previous_leaves_same_reason is False
        assert application.has_concurrent_leave is True

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_other_leaves_with_only_previous_leave_same_reason(
        self, mock_customer_get_eform, application, import_service
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

        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is False
        assert application.has_previous_leaves_same_reason is True
        assert application.has_concurrent_leave is False
        assert application.concurrent_leave is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_other_leaves_with_only_previous_leave_other_reason(
        self, mock_customer_get_eform, application, import_service
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

        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is True
        assert application.has_previous_leaves_same_reason is False
        assert application.has_concurrent_leave is False
        assert application.concurrent_leave is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_other_leaves_with_previous_leave_blank_qualifying_reason(
        self, mock_customer_get_eform, application, import_service
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
                EFormAttribute(
                    name="V2QualifyingReason1",  # left blank
                    enumValue=ModelEnum(
                        domainName="PleaseSelectYesNo", instanceValue="Please Select"
                    ),
                ),
            ],
        )

        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is True
        assert application.has_previous_leaves_same_reason is False
        assert application.has_concurrent_leave is False
        assert application.concurrent_leave is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.customer_get_eform")
    def test_set_other_leaves_with_both_types_of_previous_leave(
        self, mock_customer_get_eform, application, import_service
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

        import_service._set_other_leaves()
        assert application.has_previous_leaves_other_reason is True
        assert application.has_previous_leaves_same_reason is True
        assert application.has_concurrent_leave is False
        assert application.concurrent_leave is None

    def test_set_payment_preference_fields(self, application, import_service):
        import_service._set_payment_preference_fields()
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
        self, mock_get_payment_preferences, application, import_service
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
        import_service._set_payment_preference_fields()
        # takes first payment pref, if none is set to default
        assert application.payment_preference.account_number == "0987654321"
        assert application.has_submitted_payment_preference is True

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
    def test_set_payment_preference_fields_with_check_as_default_preference(
        self, mock_get_payment_preferences, application, import_service
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
        import_service._set_payment_preference_fields()
        assert (
            application.payment_preference.payment_method.payment_method_id
            == PaymentMethod.CHECK.payment_method_id
        )
        assert application.has_submitted_payment_preference is True
        assert application.has_mailing_address is True
        assert application.mailing_address.address_line_one == "1234 SE Elm"

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
    def test_set_payment_preference_fields_with_blank_payment_method(
        self, mock_get_payment_preferences, application, import_service
    ):
        mock_get_payment_preferences.return_value = [
            massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
                paymentMethod="", paymentPreferenceId="1234", isDefault=True
            )
        ]
        import_service._set_payment_preference_fields()
        assert application.payment_preference is None
        assert application.has_submitted_payment_preference is False

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
    def test_set_payment_preference_fields_without_address(
        self, mock_get_payment_preferences, application, import_service
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
        import_service._set_payment_preference_fields()
        assert application.has_mailing_address is False
        assert application.mailing_address is None

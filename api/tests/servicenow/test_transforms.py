import pytest

from massgov.pfml.api.models.notifications.requests import (
    ClaimantInfo,
    NotificationRequest,
    RecipientDetails,
)
from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.servicenow.models import OutboundMessage
from massgov.pfml.servicenow.transforms.notifications import (
    TransformNotificationRequest,
    format_link,
)


@pytest.fixture
def notification_request():
    return NotificationRequest(
        absence_case_id="NTN-110-ABS-01",
        fein="00-0000000",
        organization_name="Wayne Enterprises",
        claimant_info=ClaimantInfo(
            customer_id="1234", date_of_birth="1970-01-01", first_name="John", last_name="Smith"
        ),
        document_type="Legal Notice",
        recipient_type="Leave Administrator",
        recipients=[
            RecipientDetails(
                contact_id="11", email_address="j.a.doe@gmail.com", full_name="Jane Doe"
            )
        ],
        source="Self-Service",
        trigger="claim.approved",
    )


@pytest.fixture
def leave_admin_notification_request(notification_request):
    notification_request.recipient_type = "Leave Administrator"
    return notification_request


@pytest.fixture
def leave_admin_notification_request_empty_doctype(leave_admin_notification_request):
    leave_admin_notification_request.document_type = ""
    return leave_admin_notification_request


@pytest.fixture
def leave_admin_notification_request_no_doctype(leave_admin_notification_request):
    leave_admin_notification_request.document_type = None
    return leave_admin_notification_request


@pytest.fixture
def leave_admin_notification_request_employer_confirmation(leave_admin_notification_request):
    leave_admin_notification_request.trigger = "Employer Confirmation of Leave Data"
    return leave_admin_notification_request


@pytest.fixture
def claimant_notification_request(notification_request):
    notification_request.recipient_type = "Claimant"
    notification_request.recipients = [
        RecipientDetails(email_address="j.a.doe@gmail.com", first_name="Jane", last_name="Doe")
    ]

    return notification_request


@pytest.fixture
def multiple_recipients_notification_request(notification_request):
    notification_request.recipients = [
        RecipientDetails(
            contact_id="11",
            email_address="ihavethreenames@gmail.com",
            full_name="Ihave Three Names",
        ),
        RecipientDetails(
            contact_id="12", email_address="ihaveonename@gmail.com", full_name="Ihaveonename"
        ),
    ]
    notification_request.source = "Call Center"

    return notification_request


@pytest.fixture
def employer(initialize_factories_session):
    return EmployerFactory(fineos_employer_id=10)


class TestTransformNotificationRequest:
    def test_transform_leave_admin_notification_request(
        self, leave_admin_notification_request, employer
    ):
        result = TransformNotificationRequest.to_service_now(
            leave_admin_notification_request, employer
        )
        assert type(result) == OutboundMessage
        assert result.u_absence_id == "NTN-110-ABS-01"
        assert result.u_document_type == "legal_notice"
        assert result.u_organization_name == "Wayne Enterprises"
        assert result.u_source == "portal"
        assert result.u_user_type == "leave_administrator"
        assert result.u_trigger == "claim.approved"
        assert (
            result.u_link
            == "https://paidleave.mass.gov/employers/applications/status/?absence_id=NTN-110-ABS-01"
        )
        assert result.u_recipients == [
            '{"first_name": "Jane", "last_name": "Doe", "id": "11", "email": "j.a.doe@gmail.com"}'
        ]
        assert (
            result.u_claimant_info
            == '{"first_name": "John", "last_name": "Smith", "dob": "01/01/****", "id": "1234"}'
        )
        assert result.u_employer_customer_number == 10

    def test_transform_leave_admin_notification_request_empty_doctype(
        self, leave_admin_notification_request_empty_doctype, employer
    ):
        result = TransformNotificationRequest.to_service_now(
            leave_admin_notification_request_empty_doctype, employer
        )
        assert type(result) == OutboundMessage
        assert result.u_absence_id == "NTN-110-ABS-01"
        assert result.u_organization_name == "Wayne Enterprises"
        assert result.u_document_type == ""
        assert result.u_source == "portal"
        assert result.u_user_type == "leave_administrator"
        assert result.u_trigger == "claim.approved"
        assert (
            result.u_link
            == "https://paidleave.mass.gov/employers/applications/status/?absence_id=NTN-110-ABS-01"
        )
        assert result.u_recipients == [
            '{"first_name": "Jane", "last_name": "Doe", "id": "11", "email": "j.a.doe@gmail.com"}'
        ]
        assert (
            result.u_claimant_info
            == '{"first_name": "John", "last_name": "Smith", "dob": "01/01/****", "id": "1234"}'
        )
        assert result.u_employer_customer_number == 10

    def test_transform_leave_admin_notification_request_no_doctype(
        self, leave_admin_notification_request_no_doctype, employer
    ):
        result = TransformNotificationRequest.to_service_now(
            leave_admin_notification_request_no_doctype, employer
        )
        assert type(result) == OutboundMessage
        assert result.u_absence_id == "NTN-110-ABS-01"
        assert result.u_organization_name == "Wayne Enterprises"
        assert result.u_document_type == ""
        assert result.u_source == "portal"
        assert result.u_user_type == "leave_administrator"
        assert result.u_trigger == "claim.approved"
        assert (
            result.u_link
            == "https://paidleave.mass.gov/employers/applications/status/?absence_id=NTN-110-ABS-01"
        )
        assert result.u_recipients == [
            '{"first_name": "Jane", "last_name": "Doe", "id": "11", "email": "j.a.doe@gmail.com"}'
        ]
        assert (
            result.u_claimant_info
            == '{"first_name": "John", "last_name": "Smith", "dob": "01/01/****", "id": "1234"}'
        )
        assert result.u_employer_customer_number == 10

    def test_transform_claimant_notification_request(self, claimant_notification_request, employer):
        result = TransformNotificationRequest.to_service_now(
            claimant_notification_request, employer
        )
        assert type(result) == OutboundMessage
        assert result.u_absence_id == "NTN-110-ABS-01"
        assert result.u_organization_name == "Wayne Enterprises"
        assert result.u_document_type == "legal_notice"
        assert result.u_source == "portal"
        assert result.u_user_type == "claimant"
        assert result.u_trigger == "claim.approved"
        assert result.u_link == "https://paidleave.mass.gov/applications"
        assert result.u_recipients == [
            '{"first_name": "Jane", "last_name": "Doe", "id": "1234", "email": "j.a.doe@gmail.com"}'
        ]
        assert (
            result.u_claimant_info
            == '{"first_name": "John", "last_name": "Smith", "dob": "01/01/****", "id": "1234"}'
        )
        assert result.u_employer_customer_number == 10

    def test_transform_multiple_recipients_notification_request(
        self, multiple_recipients_notification_request, employer
    ):
        result = TransformNotificationRequest.to_service_now(
            multiple_recipients_notification_request, employer
        )
        assert type(result) == OutboundMessage
        assert result.u_absence_id == "NTN-110-ABS-01"
        assert result.u_organization_name == "Wayne Enterprises"
        assert result.u_document_type == "legal_notice"
        assert result.u_source == "call_center"
        assert result.u_user_type == "leave_administrator"
        assert result.u_trigger == "claim.approved"
        assert (
            result.u_link
            == "https://paidleave.mass.gov/employers/applications/status/?absence_id=NTN-110-ABS-01"
        )
        assert result.u_recipients == [
            '{"first_name": "Ihave", "last_name": "Three Names", "id": "11", "email": "ihavethreenames@gmail.com"}',
            '{"first_name": "Ihaveonename", "last_name": "", "id": "12", "email": "ihaveonename@gmail.com"}',
        ]
        assert (
            result.u_claimant_info
            == '{"first_name": "John", "last_name": "Smith", "dob": "01/01/****", "id": "1234"}'
        )
        assert result.u_employer_customer_number == 10


class TestFormatLink:
    def test_with_employer(self, leave_admin_notification_request):
        link = format_link(leave_admin_notification_request)
        expected = (
            "https://paidleave.mass.gov/employers/applications/status/?absence_id=NTN-110-ABS-01"
        )

        assert link == expected

    def test_with_employer_confirmation(
        self, leave_admin_notification_request_employer_confirmation
    ):
        link = format_link(leave_admin_notification_request_employer_confirmation)
        expected = "https://paidleave.mass.gov/employers/applications/new-application/?absence_id=NTN-110-ABS-01"

        assert link == expected

    def test_with_claimant(self, claimant_notification_request):
        link = format_link(claimant_notification_request)

        assert link == "https://paidleave.mass.gov/applications"

    def test_with_claimant_and_claim_status_enabled(
        self, monkeypatch, claimant_notification_request
    ):
        monkeypatch.setenv("USE_CLAIM_STATUS_URL", "true")

        link = format_link(claimant_notification_request)
        expected = "https://paidleave.mass.gov/applications/status/?absence_case_id=NTN-110-ABS-01#view-notices"

        assert link == expected

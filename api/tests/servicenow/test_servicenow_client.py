import uuid

import pytest
import responses

from massgov.pfml.servicenow.client import ServiceNowClient
from massgov.pfml.servicenow.exception import ServiceNowError, ServiceNowUnavailable
from massgov.pfml.servicenow.models import Claimant, OutboundMessage, Recipient


@pytest.fixture
def test_client():
    return ServiceNowClient(
        base_url="https://imaginary.com", username="harvey", password="12341234", response=True
    )


@pytest.fixture
def test_client_no_resp():
    return ServiceNowClient(
        base_url="https://imaginary.com", username="harvey", password="12341234", response=False
    )


@pytest.fixture
def test_recipient():
    return Recipient(
        first_name="Carrie", last_name="Brown", email="test@mailinator.com", id=str(uuid.uuid4())
    ).json()


@pytest.fixture
def test_claimant():
    return Claimant(
        first_name="Carrie", last_name="Brown", dob="1970-01-01", id=str(uuid.uuid4())
    ).json()


@pytest.fixture
def test_message(test_recipient, test_claimant):
    return OutboundMessage(
        u_absence_id="NTN-ABS-FAK-001",
        u_organization_name="Wayne Enterprises",
        u_claimant_info=test_claimant,
        u_document_type="Legal Notice",
        u_recipients=[test_recipient],
        u_source="Call Center",
        u_trigger="test.trigger",
        u_user_type="Leave Administrator",
        u_link="https://www.google.com",
        u_employer_customer_number=10,
    )


@pytest.fixture
def test_response():
    return {"response": "value"}


class TestServiceNowClient:
    @responses.activate
    def test_service_now_unavailable_request(self, test_client, test_message):
        responses.add(
            responses.POST,
            "https://imaginary.com/api/now/table/bogus",
            json={"error": "bad request"},
            status=503,
        )
        with pytest.raises(ServiceNowUnavailable):
            test_client.send_message(message=test_message, table="bogus")

    @responses.activate
    def test_bad_request(self, test_client, test_message):
        responses.add(
            responses.POST,
            "https://imaginary.com/api/now/table/bogus",
            json={"error": "bad request"},
            status=400,
        )
        with pytest.raises(ServiceNowError):
            test_client.send_message(message=test_message, table="bogus")

    @responses.activate
    def test_success_no_response(self, test_client_no_resp, test_message, test_response):
        responses.add(
            responses.POST,
            "https://imaginary.com/api/now/table/bogus",
            json=test_response,
            status=201,
        )
        resp = test_client_no_resp.send_message(message=test_message, table="bogus")
        assert resp is None

    @responses.activate
    def test_success_response(self, test_client, test_message, test_response):
        responses.add(
            responses.POST,
            "https://imaginary.com/api/now/table/bogus",
            json=test_response,
            status=201,
        )
        resp = test_client.send_message(message=test_message, table="bogus")
        assert resp == test_response

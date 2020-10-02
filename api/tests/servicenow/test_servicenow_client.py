import uuid

import pytest
import responses

from massgov.pfml.servicenow.client import ServiceNowClient, ServiceNowException
from massgov.pfml.servicenow.models import OutboundMessage, Recipient


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
        first="Carrie",
        last="Brown",
        email="test@mailinator.com",
        fineos_id=str(uuid.uuid4()),
        phone="",
    )


@pytest.fixture
def test_message(test_recipient):
    return OutboundMessage(
        recipients=[test_recipient], trigger="test.trigger", absence_id="NTN-ABS-FAK-001"
    )


@pytest.fixture
def test_response():
    return {"response": "value"}


class TestServiceNowClient:
    @responses.activate
    def test_bad_request(self, test_client, test_message):
        responses.add(
            responses.POST,
            "https://imaginary.com/api/now/table/bogus",
            json={"error": "bad request"},
            status=400,
        )
        with pytest.raises(ServiceNowException):
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

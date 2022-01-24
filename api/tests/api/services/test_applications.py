import mock
import pytest

import massgov
from massgov.pfml.api.services.applications import set_customer_detail_fields
from massgov.pfml.db.models.employees import Gender
from massgov.pfml.db.models.factories import ApplicationFactory


@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


@pytest.fixture
def fineos_web_id():
    return ""


@pytest.fixture
def fineos_client():
    return massgov.pfml.fineos.create_client()


@pytest.fixture
def application():
    return ApplicationFactory.create(leave_reason_id=None)


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
    assert application.mass_id == "45354352"
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
        ),
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

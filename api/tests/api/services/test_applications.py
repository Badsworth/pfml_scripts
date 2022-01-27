import mock
import pytest

import massgov
from massgov.pfml.api.services.applications import (
    set_customer_contact_detail_fields,
    set_customer_detail_fields,
    set_payment_preference_fields,
)
from massgov.pfml.db.models.employees import BankAccountType, Gender, PaymentMethod
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
            paymentMethod="Elec Funds Transfer", paymentPreferenceId="1234",
        )
    ]
    set_payment_preference_fields(fineos_client, fineos_web_id, application, test_db_session)
    assert application.payment_preference is None
    assert application.has_submitted_payment_preference is False


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_payment_preferences")
def test_set_payment_preference_fields_with_blank_payment_method(
    mock_get_payment_preferences, fineos_client, fineos_web_id, application, test_db_session
):
    mock_get_payment_preferences.return_value = [
        massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse(
            paymentMethod="", paymentPreferenceId="1234", isDefault=True,
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
    mock_read_customer_contact_details.return_value = customer_contact_details
    set_customer_contact_detail_fields(fineos_client, fineos_web_id, application, test_db_session)

    # This also asserts that the preferred phone number gets returned in this case
    # since the phone number being set is the 2nd element in the phoneNumbers array
    assert application.phone.phone_number == "+13214567890"
    assert application.phone_id == application.phone.phone_id


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

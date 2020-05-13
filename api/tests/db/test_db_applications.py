import uuid

from massgov.pfml.db.models.applications import Application, ApplicationPaymentPreference


def test_application():
    application = Application()
    application.application_id = uuid.uuid4()
    application.nickname = "My Leave Application"
    application.first_name = "John"
    application.last_name = "Doe"

    assert uuid.UUID(str(application.application_id)).version == 4
    assert application.nickname == "My Leave Application"
    assert application.first_name == "John"
    assert application.last_name == "Doe"


def test_payment_preference():
    application = Application()
    application.application_id = uuid.uuid4()

    payment_preference = ApplicationPaymentPreference()
    payment_preference.payment_pref_id = uuid.uuid4()
    payment_preference.application_id = application.application_id
    payment_preference.payment_type = "Elec Funds Transfer"
    payment_preference.account_name = "My Checking"
    payment_preference.type_of_account = "Checking"
    payment_preference.account_number = "1234567890"
    payment_preference.routing_number = "000000000"
    payment_preference.is_default = True

    assert payment_preference.application_id == application.application_id
    assert uuid.UUID(str(payment_preference.payment_pref_id)).version == 4
    assert payment_preference.payment_type == "Elec Funds Transfer"
    assert payment_preference.account_name == "My Checking"
    assert payment_preference.type_of_account == "Checking"
    assert payment_preference.account_number == "1234567890"
    assert payment_preference.routing_number == "000000000"
    assert payment_preference.is_default is True

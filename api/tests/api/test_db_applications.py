import uuid

from massgov.pfml.db.models.applications import Application, ApplicationPaymentPreference
from massgov.pfml.db.models.employees import PaymentType


def test_application(test_db_session):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.nickname = "My Leave Application"
    application.first_name = "John"
    application.last_name = "Doe"

    test_db_session.add(application)
    test_db_session.commit()

    inserted_application = test_db_session.query(Application).get(application_id)

    assert uuid.UUID(str(inserted_application.application_id)).version == 4
    assert inserted_application.nickname == "My Leave Application"
    assert inserted_application.first_name == "John"
    assert inserted_application.last_name == "Doe"


def test_payment_preference(test_db_session):
    application = Application()
    application.application_id = uuid.uuid4()

    test_db_session.add(application)

    payment_type = PaymentType()
    payment_type.payment_type_id = 1
    payment_type.payment_type_description = "ACH"

    test_db_session.add(payment_type)
    test_db_session.commit()

    payment_preference = ApplicationPaymentPreference()
    payment_preference_id = uuid.uuid4()
    payment_preference.payment_pref_id = payment_preference_id
    payment_preference.application_id = application.application_id
    payment_preference.payment_type_id = 1
    payment_preference.account_name = "My Checking"
    payment_preference.type_of_account = "Checking"
    payment_preference.account_number = "1234567890"
    payment_preference.routing_number = "000000000"
    payment_preference.is_default = True

    test_db_session.add(payment_preference)
    test_db_session.commit()

    inserted_payment_pref = test_db_session.query(ApplicationPaymentPreference).get(
        payment_preference_id
    )

    assert inserted_payment_pref.application_id == application.application_id
    assert uuid.UUID(str(inserted_payment_pref.payment_pref_id)).version == 4
    assert inserted_payment_pref.payment_type_id == 1
    assert inserted_payment_pref.account_name == "My Checking"
    assert inserted_payment_pref.type_of_account == "Checking"
    assert inserted_payment_pref.account_number == "1234567890"
    assert inserted_payment_pref.routing_number == "000000000"
    assert inserted_payment_pref.is_default is True


def test_rmv_id_fields(test_db_session):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.has_state_id = True
    application.mass_id = "123456789"

    test_db_session.add(application)
    test_db_session.commit()

    new_application = test_db_session.query(Application).get(application_id)

    assert new_application.application_id == application_id
    assert new_application.has_state_id is True
    assert new_application.mass_id == "123456789"


def test_pregnant_recent_birth_flag(test_db_session):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.pregnant_or_recent_birth = True

    test_db_session.add(application)
    test_db_session.commit()

    inserted_application = test_db_session.query(Application).get(application_id)

    assert uuid.UUID(str(inserted_application.application_id)).version == 4
    assert inserted_application.pregnant_or_recent_birth is True

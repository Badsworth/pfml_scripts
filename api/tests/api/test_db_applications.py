import uuid

import pytest

from massgov.pfml.db.models.applications import (
    Application,
    ApplicationPaymentPreference,
    ConcurrentLeave,
)
from massgov.pfml.db.models.employees import BankAccountType, PaymentMethod

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_application(test_db_session, user):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.user_id = user.user_id
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


def test_payment_preference(test_db_session, user):
    application = Application()
    application.application_id = uuid.uuid4()
    application.user_id = user.user_id

    test_db_session.add(application)

    PaymentMethod.sync_to_database(test_db_session)
    BankAccountType.sync_to_database(test_db_session)

    test_db_session.commit()

    payment_preference = ApplicationPaymentPreference()
    payment_preference.payment_method_id = 1
    payment_preference.account_method_id = 2
    payment_preference.account_number = "1234567890"
    payment_preference.routing_number = "000000000"

    test_db_session.add(payment_preference)
    application.payment_preference = payment_preference
    test_db_session.commit()

    inserted_payment_pref = (
        test_db_session.query(Application).get(application.application_id).payment_preference
    )

    assert uuid.UUID(str(inserted_payment_pref.payment_pref_id)).version == 4
    assert inserted_payment_pref.payment_method_id == 1
    assert inserted_payment_pref.account_method_id == 2
    assert inserted_payment_pref.account_number == "1234567890"
    assert inserted_payment_pref.routing_number == "000000000"


def test_rmv_id_fields(test_db_session, user):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.user_id = user.user_id
    application.has_state_id = True
    application.mass_id = "123456789"

    test_db_session.add(application)
    test_db_session.commit()

    new_application = test_db_session.query(Application).get(application_id)

    assert new_application.application_id == application_id
    assert new_application.has_state_id is True
    assert new_application.mass_id == "123456789"


def test_pregnant_recent_birth_flag(test_db_session, user):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.user_id = user.user_id
    application.pregnant_or_recent_birth = True

    test_db_session.add(application)
    test_db_session.commit()

    inserted_application = test_db_session.query(Application).get(application_id)

    assert uuid.UUID(str(inserted_application.application_id)).version == 4
    assert inserted_application.pregnant_or_recent_birth is True


def test_add_concurrent_leave(test_db_session, user):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.user_id = user.user_id

    concurrent_leave = ConcurrentLeave()
    concurrent_leave_id = uuid.uuid4()
    concurrent_leave.concurrent_leave_id = concurrent_leave_id
    concurrent_leave.leave_start_date = "2021-03-20"
    concurrent_leave.leave_end_date = "2021-04-10"
    concurrent_leave.is_for_current_employer = True

    concurrent_leave.application_id = application_id

    test_db_session.add(application)
    test_db_session.add(concurrent_leave)
    test_db_session.commit()

    inserted_application = test_db_session.query(Application).get(application_id)

    assert inserted_application.concurrent_leave.is_for_current_employer is True
    assert inserted_application.concurrent_leave.leave_start_date == "2021-03-20"
    assert inserted_application.concurrent_leave.leave_end_date == "2021-04-10"


def test_concurrent_leave_is_nullable(test_db_session, user):
    application = Application()
    application_id = uuid.uuid4()
    application.application_id = application_id
    application.user_id = user.user_id

    test_db_session.add(application)
    test_db_session.commit()

    inserted_application = test_db_session.query(Application).get(application_id)
    assert inserted_application.concurrent_leave is None

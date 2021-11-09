from urllib.parse import urlencode

from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.db.models.factories import ApplicationFactory
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


def test_get_payments_200(client, auth_token, user, test_db_session):
    absence_id = "NTN-12345-ABS-01"

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_absence_id=absence_id,
        payment_method=PaymentMethod.ACH,
        amount=750.67,
    )
    claim = payment_factory.get_or_create_claim()
    ApplicationFactory.create(claim=claim, user=user)
    payment = payment_factory.get_or_create_payment()

    querystring = urlencode({"absence_case_id": absence_id})
    response = client.get(
        "/v1/payments?{}".format(querystring), headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200

    response_body = response.get_json().get("data")
    assert response_body["absence_case_id"] == absence_id

    payment_response = response_body["payments"][0]

    assert payment_response == {
        "payment_id": str(payment.payment_id),
        "fineos_c_value": str(payment.fineos_pei_c_value),
        "fineos_i_value": str(payment.fineos_pei_i_value),
        "period_start_date": str(payment.period_start_date),
        "period_end_date": str(payment.period_end_date),
        "amount": 750.67,
        "sent_to_bank_date": str(payment.payment_date),
        "payment_method": payment.disb_method.payment_method_description,
        "expected_send_date_start": None,
        "expected_send_date_end": None,
        "status": "Delayed",
    }


def test_get_payments_returns_403_when_payments_not_associated_with_user_application(
    client, auth_token, test_db_session
):
    absence_id = "NTN-12345-ABS-01"
    # The claims will not be returned because the current user is not associated with this application.
    payment_factory = DelegatedPaymentFactory(
        test_db_session, fineos_absence_id=absence_id, payment_method=PaymentMethod.ACH
    )
    claim = payment_factory.get_or_create_claim()
    ApplicationFactory.create(claim=claim)

    payment_factory.get_or_create_payment()

    querystring = urlencode({"absence_case_id": absence_id})
    response = client.get(
        "/v1/payments?{}".format(querystring), headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_get_payments_401(client):
    absence_id = "NTN-12345-ABS-01"
    querystring = urlencode({"absence_case_id": absence_id})
    response = client.get("/v1/payments?{}".format(querystring),)

    # No auth token returns 401
    assert response.status_code == 401


def test_get_payments_403(client, employer_auth_token):
    absence_id = "NTN-12345-ABS-01"
    querystring = urlencode({"absence_case_id": absence_id})

    response = client.get(
        "/v1/payments?{}".format(querystring),
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 403

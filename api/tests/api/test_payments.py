from urllib.parse import urlencode

import pytest

from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.db.models.factories import ApplicationFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


@pytest.mark.parametrize(
    "transaction_status,status",
    [
        (FineosWritebackTransactionStatus.PAID, "Sent to bank"),
        (FineosWritebackTransactionStatus.POSTED, "Sent to bank"),
        (FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR, "Delayed"),
        (None, "Delayed"),
    ],
)
def test_get_payments_200(client, auth_token, user, test_db_session, transaction_status, status):
    absence_id = "NTN-12345-ABS-01"

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_absence_id=absence_id,
        payment_method=PaymentMethod.ACH,
        amount=750.67,
    )
    claim = payment_factory.get_or_create_claim()
    ApplicationFactory.create(claim=claim, user=user)

    if transaction_status == FineosWritebackTransactionStatus.POSTED:
        # Need to pull sent dates off of paid status record for posted statuses
        payment = payment_factory.get_or_create_payment()
        wb_detail = FineosWritebackDetails(payment=payment, transaction_status_id=11)
        test_db_session.add(wb_detail)
        payment_factory.get_or_create_payment_with_writeback(transaction_status)
    else:
        wb_detail = payment_factory.get_or_create_payment_with_writeback(transaction_status)

    test_db_session.commit()

    querystring = urlencode({"absence_case_id": absence_id})
    response = client.get(
        "/v1/payments?{}".format(querystring), headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200

    response_body = response.get_json().get("data")
    assert response_body["absence_case_id"] == absence_id

    payment_response = response_body["payments"][0]

    payment = payment_factory.payment
    sent_to_bank_date = (
        str(wb_detail.created_at.date()) if (wb_detail and status == "Sent to bank") else None
    )

    assert payment_response == {
        "payment_id": str(payment.payment_id),
        "fineos_c_value": str(payment.fineos_pei_c_value),
        "fineos_i_value": str(payment.fineos_pei_i_value),
        "period_start_date": str(payment.period_start_date),
        "period_end_date": str(payment.period_end_date),
        "amount": 750.67 if status == "Sent to bank" else None,
        "sent_to_bank_date": sent_to_bank_date,
        "payment_method": payment.disb_method.payment_method_description,
        "expected_send_date_start": sent_to_bank_date,
        "expected_send_date_end": sent_to_bank_date,
        "status": status,
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

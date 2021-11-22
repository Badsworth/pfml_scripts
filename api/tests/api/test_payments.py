from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import pytest

from massgov.pfml.api.services.payments import FrontendPaymentStatus
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.db.models.factories import ApplicationFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


@pytest.mark.parametrize(
    "transaction_status,scenario_details",
    [
        # Pending Validation Scenario - display expected dates 5-7 days after pub_eft.prenote_sent_at
        (
            FineosWritebackTransactionStatus.PENDING_PRENOTE,
            [FrontendPaymentStatus.DELAYED, None, None, 5, 7],
        ),
        # Paid Scenarios - display amount, sent_to_bank_date equal to writeback status created_at, expected dates equal to sent_to_bank_date
        (
            FineosWritebackTransactionStatus.PAID,
            [FrontendPaymentStatus.SENT_TO_BANK, 750.67, str(date.today()), 0, 0],
        ),
        (
            FineosWritebackTransactionStatus.POSTED,
            [FrontendPaymentStatus.SENT_TO_BANK, 750.67, str(date.today()), 0, 0],
        ),
        # Other Scenario - No dates displayed, only status of "Delayed"
        (
            FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR,
            [FrontendPaymentStatus.DELAYED, None, None, None, None],
        ),
        # Income Scenario - expected dates 2-4 days from writeback status created
        (
            FineosWritebackTransactionStatus.DIA_ADDITIONAL_INCOME,
            [FrontendPaymentStatus.DELAYED, None, None, 2, 4],
        ),
        # No Writeback scenario - expected dates 1-3 days from today
        (None, [FrontendPaymentStatus.PENDING, None, None, 1, 3]),
    ],
)
def test_get_payments_200(
    client, auth_token, user, test_db_session, transaction_status, scenario_details
):
    status, amount, sent_date, expected_start_delta, expected_end_delta = scenario_details

    absence_id = "NTN-12345-ABS-01"

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_absence_id=absence_id,
        payment_method=PaymentMethod.ACH,
        amount=750.67,
        set_pub_eft_in_payment=True,
        prenote_sent_at=date.today(),
    )
    payment_factory.get_or_create_pub_eft()
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

    expected_start_date = (
        str(date.today() + timedelta(days=expected_start_delta))
        if (expected_start_delta is not None)
        else None
    )
    expected_end_date = (
        str(date.today() + timedelta(days=expected_end_delta))
        if (expected_end_delta is not None)
        else None
    )

    assert payment_response == {
        "payment_id": str(payment.payment_id),
        "fineos_c_value": str(payment.fineos_pei_c_value),
        "fineos_i_value": str(payment.fineos_pei_i_value),
        "period_start_date": str(payment.period_start_date),
        "period_end_date": str(payment.period_end_date),
        "amount": amount,
        "sent_to_bank_date": sent_date,
        "payment_method": payment.disb_method.payment_method_description,
        "expected_send_date_start": expected_start_date,
        "expected_send_date_end": expected_end_date,
        "status": status,
    }


def test_get_payments_200_pending_validation_scenario_no_prenote_sent_at(
    client, auth_token, user, test_db_session
):
    absence_id = "NTN-12345-ABS-01"

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_absence_id=absence_id,
        payment_method=PaymentMethod.ACH,
        amount=750.67,
        set_pub_eft_in_payment=True,
        prenote_sent_at=None,
    )
    payment_factory.get_or_create_pub_eft()
    claim = payment_factory.get_or_create_claim()
    ApplicationFactory.create(claim=claim, user=user)

    transaction_status = FineosWritebackTransactionStatus.PENDING_PRENOTE
    payment_factory.get_or_create_payment_with_writeback(transaction_status)

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

    expected_start_date = str(date.today() + timedelta(days=6))
    expected_end_date = str(date.today() + timedelta(days=8))

    assert payment_response == {
        "payment_id": str(payment.payment_id),
        "fineos_c_value": str(payment.fineos_pei_c_value),
        "fineos_i_value": str(payment.fineos_pei_i_value),
        "period_start_date": str(payment.period_start_date),
        "period_end_date": str(payment.period_end_date),
        "amount": None,
        "sent_to_bank_date": None,
        "payment_method": payment.disb_method.payment_method_description,
        "expected_send_date_start": expected_start_date,
        "expected_send_date_end": expected_end_date,
        "status": FrontendPaymentStatus.DELAYED,
    }


def test_get_payments_200_range_before_today(client, auth_token, user, test_db_session):
    absence_id = "NTN-12345-ABS-01"

    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_absence_id=absence_id,
        payment_method=PaymentMethod.ACH,
        amount=750.67,
    )
    claim = payment_factory.get_or_create_claim()
    ApplicationFactory.create(claim=claim, user=user)

    transaction_status = FineosWritebackTransactionStatus.DIA_ADDITIONAL_INCOME
    writeback_status = payment_factory.get_or_create_payment_with_writeback(transaction_status)

    # The expected_end_date of the range (2-4 days from writeback created_at)
    # will be one day prior to todays date. In this scenario, we don't return values for
    # the expected start/end date fields
    writeback_status.created_at = datetime.today() - timedelta(days=5)

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

    assert payment_response == {
        "payment_id": str(payment.payment_id),
        "fineos_c_value": str(payment.fineos_pei_c_value),
        "fineos_i_value": str(payment.fineos_pei_i_value),
        "period_start_date": str(payment.period_start_date),
        "period_end_date": str(payment.period_end_date),
        "amount": None,
        "sent_to_bank_date": None,
        "payment_method": payment.disb_method.payment_method_description,
        "expected_send_date_start": None,
        "expected_send_date_end": None,
        "status": FrontendPaymentStatus.DELAYED,
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

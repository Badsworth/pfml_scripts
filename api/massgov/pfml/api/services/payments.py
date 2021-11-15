import uuid
from typing import Dict, List, Optional

from sqlalchemy.sql.expression import desc

from massgov.pfml.api.models.payments.responses import PaymentResponse
from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import Claim, Payment, PaymentTransactionType
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


def get_payments_with_status(db_session: Session, claim: Claim) -> Dict:
    payments = get_payments_from_db(db_session, claim.claim_id)

    return to_response_dict(payments, claim.fineos_absence_id)


def get_payments_from_db(db_session: Session, claim_id: uuid.UUID) -> List[Payment]:
    payments = (
        db_session.query(Payment)
        .filter(Payment.claim_id == claim_id,)
        .filter(
            Payment.payment_transaction_type_id
            == PaymentTransactionType.STANDARD.payment_transaction_type_id,
        )
        .filter(Payment.exclude_from_payment_status != True)  # noqa: E712
        .order_by(Payment.fineos_pei_i_value, desc(Payment.fineos_extract_import_log_id))
        .distinct(Payment.fineos_pei_i_value)
        .all()
    )

    return payments


def to_response_dict(payment_data: List[Payment], absence_case_id: Optional[str]) -> Dict:
    payments = []
    for payment in payment_data:
        payments.append(
            PaymentResponse(
                payment_id=payment.payment_id,
                fineos_c_value=payment.fineos_pei_c_value,
                fineos_i_value=payment.fineos_pei_i_value,
                period_start_date=payment.period_start_date,
                period_end_date=payment.period_end_date,
                amount=payment.amount,  # TODO (API-2046)
                sent_to_bank_date=payment.payment_date,  # TODO (API-2046)
                payment_method=payment.disb_method
                and payment.disb_method.payment_method_description,
                expected_send_date_start=None,  # TODO (API-2047)
                expected_send_date_end=None,  # TODO (API-2047)
                status="Delayed",  # TODO (API-2047)
            ).dict()
        )
    return {
        "payments": payments,
        "absence_case_id": absence_case_id,
    }

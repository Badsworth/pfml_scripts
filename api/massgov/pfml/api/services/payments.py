import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc

from massgov.pfml.api.models.payments.responses import PaymentResponse
from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import Claim, Payment, PaymentTransactionType
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)

PAID_STATUS_ID = FineosWritebackTransactionStatus.PAID.transaction_status_id
POSTED_STATUS_ID = FineosWritebackTransactionStatus.POSTED.transaction_status_id


@dataclass
class PaymentContainer:
    payment: Payment

    writeback_detail: Optional[FineosWritebackDetails] = None

    def __post_init__(self):
        self.writeback_detail = get_latest_writeback_detail(self.payment)


def get_payments_with_status(db_session: Session, claim: Claim) -> Dict:
    payment_containers = get_payments_from_db(db_session, claim.claim_id)

    return to_response_dict(payment_containers, claim.fineos_absence_id)


def get_payments_from_db(db_session: Session, claim_id: uuid.UUID) -> List[PaymentContainer]:
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
        .options(joinedload(Payment.fineos_writeback_details))  # type: ignore
        .all()
    )

    return [PaymentContainer(payment) for payment in payments]


def to_response_dict(payment_data: List[PaymentContainer], absence_case_id: Optional[str]) -> Dict:
    payments = []
    for payment_container in payment_data:
        payment = payment_container.payment
        writeback_detail = payment_container.writeback_detail

        amount = None
        sent_date = None
        expected_send_date_start = None
        expected_send_date_end = None
        status = "Delayed"

        if writeback_detail and writeback_detail.transaction_status_id == PAID_STATUS_ID:
            amount = payment.amount
            sent_date = writeback_detail.created_at
            expected_send_date_start = sent_date
            expected_send_date_end = sent_date
            status = "Sent to bank"

        payments.append(
            PaymentResponse(
                payment_id=payment.payment_id,
                fineos_c_value=payment.fineos_pei_c_value,
                fineos_i_value=payment.fineos_pei_i_value,
                period_start_date=payment.period_start_date,
                period_end_date=payment.period_end_date,
                amount=amount,
                sent_to_bank_date=sent_date,
                payment_method=payment.disb_method
                and payment.disb_method.payment_method_description,
                expected_send_date_start=expected_send_date_start,  # TODO (API-2047)
                expected_send_date_end=expected_send_date_end,  # TODO (API-2047)
                status=status,  # TODO (API-2047)
            ).dict()
        )
    return {
        "payments": payments,
        "absence_case_id": absence_case_id,
    }


def get_latest_writeback_detail(payment: Payment) -> Optional[FineosWritebackDetails]:
    writeback_details_records = payment.fineos_writeback_details  # type: ignore

    if len(writeback_details_records) == 0:
        return None

    first_detail_record = writeback_details_records[-1]

    if first_detail_record.transaction_status_id == PAID_STATUS_ID:
        return first_detail_record
    elif first_detail_record.transaction_status_id == POSTED_STATUS_ID:
        for record in reversed(writeback_details_records):
            if record.transaction_status_id == PAID_STATUS_ID:
                return record

    return None

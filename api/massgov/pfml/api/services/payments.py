import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc

from massgov.pfml.api.models.payments.responses import PaymentResponse
from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import Claim, Payment, PaymentTransactionType
from massgov.pfml.db.models.payments import FineosWritebackDetails
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus as WritebackStatus
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


class FEPaymentStatus:
    SENT_TO_BANK = "Sent to bank"
    DELAYED = "Delayed"
    PENDING = "Pending"


@dataclass
class PaymentScenarioData:
    amount: Optional[Decimal] = None
    sent_date: Optional[date] = None
    expected_send_date_start: Optional[date] = None
    expected_send_date_end: Optional[date] = None
    status: str = FEPaymentStatus.DELAYED

    SCENARIOS = {
        WritebackStatus.PENDING_PRENOTE.transaction_status_id: "pending_validation",
        WritebackStatus.DUA_ADDITIONAL_INCOME.transaction_status_id: "income",
        WritebackStatus.DIA_ADDITIONAL_INCOME.transaction_status_id: "income",
        WritebackStatus.WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850.transaction_status_id: "income",
        WritebackStatus.SELF_REPORTED_ADDITIONAL_INCOME.transaction_status_id: "income",
        WritebackStatus.PAID.transaction_status_id: "paid",
        WritebackStatus.POSTED.transaction_status_id: "paid",
        None: "no_writeback",
    }

    @classmethod
    def from_payment(cls, payment: Payment) -> "PaymentScenarioData":
        writeback_detail = get_latest_writeback_detail(payment)
        detail_id = writeback_detail.transaction_status_id if writeback_detail else None
        method_to_call = getattr(cls, cls.SCENARIOS.get(detail_id, "other"))

        return method_to_call(payment, writeback_detail)

    @classmethod
    def pending_validation(cls, payment, _):
        created_date = payment.pub_eft.prenote_sent_at if payment.pub_eft else None
        if created_date is None:
            expected_send_date_start, expected_send_date_end = get_expected_dates(
                date.today(), 6, 8
            )
        else:
            expected_send_date_start, expected_send_date_end = get_expected_dates(
                date.today(), 5, 7
            )

        return cls(
            expected_send_date_start=expected_send_date_start,
            expected_send_date_end=expected_send_date_end,
        )

    @classmethod
    def income(cls, _, writeback_detail):
        created_date = writeback_detail.created_at.date()
        expected_send_date_start, expected_send_date_end = get_expected_dates(created_date, 2, 4)

        return cls(
            expected_send_date_start=expected_send_date_start,
            expected_send_date_end=expected_send_date_end,
        )

    @classmethod
    def paid(cls, payment, writeback_detail):
        sent_date = writeback_detail.created_at.date()

        return cls(
            amount=payment.amount,
            sent_date=sent_date,
            expected_send_date_start=sent_date,
            expected_send_date_end=sent_date,
            status=FEPaymentStatus.SENT_TO_BANK,
        )

    @classmethod
    def no_writeback(cls, *_):
        expected_send_date_start, expected_send_date_end = get_expected_dates(date.today(), 1, 3)
        return cls(
            expected_send_date_start=expected_send_date_start,
            expected_send_date_end=expected_send_date_end,
            status=FEPaymentStatus.PENDING,
        )

    @classmethod
    def other(cls, *_):
        return cls()


@dataclass
class PaymentContainer:
    payment: Payment

    scenario_data: Optional[PaymentScenarioData] = None

    def __post_init__(self):
        self.scenario_data = PaymentScenarioData.from_payment(self.payment)


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
        scenario_data = payment_container.scenario_data
        if scenario_data is None:
            raise Exception

        payments.append(
            PaymentResponse(
                payment_id=payment.payment_id,
                fineos_c_value=payment.fineos_pei_c_value,
                fineos_i_value=payment.fineos_pei_i_value,
                period_start_date=payment.period_start_date,
                period_end_date=payment.period_end_date,
                amount=scenario_data.amount,
                sent_to_bank_date=scenario_data.sent_date,
                payment_method=payment.disb_method
                and payment.disb_method.payment_method_description,
                expected_send_date_start=scenario_data.expected_send_date_start,
                expected_send_date_end=scenario_data.expected_send_date_end,
                status=scenario_data.status,
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

    if first_detail_record.transaction_status_id == WritebackStatus.POSTED.transaction_status_id:
        for record in reversed(writeback_details_records):
            # TODO: Is it possible no preceding paid record will be found?
            if record.transaction_status_id == WritebackStatus.PAID.transaction_status_id:
                return record

    return first_detail_record


def get_expected_dates(
    from_date: date, range_start: int, range_end: int
) -> tuple[Optional[date], Optional[date]]:
    if (from_date + timedelta(days=range_end)) < date.today():
        expected_end, expected_start = None, None
    else:
        expected_start = from_date + timedelta(days=range_start)
        expected_end = from_date + timedelta(days=range_end)

    return (expected_start, expected_end)

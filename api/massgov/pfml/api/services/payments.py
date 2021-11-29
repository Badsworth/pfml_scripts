import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import pytz
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc

from massgov.pfml.api.models.payments.responses import PaymentResponse
from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import Claim, Payment, PaymentTransactionType
from massgov.pfml.db.models.payments import FineosWritebackDetails
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus as WritebackStatus
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


class FrontendPaymentStatus:
    SENT_TO_BANK = "Sent to bank"
    DELAYED = "Delayed"
    PENDING = "Pending"


@dataclass
class PaymentScenarioData:
    amount: Optional[Decimal] = None
    sent_date: Optional[date] = None
    expected_send_date_start: Optional[date] = None
    expected_send_date_end: Optional[date] = None
    status: str = FrontendPaymentStatus.DELAYED

    SCENARIOS = {
        WritebackStatus.PENDING_PRENOTE.transaction_status_id: "pending_validation",
        WritebackStatus.DUA_ADDITIONAL_INCOME.transaction_status_id: "reduction",
        WritebackStatus.DIA_ADDITIONAL_INCOME.transaction_status_id: "reduction",
        WritebackStatus.WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850.transaction_status_id: "reduction",
        WritebackStatus.SELF_REPORTED_ADDITIONAL_INCOME.transaction_status_id: "reduction",
        WritebackStatus.PAID.transaction_status_id: "paid",
        WritebackStatus.POSTED.transaction_status_id: "paid",
        None: "no_writeback",
    }

    @classmethod
    def compute(cls, payment: Payment) -> "PaymentScenarioData":
        writeback_detail = get_latest_writeback_detail(payment)
        detail_id = writeback_detail.transaction_status_id if writeback_detail else None
        method_to_call = getattr(cls, cls.SCENARIOS.get(detail_id, "other"))

        return method_to_call(payment=payment, writeback_detail=writeback_detail)

    @classmethod
    def pending_validation(cls, **kwargs):
        payment = kwargs["payment"]
        pub_eft = payment.pub_eft
        created_date = (
            pub_eft.prenote_sent_at.date() if pub_eft and pub_eft.prenote_sent_at else None
        )

        if created_date is None:
            # If the EFT record hasn't been sent to PUB yet, pub_eft.prenote_sent_at won't be set yet.
            # We'll assume we are going to send it within the next day, so up the 5-7 day date range by 1 to compensate.
            expected_send_date_start, expected_send_date_end = get_expected_dates(
                date.today(), range_start=6, range_end=8
            )
        else:
            # We must wait 5 days before we can approve a prenote,
            # so we recommend waiting 5-7 days from when we sent it.
            expected_send_date_start, expected_send_date_end = get_expected_dates(
                created_date, range_start=5, range_end=7
            )

        return cls(
            expected_send_date_start=expected_send_date_start,
            expected_send_date_end=expected_send_date_end,
        )

    @classmethod
    def reduction(cls, **kwargs):
        """
        Reduction scenarios require someone to manually make a change in FINEOS
        Which usually takes about 2 days. Note the payment could still be cancelled
        if the reduction ends up greater than the amount remaining.
        """
        writeback_detail = kwargs["writeback_detail"]
        created_date = to_est(writeback_detail.created_at).date()
        expected_send_date_start, expected_send_date_end = get_expected_dates(
            created_date, range_start=2, range_end=4
        )

        return cls(
            expected_send_date_start=expected_send_date_start,
            expected_send_date_end=expected_send_date_end,
        )

    @classmethod
    def paid(cls, **kwargs):
        """
        The payment has been successfully paid
        """
        payment, writeback_detail = kwargs["payment"], kwargs["writeback_detail"]
        sent_date = to_est(writeback_detail.created_at).date()

        return cls(
            amount=payment.amount,
            sent_date=sent_date,
            expected_send_date_start=sent_date,
            expected_send_date_end=sent_date,
            status=FrontendPaymentStatus.SENT_TO_BANK,
        )

    @classmethod
    def no_writeback(cls, **_):
        """
        No writeback means the payment hasn't failed any validation,
        but hasn't been sent to the bank yet. Likely it's waiting for the audit report
        so we'll consider it a pending payment
        """
        expected_send_date_start, expected_send_date_end = get_expected_dates(
            date.today(), range_start=1, range_end=3
        )
        return cls(
            expected_send_date_start=expected_send_date_start,
            expected_send_date_end=expected_send_date_end,
            status=FrontendPaymentStatus.PENDING,
        )

    @classmethod
    def other(cls, **_):
        """
        All payments that don't match one of the
        other criteria end up with the defaults and display as delayed.
        """
        return cls()


@dataclass
class PaymentContainer:
    payment: Payment
    claim: Claim

    def get_scenario_data(self) -> PaymentScenarioData:
        return PaymentScenarioData.compute(self.payment)


def get_payments_with_status(db_session: Session, claim: Claim) -> Dict:
    payments = get_payments_from_db(db_session, claim.claim_id)
    payment_containers = [PaymentContainer(payment, claim) for payment in payments]
    filtered_payments = filter_and_sort_payments(payment_containers)
    return to_response_dict(filtered_payments, claim.fineos_absence_id)


def get_payments_from_db(db_session: Session, claim_id: uuid.UUID) -> List[Payment]:
    return (
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


def to_response_dict(payment_data: List[PaymentContainer], absence_case_id: Optional[str]) -> Dict:
    payments = []
    for payment_container in payment_data:
        payment = payment_container.payment
        scenario_data = payment_container.get_scenario_data()

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
            # TODO: Log error if no preceding paid record is found.
            if record.transaction_status_id == WritebackStatus.PAID.transaction_status_id:
                return record

    return first_detail_record


def filter_and_sort_payments(payment_data: List[PaymentContainer]) -> List[PaymentContainer]:
    payments_to_keep = []

    for payment_container in payment_data:
        payment = payment_container.payment
        if (
            payment.payment_transaction_type_id
            == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
        ):
            continue

        # If a payment is not in a Paid state (Paid or Posted) and
        # the payment falls during the waiting week, we need to filter it out
        writeback_detail = get_latest_writeback_detail(payment)
        if writeback_detail and (
            writeback_detail.transaction_status_id == WritebackStatus.PAID.transaction_status_id
        ):
            payments_to_keep.append(payment_container)
        # Waiting week calculation
        elif (payment.period_start_date and payment_container.claim.absence_period_start_date) and (
            payment.period_start_date - payment_container.claim.absence_period_start_date
        ).days < 7:
            continue

        payments_to_keep.append(payment_container)

    # TODO: sort payments when @chouinar's work on API-2045 is merged
    return payments_to_keep


def get_expected_dates(
    from_date: date, range_start: int, range_end: int
) -> tuple[Optional[date], Optional[date]]:
    if (from_date + timedelta(days=range_end)) < date.today():
        expected_end, expected_start = None, None
    else:
        expected_start = from_date + timedelta(days=range_start)
        expected_end = from_date + timedelta(days=range_end)

    return (expected_start, expected_end)


def to_est(datetime_obj):
    est = pytz.timezone("US/Eastern")
    return datetime_obj.astimezone(est)

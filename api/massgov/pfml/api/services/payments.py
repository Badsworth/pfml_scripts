import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from functools import total_ordering
from typing import Any, Dict, List, Optional, Tuple

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
    CANCELLED = "Cancelled"


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
    def compute(cls, payment_container: "PaymentContainer") -> "PaymentScenarioData":
        if payment_container.is_cancelled():
            return cls.cancelled()

        writeback_detail = payment_container.writeback_detail
        detail_id = writeback_detail.transaction_status_id if writeback_detail else None
        method_to_call = getattr(cls, cls.SCENARIOS.get(detail_id, "other"))

        return method_to_call(payment=payment_container.payment, writeback_detail=writeback_detail)

    @classmethod
    def cancelled(cls, **kwargs):
        return cls(
            status=FrontendPaymentStatus.CANCELLED,
            amount=Decimal("0.00"),  # The portal wants cancellations to be for $0
        )

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


@total_ordering  # Handles supporting sort with just __eq__ and __lt__
@dataclass
class PaymentContainer:
    payment: Payment

    writeback_detail: Optional[FineosWritebackDetails] = None

    # The event that cancels this payment
    cancellation_event: Optional["PaymentContainer"] = None

    # (Only for payments that are themselves cancellations)
    # Which payment it cancels
    cancelled_payment: Optional["PaymentContainer"] = None

    def __post_init__(self):
        self.writeback_detail = get_latest_writeback_detail(self.payment)

    def get_scenario_data(self) -> PaymentScenarioData:
        return PaymentScenarioData.compute(self)

    def _get_sort_key(self) -> Any:
        return (
            self.payment.period_start_date,
            self.import_log_id(),
            int(self.payment.fineos_pei_i_value),  # type: ignore
        )

    def __eq__(self, other):
        return self._get_sort_key() == other._get_sort_key()

    def __lt__(self, other):
        return self._get_sort_key() < other._get_sort_key()

    def import_log_id(self) -> int:
        # In a function so I can ignore mypy warnings
        # The field is nullable, but a payment isn't ever
        # created without this in a real environment
        return self.payment.fineos_extract_import_log_id  # type: ignore

    def is_zero_dollar_payment(self) -> bool:
        return (
            self.payment.payment_transaction_type_id
            == PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
        )

    def is_cancelled(self) -> bool:
        if self.cancellation_event:
            return True

        if self.is_zero_dollar_payment():
            return True

        return False


def get_payments_with_status(db_session: Session, claim: Claim) -> Dict:
    """
    For a given claim, return all payments we want displayed on the
    payment status endpoint.

    1. Fetch all Standard/Cancellation/Zero Dollar payments for the claim
       ignoring any payments with `exclude_from_payment_status` and deduping
       C/I value to the latest version of the payment.

    2. For each pay period, figure out what payments are cancelled. If
       any un-cancelled payments remain, return those. Otherwise return
       the most recent cancellation.

    3. Filter payments that we don't want displayed such as raw-cancellation
       events and payments in or before the waiting week (unless paid). Sort
       the remaining payments in order of pay period and order processed.

    4. Determine the status, and various fields for a payment based on
       its writeback status and other fields. Depending on its scenario,
       return differing fields for the payment.
    """
    payment_containers = get_payments_from_db(db_session, claim.claim_id)

    consolidated_payments = consolidate_successors(payment_containers)

    filtered_payments = filter_and_sort_payments(consolidated_payments)

    return to_response_dict(filtered_payments, claim.fineos_absence_id)


def get_payments_from_db(db_session: Session, claim_id: uuid.UUID) -> List[PaymentContainer]:
    payments = (
        db_session.query(Payment)
        .filter(Payment.claim_id == claim_id,)
        .filter(
            Payment.payment_transaction_type_id.in_(
                [
                    PaymentTransactionType.STANDARD.payment_transaction_type_id,
                    PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id,
                    PaymentTransactionType.CANCELLATION.payment_transaction_type_id,
                ]
            ),
        )
        .filter(Payment.exclude_from_payment_status != True)  # noqa: E712
        .order_by(Payment.fineos_pei_i_value, desc(Payment.fineos_extract_import_log_id))
        .distinct(Payment.fineos_pei_i_value)
        .options(joinedload(Payment.fineos_writeback_details))  # type: ignore
        .all()
    )

    payment_containers = []
    for payment in payments:
        payment_containers.append(PaymentContainer(payment))
    return payment_containers


def consolidate_successors(payment_data: List[PaymentContainer]) -> List[PaymentContainer]:
    """
    Group payments by pay period, and figure out which payments
    have been cancelled.

    If a pay period has only cancelled payments, just return the latest one.
    If a pay period has any uncancelled payments, return all of them.

    For the purposes of this process, zero dollar payments are cancellations
    as they are payments that aren't going to be paid.
    """
    pay_period_data: Dict[Tuple[date, date], List[PaymentContainer]] = {}

    # First group payments by pay period
    for payment_container in payment_data:
        # Shouldn't be possible, but to make mypy happy:
        if (
            payment_container.payment.period_start_date is None
            or payment_container.payment.period_end_date is None
        ):
            logger.warning("Payment %s has no pay periods", payment_container.payment.payment_id)
            continue

        key = (
            payment_container.payment.period_start_date,
            payment_container.payment.period_end_date,
        )

        if key not in pay_period_data:
            pay_period_data[key] = []

        pay_period_data[key].append(payment_container)

    # Then for each pay period, we need to figure out
    # what payments have been cancelled.
    consolidated_payments = []
    for payments in pay_period_data.values():
        consolidated_payments.extend(_offset_cancellations(payments))

    return consolidated_payments


def _offset_cancellations(payment_containers: List[PaymentContainer]) -> List[PaymentContainer]:
    # Sort, this puts payments in FINEOS creation order
    payment_containers.sort()

    # Separate the cancellation payments out of the list
    regular_payments: List[PaymentContainer] = []
    cancellation_events: List[PaymentContainer] = []
    for payment_container in payment_containers:
        if (
            payment_container.payment.payment_transaction_type_id
            == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
        ):
            cancellation_events.append(payment_container)
        else:
            regular_payments.append(payment_container)

    # For each regular payment, find the corresponding cancellation (if it exists)
    cancelled_payments = []
    processed_payments = []
    for regular_payment in regular_payments:
        is_cancelled = False

        # Zero dollar payments are effectively cancelled payments
        if regular_payment.is_zero_dollar_payment():
            is_cancelled = True

        else:
            # We can match a cancellation event for a payment if:
            # * Cancellation occurs later than the payment (based on import log ID)
            # * Cancellation amount is the negative of the payments
            # * Cancellation isn't already cancelling another payment
            #
            # FUTURE TODO - In FINEOS' tolpaymentoutevent table
            # there are columns (C_PYMNTEIF_CANCELLATIONP and I_PYMNTEIF_CANCELLATIONP)
            # that are populated with the C/I value of the cancellation for cancelled payments
            # Having this would help let us exactly connect payments to their cancellations.
            # A backend process that adds a cancelling_payment column to payments would help a lot.
            for cancellation in cancellation_events:
                if (
                    cancellation.cancelled_payment is None
                    and cancellation.import_log_id() > regular_payment.import_log_id()
                    and abs(cancellation.payment.amount) == regular_payment.payment.amount
                ):
                    cancellation.cancelled_payment = regular_payment
                    regular_payment.cancellation_event = cancellation
                    is_cancelled = True
                    break

        if is_cancelled:
            cancelled_payments.append(regular_payment)
        else:
            processed_payments.append(regular_payment)

    # If there are only cancelled payments, return the last one
    # No need to return multiple cancelled payments for a single pay period
    if len(processed_payments) == 0 and len(cancelled_payments) > 0:
        latest_cancelled_payment = cancelled_payments[-1]
        return [latest_cancelled_payment]

    # Otherwise return all uncancelled payments - note that these
    # can still contain payments that have errored, they just aren't
    # officially cancelled yet.
    return processed_payments


def filter_and_sort_payments(payment_data: List[PaymentContainer]) -> List[PaymentContainer]:
    payments_to_keep = []

    for payment_container in payment_data:
        if (
            payment_container.payment.payment_transaction_type_id
            == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
        ):
            continue

        payments_to_keep.append(payment_container)

    payments_to_keep.sort()

    return payments_to_keep


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

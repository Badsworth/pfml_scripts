from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from functools import total_ordering
from typing import Any, Callable, Dict, List, Optional, cast

import pytz

from massgov.pfml.db.models.employees import Payment, PaymentTransactionType
from massgov.pfml.db.models.payments import (
    PENDING_ACTIVE_WRITEBACK_RECORD_STATUS,
    FineosWritebackDetails,
)
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus as WritebackStatus
from massgov.pfml.db.models.payments import LkFineosWritebackTransactionStatus
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


class FrontendPaymentStatus(str, Enum):
    SENT_TO_BANK = "Sent to bank"
    DELAYED = "Delayed"
    PENDING = "Pending"
    CANCELLED = "Cancelled"

    def get_metric_count_name(self) -> str:
        camelcased_str = self.lower().replace(" ", "_")
        return f"payment_status_{camelcased_str}_count"


# Enum used for tracking+logging why we excluded payments
# that were fetched from the DB.
class PaymentFilterReason(str, Enum):
    UNKNOWN = "Unknown"
    HAS_SUCCESSOR = "Has successor"
    CANCELLATION_EVENT = "Cancellation event"

    def get_metric_count_name(self) -> str:
        camelcased_str = self.lower().replace(" ", "_")
        return f"payment_filtered_{camelcased_str}_count"


@dataclass
class PaymentScenarioData:
    """
    Class for containing the values of a payment
    that can vary depending on the particular scenario.
    """

    amount: Optional[Decimal] = None
    sent_date: Optional[date] = None
    expected_send_date_start: Optional[date] = None
    expected_send_date_end: Optional[date] = None
    cancellation_date: Optional[date] = None
    status: FrontendPaymentStatus = FrontendPaymentStatus.DELAYED
    writeback_transaction_status: Optional[str] = None
    transaction_date: Optional[date] = None
    transaction_date_could_change: bool = True


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

    # Whether the payment is being returned in the API response (ie. not filtered)
    is_valid_for_response: bool = False

    # For any payments filtered, display a reason, defaults to unknown
    # in case a reason was not configured.
    payment_filter_reason: PaymentFilterReason = PaymentFilterReason.UNKNOWN

    # Used for tracking/logging purposes. For some filtered payments
    # indicates the payments that we instead returned.
    successors: List["PaymentContainer"] = field(default_factory=list)

    def __post_init__(self):
        self.writeback_detail = get_latest_writeback_detail(self.payment)

    def get_scenario_data(self) -> PaymentScenarioData:
        return get_payment_scenario_data(self)

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

    def get_cancellation_date(self) -> Optional[date]:
        # Zero dollar payments, assume they were cancelled
        # on the date we received it, even if it's earlier
        if self.is_zero_dollar_payment():
            return self.payment.fineos_extraction_date

        # For cancelled payments, use the date we received the
        # cancellation event as the cancellation date
        if self.cancellation_event:
            return self.cancellation_event.payment.fineos_extraction_date

        return None

    def is_legacy_payment(self) -> bool:
        return (
            self.payment.payment_transaction_type_id
            == PaymentTransactionType.STANDARD_LEGACY_MMARS.payment_transaction_type_id
        )


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


### Scenario Data Mapping Methods
# Define methods below to handle fetching
# the values to return for a particular payment scenario
# Primarily based on the writeback used in the
# get_payment_scenario_data method below.


def cancelled(payment_container: PaymentContainer) -> PaymentScenarioData:
    return PaymentScenarioData(
        status=FrontendPaymentStatus.CANCELLED,
        amount=Decimal("0.00"),  # The portal wants cancellations to be for $0
        cancellation_date=payment_container.get_cancellation_date(),
        **get_writeback_details(payment_container.writeback_detail),
    )


def pending_prenote(payment_container: PaymentContainer) -> PaymentScenarioData:
    payment = payment_container.payment
    pub_eft = payment.pub_eft
    created_date = pub_eft.prenote_sent_at.date() if pub_eft and pub_eft.prenote_sent_at else None

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

    return PaymentScenarioData(
        expected_send_date_start=expected_send_date_start,
        expected_send_date_end=expected_send_date_end,
        **get_writeback_details(payment_container.writeback_detail, created_date),
    )


def reduction(payment_container: PaymentContainer) -> PaymentScenarioData:
    """
    Reduction scenarios require someone to manually make a change in FINEOS
    Which usually takes about 2 days. Note the payment could still be cancelled
    if the reduction ends up greater than the amount remaining.
    """
    # We know writeback_detail is not null to get to this method
    writeback_detail = cast(FineosWritebackDetails, payment_container.writeback_detail)
    created_date = to_est(writeback_detail.created_at).date()
    expected_send_date_start, expected_send_date_end = get_expected_dates(
        created_date, range_start=2, range_end=4
    )

    return PaymentScenarioData(
        expected_send_date_start=expected_send_date_start,
        expected_send_date_end=expected_send_date_end,
        **get_writeback_details(payment_container.writeback_detail),
    )


def paid(payment_container: PaymentContainer) -> PaymentScenarioData:
    """
    The payment has been successfully paid
    """
    payment, writeback_detail = (
        payment_container.payment,
        cast(FineosWritebackDetails, payment_container.writeback_detail),
    )
    sent_date = to_est(writeback_detail.created_at).date()

    return PaymentScenarioData(
        amount=payment.amount,
        sent_date=sent_date,
        expected_send_date_start=sent_date,
        expected_send_date_end=sent_date,
        status=FrontendPaymentStatus.SENT_TO_BANK,
        **get_writeback_details(payment_container.writeback_detail),
    )


def pending(payment_container: PaymentContainer) -> PaymentScenarioData:
    """
    This means the payment hasn't failed any validation,
    but hasn't been sent to the bank yet. Likely it's waiting for the audit report
    or currently working its way through our system
    """
    expected_send_date_start, expected_send_date_end = get_expected_dates(
        date.today(), range_start=1, range_end=3
    )
    return PaymentScenarioData(
        expected_send_date_start=expected_send_date_start,
        expected_send_date_end=expected_send_date_end,
        status=FrontendPaymentStatus.PENDING,
        **get_writeback_details(payment_container.writeback_detail),
    )


def legacy_mmars_paid(payment_container: PaymentContainer) -> PaymentScenarioData:
    """
    Payment is a legacy payment from MMARS which stores
    the send date in a dedicated column
    """
    payment = payment_container.payment
    sent_date = payment.disb_check_eft_issue_date
    return PaymentScenarioData(
        amount=payment.amount,
        sent_date=sent_date,
        expected_send_date_start=sent_date,
        expected_send_date_end=sent_date,
        status=FrontendPaymentStatus.SENT_TO_BANK,
    )


def delayed(payment_container: PaymentContainer) -> PaymentScenarioData:
    """
    All payments that don't match one of the
    other criteria end up with the defaults and display as delayed.
    """
    return PaymentScenarioData(**get_writeback_details(payment_container.writeback_detail))


def get_writeback_details(
    writeback_detail: Optional[FineosWritebackDetails],
    override_transaction_status_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    This looks at the writeback details
    and pulls values out
    """
    if not writeback_detail:
        return {}

    writeback_transaction_status = None
    transaction_date = None
    transaction_date_could_change = True  # If no writeback status, assume it can

    # Generally the transaction status date is fine
    # but in some scenarios (eg. prenoting) we want
    # to use a date that better represents the date
    # of when the transaction started being delayed
    if override_transaction_status_date:
        transaction_date = override_transaction_status_date
    elif writeback_detail.writeback_sent_at:
        transaction_date = to_est(writeback_detail.writeback_sent_at).date()

    transaction_status = writeback_detail.transaction_status
    if transaction_status:
        writeback_transaction_status = transaction_status.transaction_status_description

        # If the writeback is pending active,
        # then the date could change as we continue
        # to receive the payment each day.
        transaction_date_could_change = (
            transaction_status.writeback_record_status == PENDING_ACTIVE_WRITEBACK_RECORD_STATUS
        )

    return {
        "writeback_transaction_status": writeback_transaction_status,
        "transaction_date": transaction_date,
        "transaction_date_could_change": transaction_date_could_change,
    }


# This needs to be defined after the above methods
# so that it can reference those methods directly
WRITEBACK_SCENARIOS: Dict[
    Optional[LkFineosWritebackTransactionStatus], Callable[[PaymentContainer], PaymentScenarioData],
] = {
    # This is a mapping from writeback status
    # to methods defined above which handle
    # how we process a particular payment
    #
    ##### Sent to Bank Scenarios (Success)
    WritebackStatus.PAID: paid,
    WritebackStatus.POSTED: paid,
    ##### Pending Scenarios (Still processing)
    WritebackStatus.PAYMENT_AUDIT_IN_PROGRESS: pending,
    WritebackStatus.PENDING_PAYMENT_AUDIT: pending,
    # Payments may not have a status, but be in our system if
    # the batch processing is actively occurring.
    None: pending,
    ##### Delay Scenarios (Errored)
    WritebackStatus.PENDING_PRENOTE: pending_prenote,
    WritebackStatus.DUA_ADDITIONAL_INCOME: reduction,
    WritebackStatus.DIA_ADDITIONAL_INCOME: reduction,
    WritebackStatus.DEPRECATED_TOTAL_BENEFITS_OVER_CAP: reduction,
    WritebackStatus.LEAVE_DURATION_MAX_EXCEEDED: reduction,
    WritebackStatus.WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850: reduction,
    WritebackStatus.SELF_REPORTED_ADDITIONAL_INCOME: reduction,
    WritebackStatus.DATA_ISSUE_IN_SYSTEM: delayed,
    WritebackStatus.FAILED_AUTOMATED_VALIDATION: delayed,
    WritebackStatus.PRENOTE_ERROR: delayed,
    WritebackStatus.ADDRESS_VALIDATION_ERROR: delayed,
    WritebackStatus.BANK_PROCESSING_ERROR: delayed,
    WritebackStatus.VOID_CHECK: delayed,
    WritebackStatus.STOP_CHECK: delayed,
    WritebackStatus.STALE_CHECK: delayed,
    WritebackStatus.LEAVE_IN_REVIEW: delayed,
    WritebackStatus.FAILED_MANUAL_VALIDATION: delayed,
    WritebackStatus.EXEMPT_EMPLOYER: delayed,
    WritebackStatus.WAITING_WEEK: delayed,
    WritebackStatus.ALREADY_PAID_FOR_DATES: delayed,
    WritebackStatus.LEAVE_DATES_CHANGE: delayed,
    WritebackStatus.UNDER_OR_OVERPAY_ADJUSTMENT: delayed,
    WritebackStatus.NAME_MISMATCH: delayed,
    # These are only used for non-standard payments
    WritebackStatus.PROCESSED: delayed,
    WritebackStatus.WITHHOLDING_ERROR: delayed,
}

# The above, but with the writeback status IDs for lookup
WRITEBACK_SCENARIOS_MAPPER: Dict[
    Optional[int], Callable[[PaymentContainer], PaymentScenarioData]
] = {
    writeback_status.transaction_status_id if writeback_status else None: method
    for writeback_status, method in WRITEBACK_SCENARIOS.items()
}


def get_payment_scenario_data(payment_container: PaymentContainer) -> PaymentScenarioData:
    if payment_container.is_cancelled():
        return cancelled(payment_container=payment_container)

    if payment_container.is_legacy_payment():
        return legacy_mmars_paid(payment_container=payment_container)

    writeback_detail = payment_container.writeback_detail
    detail_id = writeback_detail.transaction_status_id if writeback_detail else None
    method_to_call = WRITEBACK_SCENARIOS_MAPPER.get(detail_id, delayed)

    return method_to_call(payment_container)

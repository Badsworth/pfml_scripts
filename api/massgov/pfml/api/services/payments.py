import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
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
    amount: Optional[Decimal] = None
    sent_date: Optional[date] = None
    expected_send_date_start: Optional[date] = None
    expected_send_date_end: Optional[date] = None
    status: FrontendPaymentStatus = FrontendPaymentStatus.DELAYED

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

        if payment_container.is_legacy_payment():
            return cls.legacy_mmars_paid(payment=payment_container.payment)

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
    def legacy_mmars_paid(cls, **kwargs):
        """
        Payment is a legacy payment from MMARS which stores
        the send date in a dedicated column
        """
        payment = kwargs["payment"]
        sent_date = payment.disb_check_eft_issue_date
        return cls(
            amount=payment.amount,
            sent_date=sent_date,
            expected_send_date_start=sent_date,
            expected_send_date_end=sent_date,
            status=FrontendPaymentStatus.SENT_TO_BANK,
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

    def is_legacy_payment(self) -> bool:
        return (
            self.payment.payment_transaction_type_id
            == PaymentTransactionType.STANDARD_LEGACY_MMARS.payment_transaction_type_id
        )


def get_payments_with_status(db_session: Session, claim: Claim) -> Dict:
    """
    For a given claim, return all payments we want displayed on the
    payment status endpoint.

    1. Fetch all Standard/Legacy MMARS Standard/Cancellation/Zero Dollar payments for the claim
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
    # Note that legacy payments do not require additional processing
    # as they only exist in our system if they were successfully paid
    # and do not have successors or require filtering.
    payment_containers, legacy_payment_containers = get_payments_from_db(db_session, claim.claim_id)

    consolidated_payments = consolidate_successors(payment_containers)

    filtered_payments = filter_and_sort_payments(consolidated_payments)

    response = to_response_dict(
        filtered_payments + legacy_payment_containers, claim.fineos_absence_id
    )

    log_payment_status(
        claim, payment_containers
    )  # We pass in the raw, unfiltered payments for full metrics

    return response


def get_payments_from_db(
    db_session: Session, claim_id: uuid.UUID
) -> Tuple[List[PaymentContainer], List[PaymentContainer]]:
    payments = (
        db_session.query(Payment)
        .filter(Payment.claim_id == claim_id,)
        .filter(
            Payment.payment_transaction_type_id.in_(
                [
                    PaymentTransactionType.STANDARD.payment_transaction_type_id,
                    PaymentTransactionType.STANDARD_LEGACY_MMARS.payment_transaction_type_id,
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
    legacy_mmars_payment_containers = []
    for payment in payments:
        payment_container = PaymentContainer(payment)

        if payment_container.is_legacy_payment():
            legacy_mmars_payment_containers.append(payment_container)
        else:
            payment_containers.append(payment_container)

    return payment_containers, legacy_mmars_payment_containers


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
            logger.warning(
                "get_payments Payment %s has no pay periods",
                payment_container.payment.payment_id,
                extra={"payment_id": payment_container.payment.payment_id},
            )
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
            payment_container.payment_filter_reason = PaymentFilterReason.CANCELLATION_EVENT
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
        latest_cancelled_payment = cancelled_payments.pop()
        for cancelled_payment in cancelled_payments:
            cancelled_payment.payment_filter_reason = PaymentFilterReason.HAS_SUCCESSOR
            cancelled_payment.successors = [latest_cancelled_payment]

        return [latest_cancelled_payment]

    # Otherwise return all uncancelled payments - note that these
    # can still contain payments that have errored, they just aren't
    # officially cancelled yet.

    # We also want to mark the filter reason for logging purposes
    for cancelled_payment_container in cancelled_payments:
        cancelled_payment_container.payment_filter_reason = PaymentFilterReason.HAS_SUCCESSOR
        cancelled_payment_container.successors = processed_payments
    return processed_payments


def filter_and_sort_payments(payment_data: List[PaymentContainer]) -> List[PaymentContainer]:
    payments_to_keep = []

    for payment_container in payment_data:
        if (
            payment_container.payment.payment_transaction_type_id
            == PaymentTransactionType.CANCELLATION.payment_transaction_type_id
        ):
            payment_container.payment_filter_reason = PaymentFilterReason.CANCELLATION_EVENT
            continue

        payments_to_keep.append(payment_container)

    payments_to_keep.sort()

    return payments_to_keep


def to_response_dict(payment_data: List[PaymentContainer], absence_case_id: Optional[str]) -> Dict:
    payments = []
    for payment_container in payment_data:
        payment_container.is_valid_for_response = True
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


def log_payment_status(claim: Claim, payment_containers: List[PaymentContainer]) -> None:
    log_attributes: Dict[str, Any] = defaultdict(int)
    log_attributes["absence_id"] = claim.fineos_absence_id

    # For the various payment scenarios, initialize the counts to 0
    # New enums defined above automatically get added here
    for reason in PaymentFilterReason:
        log_attributes[reason.get_metric_count_name()] = 0

    for status in FrontendPaymentStatus:
        log_attributes[status.get_metric_count_name()] = 0

    returned_payments = []
    filtered_payments = []

    # Figure out what we did with the payment.
    for payment_container in payment_containers:
        # We are returning it
        if payment_container.is_valid_for_response:
            returned_payments.append(payment_container)
        else:
            # Or it was filtered prior to getting that far
            filtered_payments.append(payment_container)

    log_attributes["payments_returned_count"] = len(returned_payments)
    log_attributes["payments_filtered_count"] = len(filtered_payments)
    returned_payments.sort()
    filtered_payments.sort()

    for i, returned_payment in enumerate(returned_payments):
        scenario_data = returned_payment.get_scenario_data()
        log_attributes[scenario_data.status.get_metric_count_name()] += 1

        log_attributes[f"payment[{i}].id"] = returned_payment.payment.payment_id
        log_attributes[f"payment[{i}].c_value"] = returned_payment.payment.fineos_pei_c_value
        log_attributes[f"payment[{i}].i_value"] = returned_payment.payment.fineos_pei_i_value
        log_attributes[f"payment[{i}].period_start_date"] = (
            returned_payment.payment.period_start_date.isoformat()
            if returned_payment.payment.period_start_date
            else None
        )
        log_attributes[f"payment[{i}].period_end_date"] = (
            returned_payment.payment.period_end_date.isoformat()
            if returned_payment.payment.period_end_date
            else None
        )
        log_attributes[
            f"payment[{i}].payment_type"
        ] = returned_payment.payment.payment_transaction_type.payment_transaction_type_description
        log_attributes[f"payment[{i}].status"] = scenario_data.status.value

        if returned_payment.cancellation_event:
            log_attributes[
                f"payment[{i}].cancellation_event.c_value"
            ] = returned_payment.cancellation_event.payment.fineos_pei_c_value
            log_attributes[
                f"payment[{i}].cancellation_event.i_value"
            ] = returned_payment.cancellation_event.payment.fineos_pei_i_value

    for i, filtered_payment in enumerate(filtered_payments):
        log_attributes[filtered_payment.payment_filter_reason.get_metric_count_name()] += 1

        log_attributes[f"filtered_payment[{i}].id"] = filtered_payment.payment.payment_id
        log_attributes[
            f"filtered_payment[{i}].c_value"
        ] = filtered_payment.payment.fineos_pei_c_value
        log_attributes[
            f"filtered_payment[{i}].i_value"
        ] = filtered_payment.payment.fineos_pei_i_value
        log_attributes[f"filtered_payment[{i}].period_start_date"] = (
            filtered_payment.payment.period_start_date.isoformat()
            if filtered_payment.payment.period_start_date
            else None
        )
        log_attributes[f"filtered_payment[{i}].period_end_date"] = (
            filtered_payment.payment.period_end_date.isoformat()
            if filtered_payment.payment.period_end_date
            else None
        )
        log_attributes[
            f"filtered_payment[{i}].payment_type"
        ] = filtered_payment.payment.payment_transaction_type.payment_transaction_type_description
        log_attributes[
            f"filtered_payment[{i}].filter_reason"
        ] = filtered_payment.payment_filter_reason.value

        # Also log which C/I values succeeded the filtered payment if present
        for successor_i, successor_payment in enumerate(filtered_payment.successors):
            log_attributes[
                f"filtered_payment[{i}].successor[{successor_i}].c_value"
            ] = successor_payment.payment.fineos_pei_c_value
            log_attributes[
                f"filtered_payment[{i}].successor[{successor_i}].i_value"
            ] = successor_payment.payment.fineos_pei_i_value

        # If it's a cancellation event, add what it cancelled
        if filtered_payment.cancelled_payment:
            log_attributes[
                f"filtered_payment[{i}].cancels.c_value"
            ] = filtered_payment.cancelled_payment.payment.fineos_pei_c_value
            log_attributes[
                f"filtered_payment[{i}].cancels.i_value"
            ] = filtered_payment.cancelled_payment.payment.fineos_pei_i_value

    logger.info("get_payments success", extra=log_attributes)

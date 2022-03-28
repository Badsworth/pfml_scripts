import uuid
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc

from massgov.pfml.api.models.payments.responses import (
    PaymentDetailsResponse,
    PaymentLinesResponse,
    PaymentResponse,
)
from massgov.pfml.api.services.payments_services_util import (
    FrontendPaymentStatus,
    PaymentContainer,
    PaymentFilterReason,
)
from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import Claim, Payment, PaymentDetails, PaymentTransactionType
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


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
        .filter(Payment.claim_id == claim_id)
        .filter(
            Payment.payment_transaction_type_id.in_(
                [
                    PaymentTransactionType.STANDARD.payment_transaction_type_id,
                    PaymentTransactionType.STANDARD_LEGACY_MMARS.payment_transaction_type_id,
                    PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id,
                    PaymentTransactionType.CANCELLATION.payment_transaction_type_id,
                ]
            )
        )
        .filter(Payment.exclude_from_payment_status != True)  # noqa: E712
        .filter(
            Payment.disb_method_id.isnot(None)
        )  # Handling a bug where payments have an unset payment method
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


def get_payment_lines_responses(payment_detail: PaymentDetails) -> list[PaymentLinesResponse]:
    payment_lines = []

    # payment_lines is defined on PaymentDetails in db/models/payments.py
    for payment_line in payment_detail.payment_lines:  # type: ignore
        payment_lines.append(
            PaymentLinesResponse(
                payment_line_id=payment_line.payment_line_id,
                payment_line_c_value=payment_line.payment_line_c_value,
                payment_line_i_value=payment_line.payment_line_i_value,
                amount=payment_line.amount,
                line_type=payment_line.line_type,
            )
        )

    return payment_lines


def get_payment_details_responses(payment: Payment) -> list[PaymentDetailsResponse]:
    payment_details = []

    for payment_detail in payment.payment_details:
        payment_lines = get_payment_lines_responses(payment_detail)

        payment_details.append(
            PaymentDetailsResponse(
                payment_detail_id=payment_detail.payment_details_id,
                payment_detail_c_value=payment_detail.payment_details_c_value,
                payment_detail_i_value=payment_detail.payment_details_i_value,
                period_start_date=payment_detail.period_start_date,
                period_end_date=payment_detail.period_end_date,
                amount=payment_detail.amount,
                payment_lines=payment_lines,
            )
        )

    return payment_details


def to_response_dict(payment_data: List[PaymentContainer], absence_case_id: Optional[str]) -> Dict:
    payments = []
    for payment_container in payment_data:
        payment_container.is_valid_for_response = True
        payment = payment_container.payment
        scenario_data = payment_container.get_scenario_data()

        payment_details = get_payment_details_responses(payment)

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
                cancellation_date=scenario_data.cancellation_date,
                status=scenario_data.status,
                writeback_transaction_status=scenario_data.writeback_transaction_status,
                transaction_date=scenario_data.transaction_date,
                transaction_date_could_change=scenario_data.transaction_date_could_change,
                payment_details=payment_details,
            ).dict()
        )

    return {"payments": payments, "absence_case_id": absence_case_id}


def log_payment_status(claim: Claim, payment_containers: List[PaymentContainer]) -> None:
    log_attributes: Dict[str, Any] = defaultdict(int)
    log_attributes["absence_case_id"] = claim.fineos_absence_id
    log_attributes["fineos_customer_number"] = (
        claim.employee.fineos_customer_number if claim.employee else None
    )

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
        log_attributes[
            f"payment[{i}].writeback_transaction_status"
        ] = scenario_data.writeback_transaction_status
        log_attributes[f"payment[{i}].transaction_date"] = (
            scenario_data.transaction_date.isoformat() if scenario_data.transaction_date else None
        )
        log_attributes[
            f"payment[{i}].transaction_date_could_change"
        ] = scenario_data.transaction_date_could_change

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

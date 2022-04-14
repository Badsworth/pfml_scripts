import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import ImportLog, Payment, PaymentDetails
from massgov.pfml.db.models.payments import (
    FineosExtractVpei,
    FineosExtractVpeiPaymentDetails,
    FineosExtractVpeiPaymentLine,
    PaymentLine,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


class BackfillPayPeriodLinesStep(Step):
    """
    Step to backfill the pay period
    and PEI line records from the FINEOS extract
    staging tables into our formatted tables.

    1. Fetches all import log records associated
       with a payment. We'll use this to batch
       payments.
    2. Fetch all payments for a given import log
       ID. Note this query also simultaneously fetches
       many values associated with a payment to
       reduce DB calls.
    3. Check if the payments actually require an
       update. The newest batches won't as we've
       been updating the fields correctly.
    4. Fetch the FINEOS extract data for the payment
       details and payment lines, updating existing
       payment details and creating payment lines.
    """

    class Metrics(str, enum.Enum):

        TOTAL_BATCH_COUNT = "total_batch_count"
        PROCESSED_BATCH_COUNT = "processed_batch_count"

        PAYMENT_PROCESSED_COUNT = "payment_processed_count"
        PAYMENT_MISSING_VPEI_ID_COUNT = "payment_missing_vpei_count"

        PAYMENT_DETAIL_PROCESSED_COUNT = "payment_detail_processed_count"
        RAW_PAYMENT_DETAIL_PROCESSED_COUNT = "raw_payment_detail_processed_count"

        PAYMENT_DETAIL_MISMATCH_COUNT = "payment_detail_mismatch_count"
        PAYMENT_DETAIL_MISSING_DATE_COUNT = "payment_detail_missing_date_count"
        PAYMENT_DETAIL_MULTIPLE_MATCH_COUNT = "payment_detail_multiple_match_count"
        PAYMENT_DETAIL_ALREADY_PRESENT_COUNT = "payment_detail_already_present_count"
        PAYMENT_DETAIL_NO_RECORDS_COUNT = "payment_detail_no_records_count"
        PAYMENT_DETAIL_NO_MATCH_COUNT = "payment_detail_no_match_count"

        PAYMENT_LINE_PROCESSED_COUNT = "payment_line_processed_count"
        PAYMENT_LINE_NO_RECORDS_COUNT = "payment_line_no_records_count"
        PAYMENT_LINE_ALREADY_PRESENT_COUNT = "payment_line_already_present_count"
        PAYMENT_LINE_DETAIL_MISSING_UNEXPECTED_COUNT = (
            "payment_line_detail_missing_unexpected_count"
        )
        PAYMENT_LINE_AMOUNT_NON_NUMERIC_COUNT = "payment_line_amount_non_numeric_count"
        PAYMENT_LINE_MISSING_REQUIRED_VALUE_COUNT = "payment_line_missing_required_value_count"

    def run_step(self) -> None:

        payment_import_logs = self.get_import_log_ids()

        logger.info("Found %s import logs to process for backfill", len(payment_import_logs))
        self.set_metrics({self.Metrics.TOTAL_BATCH_COUNT: len(payment_import_logs)})

        for import_log in payment_import_logs:
            extra = self.get_extra(import_log=import_log)
            logger.info("Processing payments for batch", extra=extra)

            payments = self.get_payments_for_batch(import_log.import_log_id)
            logger.info("Found %s payments for batch", len(payments), extra=extra)

            for payment in payments:
                self.process_payment(payment, import_log)

            logger.info("Finished processing payments for batch", extra=extra)
            self.increment(self.Metrics.PROCESSED_BATCH_COUNT)
            # Commit for every batch
            self.db_session.commit()

    def get_import_log_ids(self) -> List[ImportLog]:
        """
        Get all import log IDs associated with payments
        based on the IDs attached to the payment.

        This only fetches payments that have a vpei_id
        record as we use that to figure out the FINEOS extract
        table that a payment was created from.

        This value wasn't always attached to a payment,
        but has been since October 2021. In prod it was backfilled
        but other envs don't have it set before then
        but ~5 months of data backfilled will be adequate.
        """
        import_log_ids = (
            self.db_session.query(Payment.fineos_extract_import_log_id)
            .filter(Payment.vpei_id.isnot(None))
            .distinct()
        )
        return (
            self.db_session.query(ImportLog)
            .filter(ImportLog.import_log_id.in_(import_log_ids))
            .order_by(ImportLog.import_log_id.desc())
            .all()
        )

    def get_payments_for_batch(self, import_log_id: int) -> List[Payment]:
        """
        Get every payment for a given import log ID

        Also does a joinedload to the payment_details, payment_lines, and VPEI
        table as we are going to need them and this avoids having to query
        as many times.
        """
        return (
            self.db_session.query(Payment)
            .filter(Payment.fineos_extract_import_log_id == import_log_id)
            .options(
                joinedload(Payment.payment_details),
                joinedload(Payment.payment_lines),  # type: ignore
                joinedload(Payment.vpei),  # type: ignore
            )
            .all()
        )

    def process_payment(self, payment: Payment, import_log: ImportLog) -> None:
        extra = self.get_extra(import_log=import_log, payment=payment)
        logger.info("Processing payment for backfill", extra=extra)

        # These should already be loaded and not require a DB query
        # due to how get_payments_for_batch is setup.
        payment_details: List[PaymentDetails] = payment.payment_details
        payment_lines: List[PaymentLine] = payment.payment_lines  # type: ignore
        vpei_record: FineosExtractVpei = payment.vpei  # type: ignore

        if payment_lines:
            # If payment lines exist, we're looking at a payment
            # created after we correctly were setting payment details
            # and creating payment lines.
            self.add_batch_metric(
                self.Metrics.PAYMENT_DETAIL_ALREADY_PRESENT_COUNT, import_log, len(payment_details)
            )
            self.add_batch_metric(
                self.Metrics.PAYMENT_LINE_ALREADY_PRESENT_COUNT, import_log, len(payment_lines)
            )
            logger.info("Skipping payment as it already has payment lines", extra=extra)
            return

        if not vpei_record:
            # This shouldn't happen as the import log ID query filters these out
            self.add_batch_metric(self.Metrics.PAYMENT_MISSING_VPEI_ID_COUNT, import_log)
            logger.warning(
                "Payment does not have a VPEI record - cannot process backfill", extra=extra
            )
            return

        self.add_batch_metric(self.Metrics.PAYMENT_PROCESSED_COUNT, import_log=import_log)

        raw_payment_details = (
            self.db_session.query(FineosExtractVpeiPaymentDetails)
            .filter(
                FineosExtractVpeiPaymentDetails.reference_file_id == vpei_record.reference_file_id,
                FineosExtractVpeiPaymentDetails.peclassid == vpei_record.c,
                FineosExtractVpeiPaymentDetails.peindexid == vpei_record.i,
            )
            .all()
        )
        self.process_payment_details(
            payment_details=payment_details,
            raw_payment_details=raw_payment_details,
            payment=payment,
            import_log=import_log,
        )

        raw_payment_lines = (
            self.db_session.query(FineosExtractVpeiPaymentLine)
            .filter(
                FineosExtractVpeiPaymentLine.reference_file_id == vpei_record.reference_file_id,
                FineosExtractVpeiPaymentLine.c_pymnteif_paymentlines == vpei_record.c,
                FineosExtractVpeiPaymentLine.i_pymnteif_paymentlines == vpei_record.i,
            )
            .all()
        )
        self.create_payment_lines(
            raw_payment_lines=raw_payment_lines,
            payment_details=payment_details,
            payment=payment,
            vpei=vpei_record,
            import_log=import_log,
        )

    def process_payment_details(
        self,
        payment_details: List[PaymentDetails],
        raw_payment_details: List[FineosExtractVpeiPaymentDetails],
        payment: Payment,
        import_log: ImportLog,
    ) -> None:
        """
        Update the payment details record.

        Only updates the C/I value and links
        the record to the raw payment details
        record so that any future backfills
        are much easier.
        """
        is_valid = self.validate_payment_details(
            payment_details, raw_payment_details, payment, import_log
        )
        if not is_valid:
            return

        # Iterate over the raw payment detail records
        # and try to find the corresponding record we
        # created from it based on the period start/end & amount
        for raw_payment_detail in raw_payment_details:
            found_match = False

            for payment_detail in payment_details:
                if payment_detail_matches(payment_detail, raw_payment_detail):

                    if payment_detail.vpei_payment_details_id:
                        # Make sure we aren't overwriting an existing record
                        # Could also mean two pay periods with identical info
                        # on a payment, which should also not happen
                        self.add_batch_metric(
                            self.Metrics.PAYMENT_DETAIL_MULTIPLE_MATCH_COUNT, import_log
                        )
                        logger.info(
                            "Payment detail already attached to raw record",
                            extra=self.get_extra(
                                import_log=import_log,
                                payment=payment,
                                payment_detail=payment_detail,
                            ),
                        )
                        continue

                    # Finally set the values we weren't properly setting
                    payment_detail.payment_details_c_value = raw_payment_detail.c
                    payment_detail.payment_details_i_value = raw_payment_detail.i
                    payment_detail.vpei_payment_details_id = (
                        raw_payment_detail.vpei_payment_details_id
                    )

                    logger.info(
                        "Updated payment detail",
                        extra=self.get_extra(
                            import_log=import_log,
                            payment=payment,
                            payment_detail=payment_detail,
                            raw_payment_detail=raw_payment_detail,
                        ),
                    )
                    found_match = True
                    break

            # If the raw payment detail
            # doesn't match anything
            if not found_match:
                self.add_batch_metric(self.Metrics.PAYMENT_DETAIL_NO_MATCH_COUNT, import_log)
                logger.warning(
                    "Failed to find a match for raw payment detail",
                    extra=self.get_extra(
                        import_log=import_log,
                        payment=payment,
                        raw_payment_detail=raw_payment_detail,
                    ),
                )

    def validate_payment_details(
        self,
        payment_details: List[PaymentDetails],
        raw_payment_details: List[FineosExtractVpeiPaymentDetails],
        payment: Payment,
        import_log: ImportLog,
    ) -> bool:
        """
        Pre-validate and setup some metrics regarding
        the payment detail processing.
        """
        self.add_batch_metric(
            self.Metrics.PAYMENT_DETAIL_PROCESSED_COUNT, import_log, increment=len(payment_details)
        )
        self.add_batch_metric(
            self.Metrics.RAW_PAYMENT_DETAIL_PROCESSED_COUNT,
            import_log,
            increment=len(raw_payment_details),
        )

        payment_details_count = len(payment_details)
        raw_payment_details_count = len(raw_payment_details)

        extra = self.get_extra(import_log=import_log, payment=payment)
        extra["payment_details_count"] = payment_details_count
        extra["raw_payment_details_count"] = raw_payment_details_count
        logger.info("Updating payment details for payment", extra=extra)

        if payment_details_count != raw_payment_details_count:
            # This shouldn't happen, that would mean we didn't
            # process/attach a payment detail record to a payment.
            self.add_batch_metric(self.Metrics.PAYMENT_DETAIL_MISMATCH_COUNT, import_log)
            logger.warning(
                "Payment details count does not match the raw staging table count", extra=extra
            )
            return False

        if raw_payment_details_count == 0:
            # Just do this for the metric/log, wouldn't affect logic below
            self.add_batch_metric(self.Metrics.PAYMENT_DETAIL_NO_RECORDS_COUNT, import_log)
            logger.info("No payment details for payment", extra=extra)
            return False

        return True

    def create_payment_lines(
        self,
        raw_payment_lines: List[FineosExtractVpeiPaymentLine],
        payment_details: List[PaymentDetails],
        payment: Payment,
        vpei: FineosExtractVpei,
        import_log: ImportLog,
    ) -> None:
        """
        Create payment lines records. The behavior of this mirrors
        the behavior of what we also do in the payment extract step.
        """
        self.add_batch_metric(
            self.Metrics.PAYMENT_LINE_PROCESSED_COUNT, import_log, increment=len(raw_payment_lines)
        )

        if len(raw_payment_lines) == 0:
            # We actually expect this for some scenarios
            # We've seen tax withholding + zero dollar payments
            # not have any payment lines.
            logger.info(
                "No payment lines found for payment",
                extra=self.get_extra(import_log=import_log, payment=payment),
            )
            self.add_batch_metric(self.Metrics.PAYMENT_LINE_NO_RECORDS_COUNT, import_log)
            return

        # Create a mapping for payment detail C/I value
        # as we'll reference it below. This mirrors the
        # behavior for how we do it in the payment extract
        # step already.
        payment_detail_mapping = {}
        for payment_detail in payment_details:
            key = (payment_detail.payment_details_c_value, payment_detail.payment_details_i_value)
            payment_detail_mapping[key] = payment_detail

        do_payment_detail_check = is_payment_detail_expected(payment)

        # Iterate over the raw lines and convert them
        # to payment line records in the DB, connecting
        # them to payment details and the payment.
        for raw_payment_line in raw_payment_lines:
            # This shouldn't happen as we don't come into this method
            # if the payment has any payment lines.
            if raw_payment_line.fineos_extract_import_log_id:
                logger.warning(
                    "Raw payment line was already imported - skipping",
                    extra=self.get_extra(
                        import_log=import_log, payment=payment, raw_payment_line=raw_payment_line
                    ),
                )
                continue

            raw_amount = raw_payment_line.amount_monamt
            raw_c_value = raw_payment_line.c
            raw_i_value = raw_payment_line.i
            raw_line_type = raw_payment_line.linetype

            if (
                raw_amount is None
                or raw_c_value is None
                or raw_i_value is None
                or raw_line_type is None
            ):
                self.add_batch_metric(
                    self.Metrics.PAYMENT_LINE_MISSING_REQUIRED_VALUE_COUNT, import_log
                )
                logger.warning(
                    "Cannot process payment line with null in key value",
                    extra=self.get_extra(
                        import_log=import_log, payment=payment, raw_payment_line=raw_payment_line
                    ),
                )

                continue

            # The other fields we can use raw
            # but need to verify the amount is able to
            # be converted to a decimal.
            amount = None
            try:
                amount = Decimal(raw_amount)
            except Exception:
                self.add_batch_metric(
                    self.Metrics.PAYMENT_LINE_AMOUNT_NON_NUMERIC_COUNT, import_log
                )
                logger.warning(
                    "Cannot convert amount for raw payment line",
                    extra=self.get_extra(
                        import_log=import_log, payment=payment, raw_payment_line=raw_payment_line
                    ),
                )
                continue

            related_payment_detail = payment_detail_mapping.get(
                (raw_payment_line.paymentdetailclassid, raw_payment_line.paymentdetailindexid), None
            )

            payment_line = PaymentLine(
                payment_line_id=uuid.uuid4(),  # Just so the below log has it
                vpei_payment_line_id=raw_payment_line.vpei_payment_line_id,
                payment_id=payment.payment_id,
                payment_details_id=related_payment_detail.payment_details_id
                if related_payment_detail
                else None,
                payment_line_c_value=raw_c_value,
                payment_line_i_value=raw_i_value,
                amount=amount,
                line_type=raw_line_type,
            )

            self.db_session.add(payment_line)

            # Update the import log ID to match the one
            # on the VPEI record of the payment
            raw_payment_line.fineos_extract_import_log_id = vpei.fineos_extract_import_log_id

            extra = self.get_extra(
                import_log=import_log,
                payment=payment,
                payment_detail=related_payment_detail,
                payment_line=payment_line,
                raw_payment_line=raw_payment_line,
            )
            logger.info("Connected payment line to payment", extra=extra)

            # In some cases, we don't expect payment details due to
            # FINEOS not creating them (overpayment recoveries), but
            # log a warning if it happens for other scenarios.
            if not related_payment_detail and do_payment_detail_check:
                logger.warning("Payment detail not found for payment line", extra=extra)
                self.add_batch_metric(
                    self.Metrics.PAYMENT_LINE_DETAIL_MISSING_UNEXPECTED_COUNT, import_log
                )

    def get_extra(
        self,
        import_log: ImportLog,
        payment: Optional[Payment] = None,
        payment_detail: Optional[PaymentDetails] = None,
        payment_line: Optional[PaymentLine] = None,
        raw_payment_detail: Optional[FineosExtractVpeiPaymentDetails] = None,
        raw_payment_line: Optional[FineosExtractVpeiPaymentLine] = None,
    ) -> Dict[str, Any]:
        """
        Utility method for creating an extra object for the
        log messages. There is a lot of info we might want
        in the event there is any anomalies with the backfill.

        Will also allow us to collect patterns in the payment
        line data and just generally provide some interesting metrics.
        """
        extra: Dict[str, Any] = {
            "import_log_id": import_log.import_log_id,
            "import_log_process_time": import_log.end.isoformat() if import_log.end else None,
        }

        if payment:
            extra |= payments_util.get_traceable_payment_details(payment)

        if payment_detail:
            extra |= payments_util.get_traceable_payment_period_details(payment_detail)

        if payment_line:
            extra |= payments_util.get_traceable_payment_line_details(payment_line)

        if raw_payment_detail:
            extra |= {
                "raw_vpei_payment_details_id": raw_payment_detail.vpei_payment_details_id,
                "raw_vpei_payment_details_c_value": raw_payment_detail.c,
                "raw_vpei_payment_details_i_value": raw_payment_detail.i,
                "raw_vpei_payment_details_balancing_amount": raw_payment_detail.balancingamou_monamt,
                "raw_vpei_payment_details_business_net_amount": raw_payment_detail.businessnetbe_monamt,
                "raw_vpei_payment_details_period_start_date": raw_payment_detail.paymentstartp,
                "raw_vpei_payment_details_period_end_date": raw_payment_detail.paymentendper,
                "raw_vpei_payment_details_payment_c_value": raw_payment_detail.peclassid,
                "raw_vpei_payment_details_payment_i_value": raw_payment_detail.peindexid,
                "raw_vpei_payment_details_fineos_extract_import_log_id": raw_payment_detail.fineos_extract_import_log_id,
            }

        if raw_payment_line:
            extra |= {
                "raw_vpei_payment_line_id": raw_payment_line.vpei_payment_line_id,
                "raw_vpei_payment_line_c_value": raw_payment_line.c,
                "raw_vpei_payment_line_i_value": raw_payment_line.i,
                "raw_vpei_payment_line_amount": raw_payment_line.amount_monamt,
                "raw_vpei_payment_line_type": raw_payment_line.linetype,
                "raw_vpei_payment_line_payment_c_value": raw_payment_line.c_pymnteif_paymentlines,
                "raw_vpei_payment_line_payment_i_value": raw_payment_line.i_pymnteif_paymentlines,
                "raw_vpei_payment_line_payment_details_c_value": raw_payment_line.paymentdetailclassid,
                "raw_vpei_payment_line_payment_details_i_value": raw_payment_line.paymentdetailindexid,
                "raw_vpei_payment_line_fineos_extract_import_log_id": raw_payment_line.fineos_extract_import_log_id,
            }

        return extra

    def add_batch_metric(self, name: str, import_log: ImportLog, increment: int = 1) -> None:
        """
        Utility method wrapped around our metric increment method

        Increments the usual metric + a batch metric
        so we can see metrics by import log.

        So, a metric name "metric_count" would
        create something like "batch_1234_metric_count"
        """
        self.increment(name, increment)
        self.increment(f"batch_{import_log.import_log_id}_{name}", increment)


#################
# Utility Methods
#################


def is_payment_detail_expected(payment: Payment) -> bool:
    return (
        payment.payment_transaction_type_id
        not in payments_util.Constants.OVERPAYMENT_TYPES_WITHOUT_PAYMENT_DETAILS_IDS
    )


def payment_detail_matches(
    payment_detail: PaymentDetails, raw_payment_detail: FineosExtractVpeiPaymentDetails
) -> bool:
    amount = str(payment_detail.amount)

    return (
        amount == raw_payment_detail.balancingamou_monamt
        and date_matches(raw_payment_detail.paymentstartp, payment_detail.period_start_date)
        and date_matches(raw_payment_detail.paymentendper, payment_detail.period_end_date)
    )


def date_matches(raw_date: Optional[str], existing_date: Optional[date]) -> bool:
    if not raw_date:
        return False

    if not existing_date:
        return False

    existing_date_str = existing_date.strftime("%Y-%m-%d")

    # FINEOS sends the dates as 2022-03-10 00:00:00
    # and when we process them, we drop the time bit
    # so to find the match, just check the date.
    return raw_date.startswith(existing_date_str)

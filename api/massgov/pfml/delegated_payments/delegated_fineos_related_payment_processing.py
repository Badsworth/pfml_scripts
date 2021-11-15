import enum
from typing import List
from uuid import UUID

from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Claim,
    Flow,
    Payment,
    PaymentTransactionType,
    State,
)
from massgov.pfml.db.models.payments import LinkSplitPayment
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__package__)


class RelatedPaymentsProcessingStep(Step):
    class Metrics(str, enum.Enum):
        FEDERAL_WITHHOLDING_RECORD_COUNT = "federal_withholding_record_count"
        STATE_WITHHOLDING_RECORD_COUNT = "state_withholding_record_count"

    def run_step(self) -> None:
        self.process_payments_for_split_payments()

    def process_payments_for_split_payments(self) -> None:
        """Top-level function that calls all the other functions in this file in order"""
        logger.info("Processing related payment processing step")

        # get withholding payment records
        payments: List[Payment] = self._get_withholding_payments_records()

        if not payments:
            logger.info("No payment records for related payment. Exiting early.")
            return

        for payment in payments:

            if payment.claim is None:
                raise Exception(f"Claim not found for withholding payment id: {payment.payment_id}")
            # get records for the absense id and check for duplicates
            is_duplicate_records_exists = self.is_withholding_records_have_duplicate_records(
                self.db_session, payment, str(payment.claim.fineos_absence_id)
            )

            if is_duplicate_records_exists:
                logger.info("Duplicate records exists for %s", payment.claim.fineos_absence_id)
                # to update status we need payment so getting all the payment details from above query
                # get duplicate payment records
                duplicate_payment_records = (
                    self.db_session.query(Payment)
                    .filter(Payment.claim_id == payment.claim_id)
                    .filter(Payment.period_start_date == payment.period_start_date)
                    .filter(Payment.period_end_date == payment.period_end_date)
                    .filter(Payment.payment_date == payment.payment_date)
                    .filter(Payment.amount == payment.amount)
                    .filter(Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id)
                    .all()
                )

                end_state = (
                    State.STATE_WITHHOLDING_PENDING_AUDIT
                    if (payment.payment_transaction_type_id == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id)
                    else State.FEDERAL_WITHHOLDING_PENDING_AUDIT
                )
                message = "Duplicate records found for the payment."

                for pmnt in duplicate_payment_records:
                    state_log_util.create_finished_state_log(
                        end_state=end_state,
                        outcome=state_log_util.build_outcome(message),
                        associated_model=pmnt,
                        db_session=self.db_session,
                    )
                    logger.info(
                        "Payment added to state %s", end_state.state_description,
                    )
            else:
                primary_payment_record = self._get_primary_payment_record(self.db_session, payment)
                if primary_payment_record == "":
                    raise Exception(
                        f"Primary payment id not found for withholding payment id: {payment.payment_id}"
                    )

                payment_id = primary_payment_record
                related_payment_id = payment.payment_id
                logger.info("payment_id: %s related_payment_id: %s",primary_payment_record,payment.payment_id)
                link_payment = LinkSplitPayment()
                link_payment.payment_id = payment_id
                link_payment.related_payment_id = related_payment_id
                self.db_session.add(link_payment)

    def _get_withholding_payments_records(self) -> List[Payment]:
        """this method appends fedral and state withholding payment records"""
        federal_withholding_payments = self._get_payments_for_federal_withholding(self.db_session)
        state_withholding_payments = self._get_payments_for_state_withholding(self.db_session)
        payment_container = []
        for payment in federal_withholding_payments:
            self.increment(self.Metrics.FEDERAL_WITHHOLDING_RECORD_COUNT)
            payment_container.append(payment)

        for payment in state_withholding_payments:
            self.increment(self.Metrics.STATE_WITHHOLDING_RECORD_COUNT)
            payment_container.append(payment)
        return payment_container

    def _get_payments_for_federal_withholding(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

    def _get_payments_for_state_withholding(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

    # There is possibility we can get duplicate withholding records for same absence id.
    # this function is finding those duplicates. we are setting states as FEDERAL_WITHHOLDING_PENDING_AUDIT
    # or STATE_WITHHOLDING_PENDING_AUDIT and adding it to payment audit report.
    def is_withholding_records_have_duplicate_records(
        self, db_session: db.Session, payment: Payment, fineos_absence_id: str
    ) -> bool:
        num_payments_query = (
            self.db_session.query(
                Claim.fineos_absence_id,
                Payment.period_start_date,
                Payment.period_end_date,
                Payment.payment_date,
                Payment.amount,
                Payment.fineos_extract_import_log_id,
                func.count(Payment.amount).label("records_count"),
            )
            .join(Claim, Payment.claim_id == Claim.claim_id)
            .filter(Claim.claim_id == payment.claim_id)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .filter(Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id)
            .group_by(
                Claim.fineos_absence_id,
                Payment.period_start_date,
                Payment.period_end_date,
                Payment.payment_date,
                Payment.amount,
                Payment.fineos_extract_import_log_id,
            )
            .subquery()
        )
        items = (
            self.db_session.query(num_payments_query)
            .filter(num_payments_query.c.records_count > 1)
            .all()
        )
        return len(items) > 0

    def _get_primary_payment_record(self, db_session: db.Session, payment: Payment) -> UUID:
        primary_payment_id: UUID
        payment_records = (
            db_session.query(Payment)
            .filter(Payment.claim_id == payment.claim_id)
            .filter(Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id)
            .all()
        )
        logger.info("all the payments for claim %s", payment_records)
        for p in payment_records:

            latest_state_log = state_log_util.get_latest_state_log_in_flow(
                p, Flow.DELEGATED_PAYMENT, self.db_session
            )
            if latest_state_log is None:
                raise Exception(
                    f"State log not found for payment id: {payment.payment_id}"
                )
            if latest_state_log.end_state_id not in [
                State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_id,
                State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_id,
                State.STATE_WITHHOLDING_PENDING_AUDIT.state_id,
                State.FEDERAL_WITHHOLDING_PENDING_AUDIT.state_id,
            ]:
                primary_payment_id = p.payment_id
        return primary_payment_id

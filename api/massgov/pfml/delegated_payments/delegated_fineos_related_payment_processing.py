import enum
from typing import Dict, List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Payment, PaymentTransactionType, StateLog
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    LinkSplitPayment,
    LkFineosWritebackTransactionStatus,
)
from massgov.pfml.db.models.state import Flow, LkState, State
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    stage_payment_fineos_writeback,
)
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__package__)


class RelatedPaymentsProcessingStep(Step):
    class Metrics(str, enum.Enum):
        FEDERAL_WITHHOLDING_RECORD_COUNT = "federal_withholding_record_count"
        STATE_WITHHOLDING_RECORD_COUNT = "state_withholding_record_count"
        EMPLOYER_REIMBURSEMENT_RECORD_COUNT = "employer_reimbursement_record_count"
        STANDARD_PAYMENT_RECORD_COUNT = "standard_payment_record_count"

    # End state when we have multiple primary payments
    multiple_primary_states: Dict[int, LkState] = {
        PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id: State.EMPLOYER_REIMBURSEMENT_ERROR,
        PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id: State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT,
        PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id: State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT,
    }

    # End state when we have no primary payments
    primary_not_found_states: Dict[int, LkState] = {
        PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id: State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id: State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT,
        PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id: State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT,
    }

    # End state when we have primary payment in restartable state
    primary_in_restartable_states: Dict[int, LkState] = {
        PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id: State.DELEGATED_PAYMENT_CASCADED_ERROR_RESTARTABLE,
        PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id: State.STATE_WITHHOLDING_ERROR_RESTARTABLE,
        PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id: State.FEDERAL_WITHHOLDING_ERROR_RESTARTABLE,
    }

    # End state when we have primary payment in errored state
    primary_in_error_states: Dict[int, LkState] = {
        PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id: State.DELEGATED_PAYMENT_CASCADED_ERROR,
        PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id: State.STATE_WITHHOLDING_ERROR,
        PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id: State.FEDERAL_WITHHOLDING_ERROR,
    }

    LIST_OF_RELATED_TRANSACTION_TYPE_IDS = [
        PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id,
    ]

    def run_step(self) -> None:
        """Top-level function that calls all the other functions in this file in order"""
        logger.info("Processing related payment processing step")

        self.sync_primary_to_related_payments()
        self.sync_related_payments_to_primary()

    def sync_primary_to_related_payments(self) -> None:
        logger.info("Processing primary to related payment processing")

        standard_payments: List[Payment] = self._get_standard_payments(self.db_session)

        for payment in standard_payments:
            extra = payments_util.get_traceable_payment_details(payment)
            logger.info("Processing standard payment in related payment processor", extra=extra)
            self.increment(self.Metrics.STANDARD_PAYMENT_RECORD_COUNT)
            if payment.claim is None:
                raise Exception("Claim not found for standard payment id: %s ", payment.payment_id)

            related_payment_records: List[Payment] = (
                self.db_session.query(Payment)
                .filter(Payment.claim_id == payment.claim_id)
                .filter(Payment.period_start_date >= payment.period_start_date)
                .filter(Payment.period_end_date <= payment.period_end_date)
                .filter(
                    Payment.payment_transaction_type_id.in_(
                        self.LIST_OF_RELATED_TRANSACTION_TYPE_IDS
                    )
<<<<<<< HEAD
                )
                .filter(
                    Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id
                )
                .all()
            )

            # If we have more than one Employer Reimbursement payment : set standard payment state to error
            if len(related_payment_records) > 1:
                message = "Duplicate employer reimbursement payments exists for primary payment."

                logger.info(
                    message,
                    extra=extra,
                )

                end_state = State.DELEGATED_PAYMENT_CASCADED_ERROR

                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s",
                    end_state.state_description,
                    extra=extra,
                )
                continue

            # If we do not have employer reimbursement payments. continue
            if len(related_payment_records) != 1:
                continue

            # Otherwise we will have one employer reimbursement payment
            # if it is employer reimbursement payment get the state of the payment
            # if the employer reimbursement state is in error state , set the primary payment state to error and create writeback.
            related_payment = related_payment_records[0]
            if (
                related_payment.payment_transaction_type_id
                != PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
            ):
                continue

            related_payment_state_log = state_log_util.get_latest_state_log_in_flow(
                related_payment, Flow.DELEGATED_PAYMENT, self.db_session
            )
            if related_payment_state_log is None:
                raise Exception(
                    "State log record not found for the related payment id: %s",
                    related_payment.payment_id,
                )

            if (
                related_payment_state_log.end_state_id
                != State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING.state_id
            ):
                if (
                    related_payment_state_log.end_state_id
                    in payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS
                ):
                    end_state = State.DELEGATED_PAYMENT_CASCADED_ERROR_RESTARTABLE
                else:
                    end_state = State.DELEGATED_PAYMENT_CASCADED_ERROR

                transaction_status: Optional[
                    LkFineosWritebackTransactionStatus
                ] = self._get_payment_writeback_transaction_status(related_payment)

                message = (
                    "Employer reimbursement failed validation, need to wait for it to be fixed."
                )
                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s",
                    end_state.state_description,
                    extra=extra,
                )

                related_payment_log_details = payments_util.get_traceable_payment_details(
                    related_payment
=======
>>>>>>> origin
                )
                .filter(
                    Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id
                )
                .all()
            )

            # Otherwise we will have one or more employer reimbursement payments
            # if it is employer reimbursement payment get the state of the payment
            # if the employer reimbursement state is in error state , set the primary payment state to error and create writeback.
            for related_payment in related_payment_records:
                if (
                    related_payment.payment_transaction_type_id
                    != PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
                ):
                    continue
                related_payment_state_log = state_log_util.get_latest_state_log_in_flow(
                    related_payment, Flow.DELEGATED_PAYMENT, self.db_session
                )
                if related_payment_state_log is None:
                    raise Exception(
                        "State log record not found for the related payment id: %s",
                        related_payment.payment_id,
                    )
                if (
                    related_payment_state_log.end_state_id
                    != State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING.state_id
                ):
                    if (
                        related_payment_state_log.end_state_id
                        in payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS
                    ):
                        end_state = State.DELEGATED_PAYMENT_CASCADED_ERROR_RESTARTABLE
                    else:
                        end_state = State.DELEGATED_PAYMENT_CASCADED_ERROR

                    transaction_status: Optional[
                        LkFineosWritebackTransactionStatus
                    ] = self._get_payment_writeback_transaction_status(related_payment)

                    message = (
                        "Employer reimbursement failed validation, need to wait for it to be fixed."
                    )
                    state_log_util.create_finished_state_log(
                        end_state=end_state,
                        outcome=state_log_util.build_outcome(message),
                        associated_model=payment,
                        db_session=self.db_session,
                    )
                    logger.info(
                        "Payment added to state %s",
                        end_state.state_description,
                        extra=extra,
                    )

                    related_payment_log_details = payments_util.get_traceable_payment_details(
                        related_payment
                    )

                    if transaction_status:
                        stage_payment_fineos_writeback(
                            payment=payment,
                            writeback_transaction_status=transaction_status,
                            outcome=state_log_util.build_outcome(message),
                            db_session=self.db_session,
                            import_log_id=self.get_import_log_id(),
                        )
                        logger.info(
                            "Primary payment errored because related payment has %s",
                            transaction_status.transaction_status_description,
                            extra=related_payment_log_details,
                        )
                    else:
                        logger.error(
                            "Writeback details not found for the related payment",
                            extra=related_payment_log_details,
                        )

    def _get_standard_payments(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

    def sync_related_payments_to_primary(self) -> None:
        # get employer reimbursement and withholding payment records
        related_payments: List[Payment] = self._get_related_payments()

        if not related_payments:
            logger.info("No related payment records found.")
            return
        for payment in related_payments:

            if payment.claim is None:
                raise Exception("Claim not found for related payment id: %s ", payment.payment_id)

                if transaction_status:
                    stage_payment_fineos_writeback(
                        payment=payment,
                        writeback_transaction_status=transaction_status,
                        outcome=state_log_util.build_outcome(message),
                        db_session=self.db_session,
                        import_log_id=self.get_import_log_id(),
                    )
                    logger.info(
                        "Primary payment errored because related payment has %s",
                        transaction_status.transaction_status_description,
                        extra=related_payment_log_details,
                    )
                else:
                    logger.error(
                        "Writeback details not found for the related payment",
                        extra=related_payment_log_details,
                    )

    def _get_standard_payments(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

    def sync_related_payments_to_primary(self) -> None:
        # get employer reimbursement and withholding payment records
        related_payments: List[Payment] = self._get_related_payments()

        if not related_payments:
            logger.info("No related payment records found.")
            return
        for payment in related_payments:

            if payment.claim is None:
                raise Exception("Claim not found for related payment id: %s ", payment.payment_id)

            primary_payment_records: List[Payment] = (
                self.db_session.query(Payment)
                .filter(Payment.claim_id == payment.claim_id)
                .filter(Payment.period_start_date <= payment.period_start_date)
                .filter(Payment.period_end_date >= payment.period_end_date)
                .filter(
                    Payment.payment_transaction_type_id
                    == PaymentTransactionType.STANDARD.payment_transaction_type_id
                )
                .filter(
                    Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id
                )
                .all()
            )
            transaction_type_id = (
                payment.payment_transaction_type_id
                if payment.payment_transaction_type_id is not None
                else 0
            )
            payment_log_details = payments_util.get_traceable_payment_details(payment)
            if len(primary_payment_records) > 1:
                logger.info(
                    "Duplicate primary records exist for related payment %s",
                    payment.claim.fineos_absence_id,
                    extra=payment_log_details,
                )
                # set end state
                end_state = self.multiple_primary_states[transaction_type_id]
                message = "Duplicate records found for the related payment."

                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s",
                    end_state.state_description,
                    extra=payments_util.get_traceable_payment_details(payment, end_state),
                )
                message = "Duplicate primary payment records found for the related payment record."
                # do we have to do audit
            elif len(primary_payment_records) == 0:
                logger.info(
                    "No primary payment record exists for related payment %s",
                    payment.claim.fineos_absence_id,
                    extra=payment_log_details,
                )

                # set correct state
                end_state = self.primary_not_found_states[transaction_type_id]

                message = "No primary payment found for the related payment record."

                state_log_util.create_finished_state_log(
                    end_state=end_state,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=self.db_session,
                )
                logger.info(
                    "Payment added to state %s",
                    end_state.state_description,
                    extra=payments_util.get_traceable_payment_details(payment, end_state),
                )
            else:
                primary_payment_record = primary_payment_records[0].payment_id
                if primary_payment_record == "":
                    raise Exception(
                        f"Primary payment id not found for related payment id: {payment.payment_id}"
                    )

                link_payment = LinkSplitPayment(
                    payment_id=primary_payment_record, related_payment_id=payment.payment_id
                )
                self.db_session.add(link_payment)

                logger.info(
                    "Added related payment to link_payment: Primary payment id %s , Related Payment Id %s",
                    primary_payment_record,
                    payment.payment_id,
                    extra=payment_log_details,
                )

                #  If primary payment has any validation error set related payment state to error
                payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
                    primary_payment_records[0], Flow.DELEGATED_PAYMENT, self.db_session
                )
                if payment_state_log is None:
                    raise Exception(
                        "State log record not found for the primary payment id: %s",
                        primary_payment_records[0].payment_id,
                    )
                if (
                    payment_state_log.end_state_id
                    != State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
                ):
                    if (
                        payment_state_log.end_state_id
                        in payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS
                    ):
                        end_state = self.primary_in_restartable_states[transaction_type_id]

                        outcome = state_log_util.build_outcome(
                            "Primary payment is in Error restartable state"
                        )

                        outcome = state_log_util.build_outcome(
                            "Primary payment is in Error restartable state"
                        )
                    else:
                        end_state = self.primary_in_error_states[transaction_type_id]

                        outcome = state_log_util.build_outcome("Primary payment has an error")
                    state_log_util.create_finished_state_log(
                        associated_model=payment,
                        end_state=end_state,
                        outcome=outcome,
                        db_session=self.db_session,
                    )
                    logger.info(
                        "Payment added to state %s",
                        end_state.state_description,
                        extra=payments_util.get_traceable_payment_details(payment, end_state),
                    )
                    # Get the writeback status of the standard payment
                    # Cascade standard writeback status to employer reimbursement payment
                    transaction_status: Optional[
                        LkFineosWritebackTransactionStatus
                    ] = self._get_payment_writeback_transaction_status(primary_payment_records[0])
                    if transaction_status:
                        message = "Employer reimbursement record error due to an issue with the primary payment."
                        stage_payment_fineos_writeback(
                            payment=payment,
                            writeback_transaction_status=transaction_status,
                            outcome=state_log_util.build_outcome(message),
                            db_session=self.db_session,
                            import_log_id=self.get_import_log_id(),
                        )
                    else:
                        primary_payment_log_details = payments_util.get_traceable_payment_details(
                            primary_payment_records[0]
                        )
                        logger.info(
                            "Writeback details not found for the primary payment",
                            extra=primary_payment_log_details,
                        )

    def _get_payment_writeback_transaction_status(
        self, payment: Payment
    ) -> Optional[LkFineosWritebackTransactionStatus]:
        writeback_details = (
            self.db_session.query(FineosWritebackDetails)
            .filter(FineosWritebackDetails.payment_id == payment.payment_id)
            .order_by(FineosWritebackDetails.created_at.desc())
            .first()
        )

        if writeback_details is None:
            return None

        writeback_details.writeback_sent_at = get_now_us_eastern()

        return writeback_details.transaction_status

    def _get_related_payments(self) -> List[Payment]:
        """this method appends fedral, state withholding and employer reimbursement payment records"""
        federal_withholding_payments = self._get_payments_for_federal_withholding(self.db_session)
        state_withholding_payments = self._get_payments_for_state_withholding(self.db_session)
        employer_reimbursement_payments = self._get_employer_reimbursement_payment_records(
            self.db_session
        )
        payment_container = []
        for payment in federal_withholding_payments:
            self.increment(self.Metrics.FEDERAL_WITHHOLDING_RECORD_COUNT)
            payment_container.append(payment)

        for payment in state_withholding_payments:
            self.increment(self.Metrics.STATE_WITHHOLDING_RECORD_COUNT)
            payment_container.append(payment)

        for payment in employer_reimbursement_payments:
            self.increment(self.Metrics.EMPLOYER_REIMBURSEMENT_RECORD_COUNT)
            payment_container.append(payment)

        return payment_container

    def _get_employer_reimbursement_payment_records(self, db_session: db.Session) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING,
            db_session=db_session,
        )
        return [state_log.payment for state_log in state_logs]

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

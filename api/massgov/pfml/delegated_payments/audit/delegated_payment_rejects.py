import csv
import enum
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Flow,
    LkState,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


# Not sampled payment next states
@dataclass
class NonSampledStateTransitionDescriptor:
    from_state: LkState
    to_state: LkState
    outcome: Dict[str, Any]


NOT_SAMPLED_STATE_TRANSITIONS: List[NonSampledStateTransitionDescriptor] = []

NOT_SAMPLED_STATE_TRANSITIONS.append(
    NonSampledStateTransitionDescriptor(
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        State.DELEGATED_PAYMENT_VALIDATED,
        state_log_util.build_outcome(
            "Accepted payment to be added to FINEOS Writeback - not sampled"
        ),
    )
)


NOT_SAMPLED_PAYMENT_NEXT_STATE_BY_CURRENT_STATE = {
    t.from_state.state_id: t.to_state for t in NOT_SAMPLED_STATE_TRANSITIONS
}
NOT_SAMPLED_PAYMENT_OUTCOME_BY_CURRENT_STATE = {
    t.from_state.state_id: t.outcome for t in NOT_SAMPLED_STATE_TRANSITIONS
}

NOT_SAMPLED_PENDING_STATES: List[LkState] = [st.from_state for st in NOT_SAMPLED_STATE_TRANSITIONS]
NOT_SAMPLED_PENDING_STATE_IDS: List[int] = [st.state_id for st in NOT_SAMPLED_PENDING_STATES]

# Sampled payment next states
ACCEPTED_STATE = State.DELEGATED_PAYMENT_VALIDATED
ACCEPTED_OUTCOME = state_log_util.build_outcome(
    "Accepted payment to be added to FINEOS Writeback - sampled"
)


class PaymentRejectsException(Exception):
    """An error during Payment Rejects file processing."""


def get_row(row: Dict[str, str], key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    return row.get(key, None)


class PaymentRejectsStep(Step):
    class Metrics(str, enum.Enum):
        ACCEPTED_PAYMENT_COUNT = "accepted_payment_count"
        PARSED_ROWS_COUNT = "parsed_rows_count"
        PAYMENT_STATE_LOG_MISSING_COUNT = "payment_state_log_missing_count"
        PAYMENT_STATE_LOG_NOT_IN_AUDIT_RESPONSE_PENDING_COUNT = (
            "payment_state_log_not_in_audit_response_pending_count"
        )
        REJECTED_PAYMENT_COUNT = "rejected_payment_count"
        SKIPPED_PAYMENT_COUNT = "skipped_payment_count"
        STATE_LOGS_COUNT = "state_logs_count"

    def __init__(
        self,
        db_session: db.Session,
        log_entry_db_session: db.Session,
        payment_rejects_folder_path: str = "",
    ) -> None:
        """Constructor."""
        super().__init__(db_session, log_entry_db_session)

        self.payment_rejects_folder_path = payment_rejects_folder_path
        if not payment_rejects_folder_path:
            s3_config = payments_config.get_s3_config()
            self.payment_rejects_folder_path = s3_config.pfml_payment_rejects_archive_path
            self.payment_rejects_received_folder_path = os.path.join(
                self.payment_rejects_folder_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
            )

    def run_step(self) -> None:
        self.process_rejects()

    def parse_payment_rejects_file(self, file_path: str) -> List[PaymentAuditCSV]:
        with file_util.open_stream(file_path) as csvfile:
            parsed_csv = csv.DictReader(csvfile)

            payment_rejects_rows: List[PaymentAuditCSV] = []

            for row in parsed_csv:
                payment_reject_row = PaymentAuditCSV(
                    pfml_payment_id=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id),
                    leave_type=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.leave_type),
                    fineos_customer_number=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.fineos_customer_number
                    ),
                    first_name=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.first_name),
                    last_name=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.last_name),
                    address_line_1=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.address_line_1),
                    address_line_2=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.address_line_2),
                    city=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.city),
                    state=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.state),
                    zip=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.zip),
                    is_address_verified=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.is_address_verified),
                    payment_preference=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.payment_preference),
                    scheduled_payment_date=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.scheduled_payment_date
                    ),
                    payment_period_start_date=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.payment_period_start_date
                    ),
                    payment_period_end_date=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.payment_period_end_date
                    ),
                    payment_period_weeks=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.payment_period_weeks
                    ),
                    payment_amount=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.payment_amount),
                    absence_case_number=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.absence_case_number),
                    c_value=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.c_value),
                    i_value=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.i_value),
                    employer_id=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.employer_id),
                    absence_case_creation_date=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.absence_case_creation_date
                    ),
                    case_status=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.case_status),
                    leave_request_decision=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.leave_request_decision
                    ),
                    check_description=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.check_description),
                    is_first_time_payment=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.is_first_time_payment
                    ),
                    previously_errored_payment_count=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.previously_errored_payment_count
                    ),
                    previously_rejected_payment_count=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.previously_rejected_payment_count
                    ),
                    previously_skipped_payment_count=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.previously_skipped_payment_count
                    ),
                    max_weekly_benefits_details=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.max_weekly_benefits_details
                    ),
                    dua_dia_reduction_details=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.dua_dia_reduction_details
                    ),
                    rejected_by_program_integrity=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity
                    ),
                    skipped_by_program_integrity=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity
                    ),
                    rejected_notes=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.rejected_notes),
                )
                payment_rejects_rows.append(payment_reject_row)

        return payment_rejects_rows

    def transition_audit_pending_payment_state(
        self,
        payment: Payment,
        is_rejected_payment: bool,
        is_skipped_payment: bool,
        rejected_notes: Optional[str] = None,
    ) -> None:
        payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, self.db_session
        )

        if payment_state_log is None:
            self.increment(self.Metrics.PAYMENT_STATE_LOG_MISSING_COUNT)
            raise PaymentRejectsException(
                f"No state log found for payment found in audit reject file: {payment.payment_id}"
            )

        if (
            payment_state_log.end_state_id
            != State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT.state_id
        ):
            self.increment(self.Metrics.PAYMENT_STATE_LOG_NOT_IN_AUDIT_RESPONSE_PENDING_COUNT)
            raise PaymentRejectsException(
                f"Found payment state log not in audit response pending state: {payment_state_log.end_state.state_description if payment_state_log.end_state else None}, payment_id: {payment.payment_id}"
            )

        if is_rejected_payment:
            self.increment(self.Metrics.REJECTED_PAYMENT_COUNT)
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
                state_log_util.build_outcome(f"Payment rejected with notes: {rejected_notes}"),
                self.db_session,
            )

            writeback_transaction_status = FineosWritebackTransactionStatus.FAILED_MANUAL_VALIDATION
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
                state_log_util.build_outcome(
                    cast(str, writeback_transaction_status.transaction_status_description,)
                ),
                self.db_session,
            )
            writeback_details = FineosWritebackDetails(
                payment=payment,
                transaction_status_id=writeback_transaction_status.transaction_status_id,
                import_log_id=self.get_import_log_id(),
            )
            self.db_session.add(writeback_details)
        elif is_skipped_payment:
            self.increment(self.Metrics.SKIPPED_PAYMENT_COUNT)
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
                state_log_util.build_outcome("Payment skipped"),
                self.db_session,
            )

            writeback_transaction_status = FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
                state_log_util.build_outcome(
                    cast(str, writeback_transaction_status.transaction_status_description,)
                ),
                self.db_session,
            )
            writeback_details = FineosWritebackDetails(
                payment=payment,
                transaction_status_id=writeback_transaction_status.transaction_status_id,
                import_log_id=self.get_import_log_id(),
            )
            self.db_session.add(writeback_details)
        else:
            self.increment(self.Metrics.ACCEPTED_PAYMENT_COUNT)
            state_log_util.create_finished_state_log(
                payment, ACCEPTED_STATE, ACCEPTED_OUTCOME, self.db_session
            )

    def transition_audit_pending_payment_states(
        self, payment_rejects_rows: List[PaymentAuditCSV]
    ) -> None:
        for payment_rejects_row in payment_rejects_rows:
            if payment_rejects_row.pfml_payment_id is None:
                raise PaymentRejectsException("Missing payment id column in rejects file.")

            if payment_rejects_row.rejected_by_program_integrity is None:
                raise PaymentRejectsException("Missing rejection column in rejects file.")

            if payment_rejects_row.skipped_by_program_integrity is None:
                raise PaymentRejectsException("Missing skip column in rejects file.")

            payment = (
                self.db_session.query(Payment)
                .filter(Payment.payment_id == payment_rejects_row.pfml_payment_id)
                .one_or_none()
            )

            if payment is None:
                raise PaymentRejectsException(
                    f"Could not find payment from rejects file in DB: {payment_rejects_row.pfml_payment_id}"
                )

            is_rejected_payment = payment_rejects_row.rejected_by_program_integrity == "Y"
            is_skipped_payment = payment_rejects_row.skipped_by_program_integrity == "Y"

            if is_rejected_payment and is_skipped_payment:
                raise PaymentRejectsException(
                    "Unexpected state - rejects row both rejected and skipped."
                )

            rejected_notes = payment_rejects_row.rejected_notes

            self.transition_audit_pending_payment_state(
                payment, is_rejected_payment, is_skipped_payment, rejected_notes
            )

    def _transition_not_sampled_payment_audit_pending_state(self, pending_state: LkState) -> None:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT, pending_state, self.db_session
        )
        state_log_count = len(state_logs)
        if state_log_count == 0:
            logger.info(
                "No payments found in state %s, nothing to transition",
                pending_state.state_description,
            )
            return

        next_state = NOT_SAMPLED_PAYMENT_NEXT_STATE_BY_CURRENT_STATE[pending_state.state_id]
        outcome = NOT_SAMPLED_PAYMENT_OUTCOME_BY_CURRENT_STATE[pending_state.state_id]

        logger.info(
            "%i payments found for state %s, moving them to %s",
            state_log_count,
            pending_state.state_description,
            next_state.state_description,
        )

        for state_log in state_logs:
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise PaymentRejectsException(
                    f"A state log was found without a payment while processing rejects: {state_log.state_log_id}"
                )

            state_log_util.create_finished_state_log(payment, next_state, outcome, self.db_session)

        logger.info(
            "Successfully moved %i state logs from %s to %s",
            state_log_count,
            pending_state.state_description,
            next_state.state_description,
        )

    def transition_not_sampled_payment_audit_pending_states(self):
        logger.info("Start transition of not sampled payment audit pending states")

        for pending_state in NOT_SAMPLED_PENDING_STATES:
            self._transition_not_sampled_payment_audit_pending_state(pending_state)

        logger.info("Completed transition of not sampled payment audit pending states")

    def get_rejects_files_to_process(self) -> List[str]:
        return file_util.list_files(self.payment_rejects_received_folder_path)

    def process_rejects_and_send_report(self) -> None:
        rejects_files = self.get_rejects_files_to_process()

        if len(rejects_files) == 0:
            raise PaymentRejectsException("No Payment Rejects file found.")

        if len(rejects_files) > 1:
            rejects_files.sort()
            rejects_file_names = ", ".join(rejects_files)
            raise PaymentRejectsException(
                f"Too many Payment Rejects files found: {rejects_file_names}"
            )

        # process the file
        rejects_file_name = rejects_files[0]
        payment_rejects_file_path = os.path.join(
            self.payment_rejects_received_folder_path, rejects_file_name
        )

        logger.info("Start processing Payment Rejects file: %s", payment_rejects_file_path)

        # parse the rejects file
        payment_rejects_rows: List[PaymentAuditCSV] = self.parse_payment_rejects_file(
            payment_rejects_file_path,
        )
        parsed_rows_count = len(payment_rejects_rows)
        self.set_metrics({self.Metrics.PARSED_ROWS_COUNT: parsed_rows_count})
        logger.info("Parsed %i payment rejects rows", parsed_rows_count)

        # check if returned rows match expected number in our state log
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            self.db_session,
        )
        state_log_count = len(state_logs)
        self.set_metrics({self.Metrics.STATE_LOGS_COUNT: state_log_count})

        if state_log_count != parsed_rows_count:
            raise PaymentRejectsException(
                f"Unexpected number of parsed Payment Rejects file rows - found: {parsed_rows_count}, expected: {state_log_count}"
            )

        # transition audit pending sampled states
        self.transition_audit_pending_payment_states(payment_rejects_rows)

        # transition non sampled states
        self.transition_not_sampled_payment_audit_pending_states()

        # put file in processed folder
        processed_file_path = payments_util.build_archive_path(
            self.payment_rejects_folder_path,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
            rejects_file_name,
        )
        file_util.rename_file(payment_rejects_file_path, processed_file_path)
        logger.info("Payment Rejects file in processed folder: %s", processed_file_path)

        # create reference file
        reference_file = ReferenceFile(
            file_location=processed_file_path,
            reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_REJECTS.reference_file_type_id,
        )
        self.db_session.add(reference_file)

        logger.info(
            "Created reference file for Payment Rejects file: %s", reference_file.file_location
        )

        logger.info("Done processing Payment Rejects file: %s", payment_rejects_file_path)

    def move_rejects_file_to_error_archive_folder(self, payment_rejects_archive_path: str) -> None:
        rejects_files = self.get_rejects_files_to_process()

        for rejects_file_name in rejects_files:
            payment_rejects_file_path = os.path.join(
                self.payment_rejects_received_folder_path, rejects_file_name
            )

            errored_file_path = payments_util.build_archive_path(
                payment_rejects_archive_path,
                payments_util.Constants.S3_INBOUND_ERROR_DIR,
                rejects_file_name,
            )

            file_util.rename_file(payment_rejects_file_path, errored_file_path)
            logger.warning("Payment Rejects file moved to errored folder: %s", errored_file_path)

        logger.info(
            "Done moving Payment Rejects files to error folder: %s", ", ".join(rejects_files)
        )

    def process_rejects(self):
        """Top level function to process payments rejects"""

        try:
            logger.info("Start processing payment rejects")

            s3_config = payments_config.get_s3_config()

            self.process_rejects_and_send_report()

            self.db_session.commit()

            logger.info("Done processing payment rejects")

        except Exception:
            self.db_session.rollback()
            logger.exception("Error processing Payment Rejects file")

            self.move_rejects_file_to_error_archive_folder(
                s3_config.pfml_payment_rejects_archive_path
            )

            # We do not want to run any subsequent steps if this fails
            raise

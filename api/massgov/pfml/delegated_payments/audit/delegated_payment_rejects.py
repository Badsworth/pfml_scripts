import csv
import os
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Flow,
    LkState,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    write_audit_report_rows,
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
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,
        State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK,
        state_log_util.build_outcome("Cancelled payment to be added to FINEOS Writeback"),
    )
)

NOT_SAMPLED_STATE_TRANSITIONS.append(
    NonSampledStateTransitionDescriptor(
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT,
        State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK,
        state_log_util.build_outcome("$0 payment to be added to FINEOS Writeback"),
    )
)

NOT_SAMPLED_STATE_TRANSITIONS.append(
    NonSampledStateTransitionDescriptor(
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT,
        State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK,
        state_log_util.build_outcome("Overpayment to be added to FINEOS Writeback"),
    )
)

NOT_SAMPLED_STATE_TRANSITIONS.append(
    NonSampledStateTransitionDescriptor(
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_EMPLOYER_REIMBURSEMENT,
        State.DELEGATED_PAYMENT_ADD_EMPLOYER_REIMBURSEMENT_PAYMENT_TO_FINEOS_WRITEBACK,
        state_log_util.build_outcome("Employer reimbursement to be added to FINEOS Writeback"),
    )
)

NOT_SAMPLED_STATE_TRANSITIONS.append(
    NonSampledStateTransitionDescriptor(
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        State.DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK,
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
ACCEPTED_STATE = State.DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK
ACCEPTED_OUTCOME = state_log_util.build_outcome(
    "Accepted payment to be added to FINEOS Writeback - sampled"
)


class PaymentRejectsException(Exception):
    """An error during Payment Rejects file processing."""


def get_row(row: Dict[str, str], key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    return row[key]


class PaymentRejectsStep(Step):
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
                    first_name=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.first_name),
                    last_name=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.last_name),
                    address_line_1=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.address_line_1),
                    address_line_2=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.address_line_2),
                    city=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.city),
                    state=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.state),
                    zip=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.zip),
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
                    payment_amount=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.payment_amount),
                    absence_case_number=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.absence_case_number),
                    c_value=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.c_value),
                    i_value=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.i_value),
                    employer_id=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.employer_id),
                    case_status=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.case_status),
                    is_first_time_payment=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.is_first_time_payment
                    ),
                    is_previously_errored_payment=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.is_previously_errored_payment
                    ),
                    is_previously_rejected_payment=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.is_previously_rejected_payment
                    ),
                    number_of_times_in_rejected_or_error_state=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.number_of_times_in_rejected_or_error_state
                    ),
                    rejected_by_program_integrity=get_row(
                        row, PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity
                    ),
                    rejected_notes=get_row(row, PAYMENT_AUDIT_CSV_HEADERS.rejected_notes),
                )
                payment_rejects_rows.append(payment_reject_row)

        return payment_rejects_rows

    def transition_audit_pending_payment_state(
        self, payment: Payment, is_rejected_payment: bool
    ) -> None:
        payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, self.db_session
        )

        if payment_state_log is None:
            raise PaymentRejectsException(
                f"No state log found for payment found in audit reject file: {payment.payment_id}"
            )

        if (
            payment_state_log.end_state_id
            != State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT.state_id
        ):
            raise PaymentRejectsException(
                f"Found payment state log not in audit response pending state: {payment_state_log.end_state.state_description if payment_state_log.end_state else None}, payment_id: {payment.payment_id}"
            )

        if is_rejected_payment:
            self.increment("rejected_payment_count")
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
                state_log_util.build_outcome("Payment rejected"),
                self.db_session,
            )
        else:
            self.increment("accepted_payment_count")
            state_log_util.create_finished_state_log(
                payment, ACCEPTED_STATE, ACCEPTED_OUTCOME, self.db_session
            )

    def transition_audit_pending_payment_states(
        self, payment_rejects_rows: List[PaymentAuditCSV]
    ) -> None:
        for payment_rejects_row in payment_rejects_rows:
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

            self.transition_audit_pending_payment_state(payment, is_rejected_payment)

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

    def transition_rejected_payments_to_sent_state(self):
        logger.info("Start transition of rejected payments to sent state")

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
            self.db_session,
        )
        state_log_count = len(state_logs)

        logger.info(
            "%i payments found for state %s, moving them to %s",
            state_log_count,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT.state_description,
            State.DELEGATED_PAYMENT_PAYMENT_REJECT_REPORT_SENT.state_description,
        )

        for state_log in state_logs:
            payment = state_log.payment

            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_PAYMENT_REJECT_REPORT_SENT,
                state_log_util.build_outcome("Payment Reject Report sent"),
                self.db_session,
            )

        logger.info(
            "Successfully moved %i state logs from %s to %s",
            state_log_count,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT.state_description,
            State.DELEGATED_PAYMENT_PAYMENT_REJECT_REPORT_SENT.state_description,
        )

    def process_rejects_and_send_report(
        self,
        payment_rejects_received_folder_path: str,
        payment_rejects_processed_folder_path: str,
        payment_rejects_report_outbound_folder: str,
        payment_rejects_report_sent_folder_path: str,
    ) -> None:
        # TODO Confirm we should look in a dated folder? if so today or yesterday's date?
        payment_rejects_received_folder_dated_path = os.path.join(
            payment_rejects_received_folder_path, payments_util.get_now().strftime("%Y-%m-%d")
        )
        rejects_files = file_util.list_files(payment_rejects_received_folder_dated_path)

        if len(rejects_files) == 0:
            raise PaymentRejectsException("No Payment Rejects file found.")

        if len(rejects_files) > 1:
            rejects_file_names = ", ".join(rejects_files)
            raise PaymentRejectsException(
                f"Too many Payment Rejects files found: {rejects_file_names}"
            )

        # process the file
        rejects_file_name = rejects_files[0]
        payment_rejects_file_path = os.path.join(
            payment_rejects_received_folder_dated_path, rejects_file_name
        )

        logger.info("Start processing Payment Rejects file: %s", payment_rejects_file_path)

        # parse the rejects file
        payment_rejects_rows: List[PaymentAuditCSV] = self.parse_payment_rejects_file(
            payment_rejects_file_path,
        )
        parsed_rows_count = len(payment_rejects_rows)

        logger.info("Parsed %i payment rejects rows", parsed_rows_count)

        # check if returned rows match expected number in our state log
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            self.db_session,
        )
        state_log_count = len(state_logs)
        if state_log_count != parsed_rows_count:
            raise PaymentRejectsException(
                f"Unexpected number of parsed Payment Rejects file rows - found: {parsed_rows_count}, expected: {state_log_count}"
            )

        # transition audit pending sampled states
        self.transition_audit_pending_payment_states(payment_rejects_rows)

        # transition non sampled states
        self.transition_not_sampled_payment_audit_pending_states()

        # put file in processed folder
        processed_file_path = os.path.join(
            payment_rejects_processed_folder_path,
            payments_util.get_now().strftime("%Y-%m-%d"),
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

        # create and send Payment Rejects Report file
        # TODO split this out and use state? we'll need to figure out how to get derived data to mirror PaymentAuditData

        logger.info("Creating Payment Rejects Report file")

        rejected_payment_rows: List[PaymentAuditCSV] = list(
            filter(
                lambda payment_rejects_row: payment_rejects_row.rejected_by_program_integrity
                == "Y",
                payment_rejects_rows,
            )
        )

        # write to outbound folder
        outbound_file_path = write_audit_report_rows(
            rejected_payment_rows,
            payment_rejects_report_outbound_folder,
            self.db_session,
            report_name="Payment-Rejects-Report",
        )

        if outbound_file_path is None:
            raise Exception("Payment rejects file not written to outbound folder")

        logger.info(
            "Done writing Payment Rejects Report file to outbound folder: %s", outbound_file_path
        )

        # also write it to the outbund folder
        send_file_path: Optional[pathlib.Path] = write_audit_report_rows(
            rejected_payment_rows,
            payment_rejects_report_sent_folder_path,
            self.db_session,
            report_name="Payment-Rejects-Report",
        )

        if send_file_path is None:
            raise Exception("Payment rejects file not written to sent folder")

        logger.info("Done writing Payment Rejects Report file to sent folder: %s", send_file_path)

        # transition state for rejected files
        self.transition_rejected_payments_to_sent_state()

        # create a reference file
        reference_file = ReferenceFile(
            file_location=str(send_file_path),
            reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_REJECTS_REPORT.reference_file_type_id,
        )
        self.db_session.add(reference_file)

        logger.info(
            "Created reference file for Payment Rejects Report file: %s",
            reference_file.file_location,
        )

        logger.info("Done processing Payment Rejects file: %s", payment_rejects_file_path)

    def process_rejects(self):
        """Top level function to process payments rejects"""

        try:
            logger.info("Start processing payment rejects")

            s3_config = payments_config.get_s3_config()

            self.process_rejects_and_send_report(
                s3_config.payment_rejects_received_folder_path,
                s3_config.payment_rejects_processed_folder_path,
                s3_config.payment_rejects_report_outbound_folder,
                s3_config.payment_rejects_report_sent_folder_path,
            )

            self.db_session.commit()

            logger.info("Done processing payment rejects")

        except Exception:
            self.db_session.rollback()
            logger.exception("Error processing Payment Rejects file")

            # We do not want to run any subsequent steps if this fails
            raise

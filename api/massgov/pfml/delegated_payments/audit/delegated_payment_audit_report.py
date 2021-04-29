import enum
import os
from typing import Iterable, List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Flow,
    LatestStateLog,
    LkState,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    PaymentAuditData,
    write_audit_report,
)
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


class PaymentAuditError(Exception):
    """An error in a row that prevents processing of the payment."""


class PaymentAuditReportStep(Step):
    class Metrics(str, enum.Enum):
        PAYMENT_COUNT = "payment_count"
        PAYMENT_SAMPLED_FOR_AUDIT_COUNT = "payment_sampled_for_audit_count"
        SAMPLED_PAYMENT_COUNT = "sampled_payment_count"

    def run_step(self) -> None:
        self.generate_audit_report()

    def sample_payments_for_audit_report(self) -> Iterable[Payment]:
        logger.info("Start sampling payments for audit report")

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            self.db_session,
        )
        state_log_count = len(state_logs)
        self.set_metrics({self.Metrics.SAMPLED_PAYMENT_COUNT: state_log_count})

        payments: List[Payment] = []
        for state_log in state_logs:
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise PaymentAuditError(
                    f"A state log was found without a payment in while trying to sample payments for audit report: {state_log.state_log_id}"
                )

            # transition the state sampling state
            # NOTE: we currently sample 100% of all available payments for audit.
            # In the future this will be based on a number of criteria
            # https://lwd.atlassian.net/wiki/spaces/API/pages/1309737679/Payment+Audit+and+Rejection#Sampling-Rules
            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT,
                state_log_util.build_outcome("Add to Payment Audit Report"),
                self.db_session,
            )

            payments.append(payment)
            self.increment(self.Metrics.PAYMENT_SAMPLED_FOR_AUDIT_COUNT)

        logger.info("Done sampling payments for audit report: %i", len(payments))

        return payments

    def set_sampled_payments_to_sent_state(self):
        logger.info("Start setting sampled payments to sent state")

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT,
            self.db_session,
        )

        for state_log in state_logs:
            payment = state_log.payment

            # Shouldn't happen as they should always have a payment attached
            # but due to our unassociated state log logic, it technically can happen
            # elsewhere in the code and we want to be certain it isn't happening here
            if not payment:
                raise PaymentAuditError(
                    f"A state log was found without a payment while processing audit report: {state_log.state_log_id}"
                )

            state_log_util.create_finished_state_log(
                payment,
                State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
                state_log_util.build_outcome("Payment Audit Report sent"),
                self.db_session,
            )

        logger.info("Done setting sampled payments to sent state: %i", len(state_logs))

    def build_payment_audit_data_set(
        self, payments: Iterable[Payment]
    ) -> Iterable[PaymentAuditData]:
        logger.info("Start building payment audit data for sampled payments")

        payment_audit_data_set: List[PaymentAuditData] = []

        for payment in payments:
            self.increment(self.Metrics.PAYMENT_COUNT)
            # populate payment audit data by inspecting the currently sampled payment's history
            is_first_time_payment = False
            is_previously_errored_payment = False
            is_previously_rejected_payment = False
            number_of_times_in_rejected_or_error_state = 0

            payment_history = (
                self.db_session.query(Payment)
                .filter(
                    Payment.fineos_pei_c_value == payment.fineos_pei_c_value,
                    Payment.fineos_pei_i_value == payment.fineos_pei_i_value,
                )
                .all()
            )

            if len(payment_history) == 1:
                is_first_time_payment = True
            else:
                payment_history_ids = [p.payment_id for p in payment_history]
                expected_end_states = [
                    State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id,
                    State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT.state_id,
                ]

                payment_error_or_rejected_state_log_history = (
                    self.db_session.query(StateLog)
                    .join(LatestStateLog)
                    .join(LkState, StateLog.end_state_id == LkState.state_id)
                    .filter(
                        LkState.flow_id == Flow.DELEGATED_PAYMENT.flow_id,
                        LatestStateLog.payment_id.in_(payment_history_ids),
                        StateLog.end_state_id.in_(expected_end_states),
                    )
                    .all()
                )

                payment_state_history = [
                    sl.end_state_id for sl in payment_error_or_rejected_state_log_history
                ]

                if (
                    State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
                    in payment_state_history
                ):
                    is_previously_errored_payment = True

                if (
                    State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT.state_id
                    in payment_state_history
                ):
                    is_previously_rejected_payment = True

                number_of_times_in_rejected_or_error_state = len(
                    payment_error_or_rejected_state_log_history
                )

            payment_audit_data = PaymentAuditData(
                payment=payment,
                is_first_time_payment=is_first_time_payment,
                is_previously_errored_payment=is_previously_errored_payment,
                is_previously_rejected_payment=is_previously_rejected_payment,
                number_of_times_in_rejected_or_error_state=number_of_times_in_rejected_or_error_state,
            )
            payment_audit_data_set.append(payment_audit_data)

        logger.info(
            "Done building payment audit data for sampled payments: %i",
            len(payment_audit_data_set),
        )

        return payment_audit_data_set

    def generate_audit_report(self):
        """Top level function to generate and send payment audit report"""

        try:
            logger.info("Start generating payment audit report")

            s3_config = payments_config.get_s3_config()

            # sample files
            payments: Iterable[Payment] = self.sample_payments_for_audit_report()

            # generate payment audit data
            payment_audit_data_set: Iterable[PaymentAuditData] = self.build_payment_audit_data_set(
                payments
            )

            # write the report to the archive directory
            archive_folder_path = write_audit_report(
                payment_audit_data_set,
                s3_config.pfml_error_reports_archive_path,
                self.db_session,
                report_name=payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT,
            )

            if archive_folder_path is None:
                raise Exception("Payment Audit Report file not written to outbound folder")

            logger.info(
                "Done writing Payment Audit Report file to archive folder: %s", archive_folder_path
            )

            # Copy the report to the outgoing folder for program integrity
            outgoing_file_name = f"{payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT}.csv"
            outbound_path = os.path.join(s3_config.dfml_report_outbound_path, outgoing_file_name)
            file_util.copy_file(str(archive_folder_path), str(outbound_path))

            logger.info(
                "Done copying Payment Audit Report file to outbound folder: %s", outbound_path
            )

            # create a reference file for the archived report
            reference_file = ReferenceFile(
                file_location=str(archive_folder_path),
                reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
            )
            self.db_session.add(reference_file)

            # set sampled payments as sent
            self.set_sampled_payments_to_sent_state()

            # persist changes
            self.db_session.commit()

            logger.info("Done generating payment audit report")

        except Exception:
            self.db_session.rollback()
            logger.exception("Error creating Payment Audit file")

            # We do not want to run any subsequent steps if this fails
            raise

import decimal
import enum
import os
from datetime import date
from typing import Iterable, List, Optional, Tuple, cast

from sqlalchemy.orm import joinedload

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    LkState,
    Payment,
    PaymentTransactionType,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    LinkSplitPayment,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    PaymentAuditData,
    write_audit_report,
)
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
)

logger = logging.get_logger(__name__)


class PaymentAuditError(Exception):
    """An error in a row that prevents processing of the payment."""


class PaymentAuditReportStep(Step):
    class Metrics(str, enum.Enum):
        AUDIT_PATH = "audit_path"
        PAYMENT_COUNT = "payment_count"
        PAYMENT_SAMPLED_FOR_AUDIT_COUNT = "payment_sampled_for_audit_count"
        SAMPLED_PAYMENT_COUNT = "sampled_payment_count"

    def run_step(self) -> None:
        self.generate_audit_report()

    def sample_payments_for_audit_report(self) -> Iterable[Payment]:
        logger.info("Start sampling payments for audit report")

        state_logs_containers: List[StateLog] = []

        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            self.db_session,
        )

        state_logs_containers += state_logs

        federal_withholding_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT,
            self.db_session,
        )

        state_logs_containers += federal_withholding_state_logs

        state_withholding_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            state_log_util.AssociatedClass.PAYMENT,
            State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT,
            self.db_session,
        )

        state_logs_containers += state_withholding_state_logs

        state_log_count = len(state_logs_containers)
        self.set_metrics({self.Metrics.SAMPLED_PAYMENT_COUNT: state_log_count})

        payments: List[Payment] = []
        for state_log in state_logs_containers:
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
            logger.info(
                "Sampled payment into the audit report",
                extra=payments_util.get_traceable_payment_details(
                    payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT
                ),
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

            create_payment_finished_state_log_with_writeback(
                payment=payment,
                payment_end_state=State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
                payment_outcome=state_log_util.build_outcome("Payment Audit Report sent"),
                writeback_transaction_status=FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS,
                db_session=self.db_session,
            )

            logger.info(
                "Adding payment to the audit report",
                extra=payments_util.get_traceable_payment_details(
                    payment, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT
                ),
            )

            if (
                payment.payment_transaction_type_id
                == PaymentTransactionType.STANDARD.payment_transaction_type_id
            ):
                linked_payments = _get_split_payments(self.db_session, payment)
                for payment in linked_payments:
                    if (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                    ):
                        end_state = State.STATE_WITHHOLDING_RELATED_PENDING_AUDIT
                    elif (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id
                    ):
                        end_state = State.FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT
                    elif (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
                    ):
                        end_state = State.EMPLOYER_REIMBURSEMENT_RELATED_PENDING_AUDIT
                    outcome = state_log_util.build_outcome("Related Payment Audit report sent")
                    state_log_util.create_finished_state_log(
                        associated_model=payment,
                        end_state=end_state,
                        outcome=outcome,
                        db_session=self.db_session,
                    )

        logger.info("Done setting sampled payments to sent state: %i", len(state_logs))

    def previously_audit_sent_count(self, payment: Payment) -> int:
        other_claim_payments = _get_other_claim_payments_for_payment(payment)
        previous_states = [State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT]
        return _get_state_log_count_in_state(other_claim_payments, previous_states, self.db_session)

    def audit_sent_count(self, payments: List[Payment]) -> int:
        states = [State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT]
        return _get_state_log_count_in_state(payments, states, self.db_session)

    def previously_errored_payment_count(self, payment: Payment) -> int:
        other_claim_payments = _get_other_claim_payments_for_payment(
            payment, same_payment_period=True
        )
        previous_states = [
            State.PAYMENT_FAILED_ADDRESS_VALIDATION,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
        ]
        return _get_state_log_count_in_state(other_claim_payments, previous_states, self.db_session)

    def previously_rejected_payment_count(self, payment: Payment) -> int:
        other_claim_payments = _get_other_claim_payments_for_payment(
            payment, same_payment_period=True
        )
        previous_states = [State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT]
        return _get_state_log_count_in_state(other_claim_payments, previous_states, self.db_session)

    def previously_skipped_payment_count(self, payment: Payment) -> int:
        other_claim_payments = _get_other_claim_payments_for_payment(
            payment, same_payment_period=True
        )
        previous_states = [State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE]
        return _get_state_log_count_in_state(other_claim_payments, previous_states, self.db_session)

    def previously_paid_payments(
        self, payment: Payment
    ) -> List[Tuple[Payment, Optional[FineosWritebackDetails]]]:
        related_payments = (
            self.db_session.query(Payment)
            .filter(
                Payment.period_start_date == payment.period_start_date,
                Payment.period_end_date == payment.period_end_date,
                Payment.claim_id == payment.claim_id,
                Payment.payment_id != payment.payment_id,
            )
            .options(joinedload(Payment.fineos_writeback_details))  # type: ignore
            .all()
        )
        previously_paid_payments = []

        for payment in related_payments:
            writeback_detail = (
                payment.fineos_writeback_details[-1]  # type: ignore
                if len(payment.fineos_writeback_details) > 0  # type: ignore
                else None
            )
            # In the case writeback_detail is not populated, skip the payment.
            # Filter invalid writeback details in code since we need
            # to look for paid payments that may have errored afterwards.
            if writeback_detail and writeback_detail.transaction_status_id not in [
                FineosWritebackTransactionStatus.PAID.transaction_status_id,
                FineosWritebackTransactionStatus.POSTED.transaction_status_id,
            ]:
                continue

            previously_paid_payments.append((payment, writeback_detail))

        return previously_paid_payments

    def format_previously_paid_payments(
        self, payments: list[Tuple[Payment, Optional[FineosWritebackDetails]]]
    ) -> Optional[str]:
        if len(payments) == 0:
            return None

        output = ""
        for payment, writeback_detail in payments:
            c_val = payment.fineos_pei_c_value
            i_val = payment.fineos_pei_i_value
            amount = payment.amount

            writeback_time = writeback_detail.writeback_sent_at if writeback_detail else "N/A"
            writeback_status = (
                writeback_detail.transaction_status.transaction_status_description
                if writeback_detail
                else "N/A"
            )
            output = output + (
                f"Payment C={c_val}, I={i_val}: "
                f"amount={amount}, transaction_status={writeback_status}, "
                f"writeback_sent_at={writeback_time}\n"
            )

        return output

    def calculate_federal_withholding_amount(
        self, payment: Payment, link_payments: List[Payment]
    ) -> decimal.Decimal:
        payment_amount: decimal.Decimal = decimal.Decimal(0)

        if payment.payment_transaction_type_id in [
            PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id
        ]:
            payment_amount = payment.amount
            return payment_amount

        for payment in link_payments:
            if payment.payment_transaction_type_id in [
                PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id
            ]:
                payment_amount += payment.amount

        return payment_amount

    # TODO Refactor this to one function for get all amount values.
    def calculate_state_withholding_amount(
        self, payment: Payment, link_payments: List[Payment]
    ) -> decimal.Decimal:

        payment_amount: decimal.Decimal = decimal.Decimal(0)

        if (
            payment.payment_transaction_type_id
            == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
        ):
            payment_amount = payment.amount
            return payment_amount

        for payment in link_payments:
            if payment.payment_transaction_type_id in [
                PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
            ]:
                payment_amount += payment.amount

        return payment_amount

    def calculate_employer_reimbursement_amount(
        self, payment: Payment, link_payments: List[Payment]
    ) -> decimal.Decimal:

        payment_amount: decimal.Decimal = decimal.Decimal(0)

        if (
            payment.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        ):
            payment_amount = payment.amount
            return payment_amount

        for payment in link_payments:
            if (
                payment.payment_transaction_type_id
                == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
            ):
                payment_amount += payment.amount

        return payment_amount

    # TODO Refactor this to one function for get all i values.
    def get_federal_withholding_i_value(self, link_payments: List[Payment]) -> str:
        federal_withholding_i_values = []

        for payment in link_payments:
            if payment.payment_transaction_type_id in [
                PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id
            ]:
                federal_withholding_i_values.append(payment.fineos_pei_i_value)
        return " ".join(str(v) for v in federal_withholding_i_values)

    def get_state_withholding_i_value(self, link_payments: List[Payment]) -> str:
        state_withholding_i_values = []

        for payment in link_payments:
            if payment.payment_transaction_type_id in [
                PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
            ]:
                state_withholding_i_values.append(payment.fineos_pei_i_value)
        return " ".join(str(v) for v in state_withholding_i_values)

    def get_employer_reimbursement_i_value(
        self, payment: Payment, link_payments: List[Payment]
    ) -> str:
        employer_reimbursement_i_values = []
        if (
            payment.payment_transaction_type_id
            == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
        ):
            return str(payment.fineos_pei_i_value)

        for link_payment in link_payments:
            if (
                link_payment.payment_transaction_type_id
                == PaymentTransactionType.EMPLOYER_REIMBURSEMENT.payment_transaction_type_id
            ):
                employer_reimbursement_i_values.append(link_payment.fineos_pei_i_value)
        return " ".join(str(v) for v in employer_reimbursement_i_values)

    def build_payment_audit_data_set(
        self, payments: Iterable[Payment]
    ) -> Iterable[PaymentAuditData]:
        logger.info("Start building payment audit data for sampled payments")

        payment_audit_data_set: List[PaymentAuditData] = []

        for payment in payments:
            self.increment(self.Metrics.PAYMENT_COUNT)

            # populate payment audit data by inspecting the currently sampled payment's history
            previously_audit_sent_count = self.previously_audit_sent_count(payment)
            is_first_time_payment = previously_audit_sent_count == 0

            previously_paid_payments = self.previously_paid_payments(payment)

            # Clear the net payment amount for orphaned Tax Withholdings in the audit report
            net_payment_amount = payment.amount
            if payment.payment_transaction_type_id in [
                PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id,
                PaymentTransactionType.FEDERAL_TAX_WITHHOLDING.payment_transaction_type_id,
            ]:
                net_payment_amount = decimal.Decimal(0)

            linked_payments = _get_split_payments(self.db_session, payment)
            federal_withholding_amount: decimal.Decimal = self.calculate_federal_withholding_amount(
                payment, linked_payments
            )
            state_withholding_amount: decimal.Decimal = self.calculate_state_withholding_amount(
                payment, linked_payments
            )
            employer_reimbursement_amount: decimal.Decimal = (
                self.calculate_employer_reimbursement_amount(payment, linked_payments)
            )

            payment_audit_data = PaymentAuditData(
                payment=payment,
                is_first_time_payment=is_first_time_payment,
                previously_errored_payment_count=self.previously_errored_payment_count(payment),
                previously_rejected_payment_count=self.previously_rejected_payment_count(payment),
                previously_skipped_payment_count=self.previously_skipped_payment_count(payment),
                previously_paid_payment_count=len(previously_paid_payments),
                previously_paid_payments_string=self.format_previously_paid_payments(
                    previously_paid_payments
                ),
                gross_payment_amount=str(
                    net_payment_amount
                    + federal_withholding_amount
                    + state_withholding_amount
                    + employer_reimbursement_amount
                ),
                net_payment_amount=str(net_payment_amount if net_payment_amount > 0 else ""),
                federal_withholding_amount=str(
                    federal_withholding_amount if federal_withholding_amount > 0 else ""
                ),
                state_withholding_amount=str(
                    state_withholding_amount if state_withholding_amount > 0 else ""
                ),
                employer_reimbursement_amount=str(
                    employer_reimbursement_amount if employer_reimbursement_amount > 0 else ""
                ),
                federal_withholding_i_value=self.get_federal_withholding_i_value(linked_payments),
                state_withholding_i_value=self.get_state_withholding_i_value(linked_payments),
                employer_reimbursement_i_value=self.get_employer_reimbursement_i_value(
                    payment, linked_payments
                ),
            )
            payment_audit_data_set.append(payment_audit_data)

        logger.info(
            "Done building payment audit data for sampled payments: %i", len(payment_audit_data_set)
        )

        return payment_audit_data_set

    def generate_audit_report(self):
        """Top level function to generate and send payment audit report"""

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
        self.set_metrics({self.Metrics.AUDIT_PATH: archive_folder_path})

        # Copy the report to the outgoing folder for program integrity
        outgoing_file_name = f"{payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT}.csv"
        outbound_path = os.path.join(s3_config.dfml_report_outbound_path, outgoing_file_name)
        file_util.copy_file(str(archive_folder_path), str(outbound_path))

        logger.info("Done copying Payment Audit Report file to outbound folder: %s", outbound_path)

        # create a reference file for the archived report
        reference_file = ReferenceFile(
            file_location=str(archive_folder_path),
            reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
        )
        self.db_session.add(reference_file)

        # set sampled payments as sent
        self.set_sampled_payments_to_sent_state()

        logger.info("Done generating payment audit report")


def _get_state_log_count_in_state(
    payments: List[Payment], states: List[LkState], db_session: db.Session
) -> int:
    payment_ids = [p.payment_id for p in payments]
    state_ids = [s.state_id for s in states]

    audit_report_sent_state_other_payments = (
        db_session.query(StateLog)
        .filter(StateLog.end_state_id.in_(state_ids), StateLog.payment_id.in_(payment_ids))
        .all()
    )
    return len(audit_report_sent_state_other_payments)


def _get_other_claim_payments_for_payment(
    payment: Payment, same_payment_period: bool = False
) -> List[Payment]:
    all_claim_payments = payment.claim.payments.all()
    other_claim_payments: List[Payment] = list(
        filter(lambda p: p.payment_id != payment.payment_id, all_claim_payments)
    )

    if same_payment_period:
        payment_date_tuple = _get_date_tuple(payment)
        other_claim_payments = list(
            filter(lambda p: _get_date_tuple(p) == payment_date_tuple, other_claim_payments)
        )

    return other_claim_payments


def _get_split_payments(db_session: db.Session, payment: Payment) -> List[Payment]:
    linked_split_payments: List[Payment] = (
        db_session.query(Payment)
        .join(LinkSplitPayment, Payment.payment_id == LinkSplitPayment.related_payment_id)
        .filter(LinkSplitPayment.payment_id == payment.payment_id)
        .all()
    )
    return linked_split_payments


def _get_date_tuple(payment: Payment) -> Tuple[date, date]:
    return (cast(date, payment.period_start_date), cast(date, payment.period_end_date))

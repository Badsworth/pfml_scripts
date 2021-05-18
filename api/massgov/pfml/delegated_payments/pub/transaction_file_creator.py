import enum
from typing import List, Optional, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.pub.pub_check as pub_check
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Employee,
    Payment,
    PaymentMethod,
    PrenoteState,
    PubEft,
    State,
)
from massgov.pfml.delegated_payments.check_issue_file import CheckIssueFile
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    add_eft_prenote_to_nacha_file,
    add_payments_to_nacha_file,
    create_nacha_file,
    send_nacha_file,
)
from massgov.pfml.delegated_payments.ez_check import EzCheckFile
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.ach.nacha import NachaFile

logger = logging.get_logger(__name__)


class TransactionFileCreatorStep(Step):
    check_file: Optional[EzCheckFile] = None
    positive_pay_file: Optional[CheckIssueFile] = None
    ach_file: Optional[NachaFile] = None

    class Metrics(str, enum.Enum):
        ACH_PAYMENT_COUNT = "ach_payment_count"
        ACH_PRENOTE_COUNT = "ach_prenote_count"

    def run_step(self) -> None:
        try:
            logger.info("Start creating PUB transaction file")

            # ACH
            self.add_ach_payments()
            self.add_prenotes()

            # Check and positive pay
            self.check_file, self.positive_pay_file = pub_check.create_check_file(self.db_session)

            # Send the file
            self.send_payment_files()

            # Commit pending changes to db
            self.db_session.commit()

            logger.info("Done creating PUB transaction file")

        except Exception:
            self.db_session.rollback()
            logger.exception("Error creating PUB transaction file")

            # We do not want to run any subsequent steps if this fails
            raise

    def add_prenotes(self):
        logger.info("Start adding EFT prenotes to PUB transaction file")

        # add eligible employee eft prenotes to transaction file
        employees_with_efts: List[
            Tuple[Employee, PubEft]
        ] = self._get_eft_eligible_employees_with_eft()

        if len(employees_with_efts) == 0:
            logger.info("No EFT prenotes to add to PUB transaction file")
            return

        self._create_ach_file_if_not_exists()
        # Cast the ach_file as we know it's set by _create_ach_file_if_not_exists
        add_eft_prenote_to_nacha_file(cast(NachaFile, self.ach_file), employees_with_efts)

        # transition eft states for employee
        for employee_with_eft in employees_with_efts:
            self.increment(self.Metrics.ACH_PRENOTE_COUNT)
            employee: Employee = employee_with_eft[0]
            eft: PubEft = employee_with_eft[1]

            eft.prenote_state_id = PrenoteState.PENDING_WITH_PUB.prenote_state_id
            eft.prenote_sent_at = payments_util.get_now()
            self.db_session.add(eft)

            state_log_util.create_finished_state_log(
                associated_model=employee,
                end_state=State.DELEGATED_EFT_PRENOTE_SENT,
                outcome=state_log_util.build_outcome("EFT prenote sent"),
                db_session=self.db_session,
            )

        logger.info(
            "Done adding EFT prenotes to PUB transaction file: %i", len(employees_with_efts)
        )

    def add_ach_payments(self) -> None:
        logger.info("Start adding ACH payments to PUB transaction file")

        # add eligible payments to transaction file
        payments: List[Payment] = self._get_eligible_eft_payments()

        if len(payments) == 0:
            logger.info("No ACH payments to add to PUB transaction file")
            return

        self._create_ach_file_if_not_exists()
        # Cast the ach_file as we know it's set by _create_ach_file_if_not_exists
        add_payments_to_nacha_file(cast(NachaFile, self.ach_file), payments)

        # transition states
        for payment in payments:
            self.increment(self.Metrics.ACH_PAYMENT_COUNT)
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
                outcome=state_log_util.build_outcome("PUB transaction sent"),
                db_session=self.db_session,
            )

        logger.info("Done adding ACH payments to PUB transaction file: %i", len(payments))

    def send_payment_files(self) -> None:
        s3_config = payments_config.get_s3_config()

        # We locally archive the Check & NACHA output files
        check_archive_path = s3_config.pfml_pub_check_archive_path
        ach_archive_path = s3_config.pfml_pub_ach_archive_path

        # Outgoing files to PUB go to different locations
        # NACHA and Positive Pay files go to the S3 folder that MoveIt grabs from
        # EzCheck pay file goes to the S3 folder that Sharepoint grabs from
        moveit_outgoing_path = s3_config.pub_moveit_outbound_path
        dfml_sharepoint_outgoing_path = s3_config.dfml_report_outbound_path

        if self.check_file is None:
            logger.info("No check file to send to PUB")
        else:
            ref_file = pub_check.send_check_file(
                self.check_file, check_archive_path, dfml_sharepoint_outgoing_path
            )
            self.db_session.add(ref_file)

        if self.positive_pay_file is None:
            logger.info("No positive pay file to send to PUB")
        else:
            ref_file = pub_check.send_positive_pay_file(
                self.positive_pay_file, check_archive_path, moveit_outgoing_path
            )
            self.db_session.add(ref_file)

        if self.ach_file is None:
            logger.info("No ACH file to send to PUB")
        else:
            ref_file = send_nacha_file(self.ach_file, ach_archive_path, moveit_outgoing_path)
            self.db_session.add(ref_file)

        return None

    # Pre-notes and ACH payments are sent to PUB in the same transaction file. We add them to that
    # file separately (so that we can create pre-note only files and payment only files) so we
    # separate the creation of the ACH transaction file from the process that adds records to it.
    def _create_ach_file_if_not_exists(self) -> None:
        if self.ach_file is None:
            self.ach_file = create_nacha_file()

    def _get_eligible_eft_payments(self) -> List[Payment]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
            db_session=self.db_session,
        )

        for state_log in state_logs:
            if state_log.payment.disb_method_id != PaymentMethod.ACH.payment_method_id:
                raise Exception(
                    f"Non-ACH payment method detected in state log: { state_log.state_log_id }, payment: {state_log.payment.payment_id}"
                )

        ach_payments = [state_log.payment for state_log in state_logs]

        return ach_payments

    def _get_pub_efts_for_prenote(self, employee: Employee) -> List[PubEft]:
        employee_pub_eft_pairs = employee.pub_efts.all()

        if len(employee_pub_eft_pairs) == 0:
            logger.warning("No pub eft pairs found for employee: %s", employee.employee_id)
            return []

        all_pub_efts = [epe.pub_eft for epe in employee_pub_eft_pairs]
        pending_pub_efts = [
            pub_eft
            for pub_eft in all_pub_efts
            if pub_eft.prenote_state_id == PrenoteState.PENDING_PRE_PUB.prenote_state_id
        ]

        return pending_pub_efts

    def _get_eft_eligible_employees_with_eft(self) -> List[Tuple[Employee, PubEft]]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.EMPLOYEE,
            end_state=State.DELEGATED_EFT_SEND_PRENOTE,
            db_session=self.db_session,
        )

        employees_with_eft: List[Tuple[Employee, PubEft]] = []

        for state_log in state_logs:
            employee: Employee = state_log.employee

            if employee is None:
                raise Exception(
                    f"No employee associated model on state log: {state_log.state_log_id}"
                )

            pub_efts: List[PubEft] = self._get_pub_efts_for_prenote(employee)

            if len(pub_efts) == 0:
                raise Exception(
                    f"No pending prenote pub efts associated with employee: {employee.employee_id}"
                )

            for pub_eft in pub_efts:
                employees_with_eft.append((employee, pub_eft))

        return employees_with_eft

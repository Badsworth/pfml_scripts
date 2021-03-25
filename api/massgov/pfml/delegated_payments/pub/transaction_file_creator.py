from typing import List, Optional, Tuple

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Employee,
    Payment,
    PaymentMethod,
    PrenoteState,
    PubEft,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    add_eft_prenote_to_nacha_file,
    add_payments_to_nacha_file,
    create_nacha_file,
    upload_nacha_file_to_s3,
)
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.ach.nacha import NachaFile

logger = logging.get_logger(__name__)


class TransactionFileCreatorStep(Step):
    # check_file: Optional[CheckFile] = None
    ach_file: Optional[NachaFile] = None

    def run_step(self) -> None:
        try:
            logger.info("Start creating PUB transaction file")

            s3_config = payments_config.get_s3_config()
            transaction_files_path = s3_config.pfml_pub_outbound_path

            # ACH
            self.add_ach_payments()
            self.add_prenotes()

            # Check
            self.create_check_file()

            # Send the file
            self.send_payment_files(transaction_files_path)

            # Commit pending changes to db
            self.db_session.commit()

            logger.info("Done creating PUB transaction file")

        except Exception:
            self.db_session.rollback()
            logger.exception("Error creating PUB transaction file")

            # We do not want to run any subsequent steps if this fails
            raise

    def create_check_file(self) -> None:
        # TODO: After PUB-30 is complete, call the function that adds check payments to an ACH
        # transaction file.
        #
        # self.check_file = _create_check_file()

        return None

    def add_prenotes(self):
        logger.info("Start adding EFT prenotes to PUB transaction file")

        self._create_ach_file_if_not_exists()

        # add eligible employee eft prenotes to transaction file
        employees_with_efts: List[
            Tuple[Employee, PubEft]
        ] = self._get_eft_eligible_employees_with_eft()
        add_eft_prenote_to_nacha_file(self.ach_file, employees_with_efts)

        # transition eft states for employee
        for employee_with_eft in employees_with_efts:
            employee: Employee = employee_with_eft[0]
            eft: PubEft = employee_with_eft[1]

            eft.prenote_state_id = PrenoteState.PENDING_WITH_PUB.prenote_state_id
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

        self._create_ach_file_if_not_exists()

        # add eligible payments to transaction file
        payments: List[Payment] = self._get_eligible_eft_payments()
        add_payments_to_nacha_file(self.ach_file, payments)

        # transition states
        for payment in payments:
            state_log_util.create_finished_state_log(
                associated_model=payment,
                end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
                outcome=state_log_util.build_outcome("PUB transaction sent"),
                db_session=self.db_session,
            )

        logger.info("Done adding ACH payments to PUB transaction file: %i", len(payments))

    def send_payment_files(self, ach_file_folder_path: str) -> None:
        # TODO: If we've created a check and/or ACH file send them to PUB's S3 bucket, FTP server,
        # or whatever else.
        #
        # if self.check_file is not None:
        #     _send_to_pub(self.check_file)
        #
        if self.ach_file is not None:
            ref_file = payments_util.create_pub_reference_file(
                payments_util.get_now(),
                ReferenceFileType.PUB_TRANSACTION,
                self.db_session,
                ach_file_folder_path,
            )

            upload_nacha_file_to_s3(self.ach_file, ref_file.file_location)

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

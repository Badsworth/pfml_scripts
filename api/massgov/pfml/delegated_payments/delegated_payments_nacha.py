import os
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Tuple

import massgov.pfml.db as db
from massgov.pfml.util.names import Name
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    BankAccountType,
    ClaimType,
    Employee,
    Payment,
    PaymentMethod,
    PrenoteState,
    PubEft,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.delegated_payments.util.ach.nacha import (
    Constants,
    NachaBatch,
    NachaEntry,
    NachaFile,
)

logger = logging.get_logger(__name__)


class NachaBatchType(Enum):
    MEDICAL_LEAVE = "medical leave"
    FAMILY_LEAVE = "family leave"
    PRENOTE = "prenote"


def create_nacha_file() -> NachaFile:
    return NachaFile()


def create_nacha_batch(nacha_batch_type: NachaBatchType) -> NachaBatch:
    effective_date = datetime.now()
    today = datetime.today()

    # Prenotes we put in the family leave batch if we are only processing
    # as they need to go somewhere and prenotes are for $0
    if (
        nacha_batch_type == NachaBatchType.MEDICAL_LEAVE
        or nacha_batch_type == NachaBatchType.PRENOTE
    ):
        description = Constants.description_medical_leave
    elif nacha_batch_type == NachaBatchType.FAMILY_LEAVE:
        description = Constants.description_family_leave

    else:
        raise Exception("Invalid value supplied for NACHA batch type: %s" % nacha_batch_type)

    batch = NachaBatch(effective_date, today, description)
    return batch


def send_nacha_file(
    nacha_file: NachaFile, archive_folder_path: str, outgoing_folder_path: str
) -> ReferenceFile:
    logger.info("Creating NACHA files")
    nacha_file.finalize()

    now = payments_util.get_now()
    nacha_file_name = now.strftime(payments_util.Constants.NACHA_FILE_FORMAT)
    archive_s3_path = payments_util.build_archive_path(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, nacha_file_name, now
    )

    with file_util.write_file(archive_s3_path, mode="wb") as pub_file:
        pub_file.write(nacha_file.to_bytes())
    logger.info("Wrote NACHA file to archive path %s", archive_s3_path)

    outgoing_s3_path = os.path.join(
        outgoing_folder_path, payments_util.Constants.FILE_NAME_PUB_NACHA
    )
    file_util.copy_file(archive_s3_path, outgoing_s3_path)
    logger.info("Copied NACHA file to outgoing path %s", outgoing_s3_path)

    return ReferenceFile(
        file_location=archive_s3_path,
        reference_file_type_id=ReferenceFileType.PUB_NACHA.reference_file_type_id,
    )


def add_payments_to_nacha_file(nacha_file: NachaFile, payments_with_payee_name: List[Tuple[Payment, Name]]) -> None:
    if len(payments_with_payee_name) == 0:
        logger.warning("No Payment records to add to PUB transaction file")
        return

    family_leave_nacha_batch = create_nacha_batch(NachaBatchType.FAMILY_LEAVE)
    medical_leave_nacha_batch = create_nacha_batch(NachaBatchType.MEDICAL_LEAVE)

    for payment_with_payee_name in payments_with_payee_name:
        payment = payment_with_payee_name[0]
        payee_name = payment_with_payee_name[1]

        if payment.disb_method_id != PaymentMethod.ACH.payment_method_id:
            raise Exception(f"Non-ACH payment method for payment: {payment.payment_id}")

        entry = NachaEntry(
            trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
            receiving_dfi_id=payment.pub_eft.routing_nbr,
            dfi_act_num=payment.pub_eft.account_nbr,
            amount=payment.amount,
            id=f"P{payment.pub_individual_id}",
            name=f"{payee_name.last_name} {payee_name.first_name}",
        )

        if payment.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id:
            family_leave_nacha_batch.add_entry(entry)
        elif payment.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id:
            medical_leave_nacha_batch.add_entry(entry)
        else:
            raise Exception(
                "Invalid leave type for payment. Payment ID: %s - Claim Type: %s"
                % (payment.payment_id, payment.claim_type_id)
            )

    if len(family_leave_nacha_batch.entries) > 0:
        nacha_file.add_batch(family_leave_nacha_batch)
    if len(medical_leave_nacha_batch.entries) > 0:
        nacha_file.add_batch(medical_leave_nacha_batch)


def add_eft_prenote_to_nacha_file(
    nacha_file: NachaFile, employees_with_eft_and_employee_name: List[Tuple[Employee, PubEft, Name]]
) -> None:
    if len(employees_with_eft_and_employee_name) == 0:
        logger.warning("No claimant EFTs to prenote.")
        return

    # For prenotes, we reuse the first batch if it exists
    # which is probably family leave if we had payments to send
    if len(nacha_file.batches) > 0:
        nacha_batch = nacha_file.batches[0]
        reuse_batch = True
    else:
        nacha_batch = create_nacha_batch(NachaBatchType.PRENOTE)
        reuse_batch = False

    for employee_with_eft_and_employee_name in employees_with_eft_and_employee_name:
        employee = employee_with_eft_and_employee_name[0]
        pub_eft = employee_with_eft_and_employee_name[1]
        employee_name = employee_with_eft_and_employee_name[2]

        if pub_eft.prenote_state_id != PrenoteState.PENDING_PRE_PUB.prenote_state_id:
            raise Exception(
                f"Found non pending eft trying to add to prenote list: {employee.employee_id}, eft: {pub_eft.pub_eft_id}"
            )

        entry = NachaEntry(
            trans_code=get_trans_code(pub_eft.bank_account_type_id, True, False),
            receiving_dfi_id=pub_eft.routing_nbr,
            dfi_act_num=pub_eft.account_nbr,
            amount=Decimal("0.00"),
            id=f"E{pub_eft.pub_individual_id}",
            name=f"{employee_name.last_name} {employee_name.first_name}",
        )

        nacha_batch.add_entry(entry)

    if len(nacha_batch.entries) > 0 and not reuse_batch:
        nacha_file.add_batch(nacha_batch)


def get_trans_code(bank_account_type_id: int, is_prenote: bool, is_return: bool) -> str:
    if bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id:
        if is_prenote:
            return Constants.checking_prenote_trans_code
        elif is_return:
            return Constants.checking_return_trans_code
        else:
            return Constants.checking_deposit_trans_code

    elif bank_account_type_id == BankAccountType.SAVINGS.bank_account_type_id:
        if is_prenote:
            return Constants.savings_prenote_trans_code
        elif is_return:
            return Constants.savings_return_trans_code
        else:
            return Constants.savings_deposit_trans_code

    raise Exception(
        "Unable to determine trans code for bank account type id %i" % bank_account_type_id
    )

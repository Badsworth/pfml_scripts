from datetime import datetime
from decimal import Decimal
from typing import List, Tuple

import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    BankAccountType,
    Employee,
    Payment,
    PrenoteState,
    PubEft,
)
from massgov.pfml.delegated_payments.util.ach.nacha import (
    Constants,
    NachaBatch,
    NachaEntry,
    NachaFile,
)

logger = logging.get_logger(__name__)


def create_nacha_file() -> NachaFile:
    effective_date = datetime.now()
    today = datetime.today()

    file = NachaFile()
    batch = NachaBatch(effective_date, today)

    file.add_batch(batch)

    return file


def get_nacha_batch(nacha_file: NachaFile) -> NachaBatch:
    if len(nacha_file.batches) == 0:
        raise Exception("Nacha file with no batches")

    nacha_batch: NachaBatch = nacha_file.batches[
        0
    ]  # we only use one batch for the PUB transaction file
    return nacha_batch


def upload_nacha_file_to_s3(nacha_file: NachaFile, file_path: str):
    logger.info("Creating NACHA files")

    nacha_file.finalize()

    with file_util.write_file(file_path, mode="wb") as pub_file:
        pub_file.write(nacha_file.to_bytes())


def add_payments_to_nacha_file(nacha_file: NachaFile, payments: List[Payment]):
    if len(payments) == 0:
        logger.warning("No Payment records to add to PUB transaction file")
        return

    nacha_batch: NachaBatch = get_nacha_batch(nacha_file)

    for payment in payments:
        # TODO check payment method https://lwd.atlassian.net/browse/PUB-106
        # if payment.payment_method_id != PaymentMethod.ACH.payment_method_id:
        #     raise Exception(
        #         f"Non-ACH payment method for payment: {payment.payment_id}"
        #     )

        entry = NachaEntry(
            trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False),
            receiving_dfi_id=payment.pub_eft.routing_nbr,
            dfi_act_num=payment.pub_eft.account_nbr,
            amount=payment.amount,
            id=f"P{payment.pub_individual_id}",
            name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
        )

        nacha_batch.add_entry(entry)


def add_eft_prenote_to_nacha_file(
    nacha_file: NachaFile, employees_with_eft: List[Tuple[Employee, PubEft]]
):
    if len(employees_with_eft) == 0:
        logger.warning("No claimant EFTs to prenote.")
        return

    nacha_batch: NachaBatch = get_nacha_batch(nacha_file)

    for employee_with_eft in employees_with_eft:
        employee = employee_with_eft[0]
        pub_eft = employee_with_eft[1]

        if pub_eft.prenote_state_id != PrenoteState.PENDING_PRE_PUB.prenote_state_id:
            raise Exception(
                f"Found non pending eft trying to add to prenote list: {employee.employee_id}, eft: {pub_eft.pub_eft_id}"
            )

        entry = NachaEntry(
            trans_code=get_trans_code(pub_eft.bank_account_type_id, True),
            receiving_dfi_id=pub_eft.routing_nbr,
            dfi_act_num=pub_eft.account_nbr,
            amount=Decimal("0.00"),
            id=f"E{pub_eft.pub_individual_id}",
            name=f"{employee.last_name} {employee.first_name}",
        )

        nacha_batch.add_entry(entry)


def get_trans_code(bank_account_type_id: int, is_prenote: bool) -> str:
    if bank_account_type_id == BankAccountType.CHECKING.bank_account_type_id:
        if is_prenote:
            return Constants.checking_prenote_trans_code
        else:
            return Constants.checking_deposit_trans_code

    elif bank_account_type_id == BankAccountType.SAVINGS.bank_account_type_id:
        if is_prenote:
            return Constants.savings_deposit_trans_code
        else:
            return Constants.savings_prenote_trans_code

    raise Exception(
        "Unable to determine trans code for bank account type id %i" % bank_account_type_id
    )

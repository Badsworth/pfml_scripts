import argparse
import decimal
import os
from dataclasses import dataclass
from datetime import datetime
from random import randrange
from typing import List, Tuple

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as delegated_payments_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    BankAccountType,
    ClaimType,
    EmployeeAddress,
    Payment,
    PaymentMethod,
    PrenoteState,
    State,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeePubEftPairFactory,
    EmployerFactory,
    PaymentFactory,
    PubEftFactory,
)
from massgov.pfml.delegated_payments.delegated_payments_nacha import get_trans_code
from massgov.pfml.delegated_payments.util.ach.nacha import (
    NachaAddendumResponse,
    NachaBatch,
    NachaEntry,
    NachaFile,
)

logger = logging.get_logger(__name__)

# Setup command line generator args

parser = argparse.ArgumentParser(description="Generate fake payments files and data")
parser.add_argument(
    "--folder", type=str, default="payments_files", help="Output folder for generated files"
)
parser.add_argument(
    "--skiprate",
    type=int,
    default=50,
    help="Percentage of records to skip to simulate error scenarios",
)


@dataclass
class PubPaymentReturnScenario:
    no_response: bool
    error: bool
    reason_code: str = NachaAddendumResponse.random_reason()
    return_type: str = NachaAddendumResponse.random_return_type()
    date_of_death: str = ""


@dataclass
class PubPaymentReturnScenarioData:
    scenario: PubPaymentReturnScenario
    payment: Payment


pre_note_configs = [
    PubPaymentReturnScenario(no_response=True, error=False),
    PubPaymentReturnScenario(no_response=False, error=True),
]

ach_configs = [
    PubPaymentReturnScenario(no_response=True, error=False),
    PubPaymentReturnScenario(no_response=False, error=True),
]


def write_file(folder_path: str, nacha_file: NachaFile):
    now = payments_util.get_now()
    payment_return_filename = delegated_payments_util.Constants.PUB_FILENAME_TEMPLATE.format(
        "PUB-NACHA", now.strftime("%Y%m%d"),
    )

    file_content = nacha_file.to_bytes()

    full_path = os.path.join(folder_path, payment_return_filename)

    with file_util.write_file(full_path, mode="wb") as pub_file:
        pub_file.write(file_content)


def generate_pub_return_prenote(
    db_session, nacha_batch, pre_note_configs: List[PubPaymentReturnScenario], skiprate: int = 0
) -> List[PubPaymentReturnScenarioData]:
    scenario_data_list = []

    for pre_note_config in pre_note_configs:
        # The following data will be generated elsewhere we glue together scenario data.
        mailing_address = AddressFactory.create(
            address_line_one="20 South Ave",
            city="Burlington",
            geo_state_id=1,
            geo_state_text="Massachusetts",
            zip_code="01803",
        )

        employer = EmployerFactory.create()

        employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)
        employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

        pub_eft = PubEftFactory.create(
            prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
            routing_nbr="123546789",
            account_nbr="123546789",
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        )
        EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft)

        claim = ClaimFactory.create(
            employee=employee,
            employer=employer,
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        )

        payment = PaymentFactory.create(claim=claim, pub_eft=pub_eft)

        scenario_data = PubPaymentReturnScenarioData(scenario=pre_note_config, payment=payment)

        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_EFT_PRENOTE_SENT,
            associated_model=payment,
            outcome=state_log_util.build_outcome("test"),
            db_session=db_session,
        )

        skip = _should_skip(skiprate)
        # If there should be a response, add it to the NACHA file.
        if not skip:
            if not pre_note_config.no_response:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=payment.amount,
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=pre_note_config.reason_code,
                    date_of_death=pre_note_config.date_of_death,
                    return_type=pre_note_config.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

            # If error, set a bad amount
            if pre_note_config.error:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=decimal.Decimal(10000.00),
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=pre_note_config.reason_code,
                    date_of_death=pre_note_config.date_of_death,
                    return_type=pre_note_config.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

        scenario_data_list.append(scenario_data)

    return scenario_data_list


def generate_pub_return_ach(
    db_session, nacha_batch, ach_configs: List[PubPaymentReturnScenarioData], skiprate: int = 0
):
    scenario_data_list = []

    for ach_config in ach_configs:

        # The following data will be generated elsewhere we glue together scenario data.
        mailing_address = AddressFactory.create(
            address_line_one="20 South Ave",
            city="Burlington",
            geo_state_id=1,
            geo_state_text="Massachusetts",
            zip_code="01803",
        )

        employer = EmployerFactory.create()

        employee = EmployeeFactory.create(payment_method_id=PaymentMethod.ACH.payment_method_id)
        employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

        pub_eft = PubEftFactory.create(
            prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
            routing_nbr="123546789",
            account_nbr="123546789",
            bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        )
        EmployeePubEftPairFactory.create(employee=employee, pub_eft=pub_eft)

        claim = ClaimFactory.create(
            employee=employee,
            employer=employer,
            claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        )

        payment = PaymentFactory.create(claim=claim, pub_eft=pub_eft)

        scenario_data = PubPaymentReturnScenarioData(scenario=ach_config, payment=payment)

        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            associated_model=payment,
            outcome=state_log_util.build_outcome("test"),
            db_session=db_session,
        )

        skip = _should_skip(skiprate)

        if not skip:
            if not ach_config.no_response:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=payment.amount,
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=ach_config.reason_code,
                    date_of_death=ach_config.date_of_death,
                    return_type=ach_config.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

            if ach_config.error:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=decimal.Decimal(10000.00),
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=ach_config.reason_code,
                    date_of_death=ach_config.date_of_death,
                    return_type=ach_config.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

        scenario_data_list.append(scenario_data)

    return scenario_data_list


def generate_pub_return(
    db_session,
    folder_location,
    pre_note_configs: List[PubPaymentReturnScenario] = pre_note_configs,
    ach_config: List[PubPaymentReturnScenario] = ach_configs,
    skiprate: int = 0,
) -> Tuple[List[PubPaymentReturnScenarioData], List[PubPaymentReturnScenarioData]]:
    effective_date = datetime.now()
    today = datetime.today()

    nacha_file = NachaFile()
    batch = NachaBatch(effective_date, today)

    nacha_file.add_batch(batch)

    prenote_scenario_data = generate_pub_return_prenote(
        db_session, batch, pre_note_configs, skiprate
    )
    ach_scenario_data = generate_pub_return_ach(db_session, batch, ach_config, skiprate)

    write_file(folder_location, nacha_file)

    return (prenote_scenario_data, ach_scenario_data)


def generate_pub_payment_return_file():
    logging.init(__name__)

    logger.info("Generating pub payment return file.")

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder

    skiprate = int(args.skiprate)

    if skiprate < 0 or skiprate > 100:
        raise Exception("Error rate must be an integer between 0 and 100")

    generate_pub_return(db_session, folder_path, skiprate=skiprate)

    logger.info("Done generating payment return file.")


# given a skip rate between 0 and 100, return true based on this percentage.
def _should_skip(skiprate):
    random_number = randrange(100)
    return random_number < skiprate

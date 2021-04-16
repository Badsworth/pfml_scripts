import argparse
import decimal
import os
from random import randrange
from typing import List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as delegated_payments_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import State
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    NachaBatchType,
    create_nacha_batch,
    get_trans_code,
)
from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    ScenarioData,
    ScenarioDataConfig,
    ScenarioName,
    ScenarioNameWithCount,
    generate_scenario_dataset,
)
from massgov.pfml.delegated_payments.util.ach.nacha import (
    NachaAddendumResponse,
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


def write_file(folder_path: str, nacha_file: NachaFile) -> None:
    now = payments_util.get_now()
    payment_return_filename = delegated_payments_util.Constants.PUB_FILENAME_TEMPLATE.format(
        "PUB-NACHA", now.strftime("%Y%m%d"),
    )

    file_content = nacha_file.to_bytes()

    full_path = os.path.join(folder_path, payment_return_filename)

    with file_util.write_file(full_path, mode="wb") as pub_file:
        pub_file.write(file_content)


def generate_pub_return_prenote(
    db_session: db.Session, scenario_dataset: List[ScenarioData], folder_path: str,
) -> None:
    nacha_file = NachaFile()
    nacha_batch = create_nacha_batch(NachaBatchType.MEDICAL_LEAVE)

    nacha_file.add_batch(nacha_batch)

    for scenario_data in scenario_dataset:
        scenario_descriptor = scenario_data.scenario_descriptor
        payment = scenario_data.payment
        employee = scenario_data.employee

        if payment is None:
            logger.info("Skipping scenario data with empty payment")
            continue

        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_EFT_PRENOTE_SENT,
            associated_model=payment,
            outcome=state_log_util.build_outcome("test"),
            db_session=db_session,
        )

        skip = scenario_descriptor.should_skip

        # If there should be a response, add it to the NACHA file.
        if not skip:
            if not scenario_descriptor.no_response:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=payment.amount,
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=scenario_descriptor.reason_code,
                    date_of_death=employee.date_of_death,
                    return_type=scenario_descriptor.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

            # If error, set a bad amount
            if scenario_descriptor.should_error:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=decimal.Decimal(10000.00),
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=scenario_descriptor.reason_code,
                    date_of_death=employee.date_of_death,
                    return_type=scenario_descriptor.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

    write_file(folder_path, nacha_file)


def generate_pub_return_ach(
    db_session: db.Session, scenario_dataset: List[ScenarioData], folder_path: str,
) -> None:
    nacha_file = NachaFile()
    nacha_batch = create_nacha_batch(NachaBatchType.MEDICAL_LEAVE)

    nacha_file.add_batch(nacha_batch)

    for scenario_data in scenario_dataset:
        scenario_descriptor = scenario_data.scenario_descriptor
        payment = scenario_data.payment
        employee = scenario_data.employee

        if payment is None:
            logger.info("Skipping scenario data with empty payment")
            continue

        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            associated_model=payment,
            outcome=state_log_util.build_outcome("test"),
            db_session=db_session,
        )

        skip = scenario_descriptor.should_skip

        if not skip:
            if not scenario_descriptor.no_response:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=payment.amount,
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=scenario_descriptor.reason_code,
                    date_of_death=employee.date_of_death,
                    return_type=scenario_descriptor.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

            if scenario_descriptor.should_error:
                entry = NachaEntry(
                    trans_code=get_trans_code(payment.pub_eft.bank_account_type_id, False, False),
                    receiving_dfi_id=payment.pub_eft.routing_nbr,
                    dfi_act_num=payment.pub_eft.account_nbr,
                    amount=decimal.Decimal(10000.00),
                    id=f"P{payment.pub_individual_id}",
                    name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
                )

                addendum = NachaAddendumResponse(
                    return_reason_code=scenario_descriptor.reason_code,
                    date_of_death=employee.date_of_death,
                    return_type=scenario_descriptor.return_type,
                )

                nacha_batch.add_entry(entry, addendum)

    write_file(folder_path, nacha_file)


def generate_pub_payment_return_file():
    logging.init(__name__)

    logger.info("Generating pub payment return file.")

    db_session = db.init(sync_lookups=True)
    db.models.factories.db_session = db_session

    args = parser.parse_args()
    folder_path = args.folder

    scaenario_name_with_count = ScenarioNameWithCount(scenario_name=ScenarioName.SCENARIO_A, count=1)

    config = ScenarioDataConfig(scenarios_with_count=[scaenario_name_with_count],)
    scenario_dataset = generate_scenario_dataset(config)

    generate_pub_return_prenote(db_session, scenario_dataset, folder_path)
    generate_pub_return_ach(db_session, scenario_dataset, folder_path)

    logger.info("Done generating payment return file.")


# given a skip rate between 0 and 100, return true based on this percentage.
def _should_skip(skiprate):
    random_number = randrange(100)
    return random_number < skiprate

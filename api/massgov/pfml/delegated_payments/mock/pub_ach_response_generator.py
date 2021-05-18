import os
from typing import List, Optional

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    NachaBatchType,
    create_nacha_batch,
    get_trans_code,
)
from massgov.pfml.delegated_payments.mock.scenario_data_generator import ScenarioData
from massgov.pfml.delegated_payments.util.ach.nacha import (
    NachaAddendumResponse,
    NachaBatch,
    NachaEntry,
    NachaFile,
)

logger = logging.get_logger(__name__)


class PubACHResponseGenerator:
    def __init__(self, scenario_dataset: List[ScenarioData], folder_path: str):
        self.scenario_dataset = scenario_dataset
        self.folder_path = folder_path
        self.nacha_file = NachaFile()

        self.medical_leave_nacha_batch: Optional[NachaBatch] = None
        self.family_leave_nacha_batch: Optional[NachaBatch] = None

    def run(self):
        for scenario_data in self.scenario_dataset:
            if scenario_data.scenario_descriptor.payment_method != PaymentMethod.ACH:
                continue
            self.add_response_entry_for_scenario(scenario_data)
        self.write_file()

    def add_response_entry_for_scenario(self, scenario_data: ScenarioData) -> None:
        scenario_descriptor = scenario_data.scenario_descriptor
        payment = scenario_data.payment
        employee = scenario_data.employee

        if payment is None:
            logger.warning(
                "Skipping scenario data with empty payment: %s", scenario_descriptor.scenario_name
            )
            return

        if (
            not scenario_descriptor.pub_ach_response_return
            and not scenario_descriptor.pub_ach_response_change_notification
        ):
            logger.warning(
                "Skipping returns for scenario data with name: %s and ci: %s, %s",
                scenario_descriptor.scenario_name,
                scenario_data.payment_c_value,
                scenario_data.payment_i_value,
            )
            return

        nacha_batch_type: NachaBatchType = NachaBatchType.FAMILY_LEAVE
        if scenario_descriptor.claim_type == "Employee" or not scenario_descriptor.prenoted:
            nacha_batch_type = NachaBatchType.MEDICAL_LEAVE

        nacha_batch = self.get_batch_by_type(nacha_batch_type)

        is_return = scenario_descriptor.prenoted
        is_prenote = not is_return

        pub_individual_id = payment.pub_individual_id
        if pub_individual_id and scenario_descriptor.pub_ach_return_payment_id_not_found:
            pub_individual_id = (
                pub_individual_id * 100
            )  # We might want to consider a different approach for this to avoid an overlap if we add a lot of scenarios. Maybe make it negative?

        trans_code = get_trans_code(payment.pub_eft.bank_account_type_id, is_prenote, is_return)

        id_prefix = "E" if is_prenote else "P"

        invlaid_format = (
            scenario_descriptor.pub_ach_return_invalid_payment_id_format
            or scenario_descriptor.pub_ach_return_invalid_prenote_payment_id_format
        )
        id_prefix = "X" + id_prefix if invlaid_format else id_prefix

        if scenario_descriptor.pub_ach_response_return:
            return_type = 99
            return_reason_code = scenario_descriptor.pub_ach_return_reason_code
        elif scenario_descriptor.pub_ach_response_change_notification:
            return_type = 98
            return_reason_code = scenario_descriptor.pub_ach_notification_reason_code
        else:
            raise Exception(
                "Invalid scenario - name: %s, pub_ach_response_return: %s, pub_ach_response_change_notificatio: %s",
                scenario_descriptor.scenario_name,
                scenario_descriptor.pub_ach_response_return,
                scenario_descriptor.pub_ach_response_change_notification,
            )

        entry = NachaEntry(
            trans_code=trans_code,
            receiving_dfi_id=payment.pub_eft.routing_nbr,
            dfi_act_num=payment.pub_eft.account_nbr,
            amount=payment.amount,
            id=f"{id_prefix}{pub_individual_id}",
            name=f"{employee.last_name} {employee.first_name}",
        )

        addendum = NachaAddendumResponse(
            return_type=return_type,
            return_reason_code=return_reason_code,
            date_of_death=employee.date_of_death,
        )

        nacha_batch.add_entry(entry, addendum=addendum)

    def write_file(self) -> None:
        payment_return_filename = payments_util.Constants.FILE_NAME_PUB_NACHA

        file_content = self.nacha_file.to_bytes()

        full_path = os.path.join(self.folder_path, payment_return_filename)

        with file_util.write_file(full_path, mode="wb") as pub_file:
            pub_file.write(file_content)

    def get_batch_by_type(self, nacha_batch_type: NachaBatchType) -> NachaBatch:
        if (
            nacha_batch_type == NachaBatchType.MEDICAL_LEAVE
            or nacha_batch_type == NachaBatchType.PRENOTE
        ):
            if self.medical_leave_nacha_batch is None:
                self.medical_leave_nacha_batch = create_nacha_batch(nacha_batch_type)
                self.nacha_file.add_batch(self.medical_leave_nacha_batch)
            return self.medical_leave_nacha_batch
        elif nacha_batch_type == NachaBatchType.FAMILY_LEAVE:
            if self.family_leave_nacha_batch is None:
                self.family_leave_nacha_batch = create_nacha_batch(nacha_batch_type)
                self.nacha_file.add_batch(self.family_leave_nacha_batch)
            return self.family_leave_nacha_batch
        else:
            raise Exception("Unexpected nacha batch type")

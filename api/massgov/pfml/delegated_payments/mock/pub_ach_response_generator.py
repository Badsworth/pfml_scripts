from massgov.pfml.delegated_payments.mock.scenario_data_generator import (
    ScenarioData,
)
from massgov.pfml.db.models.employees import (
    ClaimType,
    PaymentMethod,
)
from massgov.pfml.delegated_payments.delegated_payments_nacha import (
    NachaBatchType,
    create_nacha_batch,
    get_trans_code,
)
from massgov.pfml.delegated_payments.util.ach.nacha import (
    NachaAddendumResponse,
    NachaBatch,
    NachaEntry,
    NachaFile,
)


def write_file(folder_path: str, nacha_file: NachaFile) -> None:
    now = payments_util.get_now()
    timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
    payment_return_filename = f"{timestamp}-{delegated_payments_util.Constants.FILE_NAME_PUB_NACHA}"

    file_content = nacha_file.to_bytes()

    full_path = os.path.join(folder_path, payment_return_filename)

    with file_util.write_file(full_path, mode="wb") as pub_file:
        pub_file.write(file_content)


def get_or_create_nacha_batch_by_type(nacha_file: NachaFile, nacha_batch_type: NachaBatchType):
    if (
        nacha_batch_type == NachaBatchType.MEDICAL_LEAVE
        or nacha_batch_type == NachaBatchType.PRENOTE
    ):
        description = Constants.description_medical_leave
    elif nacha_batch_type == NachaBatchType.FAMILY_LEAVE:
        description = Constants.description_family_leave

    nacha_batch: Optional[NachaBatch] = nacha_file.get_batch_by_description(description)
    if nacha_batch is None:
        nacha_batch = create_nacha_batch(nacha_batch_type)
        nacha_file.add_batch(nacha_batch)

    return nacha_batch


def add_response_entry_for_scenario(scenario_data: ScenarioData, nacha_file: NachaFile):
    scenario_descriptor = scenario_data.scenario_descriptor
    payment = scenario_data.payment

    if payment is None:
        logger.warning("Skipping scenario data with empty payment")
        continue

    if scenario_descriptor.pub_ach_response_return or scenario_descriptor.pub_ach_response_change_notification:
        logger.info("Skipping returns for scenario data with ci: %s, %s", scenario_data.payment_c_value, scenario_data.payment_i_value)
        continue

    nacha_batch_type: NachaBatchType = NachaBatchType.FAMILY_LEAVE
    if scenario_descriptor.claim_type == ClaimType.MEDICAL_LEAVE or not scenario_descriptor.prenoted:
        nacha_batch_type = NachaBatchType.MEDICAL_LEAVE
    
    nacha_batch: NachaBatch = get_or_create_nacha_batch_by_type(nacha_file, nacha_batch_type)

    is_return = scenario_descriptor.prenoted
    is_prenote = not is_return

    trans_code = get_trans_code(payment.pub_eft.bank_account_type_id, is_prenote, is_return)

    id_prefix = "E" if is_prenote else "P"

    if scenario_descriptor.pub_ach_response_return:
        record_type = 99
        return_reason_code = scenario_descriptor.pub_ach_return_reason_code
    elif scenario_descriptor.pub_ach_response_change_notification:
        record_type = 98
        return_reason_code = scenario_descriptor.pub_ach_notification_reason_code
    else:
        raise Exception("Invalid scenario")


    entry = NachaEntry(
        trans_code=trans_code,
        receiving_dfi_id=payment.pub_eft.routing_nbr,
        dfi_act_num=payment.pub_eft.account_nbr,
        amount=payment.amount,
        id=f"{id_prefix}{payment.pub_individual_id}",
        name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
    )

    addendum = NachaAddendumResponse(
        return_type=return_type,
        return_reason_code=return_reason_code,
        date_of_death=employee.date_of_death,        
    )

    nacha_batch.add_entry(entry, addendum=addendum)

    
def generate_pub_ach_return(scenario_dataset: List[ScenarioData], folder_path: str):
    nacha_file: NachaFile = NachaFile()

    for scenario_data in scenario_dataset:
        if not scenario_data.scenario_descriptor.payment_method == PaymentMethod.ACH:
            continue

        add_response_entry_for_scenario(scenario_data, nacha_file)

    write_file(folder_path, nacha_file)
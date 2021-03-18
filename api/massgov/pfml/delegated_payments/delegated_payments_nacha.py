from datetime import datetime
from typing import List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Payment, PaymentMethod, ReferenceFileType, State
from massgov.pfml.delegated_payments.util.ach.nacha import NachaBatch, NachaEntry, NachaFile

logger = logging.get_logger(__name__)

PAYMENT_STATE_LOG_PICKUP_STATE = State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT


def add_payments_to_nacha_batch(db_session, nacha_batch, payments) -> NachaFile:
    if len(payments) == 0:
        raise Exception("No Payment records added to PUB")

    for payment in payments:
        entry = NachaEntry(
            receiving_dfi_id=payment.claim.employee.eft.routing_nbr,
            dfi_act_num=payment.claim.employee.eft.account_nbr,
            amount=payment.amount,
            # TODO: we are still determining what this ID value should be.
            id=f"{payment.fineos_pei_c_value}{payment.fineos_pei_i_value}",
            name=f"{payment.claim.employee.last_name} {payment.claim.employee.first_name}",
        )

        state_log_util.create_finished_state_log(
            associated_model=payment,
            end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            outcome=state_log_util.build_outcome("PUB transaction sent"),
            db_session=db_session,
        )

        nacha_batch.add_entry(entry)


def upload_nacha_file_to_s3(db_session, nacha_file) -> str:
    logger.info("Creating NACHA files")

    now = payments_util.get_now()
    nacha_file.finalize()

    ref_file = payments_util.create_pub_reference_file(
        now,
        ReferenceFileType.PUB_TRANSACTION,
        db_session,
        payments_config.get_s3_config().pfml_pub_outbound_path,
    )

    with file_util.write_file(ref_file.file_location, mode="wb") as pub_file:
        pub_file.write(nacha_file.to_bytes())

    db_session.commit()

    return ref_file.file_location


def create_nacha_file(db_session: db.Session) -> NachaFile:
    effective_date = datetime.now()
    today = datetime.today()

    file = NachaFile()
    batch = NachaBatch(effective_date, today)
    payments = _get_eligible_payments(db_session)

    add_payments_to_nacha_batch(db_session, batch, payments)

    file.add_batch(batch)
    batch.finalize()

    return file


def _get_eligible_payments(db_session: db.Session) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=PAYMENT_STATE_LOG_PICKUP_STATE,
        db_session=db_session,
    )

    # Raise an error if any payments
    for state_log in state_logs:
        if state_log.payment.disb_method_id != PaymentMethod.ACH.payment_method_id:
            raise Exception(
                f"Non-ACH payment method detected in state log: { state_log.state_log_id }"
            )

    ach_payments = [state_log.payment for state_log in state_logs]

    return ach_payments

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as pfml_db
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.common as common
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Employee, State, StateLog, TaxIdentifier
from massgov.pfml.util import assert_never

logger = logging.get_logger(__name__)


def process(pfml_db_session: pfml_db.Session, data_mart_engine: data_mart.Engine) -> None:
    common.process_employees_in_state(
        pfml_db_session, data_mart_engine, State.EFT_PENDING, process_state_log
    )


def process_state_log(
    pfml_db_session: pfml_db.Session,
    data_mart_conn: data_mart.Connection,
    state_log: StateLog,
    employee: Employee,
    tax_id: TaxIdentifier,
) -> None:
    vendor_info = data_mart.get_vendor_info(data_mart_conn, tax_id.tax_identifier)

    if not vendor_info:
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=state_log.start_state,
            outcome=state_log_util.build_outcome("Queried Data Mart: Vendor does not exist yet"),
            db_session=pfml_db_session,
        )
        return None

    if (
        vendor_info.eft_status is None
        or vendor_info.eft_status is data_mart.EFTStatus.PRENOTE_REQUESTED
        or vendor_info.eft_status is data_mart.EFTStatus.PRENOTE_PENDING
    ):
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=state_log.start_state,
            outcome=state_log_util.build_outcome("Queried Data Mart: EFT pending"),
            db_session=pfml_db_session,
        )
    elif (
        vendor_info.eft_status is data_mart.EFTStatus.NOT_APPLICABLE
        or vendor_info.eft_status is data_mart.EFTStatus.NOT_ELIGIBILE_FOR_EFT
        or vendor_info.eft_status is data_mart.EFTStatus.EFT_HOLD
        or vendor_info.eft_status is data_mart.EFTStatus.PRENOTE_REJECTED
    ):
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.ADD_TO_EFT_ERROR_REPORT,
            outcome=state_log_util.build_outcome(
                f"Queried Data Mart: EFT error. Prenote reason: {vendor_info.prenote_return_reason} {vendor_info.prenote_hold_reason}"
            ),
            db_session=pfml_db_session,
        )
    elif vendor_info.eft_status is data_mart.EFTStatus.ELIGIBILE_FOR_EFT:
        if vendor_info.generate_eft_payment is True:
            state_log_util.finish_state_log(
                state_log=state_log,
                end_state=State.EFT_ELIGIBLE,
                outcome=state_log_util.build_outcome("Valid EFT information"),
                db_session=pfml_db_session,
            )
        else:
            state_log_util.finish_state_log(
                state_log=state_log,
                end_state=State.ADD_TO_EFT_ERROR_REPORT,
                outcome=state_log_util.build_outcome(
                    "Vendor eft_status is ELIGIBILE_FOR_EFT, but generate_eft_payment is not true"
                ),
                db_session=pfml_db_session,
            )
    else:
        assert_never(vendor_info.eft_status)

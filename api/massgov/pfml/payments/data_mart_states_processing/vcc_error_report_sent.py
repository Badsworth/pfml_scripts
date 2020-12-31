import massgov.pfml.db as pfml_db
import massgov.pfml.payments.data_mart as data_mart
import massgov.pfml.payments.data_mart_states_processing.common as common
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Employee, State, StateLog, TaxIdentifier

logger = logging.get_logger(__name__)


def process(pfml_db_session: pfml_db.Session, data_mart_engine: data_mart.Engine) -> None:
    common.process_employees_in_state(
        pfml_db_session, data_mart_engine, State.VCC_ERROR_REPORT_SENT, process_state_log
    )


def process_state_log(
    pfml_db_session: pfml_db.Session,
    data_mart_conn: data_mart.Connection,
    state_log: StateLog,
    employee: Employee,
    tax_id: TaxIdentifier,
) -> None:
    potential_issues = common.query_data_mart_for_issues_and_updates(
        data_mart_conn, employee, tax_id
    )

    # commit any potential employee updates from above before processing
    # potential issues
    pfml_db_session.commit()

    common.process_data_mart_issues(
        pfml_db_session,
        state_log,
        employee,
        potential_issues,
        missing_vendor_state=state_log.start_state,
        mismatched_data_state=state_log.start_state,
    )

from datetime import datetime
from typing import Any, Dict, Optional, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
from massgov.pfml.db.models.employees import LkState, Payment, State, StateLog
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    LkFineosWritebackTransactionStatus,
)


def create_payment_finished_state_log_with_writeback(
    payment: Payment,
    payment_end_state: LkState,
    payment_outcome: Dict[str, Any],
    writeback_transaction_status: LkFineosWritebackTransactionStatus,
    db_session: db.Session,
    writeback_outcome: Optional[Dict[str, Any]] = None,
    start_time: Optional[datetime] = None,
    import_log_id: Optional[int] = None,
) -> StateLog:
    # Create the specified payment flow state log
    payment_state_log = state_log_util.create_finished_state_log(
        payment,
        payment_end_state,
        payment_outcome,
        db_session,
        start_time=start_time,
        import_log_id=import_log_id,
    )

    stage_payment_fineos_writeback(
        payment=payment,
        writeback_transaction_status=writeback_transaction_status,
        outcome=writeback_outcome,
        db_session=db_session,
        start_time=start_time,
        import_log_id=import_log_id,
    )

    return payment_state_log


def stage_payment_fineos_writeback(
    payment: Payment,
    writeback_transaction_status: LkFineosWritebackTransactionStatus,
    db_session: db.Session,
    outcome: Optional[Dict[str, Any]] = None,
    start_time: Optional[datetime] = None,
    import_log_id: Optional[int] = None,
) -> FineosWritebackDetails:
    # Create the state log, note this is in the DELEGATED_PEI_WRITEBACK flow
    writeback_outcome = outcome or state_log_util.build_outcome(
        writeback_transaction_status.transaction_status_description
    )

    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        writeback_outcome,
        db_session,
        start_time=start_time,
        import_log_id=import_log_id,
    )

    # Stage the writeback entry
    writeback_details = FineosWritebackDetails(
        payment=payment,
        transaction_status_id=writeback_transaction_status.transaction_status_id,
        import_log_id=cast(int, import_log_id),
    )
    db_session.add(writeback_details)

    return writeback_details

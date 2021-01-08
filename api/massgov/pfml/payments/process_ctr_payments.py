import massgov.pfml.payments.moveit as moveit
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.payments.ctr_outbound_return import process_ctr_outbound_returns
from massgov.pfml.payments.data_mart_states_processing import (
    process_all_states as process_data_mart,
)
from massgov.pfml.payments.error_reports import send_ctr_error_reports
from massgov.pfml.payments.gax import build_gax_files_for_s3
from massgov.pfml.payments.vcc import build_vcc_files_for_s3
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


def make_db_session() -> db.Session:
    return db.init()


def ctr_process():
    """Entry point for CTR Payment Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    with db.session_scope(make_db_session(), close=True) as db_session:
        _ctr_process(db_session)


def _ctr_process(db_session: db.Session) -> None:
    """Process CTR Payments"""
    logger.info("Start processing CTR payments")

    # 1. Grab files from SFTP/MOVEit, upload to S3
    moveit.pickup_files_from_moveit(db_session)

    # 2. Process Outbound Return files from CTR
    process_ctr_outbound_returns(db_session)

    # 3.Run queries against Data Mart
    process_data_mart(db_session)

    # 4. Create GAX files
    build_gax_files_for_s3(db_session)

    # 5. Create VCC files
    build_vcc_files_for_s3(db_session)

    # 6. Upload files from S3 to MOVEit
    moveit.send_files_to_moveit(db_session)

    # 7. Send BIEVNT and other OSM Reports
    send_ctr_error_reports(db_session)

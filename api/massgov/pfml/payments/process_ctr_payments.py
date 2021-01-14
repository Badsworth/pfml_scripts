import argparse
import sys
from typing import List

import massgov.pfml.payments.moveit as moveit
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.payments.data_mart_states_processing import (
    process_all_states as process_data_mart,
)
from massgov.pfml.payments.error_reports import send_ctr_error_reports
from massgov.pfml.payments.gax import build_gax_files_for_s3
from massgov.pfml.payments.outbound_return import process_outbound_returns
from massgov.pfml.payments.vcc import build_vcc_files_for_s3
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


ALL = "ALL"
PICKUP_FROM_MOVEIT = "pickup-from-moveit"
CTR_OUTBOUND_RETURN = "ctr-outbound-return"
DATA_MART = "data-mart"
GAX = "gax"
VCC = "vcc"
SEND_TO_MOVEIT = "send-to-moveit"
ERROR_REPORT = "error-report"
ALLOWED_VALUES = [
    ALL,
    PICKUP_FROM_MOVEIT,
    CTR_OUTBOUND_RETURN,
    DATA_MART,
    GAX,
    VCC,
    SEND_TO_MOVEIT,
    ERROR_REPORT,
]


class Configuration:
    pickup_from_moveit: bool
    do_ctr_outbound_return: bool
    query_data_mart: bool
    make_gax: bool
    make_vcc: bool
    send_to_moveit: bool
    make_error_report: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Process payment and vendor data for the Comptroller"
        )
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=[ALL],
            help="Indicate which steps of the process to run",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        if ALL in steps:
            self.pickup_from_moveit = True
            self.do_ctr_outbound_return = True
            self.query_data_mart = True
            self.make_gax = True
            self.make_vcc = True
            self.send_to_moveit = True
            self.make_error_report = True
        else:
            self.pickup_from_moveit = PICKUP_FROM_MOVEIT in steps
            self.do_ctr_outbound_return = CTR_OUTBOUND_RETURN in steps
            self.query_data_mart = DATA_MART in steps
            self.make_gax = GAX in steps
            self.make_vcc = VCC in steps
            self.send_to_moveit = SEND_TO_MOVEIT in steps
            self.make_error_report = ERROR_REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def ctr_process():
    """Entry point for CTR Payment Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session:
        _ctr_process(db_session, config)


def _ctr_process(db_session: db.Session, config: Configuration) -> None:
    """Process CTR Payments"""
    logger.info("Start processing CTR payments")

    # 1. Grab files from SFTP/MOVEit, upload to S3
    if config.pickup_from_moveit:
        moveit.pickup_files_from_moveit(db_session)

    # 2. Process Outbound Return files from CTR
    if config.do_ctr_outbound_return:
        process_outbound_returns(db_session)

    # 3.Run queries against Data Mart
    if config.query_data_mart:
        process_data_mart(db_session)

    # 4. Create GAX files, send BIEVNT email
    if config.make_gax:
        build_gax_files_for_s3(db_session)

    # 5. Create VCC files, send BIEVNT email
    if config.make_vcc:
        build_vcc_files_for_s3(db_session)

    # 6. Upload files from S3 to MOVEit
    if config.send_to_moveit:
        moveit.send_files_to_moveit(db_session)

    # 7. Send OSM Reports
    if config.make_error_report:
        send_ctr_error_reports(db_session)

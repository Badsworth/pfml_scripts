import argparse
import pathlib
import sys
import tempfile
from typing import List

import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.payments.error_reports import send_fineos_error_reports
from massgov.pfml.payments.fineos_payment_export import (
    process_extract_data as process_fineos_extract_data,
)
from massgov.pfml.payments.fineos_pei_writeback import process_payments_for_writeback
from massgov.pfml.payments.fineos_vendor_export import process_vendor_extract_data
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)

ALL = "ALL"
VENDOR_EXTRACT = "vendor-extract"
PAYMENT_EXTRACT = "payment-extract"
PEI_WRITEBACK = "pei-writeback"
ERROR_REPORT = "error-report"
ALLOWED_VALUES = [ALL, VENDOR_EXTRACT, PAYMENT_EXTRACT, PEI_WRITEBACK, ERROR_REPORT]


class Configuration:
    do_vendor_extract: bool
    do_payment_extract: bool
    make_pei_writeback: bool
    make_error_report: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Process FINEOS payment and vendor exports")
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
            self.do_vendor_extract = True
            self.do_payment_extract = True
            self.make_pei_writeback = True
            self.make_error_report = True
        else:
            self.do_vendor_extract = VENDOR_EXTRACT in steps
            self.do_payment_extract = PAYMENT_EXTRACT in steps
            self.make_pei_writeback = PEI_WRITEBACK in steps
            self.make_error_report = ERROR_REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def fineos_process():
    """Entry point for FINEOS Payment Exports Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session:
        _fineos_process(db_session, config)


def _fineos_process(db_session: db.Session, config: Configuration) -> None:
    """Process FINEOS Payment Exports"""
    logger.info("Start - FINEOS Payments ECS Task")

    # 1. Process Vendor Export files from FINEOS
    if config.do_vendor_extract:
        try:
            process_vendor_extract_data(db_session)
        except Exception:
            logger.exception("Error processing payments vendor extract")

    # 2. Process Payment Export files from FINEOS
    if config.do_payment_extract:
        try:
            # TODO move temporary directory into top level function, only pass db session
            with tempfile.TemporaryDirectory() as download_directory:
                process_fineos_extract_data(pathlib.Path(download_directory), db_session)
        except Exception:
            logger.exception("Error processing FINEOS payments extract")

    # 3. Create PEI Writeback files and send to FINEOS
    if config.make_pei_writeback:
        try:
            process_payments_for_writeback(db_session)
        except Exception:
            logger.exception("Error creating and sending PEI writeback files to FINEOS")

    # 4. Send OSM Reports
    if config.make_error_report:
        try:
            send_fineos_error_reports(db_session)
        except Exception:
            logger.exception("Error sending FINEOS error reports")

    logger.info("Done - FINEOS Payments ECS Task")

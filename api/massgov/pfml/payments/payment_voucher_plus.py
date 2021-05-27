#
# New and improved! Payment Voucher+ - main entrypoint.
#
# Runs the following in order:
# 1. Processes FINEOS vendor extracts and generates the CPS vendor extract error report
# 2. Runs the Data Mart queries
# 3. Creates the Payment Voucher
#
# Steps 1 & 2 make database changes, but step 3 does not.
#
# To run this as an ECS task:
#   bin/run-ecs-task/run-task.sh <env> manual-payments <FIRSTNAME>.<LASTNAME> payments-payment-voucher-plus --steps all
#
# Test run this locally:
#
# Requires these env vars:
# - FINEOS_DATA_EXPORT_PATH=
# - PFML_FINEOS_INBOUND_PATH=
# - PFML_ERROR_REPORTS_PATH=
# - PFML_VOUCHER_OUTPUT_PATH=
# - FINEOS_VENDOR_MAX_HISTORY_DATE=
# - DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS=
#
# Run:
#   poetry run fineos-payments-mock-generate --folder mock_fineos_payments_files --fein 526000028 --ssn 626000028 2>&1 | python3 -u massgov/pfml/util/logging/decodelog.py
#   poetry run payments-payment-voucher-plus 2>&1 | python3 -u massgov/pfml/util/logging/decodelog.py
#

import argparse
import datetime
import os
import sys
from typing import List, Optional

import massgov.pfml.db as db
import massgov.pfml.payments.config as payments_config
import massgov.pfml.util.logging as logging
from massgov.pfml.payments.data_mart_states_processing import DataMartStep
from massgov.pfml.payments.error_reports import VendorExtractErrorReportStep
from massgov.pfml.payments.fineos_vendor_export import VendorExtractStep
from massgov.pfml.payments.manual.payment_voucher import Configuration as VoucherConfiguration
from massgov.pfml.payments.manual.payment_voucher import PaymentVoucherStep
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)


ALL = "all"
VENDOR_EXTRACT = "vendor-extract"
DATA_MART = "data-mart"
PAYMENT_VOUCHER = "payment-voucher"
ALLOWED_VALUES = [
    ALL,
    VENDOR_EXTRACT,
    DATA_MART,
    PAYMENT_VOUCHER,
]


class Configuration:
    run_vendor_extract: bool
    run_data_mart: bool
    run_payment_voucher: bool
    voucher_config: Optional[VoucherConfiguration] = None

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Process Payment Voucher and supporting actions."
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
            self.run_vendor_extract = True
            self.run_data_mart = True
            self.run_payment_voucher = True
        else:
            self.run_vendor_extract = VENDOR_EXTRACT in steps
            self.run_data_mart = DATA_MART in steps
            self.run_payment_voucher = PAYMENT_VOUCHER in steps

        if self.run_payment_voucher:
            payments_s3_config = payments_config.get_s3_config()
            today_datestr = datetime.date.today().isoformat()
            output_path = os.path.join(payments_s3_config.pfml_voucher_output_path, today_datestr)
            self.voucher_config = VoucherConfiguration(
                [payments_s3_config.fineos_data_export_path, output_path]
            )


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("payments-payment-voucher-plus")
def main():
    """Entry point for Payment Voucher plus supporting actions"""
    try:
        config = Configuration(sys.argv[1:])
    except Exception as e:
        logger.exception("%s", e)
        sys.exit(1)

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _payment_voucher_plus(db_session, log_entry_db_session, config)


def _payment_voucher_plus(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Run Payment Voucher+ Process."""
    logger.info("Start - Payment Voucher+ ECS Task")

    # Process FINEOS vendor extracts and generate CPS vendor extract error report.
    if config.run_vendor_extract:
        try:
            VendorExtractStep(
                db_session=db_session, log_entry_db_session=log_entry_db_session
            ).run()
        except Exception:
            logger.exception("Unexpected exception encountered while running vendor extract step.")

        try:
            VendorExtractErrorReportStep(
                db_session=db_session, log_entry_db_session=log_entry_db_session
            ).run()
        except Exception:
            logger.exception(
                "Unexpected exception encountered while running vendor extract error report step."
            )

    # Run Data Mart queries.
    if config.run_data_mart:
        try:
            DataMartStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()
        except Exception:
            logger.exception("Unexpected exception encountered while running data mart step.")

    # Create the Payment Voucher.
    if config.run_payment_voucher:
        try:
            if config.voucher_config is None:
                logger.error("Unexpected error with payment voucher configuration")
            else:
                PaymentVoucherStep(
                    db_session=db_session,
                    log_entry_db_session=log_entry_db_session,
                    config=config.voucher_config,
                ).run()
        except Exception:
            logger.exception("Unexpected exception encountered while running payment voucher step.")

    logger.info("End - Payment Voucher+ ECS Task")

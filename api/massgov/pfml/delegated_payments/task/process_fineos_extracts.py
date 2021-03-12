import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.delegated_fineos_claimant_extract import ClaimantExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import PaymentExtractStep
from massgov.pfml.delegated_payments.state_cleanup_step import StateCleanupStep
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


ALL = "ALL"
RUN_AUDIT_CLEANUP = "audit-cleanup"
CLAIMANT_EXTRACT = "claimant-extract"
PAYMENT_EXTRACT = "payment-extract"
SAMPLE_PAYMENTS = "sample-payments"
CREATE_AUDIT_REPORT = "audit-report"
ERROR_REPORT = "error-report"
ALLOWED_VALUES = [
    ALL,
    RUN_AUDIT_CLEANUP,
    CLAIMANT_EXTRACT,
    PAYMENT_EXTRACT,
    SAMPLE_PAYMENTS,
    CREATE_AUDIT_REPORT,
    ERROR_REPORT,
]


class Configuration:
    do_audit_cleanup: bool
    do_claimant_extract: bool
    do_payment_extract: bool
    do_sample_payments: bool
    make_audit_report: bool
    make_error_report: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Process FINEOS payment and claimant exports and create an audit report"
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
            self.do_audit_cleanup = True
            self.do_claimant_extract = True
            self.do_payment_extract = True
            self.do_sample_payments = True
            self.make_audit_report = True
            self.make_error_report = True
        else:
            self.do_audit_cleanup = RUN_AUDIT_CLEANUP in steps
            self.do_claimant_extract = CLAIMANT_EXTRACT in steps
            self.do_payment_extract = PAYMENT_EXTRACT in steps
            self.do_sample_payments = SAMPLE_PAYMENTS in steps
            self.make_audit_report = CREATE_AUDIT_REPORT in steps
            self.make_error_report = CREATE_AUDIT_REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def main():
    """Entry point for PUB Payment Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session:
        _process_fineos_extracts(db_session, config)


def _process_fineos_extracts(db_session_raw: db.Session, config: Configuration) -> None:
    """Process FINEOS Payments Extracts"""
    logger.info("Start - FINEOS Payment+Claimant Extract ECS Task")

    # db_session_raw is used for the log entries and
    # this db_session is used by each of the steps directly.
    with db.session_scope(db_session_raw) as db_session:
        if config.do_audit_cleanup:
            StateCleanupStep(db_session=db_session, log_entry_db_session=db_session_raw).run()

        if config.do_claimant_extract:
            ClaimantExtractStep(db_session=db_session, log_entry_db_session=db_session_raw).run()

        if config.do_payment_extract:
            PaymentExtractStep(db_session=db_session, log_entry_db_session=db_session_raw).run()

        if config.do_sample_payments:
            # TODO
            # SamplePaymentStep(db_session=db_session, log_entry_db_session=db_session_raw).run()
            pass

        if config.make_audit_report:
            # TODO
            # MakeAuditReportStep(db_session=db_session, log_entry_db_session=db_session_raw).run()
            pass

        if config.make_error_report:
            # TODO - we might not need to do this anymore
            pass

    logger.info("End - FINEOS Payment+Claimant Extract ECS Task")

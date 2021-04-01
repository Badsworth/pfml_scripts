import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.address_validation import AddressValidationStep
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditReportStep,
)
from massgov.pfml.delegated_payments.delegated_fineos_claimant_extract import ClaimantExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import PaymentExtractStep
from massgov.pfml.delegated_payments.state_cleanup_step import StateCleanupStep
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


ALL = "ALL"
RUN_AUDIT_CLEANUP = "audit-cleanup"
CLAIMANT_EXTRACT = "claimant-extract"
PAYMENT_EXTRACT = "payment-extract"
VALIDATE_ADDRESSES = "validate-addresses"
CREATE_AUDIT_REPORT = "audit-report"
ERROR_REPORT = "error-report"
ALLOWED_VALUES = [
    ALL,
    RUN_AUDIT_CLEANUP,
    CLAIMANT_EXTRACT,
    PAYMENT_EXTRACT,
    VALIDATE_ADDRESSES,
    CREATE_AUDIT_REPORT,
    ERROR_REPORT,
]


class Configuration:
    do_audit_cleanup: bool
    do_claimant_extract: bool
    do_payment_extract: bool
    validate_addresses: bool
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
            self.validate_addresses = True
            self.make_audit_report = True
            self.make_error_report = True
        else:
            self.do_audit_cleanup = RUN_AUDIT_CLEANUP in steps
            self.do_claimant_extract = CLAIMANT_EXTRACT in steps
            self.do_payment_extract = PAYMENT_EXTRACT in steps
            self.validate_addresses = VALIDATE_ADDRESSES in steps
            self.make_audit_report = CREATE_AUDIT_REPORT in steps
            self.make_error_report = CREATE_AUDIT_REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def main():
    """Entry point for PUB Payment Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_fineos_extracts(db_session, log_entry_db_session, config)


def _process_fineos_extracts(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process FINEOS Payments Extracts"""
    logger.info("Start - FINEOS Payment+Claimant Extract ECS Task")

    if config.do_audit_cleanup:
        StateCleanupStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.do_claimant_extract:
        ClaimantExtractStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.do_payment_extract:
        PaymentExtractStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.validate_addresses:
        AddressValidationStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_audit_report:
        PaymentAuditReportStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_error_report:
        # TODO
        pass

    logger.info("End - FINEOS Payment+Claimant Extract ECS Task")

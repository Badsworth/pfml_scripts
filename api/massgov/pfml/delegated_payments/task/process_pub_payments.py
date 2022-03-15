import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.audit.delegated_payment_rejects import PaymentRejectsStep
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import PaymentExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.delegated_fineos_related_payment_post_processing import (
    RelatedPaymentsPostProcessingStep,
)
from massgov.pfml.delegated_payments.payment_methods_split_step import PaymentMethodsSplitStep
from massgov.pfml.delegated_payments.pickup_response_files_step import PickupResponseFilesStep
from massgov.pfml.delegated_payments.pub.transaction_file_creator import TransactionFileCreatorStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    CREATE_PUB_FILES_REPORTS,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)


ALL = "ALL"
PICKUP_FILES = "pickup"
PROCESS_AUDIT_REJECT = "audit-reject"
SPLIT_PAYMENT_METHODS = "split-payment-methods"
PUB_TRANSACTION = "pub-transaction"
RELATED_PAYMENT_POST_PROCESSING = "related-payment-post-processing"
CREATE_PEI_WRITEBACK = "initial-writeback"
REPORT = "report"
ALLOWED_VALUES = [
    ALL,
    PICKUP_FILES,
    PROCESS_AUDIT_REJECT,
    SPLIT_PAYMENT_METHODS,
    PUB_TRANSACTION,
    RELATED_PAYMENT_POST_PROCESSING,
    CREATE_PEI_WRITEBACK,
    REPORT,
]


class Configuration:
    pickup_files: bool
    process_audit_reject: bool
    split_payment_methods: bool
    pub_transaction: bool
    do_related_payment_post_processing: bool
    create_pei_writeback: bool
    make_reports: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Create and send PUB transactions for ACH pre-notes, check, and ACH payments"
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
            self.pickup_files = True
            self.process_audit_reject = True
            self.split_payment_methods = True
            self.pub_transaction = True
            self.do_related_payment_post_processing = True
            self.create_pei_writeback = True
            self.make_reports = True
        else:
            self.pickup_files = PICKUP_FILES in steps
            self.process_audit_reject = PROCESS_AUDIT_REJECT in steps
            self.split_payment_methods = SPLIT_PAYMENT_METHODS in steps
            self.pub_transaction = PUB_TRANSACTION in steps
            self.do_related_payment_post_processing = RELATED_PAYMENT_POST_PROCESSING in steps
            self.create_pei_writeback = CREATE_PEI_WRITEBACK in steps
            self.make_reports = REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-create-pub-files")
def main():
    """Entry point for PUB Payment Processing"""
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_pub_payments(db_session, log_entry_db_session, config)


def _process_pub_payments(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    """Process PUB Payments"""
    logger.info("Start - PUB Payments ECS Task")
    start_time = get_now_us_eastern()

    if config.pickup_files:
        PickupResponseFilesStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.process_audit_reject:
        PaymentRejectsStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.split_payment_methods:
        PaymentMethodsSplitStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.pub_transaction:
        TransactionFileCreatorStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.do_related_payment_post_processing:
        RelatedPaymentsPostProcessingStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.create_pei_writeback:
        FineosPeiWritebackStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_reports:
        ReportStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            report_names=CREATE_PUB_FILES_REPORTS,
            sources_to_clear_from_report_queue=[PaymentExtractStep],
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-create-pub-files")
    logger.info("Done - PUB Payments ECS Task")

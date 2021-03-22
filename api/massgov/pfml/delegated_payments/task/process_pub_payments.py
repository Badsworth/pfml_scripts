import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.audit.delegated_payment_rejects import PaymentRejectsStep
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.payment_methods_split_step import PaymentMethodsSplitStep
from massgov.pfml.delegated_payments.pub.transaction_file_creator import TransactionFileCreatorStep
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


ALL = "ALL"
PROCESS_AUDIT_REJECT = "audit-reject"
CREATE_PEI_WRITEBACK = "initial-writeback"
SPLIT_PAYMENT_METHODS = "split-payment-methods"
PUB_TRANSACTION = "pub-transaction"
ALLOWED_VALUES = [
    ALL,
    PROCESS_AUDIT_REJECT,
    CREATE_PEI_WRITEBACK,
    SPLIT_PAYMENT_METHODS,
    PUB_TRANSACTION,
]


class Configuration:
    process_audit_reject: bool
    create_pei_writeback: bool
    split_payment_methods: bool
    pub_transaction: bool

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
            self.process_audit_reject = True
            self.create_pei_writeback = True
            self.split_payment_methods = True
            self.pub_transaction = True
        else:
            self.process_audit_reject = PROCESS_AUDIT_REJECT in steps
            self.create_pei_writeback = CREATE_PEI_WRITEBACK in steps
            self.split_payment_methods = SPLIT_PAYMENT_METHODS in steps
            self.pub_transaction = PUB_TRANSACTION in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


def main():
    """Entry point for PUB Payment Processing"""
    audit.init_security_logging()
    logging.init(__name__)

    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session:
        _process_pub_payments(db_session, config)


def _process_pub_payments(db_session_raw: db.Session, config: Configuration) -> None:
    """Process PUB Payments"""
    logger.info("Start - PUB Payments ECS Task")

    # db_session_raw is used for the log entries and
    # this db_session is used by each of the steps directly.
    with db.session_scope(db_session_raw) as db_session:
        if config.process_audit_reject:
            PaymentRejectsStep(db_session=db_session, log_entry_db_session=db_session_raw).run()

        if config.create_pei_writeback:
            FineosPeiWritebackStep(db_session=db_session, log_entry_db_session=db_session_raw).run()

        if config.split_payment_methods:
            PaymentMethodsSplitStep(
                db_session=db_session, log_entry_db_session=db_session_raw
            ).run()

        if config.pub_transaction:
            TransactionFileCreatorStep(
                db_session=db_session, log_entry_db_session=db_session_raw
            ).run()

    logger.info("Done - PUB Payments ECS Task")

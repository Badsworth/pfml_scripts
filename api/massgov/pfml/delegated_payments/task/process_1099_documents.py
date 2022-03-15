import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.irs_1099.audit_batch import AuditBatchStep
from massgov.pfml.delegated_payments.irs_1099.generate_1099_irs_filing import (
    Generate1099IRSfilingStep,
)
from massgov.pfml.delegated_payments.irs_1099.generate_documents import Generate1099DocumentsStep
from massgov.pfml.delegated_payments.irs_1099.merge_documents import Merge1099Step
from massgov.pfml.delegated_payments.irs_1099.populate_1099 import Populate1099Step
from massgov.pfml.delegated_payments.irs_1099.populate_mmars_payments import (
    PopulateMmarsPaymentsStep,
)
from massgov.pfml.delegated_payments.irs_1099.populate_payments import PopulatePaymentsStep
from massgov.pfml.delegated_payments.irs_1099.populate_refunds import PopulateRefundsStep
from massgov.pfml.delegated_payments.irs_1099.populate_withholdings import PopulateWithholdingsStep
from massgov.pfml.delegated_payments.irs_1099.upload_documents import Upload1099DocumentsStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import IRS_1099_REPORTS
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)

ALL = "ALL"
AUDIT_BATCH = "audit-batch"
POPULATE_MMARS_PAYMENTS = "populate-mmars-payments"
POPULATE_PAYMENTS = "populate-payments"
POPULATE_WITHHOLDINGS = "populate-withholdings"
POPULATE_REFUNDS = "populate-refunds"
POPULATE_1099 = "populate-1099"
GENERATE_1099_DOCUMENTS = "generate-1099-documents"
MERGE_1099_DOCUMENTS = "merge-1099-documents"
GENERATE_1099_IRS_FILING = "generate-1099-irs-filing"
REPORT = "report"
UPLOAD_1099_DOCUMENTS = "upload-1099-documents"
ALLOWED_VALUES = [
    ALL,
    AUDIT_BATCH,
    POPULATE_MMARS_PAYMENTS,
    POPULATE_PAYMENTS,
    POPULATE_WITHHOLDINGS,
    POPULATE_REFUNDS,
    POPULATE_1099,
    GENERATE_1099_DOCUMENTS,
    MERGE_1099_DOCUMENTS,
    GENERATE_1099_IRS_FILING,
    REPORT,
    UPLOAD_1099_DOCUMENTS,
]


class Configuration:
    db_audit_batch: bool
    do_populate_mmars_payments: bool
    do_populate_payments: bool
    db_populate_withholdings: bool
    db_populate_refunds: bool
    db_populate_1099: bool
    generate_1099_documents: bool
    merge_1099_documents: bool
    generate_1099_irs_filing: bool
    make_reports: bool
    upload_1099_documents: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Process 1099 documents and merge 1099 documents and create an audit report"
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
            self.db_audit_batch = True
            self.do_populate_mmars_payments = True
            self.do_populate_payments = True
            self.db_populate_withholdings = True
            self.db_populate_refunds = True
            self.db_populate_1099 = True
            self.generate_1099_documents = True
            self.merge_1099_documents = True
            self.generate_1099_irs_filing = True
            self.make_reports = True
            self.upload_1099_documents = False
        else:
            self.db_audit_batch = AUDIT_BATCH in steps
            self.do_populate_mmars_payments = POPULATE_MMARS_PAYMENTS in steps
            self.do_populate_payments = POPULATE_PAYMENTS in steps
            self.db_populate_withholdings = POPULATE_WITHHOLDINGS in steps
            self.db_populate_refunds = POPULATE_REFUNDS in steps
            self.db_populate_1099 = POPULATE_1099 in steps
            self.generate_1099_documents = GENERATE_1099_DOCUMENTS in steps
            self.merge_1099_documents = MERGE_1099_DOCUMENTS in steps
            self.generate_1099_irs_filing = GENERATE_1099_IRS_FILING in steps
            self.make_reports = REPORT in steps
            self.upload_1099_documents = UPLOAD_1099_DOCUMENTS in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-process-1099-documents")
def main():
    """Entry point for PUB Payment 1099 Documents Processing"""
    config = Configuration(sys.argv[1:])

    with db.session_scope(make_db_session(), close=True) as db_session, db.session_scope(
        make_db_session(), close=True
    ) as log_entry_db_session:
        _process_1099_documents(db_session, log_entry_db_session, config)


def _process_1099_documents(
    db_session: db.Session, log_entry_db_session: db.Session, config: Configuration
) -> None:
    logger.info("Start - 1099 Documents ECS Task")
    start_time = get_now_us_eastern()

    if config.db_audit_batch:
        AuditBatchStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.do_populate_mmars_payments:
        PopulateMmarsPaymentsStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.do_populate_payments:
        PopulatePaymentsStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.db_populate_withholdings:
        PopulateWithholdingsStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.db_populate_refunds:
        PopulateRefundsStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.db_populate_1099:
        Populate1099Step(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.generate_1099_documents:
        Generate1099DocumentsStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.merge_1099_documents:
        Merge1099Step(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.generate_1099_irs_filing:
        Generate1099IRSfilingStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_reports:
        ReportStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            report_names=IRS_1099_REPORTS,
        ).run()

    if config.upload_1099_documents:
        Upload1099DocumentsStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-process-1099-documents")

    logger.info("End - 1099 Documents ECS Task")

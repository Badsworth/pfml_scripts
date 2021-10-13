import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.irs_1099.audit_batch import AuditBatchStep
from massgov.pfml.delegated_payments.irs_1099.generate_documents import Generate1099DocumentsStep
from massgov.pfml.delegated_payments.irs_1099.generate_pub_1220_filing import (
    GeneratePub1220filingStep,
)
from massgov.pfml.delegated_payments.irs_1099.merge_documents import Merge1099Step
from massgov.pfml.delegated_payments.irs_1099.populate_1099 import Populate1099Step
from massgov.pfml.delegated_payments.irs_1099.populate_mmars import PopulateMmarsStep
from massgov.pfml.delegated_payments.irs_1099.populate_pub import PopulatePubStep
from massgov.pfml.delegated_payments.irs_1099.populate_refunds import PopulateRefundsStep
from massgov.pfml.delegated_payments.irs_1099.populate_withholding import PopulateWithholdingStep
from massgov.pfml.delegated_payments.irs_1099.upload_documents import Upload1099DocumentsStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_1099_DOCUMENT_REPORTS,
)
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)

ALL = "ALL"
AUDIT_BATCH = "audit-batch"
POPULATE_MMARS = "populate-mmars"
POPULATE_PUB = "populate-pub"
POPULATE_WITHHOLDINGS = "populate-withholding"
POPULATE_REFUNDS = "populate-refunds"
POPULATE_1099 = "populate-1099"
GENERATE_1099_DOCUMENTS = "generate-1099-documents"
UPLOAD_1099_DOCUMENTS = "upload-1099-documents"
MERGE_1099_DOCUMENTS = "merge-1099-documents"
GENERATE_PUB1220_FILING = "generate-pub1220-filing"
REPORT = "report"
ALLOWED_VALUES = [
    ALL,
    AUDIT_BATCH,
    POPULATE_MMARS,
    POPULATE_PUB,
    POPULATE_WITHHOLDINGS,
    POPULATE_REFUNDS,
    POPULATE_1099,
    GENERATE_1099_DOCUMENTS,
    UPLOAD_1099_DOCUMENTS,
    MERGE_1099_DOCUMENTS,
    GENERATE_PUB1220_FILING,
    REPORT,
]


class Configuration:
    db_audit_batch: bool
    do_populate_mmars: bool
    do_populate_pub: bool
    db_populate_withholding: bool
    db_populate_refunds: bool
    db_populate_1099: bool
    generate_1099_documents: bool
    upload_1099_dochuments: bool
    merge_1099_documents: bool
    generate_pub1220_filing: bool
    make_reports: bool

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
            self.do_populate_mmars = True
            self.do_populate_pub = True
            self.db_populate_withholding = True
            self.db_populate_refunds = True
            self.db_populate_1099 = True
            self.generate_1099_documents = True
            self.upload_1099_documents = True
            self.merge_1099_documents = True
            self.generate_pub1220_filing = True
            self.make_reports = True
        else:
            self.db_audit_batch = AUDIT_BATCH in steps
            self.do_populate_mmars = POPULATE_MMARS in steps
            self.do_populate_pub = POPULATE_PUB in steps
            self.db_populate_withholding = POPULATE_WITHHOLDINGS in steps
            self.db_populate_refunds = POPULATE_REFUNDS in steps
            self.db_populate_1099 = POPULATE_1099 in steps
            self.generate_1099_documents = GENERATE_1099_DOCUMENTS in steps
            self.upload_1099_documents = UPLOAD_1099_DOCUMENTS in steps
            self.merge_1099_documents = MERGE_1099_DOCUMENTS in steps
            self.generate_pub1220_filing = GENERATE_PUB1220_FILING in steps
            self.make_reports = REPORT in steps


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
    start_time = payments_util.get_now()

    if config.db_audit_batch:
        AuditBatchStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.do_populate_mmars:
        PopulateMmarsStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.do_populate_pub:
        PopulatePubStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.db_populate_withholding:
        PopulateWithholdingStep(
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

    if config.upload_1099_documents:
        Upload1099DocumentsStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.merge_1099_documents:
        Merge1099Step(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.generate_pub1220_filing:
        GeneratePub1220filingStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_reports:
        ReportStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            report_names=PROCESS_1099_DOCUMENT_REPORTS,
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-process-1099-documents")

    logger.info("End - 1099 Documents Extract ECS Task")

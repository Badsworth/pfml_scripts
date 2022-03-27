import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.delegated_payments.address_validation import AddressValidationStep
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditReportStep,
)
from massgov.pfml.delegated_payments.delegated_fineos_1099_extract import Data1099ExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_claimant_extract import ClaimantExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_payment_extract import PaymentExtractStep
from massgov.pfml.delegated_payments.delegated_fineos_pei_writeback import FineosPeiWritebackStep
from massgov.pfml.delegated_payments.delegated_fineos_related_payment_processing import (
    RelatedPaymentsProcessingStep,
)
from massgov.pfml.delegated_payments.fineos_extract_step import (
    CLAIMANT_EXTRACT_CONFIG,
    PAYMENT_EXTRACT_CONFIG,
    REQUEST_1099_EXTRACT_CONFIG,
    VBI_TASKREPORT_SOM_EXTRACT_CONFIG,
    FineosExtractStep,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    PROCESS_FINEOS_EXTRACT_REPORTS,
)
from massgov.pfml.delegated_payments.state_cleanup_step import StateCleanupStep
from massgov.pfml.delegated_payments.weekly_max.max_weekly_benefit_amount_validation_step import (
    MaxWeeklyBenefitAmountValidationStep,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime import get_now_us_eastern

logger = logging.get_logger(__name__)

ALL = "ALL"
RUN_AUDIT_CLEANUP = "audit-cleanup"
CONSUME_FINEOS_CLAIMANT = "consume-fineos-claimant"
CONSUME_FINEOS_PAYMENT = "consume-fineos-payment"
VBI_TASKREPORT_EXTRACT = "vbi-taskreport-extract"
CLAIMANT_EXTRACT = "claimant-extract"
PAYMENT_EXTRACT = "payment-extract"
CONSUME_FINEOS_1099_REQUEST_EXTRACT = "consume-fineos-1099-request"
IRS_1099_REQUEST_EXTRACT = "irs-1099-request-extract"
VALIDATE_ADDRESSES = "validate-addresses"
VALIDATE_MAX_WEEKLY_BENEFIT_AMOUNT = "validate-max-weekly-benefit-amount"
PAYMENT_POST_PROCESSING = "payment-post-processing"
RELATED_PAYMENT_PROCESSING = "related-payment-processing"
CREATE_AUDIT_REPORT = "audit-report"
CREATE_PEI_WRITEBACK = "initial-writeback"
REPORT = "report"


ALLOWED_VALUES = [
    ALL,
    RUN_AUDIT_CLEANUP,
    CONSUME_FINEOS_CLAIMANT,
    CONSUME_FINEOS_PAYMENT,
    VBI_TASKREPORT_EXTRACT,
    CLAIMANT_EXTRACT,
    PAYMENT_EXTRACT,
    CONSUME_FINEOS_1099_REQUEST_EXTRACT,
    IRS_1099_REQUEST_EXTRACT,
    VALIDATE_ADDRESSES,
    PAYMENT_POST_PROCESSING,
    RELATED_PAYMENT_PROCESSING,
    CREATE_AUDIT_REPORT,
    CREATE_PEI_WRITEBACK,
    REPORT,
    VALIDATE_MAX_WEEKLY_BENEFIT_AMOUNT,
]


class Configuration:
    do_audit_cleanup: bool
    consume_fineos_claimant: bool
    consume_fineos_payment: bool
    do_vbi_taskreport_extract: bool
    do_claimant_extract: bool
    do_payment_extract: bool
    consume_fineos_1099_request: bool
    do_irs_1099_request_extract: bool
    validate_addresses: bool
    validate_max_weekly_benefit_amount: bool
    do_payment_post_processing: bool
    do_related_payment_processing: bool
    make_audit_report: bool
    create_pei_writeback: bool
    make_reports: bool

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
            self.consume_fineos_claimant = True
            self.consume_fineos_payment = True
            self.do_vbi_taskreport_extract = True
            self.do_claimant_extract = True
            self.do_payment_extract = True
            self.consume_fineos_1099_request = True
            self.do_irs_1099_request_extract = True
            self.validate_addresses = True
            self.validate_max_weekly_benefit_amount = True
            self.do_payment_post_processing = True
            self.do_related_payment_processing = True
            self.make_audit_report = True
            self.create_pei_writeback = True
            self.make_reports = True

        else:
            self.do_audit_cleanup = RUN_AUDIT_CLEANUP in steps
            self.consume_fineos_claimant = CONSUME_FINEOS_CLAIMANT in steps
            self.consume_fineos_payment = CONSUME_FINEOS_PAYMENT in steps
            self.do_vbi_taskreport_extract = VBI_TASKREPORT_EXTRACT in steps
            self.do_claimant_extract = CLAIMANT_EXTRACT in steps
            self.do_payment_extract = PAYMENT_EXTRACT in steps
            self.consume_fineos_1099_request = CONSUME_FINEOS_1099_REQUEST_EXTRACT in steps
            self.do_irs_1099_request_extract = IRS_1099_REQUEST_EXTRACT in steps
            self.validate_addresses = VALIDATE_ADDRESSES in steps
            self.validate_max_weekly_benefit_amount = VALIDATE_MAX_WEEKLY_BENEFIT_AMOUNT in steps
            self.do_payment_post_processing = PAYMENT_POST_PROCESSING in steps
            self.do_related_payment_processing = RELATED_PAYMENT_PROCESSING in steps
            self.make_audit_report = CREATE_AUDIT_REPORT in steps
            self.create_pei_writeback = CREATE_PEI_WRITEBACK in steps
            self.make_reports = REPORT in steps


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("pub-payments-process-fineos")
def main():
    """Entry point for PUB Payment Processing"""
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
    start_time = get_now_us_eastern()

    if config.do_audit_cleanup:
        StateCleanupStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.consume_fineos_claimant:
        FineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            extract_config=CLAIMANT_EXTRACT_CONFIG,
        ).run()

    if config.consume_fineos_payment:
        FineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            extract_config=PAYMENT_EXTRACT_CONFIG,
        ).run()

    if config.do_vbi_taskreport_extract:
        FineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            extract_config=VBI_TASKREPORT_SOM_EXTRACT_CONFIG,
        ).run()

    if config.do_claimant_extract:
        ClaimantExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            should_add_to_report_queue=True,
        ).run()

    if config.do_payment_extract:
        PaymentExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            should_add_to_report_queue=True,
        ).run()

    if config.consume_fineos_1099_request:
        FineosExtractStep(
            db_session=db_session,
            log_entry_db_session=log_entry_db_session,
            extract_config=REQUEST_1099_EXTRACT_CONFIG,
        ).run()

    if config.do_irs_1099_request_extract:
        Data1099ExtractStep(db_session=db_session, log_entry_db_session=log_entry_db_session).run()

    if config.validate_addresses:
        AddressValidationStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.validate_max_weekly_benefit_amount:
        MaxWeeklyBenefitAmountValidationStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.do_payment_post_processing:
        PaymentPostProcessingStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.do_related_payment_processing:
        RelatedPaymentsProcessingStep(
            db_session=db_session, log_entry_db_session=log_entry_db_session
        ).run()

    if config.make_audit_report:
        PaymentAuditReportStep(
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
            report_names=PROCESS_FINEOS_EXTRACT_REPORTS,
            sources_to_clear_from_report_queue=[ClaimantExtractStep],
        ).run()

    payments_util.create_success_file(start_time, "pub-payments-process-fineos")
    logger.info("End - FINEOS Payment+Claimant Extract ECS Task")

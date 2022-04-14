import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ReportName(str, Enum):
    CLAIMANT_EXTRACT_ERROR_REPORT = "claimant-extract-error-report"
    PAYMENT_EXTRACT_ERROR_REPORT = "payment-extract-error-report"
    ADDRESS_ERROR_REPORT = "address-error-report"
    MAX_WEEKLY_BENEFIT_AMOUNT_ERROR_REPORT = "max-weekly-benefit-amount-error-report"
    OVERPAYMENT_REPORT = "overpayment-report"
    ZERO_DOLLAR_PAYMENT_REPORT = "zero-dollar-payment-report"
    CANCELLATION_REPORT = "cancellation-report"
    EMPLOYER_REIMBURSEMENT_REPORT = "employer-reimbursement-report"
    ACH_PAYMENT_REPORT = "ach-payment-report"
    CHECK_PAYMENT_REPORT = "check-payment-report"
    DAILY_CASH_REPORT = "daily-cash-report"
    PUB_ERROR_REPORT = "pub-error-report"
    PAYMENT_RECONCILIATION_SUMMARY_REPORT = "payment-reconciliation-summary-report"
    PAYMENT_REJECT_REPORT = "payment-reject-report"
    PAYMENT_FULL_SNAPSHOT_RECONCILIATION_SUMMARY_REPORT = (
        "payment-full-snapshot-reconciliation-summary-report"
    )
    PAYMENT_FULL_SNAPSHOT_RECONCILIATION_DETAIL_REPORT = (
        "payment-full-snapshot-reconciliation-detail-report"
    )
    IRS_1099_REPORT = "irs-1099-report"
    FEDERAL_WITHHOLDING_PROCESSED_REPORT = "federal-withholding-processed-report"
    STATE_WITHHOLDING_PROCESSED_REPORT = "state-withholding-processed-report"
    TAX_WITHHOLDING_CUMULATIVE_REPORT = "tax-withholding-cumulative-report"
    WEEKLY_PAYMENT_SUMMARY_REPORT = "weekly-payment-summary-report"


REPORT_NAMES = [x for x in ReportName]

# Reports grouped by processing tasks
PROCESS_FINEOS_EXTRACT_REPORTS: List[ReportName] = [
    ReportName.CLAIMANT_EXTRACT_ERROR_REPORT,
    ReportName.PAYMENT_EXTRACT_ERROR_REPORT,
    ReportName.ADDRESS_ERROR_REPORT,
    ReportName.MAX_WEEKLY_BENEFIT_AMOUNT_ERROR_REPORT,
    ReportName.OVERPAYMENT_REPORT,
    ReportName.ZERO_DOLLAR_PAYMENT_REPORT,
    ReportName.CANCELLATION_REPORT,
    ReportName.EMPLOYER_REIMBURSEMENT_REPORT,
]
CREATE_PUB_FILES_REPORTS: List[ReportName] = [
    ReportName.ACH_PAYMENT_REPORT,
    ReportName.CHECK_PAYMENT_REPORT,
    ReportName.DAILY_CASH_REPORT,
    ReportName.PAYMENT_REJECT_REPORT,
    ReportName.PAYMENT_RECONCILIATION_SUMMARY_REPORT,
    ReportName.FEDERAL_WITHHOLDING_PROCESSED_REPORT,
    ReportName.STATE_WITHHOLDING_PROCESSED_REPORT,
    ReportName.TAX_WITHHOLDING_CUMULATIVE_REPORT,
    ReportName.WEEKLY_PAYMENT_SUMMARY_REPORT,
]
PROCESS_PUB_RESPONSES_REPORTS: List[ReportName] = [ReportName.PUB_ERROR_REPORT]
PROCESS_FINEOS_RECONCILIATION_REPORTS: List[ReportName] = [
    ReportName.PAYMENT_FULL_SNAPSHOT_RECONCILIATION_SUMMARY_REPORT,
    ReportName.PAYMENT_FULL_SNAPSHOT_RECONCILIATION_DETAIL_REPORT,
]


IRS_1099_REPORTS: List[ReportName] = [ReportName.IRS_1099_REPORT]


@dataclass
class Report:
    sql_command: str
    report_name: ReportName


def _get_report_sql_command_from_file(sql_file_name: str) -> str:
    expected_output = open(
        os.path.join(os.path.dirname(__file__), "sql", f"{sql_file_name}.sql"), "r"
    ).read()
    return expected_output


REPORTS: List[Report] = [
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.CLAIMANT_EXTRACT_ERROR_REPORT),
        report_name=ReportName.CLAIMANT_EXTRACT_ERROR_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.PAYMENT_EXTRACT_ERROR_REPORT),
        report_name=ReportName.PAYMENT_EXTRACT_ERROR_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.ADDRESS_ERROR_REPORT),
        report_name=ReportName.ADDRESS_ERROR_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(
            ReportName.MAX_WEEKLY_BENEFIT_AMOUNT_ERROR_REPORT
        ),
        report_name=ReportName.MAX_WEEKLY_BENEFIT_AMOUNT_ERROR_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.OVERPAYMENT_REPORT),
        report_name=ReportName.OVERPAYMENT_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.ZERO_DOLLAR_PAYMENT_REPORT),
        report_name=ReportName.ZERO_DOLLAR_PAYMENT_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.CANCELLATION_REPORT),
        report_name=ReportName.CANCELLATION_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.EMPLOYER_REIMBURSEMENT_REPORT),
        report_name=ReportName.EMPLOYER_REIMBURSEMENT_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.ACH_PAYMENT_REPORT),
        report_name=ReportName.ACH_PAYMENT_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.CHECK_PAYMENT_REPORT),
        report_name=ReportName.CHECK_PAYMENT_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.DAILY_CASH_REPORT),
        report_name=ReportName.DAILY_CASH_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.PUB_ERROR_REPORT),
        report_name=ReportName.PUB_ERROR_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(
            ReportName.PAYMENT_RECONCILIATION_SUMMARY_REPORT
        ),
        report_name=ReportName.PAYMENT_RECONCILIATION_SUMMARY_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.PAYMENT_REJECT_REPORT),
        report_name=ReportName.PAYMENT_REJECT_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(
            ReportName.PAYMENT_FULL_SNAPSHOT_RECONCILIATION_SUMMARY_REPORT
        ),
        report_name=ReportName.PAYMENT_FULL_SNAPSHOT_RECONCILIATION_SUMMARY_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(
            ReportName.PAYMENT_FULL_SNAPSHOT_RECONCILIATION_DETAIL_REPORT
        ),
        report_name=ReportName.PAYMENT_FULL_SNAPSHOT_RECONCILIATION_DETAIL_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.IRS_1099_REPORT),
        report_name=ReportName.IRS_1099_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(
            ReportName.FEDERAL_WITHHOLDING_PROCESSED_REPORT
        ),
        report_name=ReportName.FEDERAL_WITHHOLDING_PROCESSED_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(
            ReportName.STATE_WITHHOLDING_PROCESSED_REPORT
        ),
        report_name=ReportName.STATE_WITHHOLDING_PROCESSED_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.TAX_WITHHOLDING_CUMULATIVE_REPORT),
        report_name=ReportName.TAX_WITHHOLDING_CUMULATIVE_REPORT,
    ),
    Report(
        sql_command=_get_report_sql_command_from_file(ReportName.WEEKLY_PAYMENT_SUMMARY_REPORT),
        report_name=ReportName.WEEKLY_PAYMENT_SUMMARY_REPORT,
    ),
]

REPORTS_BY_NAME: Dict[ReportName, Report] = {r.report_name: r for r in REPORTS}


def get_report_by_name(report_name: ReportName) -> Optional[Report]:
    return REPORTS_BY_NAME[report_name]

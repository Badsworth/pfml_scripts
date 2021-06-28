import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ReportName(str, Enum):
    CLAIMANT_EXTRACT_ERROR_REPORT = "claimant-extract-error-report"
    PAYMENT_EXTRACT_ERROR_REPORT = "payment-extract-error-report"
    ADDRESS_ERROR_REPORT = "address-error-report"
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


# Reports grouped by processing tasks
PROCESS_FINEOS_EXTRACT_REPORTS: List[ReportName] = [
    ReportName.CLAIMANT_EXTRACT_ERROR_REPORT,
    ReportName.PAYMENT_EXTRACT_ERROR_REPORT,
    ReportName.ADDRESS_ERROR_REPORT,
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
]
PROCESS_PUB_RESPONSES_REPORTS: List[ReportName] = [ReportName.PUB_ERROR_REPORT]


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
]

REPORTS_BY_NAME: Dict[ReportName, Report] = {r.report_name: r for r in REPORTS}


def get_report_by_name(report_name: ReportName) -> Optional[Report]:
    return REPORTS_BY_NAME[report_name]

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class FolderName(str, Enum):
    PROGRAM_INTEGRITY = "program-integrity"
    FINANCE = "finance"


class ReportName(str, Enum):
    CLAIMANT_EXTRACT_ERROR_REPORT = "claimant-extract-error-report"
    PAYMENT_EXTRACT_ERROR_REPORT = "payment-extract-error-report"
    ADDRESS_ERROR_REPORT = "address-error-report"
    OVERPAYMENT_REPORT = "overpayment-report"
    ZERO_DOLLAR_PAYMENT_REPORT = "zero-dollar-payment_report"
    CANCELLATION_REPORT = "cancellation-report"
    EMPLOYER_REIMBURSEMENT_REPORT = "employer-reimbursement-report"
    PUB_PAYMENT_REPORT = "pub-payment-report"
    DAILY_CASH_REPORT = "daily-cash-report"
    PUB_ERROR_REPORT = "pub-error-report"
    EFT_ERROR_REPORT = "eft-error-report"
    PAYMENT_RECONCILIATION_SUMMARY_REPORT = "payment-reconciliation-summary-report"


# Reports grouped by processing tasks
PROCESS_FINEOS_EXTRACT_REPORTS: List[ReportName] = [
    ReportName.CLAIMANT_EXTRACT_ERROR_REPORT,
    ReportName.PAYMENT_EXTRACT_ERROR_REPORT,
    ReportName.ADDRESS_ERROR_REPORT,
    ReportName.PAYMENT_RECONCILIATION_SUMMARY_REPORT,
]
CREATE_PUB_FILES_REPORTS: List[ReportName] = [
    ReportName.OVERPAYMENT_REPORT,
    ReportName.ZERO_DOLLAR_PAYMENT_REPORT,
    ReportName.CANCELLATION_REPORT,
    ReportName.EMPLOYER_REIMBURSEMENT_REPORT,
    ReportName.PUB_PAYMENT_REPORT,
    ReportName.DAILY_CASH_REPORT,
]
PROCESS_PUB_RESPONSES_REPORTS: List[ReportName] = [
    ReportName.PUB_ERROR_REPORT,
    ReportName.EFT_ERROR_REPORT,
]


@dataclass
class Report:
    sql_command: str
    report_name: ReportName
    folder_name: FolderName


REPORTS: List[Report] = [
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.CLAIMANT_EXTRACT_ERROR_REPORT,
        folder_name=FolderName.PROGRAM_INTEGRITY,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.PAYMENT_EXTRACT_ERROR_REPORT,
        folder_name=FolderName.PROGRAM_INTEGRITY,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.ADDRESS_ERROR_REPORT,
        folder_name=FolderName.PROGRAM_INTEGRITY,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.OVERPAYMENT_REPORT,
        folder_name=FolderName.FINANCE,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.ZERO_DOLLAR_PAYMENT_REPORT,
        folder_name=FolderName.FINANCE,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.CANCELLATION_REPORT,
        folder_name=FolderName.FINANCE,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.EMPLOYER_REIMBURSEMENT_REPORT,
        folder_name=FolderName.FINANCE,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.PUB_PAYMENT_REPORT,
        folder_name=FolderName.FINANCE,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.DAILY_CASH_REPORT,
        folder_name=FolderName.FINANCE,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.PUB_ERROR_REPORT,
        folder_name=FolderName.PROGRAM_INTEGRITY,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.EFT_ERROR_REPORT,
        folder_name=FolderName.PROGRAM_INTEGRITY,
    ),
    Report(
        sql_command="select * from lk_state",
        report_name=ReportName.PAYMENT_RECONCILIATION_SUMMARY_REPORT,
        folder_name=FolderName.FINANCE,
    ),
]

REPORTS_BY_NAME: Dict[ReportName, Report] = {r.report_name: r for r in REPORTS}


def get_report_by_name(report_name: ReportName) -> Optional[Report]:
    return REPORTS_BY_NAME[report_name]

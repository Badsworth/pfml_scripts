import re
from typing import List

import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employee, Payment
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.delegated_payments.abstract_step_processor import AbstractStepProcessor
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.delegated_payments_util import get_traceable_payment_details
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PostProcessingMetrics,
)
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class DORFineosEmployeeNameMismatchProcessor(AbstractStepProcessor):
    """
    Checks if the employee name populated by DOR is different from the FINEOS name.
    Returns a message for for use by the audit report.
    """

    Metrics = PostProcessingMetrics

    lines: List[str]

    def __init__(self, step: Step) -> None:
        super().__init__(step)
        self.lines = []

    def process(self, payment: Payment) -> None:
        self.lines = []
        if not payment.claim or not payment.claim.employee:
            return None

        # This case is not possible since it will be caught in the extract stage
        # This is needed for the linter
        if payment.fineos_employee_first_name is None or payment.fineos_employee_last_name is None:
            raise Exception(
                f"payment in processing has no fineos first name and last name: {payment.payment_id}"
            )

        employee: Employee = payment.claim.employee

        is_name_mismatch = self.is_name_mismatch(
            employee.first_name,
            employee.last_name,
            payment.fineos_employee_first_name,
            payment.fineos_employee_last_name,
        )
        if not is_name_mismatch:
            self.increment(self.Metrics.PAYMENT_DOR_FINEOS_NAME_PASS_COUNT)
            logger.info(
                "Payment passed name mismatch validation",
                extra=get_traceable_payment_details(payment),
            )
            return

        # Otherwise it failed the name check
        self.increment(self.Metrics.PAYMENT_DOR_FINEOS_NAME_MISMATCH_COUNT)

        logger.info(
            "Payment has mismatch between DOR and FINEOS employee names, adding notes to audit report",
            extra=get_traceable_payment_details(payment),
        )

        messages: List[str] = []
        messages.append(f"DOR Name: {employee.first_name} {employee.last_name}")
        messages.append(
            f"FINEOS Name: {payment.fineos_employee_first_name} {payment.fineos_employee_last_name}"
        )
        mismatch_message = "\n".join(messages)

        stage_payment_audit_report_details(
            payment,
            PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH,
            mismatch_message,
            self.get_import_log_id(),
            self.db_session,
        )

    def is_name_mismatch(
        self, dor_first_name: str, dor_last_name: str, fineos_first_name: str, fineos_last_name: str
    ) -> bool:
        dor_first_name_trimmed = trim_name(dor_first_name)
        dor_last_name_trimmed = trim_name(dor_last_name)
        fineos_first_name_trimmed = trim_name(fineos_first_name)
        fineos_last_name_trimmed = trim_name(fineos_last_name)

        # If any parts of a name are too short, we will add it
        # as it might mean someone has just an initial like "J Smith" for a first name
        if any(
            len(name) < 2
            for name in [
                dor_first_name_trimmed,
                dor_last_name_trimmed,
                fineos_first_name_trimmed,
                fineos_last_name_trimmed,
            ]
        ):
            return True

        # We only deem a name mismatched if both the first and last names
        # do not match. This avoids the noise of someone legitimately changing
        # their first or last name, or very minor spelling mistakes. The
        # goal of this check is to find cases where the person in DOR and FINEOS
        # associated with an SSN are very clearly different which we can
        # assume is likely for cases where neither name matches

        # If they match, no issue
        if (
            dor_first_name_trimmed in fineos_first_name_trimmed
            or dor_last_name_trimmed in fineos_last_name_trimmed
        ):
            return False

        # If the names are backwards in one system, that's also fine
        # Note, this is doing first == last for both pairs
        if (
            dor_first_name_trimmed in fineos_last_name_trimmed
            or dor_last_name_trimmed in fineos_first_name_trimmed
        ):
            self.increment(self.Metrics.PAYMENT_DOR_FINEOS_NAME_SWAPPED_COUNT)
            return False

        # Nothing is matching, should flag these to be manually reviewed
        return True


def trim_name(name: str) -> str:
    """
    Remove miscellaneous characters and spaces from a name
    """
    return re.sub(r"[^a-z]", "", name.lower())

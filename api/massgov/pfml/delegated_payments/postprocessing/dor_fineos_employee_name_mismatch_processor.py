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
    make_payment_log,
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

        name_mismatch = self.is_name_mismatch(
            employee.last_name, payment.fineos_employee_last_name
        ) or self.is_name_mismatch(employee.first_name, payment.fineos_employee_first_name)
        if name_mismatch:
            self.increment(self.Metrics.PAYMENT_DOR_FINEOS_NAME_MISMATCH)
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

            logger.info(
                "Payment %s has mismatch between DOR and FINEOS employee names, creating audit report details",
                make_payment_log(payment),
                extra=get_traceable_payment_details(payment),
            )

    def is_name_mismatch(self, dor_name: str, fineos_name: str) -> bool:
        dor_name_for_compare = dor_name.lower().replace("-", " ").strip()
        fineos_name_for_compare = fineos_name.lower().replace("-", " ").strip()

        if len(dor_name_for_compare) < 2 or len(fineos_name_for_compare) < 2:
            return True

        if (
            dor_name_for_compare in fineos_name_for_compare
            or fineos_name_for_compare in dor_name_for_compare
        ):
            return False

        return True

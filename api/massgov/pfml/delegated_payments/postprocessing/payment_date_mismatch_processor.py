from typing import List

import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import AbsencePeriod, Employee, Payment
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.db.queries.absence_periods import get_employee_absence_periods_for_leave_request
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


class PaymentDateMismatchProcessor(AbstractStepProcessor):
    """
    Checks if a payment for a benefit week falls outside of the approved leave dates.
    Returns a message for for use by the audit report.
    """

    Metrics = PostProcessingMetrics

    def __init__(self, step: Step) -> None:
        super().__init__(step)

    def is_payment_date_mismatch(
        self, payment: Payment, absence_periods: List[AbsencePeriod]
    ) -> bool:
        if (
            payment.is_adhoc_payment
            or payment.period_start_date is None
            or payment.period_end_date is None
        ):
            return False

        for absence_period in absence_periods:
            if (
                absence_period.absence_period_start_date is None
                or absence_period.absence_period_end_date is None
            ):
                continue
            if datetime_util.is_range_contained(
                (absence_period.absence_period_start_date, absence_period.absence_period_end_date),
                (payment.period_start_date, payment.period_end_date),
            ):
                return False

        return True

    def get_log_message(self, payment: Payment, absence_periods: List[AbsencePeriod]) -> str:
        messages: List[str] = []
        messages.append(
            f"Payment for {payment.period_start_date} -> {payment.period_end_date} outside all leave dates."
        )
        absence_periods_str = ", ".join(
            [
                f"{x.absence_period_start_date} -> {x.absence_period_end_date}"
                for x in absence_periods
            ]
        )
        if len(absence_periods_str) == 0:
            messages.append("Had no absence periods.")
        else:
            messages.append(f"Had absence periods for {absence_periods_str}.")

        message = " ".join(messages)
        return message

    def process(self, payment: Payment) -> None:
        # Should not be possible, but to make mypy happy
        if not payment.claim or not payment.claim.employee or not payment.fineos_leave_request_id:
            self.increment(self.Metrics.PAYMENT_DATE_MISSING_REQUIRED_DATA_COUNT)
            logger.warn(
                "Payment missing data required for validation",
                extra=get_traceable_payment_details(payment),
            )
            return None

        employee: Employee = payment.claim.employee
        absence_periods = get_employee_absence_periods_for_leave_request(
            self.db_session, employee.employee_id, payment.fineos_leave_request_id
        )
        is_payment_date_mismatch = self.is_payment_date_mismatch(payment, absence_periods)

        if not is_payment_date_mismatch:
            self.increment(self.Metrics.PAYMENT_DATE_PASS_COUNT)
            logger.info(
                "Payment passed date mismatch validation",
                extra=get_traceable_payment_details(payment),
            )
            return

        self.increment(self.Metrics.PAYMENT_DATE_MISMATCH_COUNT)

        logger.info(
            "Payment date is outside of the approved leave dates on the claim, adding notes to audit report",
            extra=get_traceable_payment_details(payment),
        )
        message = self.get_log_message(payment, absence_periods)

        stage_payment_audit_report_details(
            payment,
            PaymentAuditReportType.PAYMENT_DATE_MISMATCH,
            message,
            self.get_import_log_id(),
            self.db_session,
        )

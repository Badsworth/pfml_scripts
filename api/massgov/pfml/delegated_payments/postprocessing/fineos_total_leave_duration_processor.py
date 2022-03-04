from typing import List, Optional

from pydantic.types import UUID4

import massgov.pfml.api.eligibility.benefit_year as benefit_year_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.absences import AbsencePeriodType, AbsenceStatus
from massgov.pfml.db.models.employees import Employee, Payment
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.db.queries.absence_periods import get_employee_absence_periods
from massgov.pfml.delegated_payments.abstract_step_processor import AbstractStepProcessor
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.delegated_payments_util import get_traceable_payment_details
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PostProcessingMetrics,
)
from massgov.pfml.delegated_payments.util.leave_calculator import (
    LeaveCalculator,
    LeaveDurationResult,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


class FineosTotalLeaveDurationProcessor(AbstractStepProcessor):
    """
    Fineos is not able to enforce the 26 week total leave maximum
    per the program regulations. Leave type limits are 12 and 20
    weeks for family and medical leave respectively.

    Checks if the claimaint's total leave duration per employer
    will exceed 26 weeks and returns a message for use by the audit report.
    """

    Metrics = PostProcessingMetrics

    MAX_LEAVE_THRESHOLD = 182  # 26 weeks == 182 days
    ABSENCE_STATUS_IDS = [
        AbsenceStatus.APPROVED.absence_status_id,
        AbsenceStatus.COMPLETED.absence_status_id,
        AbsenceStatus.IN_REVIEW.absence_status_id,
    ]
    CONTINUOUS_PERIOD_TYPE_ID = AbsencePeriodType.CONTINUOUS.absence_period_type_id

    def process(self, payment: Payment) -> None:
        if not payment.claim or not payment.claim.employee:
            return None

        found_leave_exceeding_threshold = self.found_leave_duration_exceeding_threshold(payment)

        if len(found_leave_exceeding_threshold) == 0:
            self.increment(self.Metrics.PAYMENT_LEAVE_DURATION_PASS_COUNT)
            logger.info(
                "Payment passed leave duration validation", get_traceable_payment_details(payment)
            )
            return

        self.increment(self.Metrics.PAYMENT_LEAVE_DURATION_THRESHOLD_EXCEEDED_COUNT)

        message = self.get_log_message(found_leave_exceeding_threshold, payment)
        stage_payment_audit_report_details(
            payment,
            PaymentAuditReportType.EXCEEDS_26_WEEKS_TOTAL_LEAVE,
            message,
            self.get_import_log_id(),
            self.db_session,
        )

    def found_leave_duration_exceeding_threshold(
        self, payment: Payment
    ) -> List[LeaveDurationResult]:
        employee: Employee = payment.claim.employee
        benefit_years = benefit_year_util.get_all_benefit_years_by_employee_id(
            self.db_session, employee.employee_id
        )

        # This should not be possible conisdering the previous
        # line backfills benefit years based on leave absence history.
        if benefit_years is None or len(benefit_years) == 0:
            self.increment(self.Metrics.PAYMENT_LEAVE_DURATION_MISSING_BENEFIT_YEAR_COUNT)
            logger.warning(
                "Payment in processing has no associated benefit years",
                get_traceable_payment_details(payment),
            )
            return []

        leave_calculator = LeaveCalculator(benefit_years)

        absence_periods = get_employee_absence_periods(
            self.db_session, employee.employee_id, self.ABSENCE_STATUS_IDS
        )

        # Only consider absence periods that are continuous
        filtered_absence_periods = []
        for absence_period in absence_periods:
            if absence_period.absence_period_type_id == self.CONTINUOUS_PERIOD_TYPE_ID:
                filtered_absence_periods.append(absence_period)
                continue
            logger.info(
                "Skipping absence period with non-continuous leave",
                extra={
                    **get_traceable_payment_details(payment),
                    "absence_period_id": absence_period.absence_period_id,
                    "absence_period_type_id": absence_period.absence_period_type_id,
                },
            )

        leave_calculator.set_benefit_year_absence_periods(filtered_absence_periods)

        found_leave_exceeding_threshold = leave_calculator.benefit_years_exceeding_threshold(
            self.MAX_LEAVE_THRESHOLD
        )
        return found_leave_exceeding_threshold

    def get_log_message(
        self, leave_duration_results: List[LeaveDurationResult], payment: Payment
    ) -> str:
        log_details = get_traceable_payment_details(payment)
        messages: List[str] = []
        leave_duration_results.sort(key=lambda x: (x.benefit_year_start_date, x.employer_id))
        current_benefit_year_id: Optional[UUID4] = None
        for result in leave_duration_results:
            if current_benefit_year_id != result.benefit_year_id:
                messages.append(
                    f"Benefit Year Start: {result.benefit_year_start_date}, Benefit Year End: {result.benefit_year_end_date}"
                )
                log_details |= {
                    "benefit_year_id": result.benefit_year_id,
                    "employer_id": result.employer_id,
                    "fineos_employer_id": result.fineos_employer_id,
                    "benefit_year_start_date": result.benefit_year_start_date,
                    "benefit_year_end_date": result.benefit_year_end_date,
                    "benefit_year_leave_duration_for_employer": result.duration,
                }

            logger.info(
                "Payment has a leave duration exceeding the threshold for days per employer in a benefit year, adding notes to audit report",
                extra=log_details,
            )
            messages.append(
                f"- Employer ID: {result.fineos_employer_id}, Leave Duration: {result.duration}"
            )
            current_benefit_year_id = result.benefit_year_id

        return "\n".join(messages)

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List

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

# The min/max difference between pay periods
# to be considered adjacent. Note that two
# days in a row have a diff of 1 (Tues - Mon = 1)
MIN_DIFF_BETWEEN_PERIODS: int = 1
MAX_DIFF_BETWEEN_PERIODS: int = 4


@dataclass
class AbsencePeriodGroup:
    absence_periods: List[AbsencePeriod]
    start_date: date = field(init=False)
    end_date: date = field(init=False)

    def __post_init__(self):
        # We only created this group with
        # absence periods that had a start/end date
        # so we know they are all non-none
        self.start_date = min([absence_period.absence_period_start_date for absence_period in self.absence_periods])  # type: ignore
        self.end_date = max([absence_period.absence_period_end_date for absence_period in self.absence_periods])  # type: ignore

    def get_log_extra(self) -> Dict[str, Any]:
        extra = {
            "absence_period_group_start_date": datetime_util.date_to_isoformat(self.start_date),
            "absence_period_group_end_date": datetime_util.date_to_isoformat(self.end_date),
            "absence_period_count": len(self.absence_periods),
        }
        for i, absence_period in enumerate(self.absence_periods):
            extra[f"absence_period[{i}].absence_period_id"] = str(absence_period.absence_period_id)
            extra[
                f"absence_period[{i}].fineos_absence_period_class_id"
            ] = absence_period.fineos_absence_period_class_id
            extra[
                f"absence_period[{i}].fineos_absence_period_index_id"
            ] = absence_period.fineos_absence_period_index_id
            extra[
                f"absence_period[{i}].absence_period_start_date"
            ] = datetime_util.date_to_isoformat(absence_period.absence_period_start_date)
            extra[f"absence_period[{i}].absence_period_end_date"] = datetime_util.date_to_isoformat(
                absence_period.absence_period_end_date
            )

        return extra


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
        extra = get_traceable_payment_details(payment)
        if payment.is_adhoc_payment:
            logger.info("Skipping payment date mismatch check for adhoc payment", extra=extra)
            return False
        if payment.period_start_date is None or payment.period_end_date is None:
            logger.error(
                "Skipping payment date mismatch check as payment is missing required field",
                extra=extra,
            )
            return False

        absence_period_groups = self.group_absence_periods(payment, absence_periods)

        for absence_period_group in absence_period_groups:
            absence_extra = absence_period_group.get_log_extra() | extra
            logger.info(
                "Checking if payment period is within group of absence periods", extra=absence_extra
            )
            if datetime_util.is_range_contained(
                (absence_period_group.start_date, absence_period_group.end_date),
                (payment.period_start_date, payment.period_end_date),
            ):
                logger.info("Payment is in a group of absence periods", extra=absence_extra)
                return False

        return True

    def group_absence_periods(
        self, payment: Payment, absence_periods: List[AbsencePeriod]
    ) -> List[AbsencePeriodGroup]:
        """
        Payments are expected to fit within a leave request which
        is made of absence periods. But a payment may cross absence
        periods. This method aims to make absence period groups
        that handle the below cases.

        For example, a payment from 1/26 -> 2/3 is valid if the
        absence periods are 1/1 -> 1/31, and 2/1 -> 2/28. While
        it's not perfectly in either one, they both make up an entire
        leave and it's valid.

        Additionally, sometimes FINEOS has gaps in a leave due to
        the days someone works. For example, one absence period may
        end on Friday (1/1), but the next not start until Tuesday (1/5).
        This isn't really a gap, and if a payment crosses it, we are fine with it.

        However, sometimes the absence periods are incorrect created
        with a several month gap, these aren't allowed, and we will
        treat those as separate.
        """
        # Filter absence periods without dates set
        extra_base = get_traceable_payment_details(payment)

        valid_absence_periods = []
        for absence_period in absence_periods:
            if (
                absence_period.absence_period_start_date is None
                or absence_period.absence_period_end_date is None
            ):
                extra = {
                    "absence_period_id": str(absence_period.absence_period_id),
                    "absence_period_start_date": datetime_util.date_to_isoformat(
                        absence_period.absence_period_start_date
                    ),
                    "absence_period_end_date": datetime_util.date_to_isoformat(
                        absence_period.absence_period_end_date
                    ),
                } | extra_base
                logger.warning(
                    "Absence period is missing start or end, cannot use for processing", extra=extra
                )
                continue

            valid_absence_periods.append(absence_period)

        if len(valid_absence_periods) == 0:
            logger.warning(
                "No valid absence periods found for payment to check pay period against",
                extra=extra_base,
            )
            return []

        # Ignoring mypy complaining about
        # sorting by a null value as we just
        # validated it's not null
        valid_absence_periods.sort(
            key=lambda absence_period: absence_period.absence_period_start_date  # type: ignore
        )

        adjacent_absent_periods: List[AbsencePeriod] = []
        absence_period_groups: List[AbsencePeriodGroup] = []
        for absence_period in valid_absence_periods:
            # First record scenario
            if len(adjacent_absent_periods) == 0:
                adjacent_absent_periods.append(absence_period)
                continue

            last_absence_period = adjacent_absent_periods[-1]
            diff_between_periods = (
                absence_period.absence_period_start_date  # type: ignore
                - last_absence_period.absence_period_end_date
            ).days

            # We sometimes get absence periods with the same
            # dates, but likely other values different. Just
            # group those the same.
            if (
                last_absence_period.absence_period_end_date
                == absence_period.absence_period_end_date
                and last_absence_period.absence_period_start_date
                == absence_period.absence_period_start_date
            ):
                adjacent_absent_periods.append(absence_period)

            elif MIN_DIFF_BETWEEN_PERIODS <= diff_between_periods <= MAX_DIFF_BETWEEN_PERIODS:
                # Absence Period occurs right after or close enough
                # after to reasonably group them
                adjacent_absent_periods.append(absence_period)

            else:
                # Otherwise finish that group and reinitialize the list
                absence_period_groups.append(AbsencePeriodGroup(adjacent_absent_periods))
                adjacent_absent_periods = [absence_period]

        # Whatever remains is a group.
        absence_period_groups.append(AbsencePeriodGroup(adjacent_absent_periods))
        return absence_period_groups

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

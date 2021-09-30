from datetime import timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import asc

import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    DiaReductionPayment,
    DuaReductionPayment,
    Employee,
    Payment,
)
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

logger = logging.get_logger(__name__)


class DuaDiaReductionsProcessor(AbstractStepProcessor):
    """
    Checks for existing DUA or DIA reductions with the current payment.
    Returns a message for overlapping reductions for use by the audit report.

    https://lwd.atlassian.net/wiki/spaces/API/pages/1961033777/Checking+payments+for+DUA+DIA+reductions
    """

    Metrics = PostProcessingMetrics

    lines: List[str]

    def __init__(self, step: Step) -> None:
        super().__init__(step)
        self.lines = []

    def process(self, payment: Payment) -> None:
        self.lines = []
        self.check_dua(payment)

        if len(self.lines) > 0:
            self.lines.append("")

        self.check_dia(payment)

        if len(self.lines) > 0:
            message = "\n".join(self.lines)

            stage_payment_audit_report_details(
                payment,
                PaymentAuditReportType.DUA_DIA_REDUCTION,
                message,
                self.get_import_log_id(),
                self.db_session,
            )

            logger.info(
                "Payment %s has overlapping DUA or DIA reductions, creating audit report details",
                make_payment_log(payment),
                extra=get_traceable_payment_details(payment),
            )

    def check_dua(self, payment: Payment) -> None:
        employee = self._get_employee(payment)
        if employee is None:
            return None

        # Include DUA reductions where the request_week_begin_date overlaps with the payment period start and end
        # Also include if the derived end date (request_week_begin_date + 6) also overlaps
        overlapping_dua_reductions = (
            self.db_session.query(DuaReductionPayment)
            .filter(
                DuaReductionPayment.fineos_customer_number == employee.fineos_customer_number,
                or_(
                    and_(
                        DuaReductionPayment.request_week_begin_date >= payment.period_start_date,
                        DuaReductionPayment.request_week_begin_date <= payment.period_end_date,
                    ),
                    and_(
                        DuaReductionPayment.request_week_begin_date + timedelta(6)
                        >= payment.period_start_date,
                        DuaReductionPayment.request_week_begin_date + timedelta(6)
                        <= payment.period_end_date,
                    ),
                ),
            )
            .order_by(asc(DuaReductionPayment.request_week_begin_date))
            .all()
        )

        if len(overlapping_dua_reductions) > 0:
            self.lines.append("DUA Reductions:")

        for dua_reduction in overlapping_dua_reductions:
            self.increment(self.Metrics.PAYMENT_DUA_REDUCTION_OVERLAP)
            amount = (
                round(Decimal(dua_reduction.payment_amount_cents) / Decimal("100.00"), 2)
                if dua_reduction.payment_amount_cents
                else Decimal("0.00")
            )
            gross_amount = (
                round(Decimal(dua_reduction.gross_payment_amount_cents) / Decimal("100.00"), 2)
                if dua_reduction.gross_payment_amount_cents
                else Decimal("0.00")
            )

            calculated_request_week_end_date = (
                dua_reduction.request_week_begin_date + timedelta(6)
                if dua_reduction.request_week_begin_date
                else "N/A"
            )
            fraud_indicator = dua_reduction.fraud_indicator or "N/A"

            dua_info_items = []
            dua_info_items.append(f"Payment Date: {dua_reduction.payment_date}")
            dua_info_items.append(f"Amount: {amount}")
            dua_info_items.append(f"Gross Payment Amount: {gross_amount}")
            dua_info_items.append(
                f"Request Week Begin Date: {dua_reduction.request_week_begin_date}"
            )
            dua_info_items.append(
                f"Calculated Request Week End Date: {calculated_request_week_end_date}"
            )
            dua_info_items.append(
                f"Benefit Year Begin Date: {dua_reduction.benefit_year_begin_date}"
            )
            dua_info_items.append(f"Benefit Year End Date: {dua_reduction.benefit_year_end_date}")
            dua_info_items.append(f"Fraud Indicator: {fraud_indicator}")
            dua_line = ", ".join(dua_info_items)
            self.lines.append(f"- {dua_line}")

    def check_dia(self, payment: Payment) -> None:
        employee = self._get_employee(payment)
        if employee is None:
            return None

        dia_reductions = (
            self.db_session.query(DiaReductionPayment)
            .filter(DiaReductionPayment.fineos_customer_number == employee.fineos_customer_number)
            .order_by(asc(DiaReductionPayment.award_created_date))
            .all()
        )

        if len(dia_reductions) > 0:
            self.lines.append("DIA Reductions:")

        for dia_reduction in dia_reductions:
            self.increment(self.Metrics.PAYMENT_DIA_REDUCTION_OVERLAP)
            dia_info_items = []
            dia_info_items.append(f"Award Date: {dia_reduction.award_created_date}")
            dia_info_items.append(f"Start Date: {dia_reduction.start_date}")
            dia_info_items.append(f"Amount: {dia_reduction.award_amount}")
            dia_info_items.append(f"Weekly Amount: {dia_reduction.weekly_amount}")
            dia_info_items.append(f"Event Created Date: {dia_reduction.eve_created_date}")
            dia_line = ", ".join(dia_info_items)
            self.lines.append(f"- {dia_line}")

    def _get_employee(self, payment: Payment) -> Optional[Employee]:
        if payment.claim:
            return payment.claim.employee

        return None

import datetime
import decimal
from typing import Tuple

import massgov.pfml.db
from massgov.pfml.api.eligibility.benefit import calculate_weekly_benefit_amount
from massgov.pfml.db.models.applications import BenefitsMetrics, UnemploymentMetric

logger = massgov.pfml.util.logging.get_logger(__name__)


def fetch_state_metric(
    db_session: massgov.pfml.db.Session, effective_date: datetime.date
) -> Tuple[BenefitsMetrics, UnemploymentMetric]:
    """Return state metrics effective on the given date."""

    benefits_metrics = (
        db_session.query(BenefitsMetrics)
        .filter(BenefitsMetrics.effective_date <= effective_date)
        .order_by(BenefitsMetrics.effective_date.desc())
        .first()
    )

    if benefits_metrics is None:
        logger.warning("Benefits metrics were not found for effective_date %s", effective_date)
        raise RuntimeError(
            "Benefits metrics were not found for effective_date {}".format(effective_date)
        )

    unemployment_metric = (
        db_session.query(UnemploymentMetric)
        .filter(UnemploymentMetric.effective_date <= effective_date)
        .order_by(UnemploymentMetric.effective_date.desc())
        .first()
    )

    if unemployment_metric is None:
        logger.warning("Unemployment metrics were not found for effective_date %s", effective_date)
        raise RuntimeError(
            "Unemployment metrics were not found for effective_date {}".format(effective_date)
        )

    return (benefits_metrics, unemployment_metric)


def wages_gte_unemployment_min(
    total_wages: decimal.Decimal, unemployment_min_earnings: decimal.Decimal
) -> bool:
    """Evaluate whether total wages, calculated from employee specific DOR data,
    are less than the unemployment minimum. The minimum unemployment figure is set
    each year on Oct. 1st and is stored in the UnemploymentMetric table."""

    if total_wages < unemployment_min_earnings:
        return False

    return True


def wages_gte_thirty_times_wba(
    total_wages: decimal.Decimal,
    individual_average_weekly_wage: decimal.Decimal,
    state_average_weekly_wage: decimal.Decimal,
    maximum_weekly_benefit_amount: decimal.Decimal,
) -> bool:
    # Terminology note: wba = weekly benefit amount

    wba = calculate_weekly_benefit_amount(
        individual_average_weekly_wage, state_average_weekly_wage, maximum_weekly_benefit_amount
    )

    eligibility_threshold = wba * 30

    if total_wages < eligibility_threshold:
        return False

    return True

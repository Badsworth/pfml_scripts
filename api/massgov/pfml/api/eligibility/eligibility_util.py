import datetime
import decimal

import massgov.pfml.db
from massgov.pfml.api.eligibility.benefit import calculate_weekly_benefit_amount
from massgov.pfml.db.models.applications import StateMetric

logger = massgov.pfml.util.logging.get_logger(__name__)


def fetch_state_metric(
    db_session: massgov.pfml.db.Session, effective_date: datetime.date
) -> StateMetric:
    """Return state metrics effective on the given date."""

    state_metric = (
        db_session.query(StateMetric)
        .filter(StateMetric.effective_date <= effective_date)
        .order_by(StateMetric.effective_date.desc())
        .first()
    )

    if state_metric is None:
        logger.warning("State metric data was not found for effective_date %s", effective_date)
        raise RuntimeError(
            "State metric data was not found for effective_date {}".format(effective_date)
        )

    return state_metric


def wages_gte_unemployment_min(
    total_wages: decimal.Decimal, unemployment_min_earnings: decimal.Decimal
) -> bool:
    """Evaluate whether total wages, calculated from employee specific DOR data,
    are less than the unemployment minimum. The minimum unemployment figure is set
    each year on Oct. 1st and is stored in the StateMetric table."""

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

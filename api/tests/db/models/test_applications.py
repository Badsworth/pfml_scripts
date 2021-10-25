import datetime
from decimal import Decimal

from massgov.pfml.api.eligibility import eligibility_util
from massgov.pfml.db.models.factories import StateMetricFactory


def test_state_metric_init(initialize_factories_session, test_db_session):
    StateMetricFactory.create(
        effective_date=datetime.date(2021, 7, 1),
        unemployment_minimum_earnings=5200,
        average_weekly_wage=1555.75,
        maximum_weekly_benefit_amount=1000,
    )

    effective_date = datetime.date(2021, 9, 30)
    state_metric = eligibility_util.fetch_state_metric(test_db_session, effective_date)

    assert state_metric.maximum_weekly_benefit_amount == 1000

    # When maximum_weekly_benefit_amount is None this will be calculated as 64% of the average
    # weekly wage
    StateMetricFactory.create(
        effective_date=datetime.date(2022, 1, 1),
        unemployment_minimum_earnings=5300,
        average_weekly_wage=1666.75,
        maximum_weekly_benefit_amount=None,
    )

    effective_date = datetime.date(2022, 9, 30)
    state_metric = eligibility_util.fetch_state_metric(test_db_session, effective_date)
    expected_maximum_weekly_benefit_amount = round(Decimal(1666.75) * Decimal(0.64), 2)

    assert state_metric.maximum_weekly_benefit_amount == expected_maximum_weekly_benefit_amount

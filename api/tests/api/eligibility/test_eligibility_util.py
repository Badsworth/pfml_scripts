#
# Tests for massgov.pfml.api.eligibility.eligibility_util.
#

import datetime
import decimal

from massgov.pfml.api.eligibility import eligibility_util
from massgov.pfml.db.models.factories import StateMetricFactory


def test_wages_gte_unemployment_min_true():
    total_wages = 100000
    unemployment_min_earnings = 5100

    is_eligible = eligibility_util.wages_gte_unemployment_min(
        total_wages, unemployment_min_earnings
    )

    assert is_eligible is True


def test_wages_gte_unemployment_min_false():
    total_wages = 100
    unemployment_min_earnings = 5100

    is_eligible = eligibility_util.wages_gte_unemployment_min(
        total_wages, unemployment_min_earnings
    )

    assert is_eligible is False


def test_wages_gte_thirty_times_wba_true():
    total_wages = 40000
    state_average_weekly_wage = decimal.Decimal("1431.66")
    individual_average_weekly_wage = 1538

    is_eligible = eligibility_util.wages_gte_thirty_times_wba(
        total_wages,
        individual_average_weekly_wage,
        state_average_weekly_wage,
        datetime.date(2021, 1, 1),
    )

    assert is_eligible is True


def test_wages_gte_thirty_times_wba_false():
    total_wages = 1100
    state_average_weekly_wage = decimal.Decimal("1431.66")
    individual_average_weekly_wage = 423

    is_eligible = eligibility_util.wages_gte_thirty_times_wba(
        total_wages,
        individual_average_weekly_wage,
        state_average_weekly_wage,
        datetime.date(2021, 1, 1),
    )

    assert is_eligible is False


def test_wages_gte_thirty_times_wba_mid():
    total_wages = 20000
    state_average_weekly_wage = decimal.Decimal("1431.66")
    individual_average_weekly_wage = 769

    is_eligible = eligibility_util.wages_gte_thirty_times_wba(
        total_wages,
        individual_average_weekly_wage,
        state_average_weekly_wage,
        datetime.date(2021, 1, 1),
    )

    assert is_eligible is True


def test_fetch_state_metric(test_db_session):
    effective_date = datetime.date(2020, 10, 1)
    state_metric = eligibility_util.fetch_state_metric(test_db_session, effective_date)

    assert state_metric.unemployment_minimum_earnings == 5100
    assert state_metric.average_weekly_wage == decimal.Decimal("1431.66")


def test_fetch_state_metric_multiple_yrs(initialize_factories_session, test_db_session):
    StateMetricFactory.create(
        effective_date=datetime.date(2018, 10, 1),
        unemployment_minimum_earnings=4700,
        average_weekly_wage=1300.75,
    )

    StateMetricFactory.create(
        effective_date=datetime.date(2021, 10, 1),
        unemployment_minimum_earnings=5200,
        average_weekly_wage=1555.75,
    )

    StateMetricFactory.create(
        effective_date=datetime.date(2022, 10, 1),
        unemployment_minimum_earnings=5300,
        average_weekly_wage=1666.75,
    )

    state_metric_2019 = StateMetricFactory.create()

    effective_date = datetime.date(2020, 9, 30)
    state_metric = eligibility_util.fetch_state_metric(test_db_session, effective_date)

    assert (
        state_metric.unemployment_minimum_earnings
        == state_metric_2019.unemployment_minimum_earnings
    )
    assert state_metric.average_weekly_wage == state_metric_2019.average_weekly_wage

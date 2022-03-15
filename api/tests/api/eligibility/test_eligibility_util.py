#
# Tests for massgov.pfml.api.eligibility.eligibility_util.
#

import datetime
import decimal

from massgov.pfml.api.eligibility import eligibility_util
from massgov.pfml.db.models.factories import BenefitsMetricsFactory, UnemploymentMetricFactory


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
    maximum_weekly_benefit_amount = 850

    is_eligible = eligibility_util.wages_gte_thirty_times_wba(
        total_wages,
        individual_average_weekly_wage,
        state_average_weekly_wage,
        maximum_weekly_benefit_amount,
    )

    assert is_eligible is True


def test_wages_gte_thirty_times_wba_false():
    total_wages = 1100
    state_average_weekly_wage = decimal.Decimal("1431.66")
    individual_average_weekly_wage = 423
    maximum_weekly_benefit_amount = 850

    is_eligible = eligibility_util.wages_gte_thirty_times_wba(
        total_wages,
        individual_average_weekly_wage,
        state_average_weekly_wage,
        maximum_weekly_benefit_amount,
    )

    assert is_eligible is False


def test_wages_gte_thirty_times_wba_mid():
    total_wages = 20000
    state_average_weekly_wage = decimal.Decimal("1431.66")
    individual_average_weekly_wage = 769
    maximum_weekly_benefit_amount = 850

    is_eligible = eligibility_util.wages_gte_thirty_times_wba(
        total_wages,
        individual_average_weekly_wage,
        state_average_weekly_wage,
        maximum_weekly_benefit_amount,
    )

    assert is_eligible is True


def test_fetch_state_metric(test_db_session):
    effective_date = datetime.date(2020, 10, 1)
    (benefits_metrics_data, unemployment_metric_data) = eligibility_util.fetch_state_metric(
        test_db_session, effective_date
    )

    assert unemployment_metric_data.unemployment_minimum_earnings == 5100
    assert benefits_metrics_data.average_weekly_wage == decimal.Decimal("1431.66")
    assert benefits_metrics_data.maximum_weekly_benefit_amount == 850


def test_fetch_state_metric_multiple_yrs(initialize_factories_session, test_db_session):
    BenefitsMetricsFactory.create(
        effective_date=datetime.date(2018, 10, 1),
        average_weekly_wage=1300.75,
        maximum_weekly_benefit_amount=None,
    )

    UnemploymentMetricFactory.create(
        effective_date=datetime.date(2018, 10, 1), unemployment_minimum_earnings=4700
    )

    BenefitsMetricsFactory.create(
        effective_date=datetime.date(2021, 10, 1),
        average_weekly_wage=1555.75,
        maximum_weekly_benefit_amount=None,
    )

    UnemploymentMetricFactory.create(
        effective_date=datetime.date(2021, 10, 1), unemployment_minimum_earnings=5200
    )

    BenefitsMetricsFactory.create(
        effective_date=datetime.date(2022, 10, 1),
        average_weekly_wage=1666.75,
        maximum_weekly_benefit_amount=None,
    )

    UnemploymentMetricFactory.create(
        effective_date=datetime.date(2022, 10, 1), unemployment_minimum_earnings=5300
    )

    benefits_metrics_2019 = BenefitsMetricsFactory.create()
    unemployment_metric_2019 = UnemploymentMetricFactory.create()

    effective_date = datetime.date(2020, 9, 30)
    (benefits_metrics_data, unemployment_metric_data) = eligibility_util.fetch_state_metric(
        test_db_session, effective_date
    )

    assert (
        unemployment_metric_data.unemployment_minimum_earnings
        == unemployment_metric_2019.unemployment_minimum_earnings
    )
    assert benefits_metrics_data.average_weekly_wage == benefits_metrics_2019.average_weekly_wage
    assert (
        benefits_metrics_data.maximum_weekly_benefit_amount
        == benefits_metrics_2019.maximum_weekly_benefit_amount
    )

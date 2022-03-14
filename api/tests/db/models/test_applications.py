import datetime
from decimal import Decimal

from massgov.pfml.api.eligibility import eligibility_util
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    BenefitsMetricsFactory,
    UnemploymentMetricFactory,
)


def test_state_metric_init(initialize_factories_session, test_db_session):
    BenefitsMetricsFactory.create(
        effective_date=datetime.date(2021, 7, 1),
        average_weekly_wage=1555.75,
        maximum_weekly_benefit_amount=1000,
    )

    UnemploymentMetricFactory.create(
        effective_date=datetime.date(2021, 7, 1), unemployment_minimum_earnings=5200
    )

    effective_date = datetime.date(2021, 9, 30)
    (benefits_metrics_data, unemployment_metric_data) = eligibility_util.fetch_state_metric(
        test_db_session, effective_date
    )

    assert benefits_metrics_data.maximum_weekly_benefit_amount == 1000

    # When maximum_weekly_benefit_amount is None this will be calculated as 64% of the average
    # weekly wage
    BenefitsMetricsFactory.create(
        effective_date=datetime.date(2022, 1, 1),
        average_weekly_wage=1666.75,
        maximum_weekly_benefit_amount=None,
    )

    UnemploymentMetricFactory.create(
        effective_date=datetime.date(2022, 1, 1), unemployment_minimum_earnings=5300
    )

    effective_date = datetime.date(2022, 1, 1)
    (benefits_metrics_data, unemployment_metric_data) = eligibility_util.fetch_state_metric(
        test_db_session, effective_date
    )
    expected_maximum_weekly_benefit_amount = round(Decimal(1666.75) * Decimal(0.64), 2)

    assert (
        benefits_metrics_data.maximum_weekly_benefit_amount
        == expected_maximum_weekly_benefit_amount
    )


def test_split_with_application(initialize_factories_session, test_db_session):
    first_application = ApplicationFactory.create()
    assert first_application.split_from_application_id is None
    assert first_application.split_from_application is None
    assert first_application.split_into_application is None

    second_application = ApplicationFactory.create(
        split_from_application_id=first_application.application_id
    )

    test_db_session.commit()
    test_db_session.refresh(first_application)

    assert first_application.split_from_application_id is None
    assert first_application.split_into_application_id == second_application.application_id

    assert second_application.split_from_application_id == first_application.application_id
    assert second_application.split_into_application_id is None

    assert (
        first_application.split_into_application.application_id == second_application.application_id
    )
    assert (
        second_application.split_from_application.application_id == first_application.application_id
    )

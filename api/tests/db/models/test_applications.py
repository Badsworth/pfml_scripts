import datetime
from decimal import Decimal

from massgov.pfml.api.eligibility import eligibility_util
from massgov.pfml.db.models.applications import Holiday, _are_holidays_valid
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


def test_validate_holidays():
    sunday_holiday = Holiday(
        holiday_id=6,
        date=datetime.date(2022, 6, 19),
        holiday_name="Juneteenth Independence Day",
    )

    assert _are_holidays_valid([sunday_holiday]) is False

    id_1_holiday_1 = Holiday(
        holiday_id=1,
        date=datetime.date(2022, 6, 20),
        holiday_name="Juneteenth Independence Day",
    )
    id_1_holiday_2 = Holiday(
        holiday_id=1,
        date=datetime.date(2022, 1, 1),
        holiday_name="Juneteenth Independence Day",
    )

    assert _are_holidays_valid([id_1_holiday_1, id_1_holiday_2]) is False

    valid_holidays = [
        Holiday(holiday_id=1, date=datetime.date(2022, 1, 1), holiday_name="New Year's Day"),
        Holiday(
            holiday_id=2,
            date=datetime.date(2022, 1, 17),
            holiday_name="Martin Luther King, Jr. Day",
        ),
        Holiday(
            holiday_id=3, date=datetime.date(2022, 2, 21), holiday_name="Washington's Birthday"
        ),
        Holiday(holiday_id=4, date=datetime.date(2022, 4, 18), holiday_name="Patriots' Day"),
        Holiday(holiday_id=5, date=datetime.date(2022, 5, 30), holiday_name="Memorial Day"),
        Holiday(
            holiday_id=6,
            date=datetime.date(2022, 6, 20),
            holiday_name="Juneteenth Independence Day",
        ),
        Holiday(holiday_id=7, date=datetime.date(2022, 7, 4), holiday_name="Independence Day"),
        Holiday(holiday_id=8, date=datetime.date(2022, 9, 5), holiday_name="Labor Day"),
        Holiday(holiday_id=9, date=datetime.date(2022, 10, 10), holiday_name="Columbus Day"),
        Holiday(holiday_id=10, date=datetime.date(2022, 11, 11), holiday_name="Veterans' Day"),
        Holiday(holiday_id=11, date=datetime.date(2022, 11, 24), holiday_name="Thanksgiving Day"),
        Holiday(holiday_id=12, date=datetime.date(2022, 12, 26), holiday_name="Christmas Day"),
    ]

    assert _are_holidays_valid(valid_holidays) is True

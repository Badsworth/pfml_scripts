from datetime import date, timedelta

import pytest

from massgov.pfml.api.eligibility import eligibility
from massgov.pfml.db.models.factories import EmployeeFactory


@pytest.fixture
def employee():
    employee = EmployeeFactory.create()
    return employee


def test_set_eligibility_date():
    today = date.today()
    yesterday = today - timedelta(days=1)
    _app_date = eligibility.calculate_effective_date(today, yesterday)

    assert _app_date == today

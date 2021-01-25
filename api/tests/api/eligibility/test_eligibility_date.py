from datetime import date, timedelta

from massgov.pfml.api.eligibility.eligibility_date import eligibility_date


def test_eligibility_date():
    today = date.today()
    yesterday = today - timedelta(days=1)
    _eligibility_date = eligibility_date(today, yesterday)

    assert _eligibility_date == today

    _eligibility_date = eligibility_date(yesterday, today)
    assert _eligibility_date == yesterday

from datetime import date, datetime, timedelta
from decimal import Decimal

from freezegun import freeze_time

from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, EmployerQuarterlyContributionFactory
from massgov.pfml.util.strings import format_fein


def test_employers_receive_201_from_add_fein(
    monkeypatch, client, employer_user, employer_auth_token, test_db_session
):
    current_employer = EmployerFactory.create()
    employer_to_add = EmployerFactory.create(employer_fein="999999999")
    yesterday = datetime.now() - timedelta(days=1)
    EmployerQuarterlyContributionFactory.create(
        employer=employer_to_add, filing_period=yesterday.strftime("%Y-%m-%d")
    )

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=current_employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )

    test_db_session.add(link)
    test_db_session.commit()

    post_body = {"employer_fein": "99-9999999"}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    response_data = response.get_json()["data"]
    assert response.status_code == 201
    assert response_data["employer_dba"] == employer_to_add.employer_dba
    assert response_data["employer_fein"] == format_fein(employer_to_add.employer_fein)
    assert type(response_data["employer_id"]) is str


def test_employers_receive_402_if_no_withholding_data(client, employer_auth_token):
    EmployerFactory.create(employer_fein="999999999")

    post_body = {"employer_fein": "99-9999999"}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    errors = response.get_json().get("errors")

    assert response.status_code == 402
    assert {
        "field": "employer_fein",
        "message": "Employer has no verification data",
        "type": "employer_requires_verification_data",
    } in errors


def test_employers_receive_400_if_fein_missing(client, employer_auth_token):
    post_body = {"employer_fein": None}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    errors = response.get_json().get("errors")

    assert response.status_code == 400
    assert {
        "field": "employer_fein",
        "message": "employer_fein is required",
        "type": "required",
    } in errors


def test_employers_receive_400_if_ein_invalid_format(client, employer_auth_token):
    # Too short
    post_body = {"employer_fein": "123"}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    errors = response.get_json().get("errors")

    assert response.status_code == 400
    assert {
        "field": "employer_fein",
        "message": "'123' does not match '^\\\\d{2}-\\\\d{7}$'",
        "rule": "^\\d{2}-\\d{7}$",
        "type": "pattern",
    } in errors


def test_employers_receive_409_if_duplicate_fein(
    client, employer_user, employer_auth_token, test_db_session
):
    employer_to_add = EmployerFactory.create(employer_fein="999999999")
    yesterday = datetime.now() - timedelta(days=1)
    EmployerQuarterlyContributionFactory.create(
        employer=employer_to_add, filing_period=yesterday.strftime("%Y-%m-%d")
    )

    link = UserLeaveAdministrator(user=employer_user, employer=employer_to_add)
    test_db_session.add(link)
    test_db_session.commit()

    post_body = {"employer_fein": "99-9999999"}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    errors = response.get_json().get("errors")

    assert response.status_code == 409
    assert {
        "field": "employer_fein",
        "message": "Duplicate employer for user",
        "type": "duplicate",
    } in errors


@freeze_time("2021-05-01")
def test_employers_receive_200_and_most_recent_historical_date_from_get_withholding_dates(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(
        employer=employer,
        filing_period=date(2020, 6, 30),
        employer_total_pfml_contribution=Decimal("15234.58"),
    )
    EmployerQuarterlyContributionFactory.create(
        employer=employer,
        filing_period=date(2020, 3, 31),
        employer_total_pfml_contribution=Decimal("15234.58"),
    )
    EmployerQuarterlyContributionFactory.create(
        employer=employer,
        # Future date! Shouldn't be returned when there's historical data
        filing_period=date(2021, 9, 30),
        employer_total_pfml_contribution=Decimal("15234.58"),
    )
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_data = response.get_json()["data"]

    assert response.status_code == 200
    assert response_data["filing_period"] == "2020-06-30"


@freeze_time("2021-05-01")
def test_employers_receive_future_withholding_if_no_past_withholding(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(
        employer=employer,
        employer_total_pfml_contribution=Decimal("15234.58"),
        filing_period=date(2021, 9, 30),
    )
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_data = response.get_json()["data"]

    assert response.status_code == 200
    assert response_data["filing_period"] == "2021-09-30"


@freeze_time("2021-05-01")
def test_employers_receive_future_withholding_if_0_amount_past_withholding(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(
        # Within past year, but 0 amount
        employer=employer,
        employer_total_pfml_contribution=0,
        filing_period=date(2020, 6, 30),
    )
    EmployerQuarterlyContributionFactory.create(
        employer=employer,
        # Future non-zero amount
        employer_total_pfml_contribution=Decimal("15234.58"),
        filing_period=date(2021, 9, 30),
    )
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_data = response.get_json()["data"]

    assert response.status_code == 200
    assert response_data["filing_period"] == "2021-09-30"


@freeze_time("2021-05-01")
def test_employers_receive_future_withholding_if_old_past_withholding(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(
        # Non-zero amount, but over a year ago
        employer=employer,
        employer_total_pfml_contribution=Decimal("15234.58"),
        filing_period=date(2020, 1, 30),
    )
    EmployerQuarterlyContributionFactory.create(
        employer=employer,
        # Future non-zero amount
        employer_total_pfml_contribution=Decimal("15234.58"),
        filing_period=date(2021, 9, 30),
    )
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_data = response.get_json()["data"]

    assert response.status_code == 200
    assert response_data["filing_period"] == "2021-09-30"


def test_employers_receive_402_for_no_contributions(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()

    # Create other contributions to confirm we're limiting the check to the target employer
    EmployerQuarterlyContributionFactory.create(employer=EmployerFactory.create())

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    assert response.status_code == 402


@freeze_time("2021-05-01")
def test_employers_receive_402_for_old_contributions(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    current_date = date.today()
    two_years_ago = date(current_date.year - 2, current_date.month, current_date.day)
    EmployerQuarterlyContributionFactory.create(
        employer=employer, filing_period=two_years_ago, employer_total_pfml_contribution=100
    )

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    assert response.status_code == 402


def test_employers_receive_402_for_zero_amount_contributions(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    EmployerQuarterlyContributionFactory.create(
        employer=employer, filing_period=date.today(), employer_total_pfml_contribution=0
    )

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/withholding/{employer.employer_id}",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    assert response.status_code == 402

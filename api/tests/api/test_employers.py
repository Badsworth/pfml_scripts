from datetime import date, datetime
from decimal import Decimal

from massgov.pfml.db.models.employees import EmployerQuarterlyContribution, UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, EmployerQuarterlyContributionFactory
from massgov.pfml.util.strings import mask_fein


def test_employers_receive_201_from_add_fein(
    client, employer_user, employer_auth_token, test_db_session
):
    current_employer = EmployerFactory.create()
    employer_to_add = EmployerFactory.create(employer_fein="999999999")

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=current_employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )

    test_db_session.add(link)
    test_db_session.commit()

    post_body = {"employer_fein": "999999999"}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    response_data = response.get_json()["data"]
    assert response.status_code == 201
    assert response_data["employer_dba"] == employer_to_add.employer_dba
    assert response_data["employer_fein"] == mask_fein(employer_to_add.employer_fein)
    assert type(response_data["employer_id"]) is str


def test_employers_receive_400_from_bad_fein(
    client, employer_user, employer_auth_token, test_db_session
):
    current_employer = EmployerFactory.create()

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=current_employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )

    test_db_session.add(link)
    test_db_session.commit()

    post_body = {"employer_fein": "999999999"}

    response = client.post(
        "/v1/employers/add",
        json=post_body,
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 400


def test_employers_receive_200_and_most_recent_date_from_get_withholding_dates(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()

    employer_contribution_row_1 = EmployerQuarterlyContribution(
        employer_id=employer.employer_id,
        filing_period=date(2020, 6, 30),
        pfm_account_id="12345678912345",
        employer_total_pfml_contribution=Decimal("15234.58"),
        dor_received_date=datetime.now(),
        dor_updated_date=datetime.now(),
    )
    employer_contribution_row_2 = EmployerQuarterlyContribution(
        employer_id=employer.employer_id,
        filing_period=date(2020, 3, 31),
        pfm_account_id="12345678912345",
        employer_total_pfml_contribution=Decimal("15234.58"),
        dor_received_date=datetime.now(),
        dor_updated_date=datetime.now(),
    )
    test_db_session.add(employer_contribution_row_1)
    test_db_session.add(employer_contribution_row_2)
    test_db_session.commit()

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


def test_employers_receive_402_for_no_contributions(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()

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

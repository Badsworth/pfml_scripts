from datetime import date, datetime
from decimal import Decimal

from massgov.pfml.db.models.employees import EmployerQuarterlyContribution, UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory


def test_employers_receive_200_and_most_recent_date_from_get_withholding_dates(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create(employer_fein="999999999")

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
        "/v1/employers/withholding/999999999",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_data = response.get_json()["data"]

    assert response.status_code == 200
    assert response_data["filing_period"] == "2020-06-30"


def test_employers_receive_400_for_wrong_fein(
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
        "/v1/employers/withholding/999999999",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    assert response.status_code == 400


def test_employers_receive_404_for_no_contributions(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create(employer_fein="999999999")

    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/employers/withholding/999999999",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    assert response.status_code == 404

import pytest

import tests.api
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory, EmployerQuarterlyContributionFactory
from massgov.pfml.db.models.verifications import Verification

verifications_body = {
    "employer_id": "6e441845-a933-4a0b-827b-ec5bf467429e",
    "withholding_amount": 10,
    "withholding_quarter": "2021-01-15",
}


@pytest.fixture
def employer():
    return EmployerFactory.create()


@pytest.fixture
def employer_quarterly_contribution():
    return EmployerQuarterlyContributionFactory.create()


def test_error_if_user_not_connected_to_employer(caplog, client, employer_auth_token):
    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )
    assert response.status_code == 400
    tests.api.validate_error_response(
        response, 400, message="User not associated with this employer."
    )
    assert "User not associated with this employer." in caplog.text


def test_error_if_withholding_data_not_in_db(
    caplog, client, employer_auth_token, test_db_session, employer_user, employer
):
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    verifications_body["employer_id"] = employer.employer_id

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )
    assert response.status_code == 400
    tests.api.validate_error_response(
        response, 400, message="Employer has no quarterly contribution data."
    )
    assert "Employer has no quarterly contribution data." in caplog.text


def test_error_if_withholding_amount_is_incorrect(
    caplog,
    client,
    employer_auth_token,
    test_db_session,
    employer_quarterly_contribution,
    employer_user,
):
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer_quarterly_contribution.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body["withholding_amount"] = (
        employer_quarterly_contribution.employer_total_pfml_contribution + 1
    )
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

    assert response.status_code == 400
    tests.api.validate_error_response(response, 400, message="Withholding amount is incorrect.")
    assert "Withholding amount is incorrect." in caplog.text


def test_verification_successful_for_valid_data(
    client, employer_auth_token, test_db_session, employer_quarterly_contribution, employer_user
):
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer_quarterly_contribution.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body[
        "withholding_amount"
    ] = employer_quarterly_contribution.employer_total_pfml_contribution
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

    assert response.status_code == 201
    verification = test_db_session.query(Verification).first()
    user_leave_administrator = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(
            UserLeaveAdministrator.user_leave_administrator_id == link.user_leave_administrator_id
        )
        .one_or_none()
    )
    assert user_leave_administrator.employer_id == employer_quarterly_contribution.employer_id
    assert user_leave_administrator.verification_id == verification.verification_id

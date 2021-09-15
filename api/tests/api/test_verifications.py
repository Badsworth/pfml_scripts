import logging  # noqa: B1
from datetime import datetime, timedelta
from unittest import mock

import pytest
from werkzeug.exceptions import ServiceUnavailable

import tests.api
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    EmployerFactory,
    EmployerQuarterlyContributionFactory,
    VerificationFactory,
)
from massgov.pfml.db.models.verifications import Verification, VerificationType
from massgov.pfml.util.strings import format_fein

# every test in here requires real resources
pytestmark = pytest.mark.integration

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


@pytest.fixture
def verification():
    return VerificationFactory.create()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_error_if_user_not_connected_to_employer(
    mock_fineos_call, caplog, client, employer_auth_token
):
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
    mock_fineos_call.assert_not_called()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_error_if_withholding_data_not_in_db(
    mock_fineos_call, caplog, client, employer_auth_token, test_db_session, employer_user, employer
):
    link = UserLeaveAdministrator(user_id=employer_user.user_id, employer_id=employer.employer_id,)
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
    mock_fineos_call.assert_not_called()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_error_if_withholding_amount_is_outside_threshold(
    mock_fineos_call,
    client,
    employer_auth_token,
    test_db_session,
    employer_quarterly_contribution,
    employer_user,
):
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer_quarterly_contribution.employer_id,
    )
    test_db_session.add(link)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body["withholding_amount"] = (
        employer_quarterly_contribution.employer_total_pfml_contribution + 0.11
    )
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

    assert response.status_code == 400
    tests.api.validate_error_response(response, 400, message="Withholding amount is incorrect.")
    mock_fineos_call.assert_not_called()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_verification_successful_for_valid_data(
    mock_fineos_call,
    caplog,
    client,
    employer_auth_token,
    test_db_session,
    employer_quarterly_contribution,
    employer_user,
):
    mock_fineos_call.return_value = ["", ""]
    caplog.set_level(logging.INFO)  # noqa: B1
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer_quarterly_contribution.employer_id,
    )

    # Must be at least 1 day ago for employer.has_verification_data to be True
    employer_quarterly_contribution.filing_period = (datetime.now() - timedelta(1)).strftime(
        "%Y-%m-%d"
    )

    test_db_session.add(link)
    test_db_session.add(employer_quarterly_contribution)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body[
        "withholding_amount"
    ] = employer_quarterly_contribution.employer_total_pfml_contribution
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period
    assert link.fineos_web_id is None

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

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
    assert "Successfully verified user." in caplog.text

    assert (
        verification.verification_type_id == VerificationType.PFML_WITHHOLDING.verification_type_id
    )

    assert response.status_code == 201
    response_body = response.get_json()
    assert response_body.get("data")["user_id"] == str(employer_user.user_id)
    assert response_body.get("data")["roles"] == [
        {"role_description": "Employer", "role_id": 3},
    ]

    employer = employer_quarterly_contribution.employer
    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer.employer_dba,
            "employer_fein": format_fein(employer.employer_fein),
            "employer_id": str(employer.employer_id),
            "has_fineos_registration": True,
            "verified": True,
            "has_verification_data": True,
        }
    ]
    assert user_leave_administrator.fineos_web_id is not None
    mock_fineos_call.assert_called_once()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_verification_successful_for_data_within_threshold(
    mock_fineos_call,
    caplog,
    client,
    employer_auth_token,
    test_db_session,
    employer_quarterly_contribution,
    employer_user,
):
    mock_fineos_call.return_value = ["", ""]
    caplog.set_level(logging.INFO)  # noqa: B1
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer_quarterly_contribution.employer_id,
    )

    # Must be at least 1 day ago for employer.has_verification_data to be True
    employer_quarterly_contribution.filing_period = (datetime.now() - timedelta(1)).strftime(
        "%Y-%m-%d"
    )

    test_db_session.add(link)
    test_db_session.add(employer_quarterly_contribution)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body["withholding_amount"] = (
        employer_quarterly_contribution.employer_total_pfml_contribution - 0.10
    )
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period
    assert link.fineos_web_id is None

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

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
    assert "Successfully verified user." in caplog.text

    assert (
        verification.verification_type_id == VerificationType.PFML_WITHHOLDING.verification_type_id
    )

    assert response.status_code == 201
    response_body = response.get_json()
    assert response_body.get("data")["user_id"] == str(employer_user.user_id)
    assert response_body.get("data")["roles"] == [
        {"role_description": "Employer", "role_id": 3},
    ]

    employer = employer_quarterly_contribution.employer
    assert response_body.get("data")["user_leave_administrators"] == [
        {
            "employer_dba": employer.employer_dba,
            "employer_fein": format_fein(employer.employer_fein),
            "employer_id": str(employer.employer_id),
            "has_fineos_registration": True,
            "verified": True,
            "has_verification_data": True,
        }
    ]
    assert user_leave_administrator.fineos_web_id is not None
    mock_fineos_call.assert_called_once()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_error_if_users_been_verified(
    mock_fineos_call,
    client,
    employer_auth_token,
    test_db_session,
    employer_user,
    employer,
    verification,
):
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer.employer_id, verification=verification,
    )

    test_db_session.add(link)
    test_db_session.commit()

    verifications_body["employer_id"] = employer.employer_id

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

    assert response.status_code == 409
    tests.api.validate_error_response(response, 409, message="User has already been verified.")
    mock_fineos_call.assert_not_called()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_rollback_when_fineos_call_failed(
    mock_fineos_call,
    caplog,
    client,
    employer_auth_token,
    test_db_session,
    employer_quarterly_contribution,
    employer_user,
):
    mock_fineos_call.return_value = ["400", "Unepexted error on fineos side"]
    caplog.set_level(logging.INFO)  # noqa: B1
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer_quarterly_contribution.employer_id,
    )
    # Must be at least 1 day ago for employer.has_verification_data to be True
    employer_quarterly_contribution.filing_period = (datetime.now() - timedelta(1)).strftime(
        "%Y-%m-%d"
    )

    test_db_session.add(link)
    test_db_session.add(employer_quarterly_contribution)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body[
        "withholding_amount"
    ] = employer_quarterly_contribution.employer_total_pfml_contribution
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period

    assert link.fineos_web_id is None
    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

    verification = test_db_session.query(Verification).one_or_none()

    user_leave_administrator = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(
            UserLeaveAdministrator.user_leave_administrator_id == link.user_leave_administrator_id
        )
        .one_or_none()
    )

    assert verification is None
    assert response.status_code == ServiceUnavailable.code
    assert user_leave_administrator.employer_id == employer_quarterly_contribution.employer_id
    assert user_leave_administrator.verification_id is None
    assert user_leave_administrator.fineos_web_id is None
    assert "Failed to verify user, fineos error." in caplog.text
    mock_fineos_call.assert_called_once()


@mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.create_or_update_leave_admin")
def test_rollback_when_fineos_call_failed_unexpected_raise_error(
    mock_fineos_call,
    caplog,
    client,
    employer_auth_token,
    test_db_session,
    employer_quarterly_contribution,
    employer_user,
):
    # exception raise by fineos request failure
    mock.side_effect = Exception("Unepexted error on fineos side")

    caplog.set_level(logging.INFO)  # noqa: B1
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id, employer_id=employer_quarterly_contribution.employer_id,
    )

    # Must be at least 1 day ago for employer.has_verification_data to be True
    employer_quarterly_contribution.filing_period = (datetime.now() - timedelta(1)).strftime(
        "%Y-%m-%d"
    )

    test_db_session.add(link)
    test_db_session.add(employer_quarterly_contribution)
    test_db_session.commit()

    verifications_body["employer_id"] = employer_quarterly_contribution.employer_id
    verifications_body[
        "withholding_amount"
    ] = employer_quarterly_contribution.employer_total_pfml_contribution
    verifications_body["withholding_quarter"] = employer_quarterly_contribution.filing_period
    assert link.fineos_web_id is None

    response = client.post(
        "/v1/employers/verifications",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=verifications_body,
    )

    verification = test_db_session.query(Verification).one_or_none()

    user_leave_administrator = (
        test_db_session.query(UserLeaveAdministrator)
        .filter(
            UserLeaveAdministrator.user_leave_administrator_id == link.user_leave_administrator_id
        )
        .one_or_none()
    )

    assert verification is None
    assert response.status_code == ServiceUnavailable.code
    assert user_leave_administrator.employer_id == employer_quarterly_contribution.employer_id
    assert user_leave_administrator.verification_id is None
    assert user_leave_administrator.fineos_web_id is None
    assert "Failed to verify user, fineos error." in caplog.text
    mock_fineos_call.assert_called_once()


def test_manual_verification(client, test_db_session):
    # Just a test to ensure we have a "MANUAL" type for Verifications

    model = Verification(verification_type_id=VerificationType.MANUAL.verification_type_id)
    model.verification_metadata = {"testing": "manual verification test"}
    test_db_session.add(model)
    test_db_session.commit()

    manual_verifications = (
        test_db_session.query(Verification)
        .filter(Verification.verification_type_id == VerificationType.MANUAL.verification_type_id)
        .all()
    )
    assert len(manual_verifications) == 1

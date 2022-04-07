from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from unittest import mock

import factory  # this is from the factory_boy package
import pytest
from jose import jwt
from jose.constants import ALGORITHMS

import massgov.pfml.util.datetime as datetime_util
import tests.api
from massgov.pfml.api.claims import map_request_decision_param_to_db_columns
from massgov.pfml.api.services.claims import ClaimWithdrawnError
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.applications import FINEOSWebIdExt
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    Claim,
    LeaveRequestDecision,
    LkManagedRequirementStatus,
    ManagedRequirement,
    ManagedRequirementStatus,
    ManagedRequirementType,
    Role,
    State,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    TaxIdentifierFactory,
    UserFactory,
    VerificationFactory,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.util.pydantic.types import FEINFormattedStr
from massgov.pfml.util.strings import format_fein


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


@pytest.fixture
def test_verification():
    return VerificationFactory.create()


@pytest.fixture
def update_claim_body():
    return {
        "comment": "string",
        "employer_benefits": [
            {
                "benefit_amount_dollars": 0,
                "benefit_amount_frequency": "Per Day",
                "benefit_end_date": "1970-01-01",
                "benefit_start_date": "1970-01-01",
                "benefit_type": "Accrued paid leave",
            }
        ],
        "employer_decision": "Approve",
        "fraud": "Yes",
        "has_amendments": False,
        "hours_worked_per_week": 40,
        "previous_leaves": [
            {
                "leave_end_date": "2021-02-06",
                "leave_start_date": "2021-01-25",
                "leave_reason": "Pregnancy",
            }
        ],
        "leave_reason": "Pregnancy/Maternity",
    }


@pytest.fixture
def employer():
    return EmployerFactory.create()


@pytest.fixture
def claim(employer):
    return ClaimFactory.create(employer_id=employer.employer_id)


@pytest.fixture
def user_leave_admin(employer_user, employer, test_verification):
    return UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
        verification=test_verification,
    )


def assert_claim_response_equal_to_claim_query(
    claim_response, claim_query, has_paid_payments=False
) -> bool:
    if claim_query.absence_period_end_date:
        assert claim_response[
            "absence_period_end_date"
        ] == claim_query.absence_period_end_date.strftime("%Y-%m-%d")
    else:
        assert claim_response["absence_period_end_date"] is None
    if claim_query.absence_period_start_date:
        assert claim_response[
            "absence_period_start_date"
        ] == claim_query.absence_period_start_date.strftime("%Y-%m-%d")
    else:
        assert claim_response["absence_period_start_date"] is None
    assert claim_response["fineos_absence_id"] == claim_query.fineos_absence_id
    assert claim_response["fineos_notification_id"] == claim_query.fineos_notification_id
    assert claim_response["employer"]["employer_dba"] == claim_query.employer.employer_dba
    assert claim_response["employer"]["employer_fein"] == FEINFormattedStr.validate_type(
        claim_query.employer.employer_fein
    )
    assert claim_response["employer"]["employer_id"] == str(claim_query.employer.employer_id)
    assert claim_response["employee"]["first_name"] == claim_query.employee.first_name
    assert claim_response["employee"]["middle_name"] == claim_query.employee.middle_name
    assert claim_response["employee"]["last_name"] == claim_query.employee.last_name
    assert claim_response["employee"]["other_name"] == claim_query.employee.other_name
    assert claim_response["claim_type_description"] == claim_query.claim_type.claim_type_description
    assert claim_response["has_paid_payments"] == has_paid_payments


def assert_claim_pfml_crm_response_equal_to_claim_query(claim_response, claim_query) -> bool:
    assert claim_response["fineos_absence_id"] == claim_query.fineos_absence_id
    assert claim_response["fineos_notification_id"] == claim_query.fineos_notification_id
    assert claim_response["employee"]["employee_id"] == str(claim_query.employee.employee_id)
    assert (
        claim_response["employee"]["fineos_customer_number"]
        == claim_query.employee.fineos_customer_number
    )
    assert claim_response["employee"]["first_name"] == claim_query.employee.first_name
    assert claim_response["employee"]["middle_name"] == claim_query.employee.middle_name
    assert claim_response["employee"]["last_name"] == claim_query.employee.last_name
    assert claim_response["employee"]["other_name"] == claim_query.employee.other_name

    # Ensure only fields in ClaimForPfmlCrmResponse are returned
    assert "claim_type_description" not in claim_response
    assert "has_paid_payments" not in claim_response
    assert "employer" not in claim_response
    assert "created_at" not in claim_response
    assert "absence_period_end_date" not in claim_response
    assert "absence_period_start_date" not in claim_response
    assert "absence_periods" not in claim_response
    assert "managed_requirements" not in claim_response


def assert_detailed_claim_response_equal_to_claim_query(
    claim_response, claim_query, application=None, has_paid_payments=False
) -> bool:
    if application:
        assert claim_response["application_id"] == str(application.application_id)
    assert claim_response["fineos_absence_id"] == claim_query.fineos_absence_id
    assert claim_response["fineos_notification_id"] == claim_query.fineos_notification_id
    assert claim_response["employer"]["employer_dba"] == claim_query.employer.employer_dba
    assert claim_response["employer"]["employer_fein"] == FEINFormattedStr.validate_type(
        claim_query.employer.employer_fein
    )
    assert claim_response["employer"]["employer_id"] == str(claim_query.employer.employer_id)
    assert claim_response["employee"]["first_name"] == claim_query.employee.first_name
    assert claim_response["employee"]["middle_name"] == claim_query.employee.middle_name
    assert claim_response["employee"]["last_name"] == claim_query.employee.last_name
    assert claim_response["employee"]["other_name"] == claim_query.employee.other_name
    assert claim_response["has_paid_payments"] == has_paid_payments


def leave_period_response_equal_leave_period_query(
    leave_period_response, leave_period_query
) -> bool:
    return (
        leave_period_response["absence_period_start_date"]
        == leave_period_query["absence_period_start_date"]
        and leave_period_response["absence_period_end_date"]
        == leave_period_query["absence_period_end_date"]
        and leave_period_response["request_decision"] == leave_period_query["request_decision"]
        and leave_period_response["period_type"] == leave_period_query["period_type"]
        and leave_period_response["reason"] == leave_period_query["reason"]
        and leave_period_response["reason_qualifier_one"]
        == leave_period_query["reason_qualifier_one"]
    )


# TODO (CP-2636): Refactor tests to use fixtures
class TestGetClaimEndpoint:
    @pytest.fixture
    def setup_db(self, test_db_session, fineos_web_id_ext, application):
        test_db_session.add(fineos_web_id_ext)
        test_db_session.commit()

    @pytest.fixture
    def employer(self):
        return EmployerFactory.create(employer_fein="112222222")

    @pytest.fixture
    def employee(self):
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="123456789")
        return EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)

    @pytest.fixture
    def fineos_web_id_ext(self, employee, employer):
        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "web_id"

        return fineos_web_id_ext

    @pytest.fixture
    def claim(self, employer, employee):
        return ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="foo",
        )

    @pytest.fixture
    def application(self, user, claim):
        return ApplicationFactory.create(user=user, claim=claim)

    def test_get_claim_claim_does_not_exist(self, caplog, client, auth_token):
        response = client.get(
            "/v1/claims/NTN-100-ABS-01", headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404
        tests.api.validate_error_response(response, 404, message="Claim not in PFML database.")
        assert "Claim not in PFML database." in caplog.text

    def test_get_claim_user_has_no_access(self, caplog, client, auth_token):
        claim = ClaimFactory.create()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403
        tests.api.validate_error_response(
            response, 403, message="User does not have access to claim."
        )
        assert "User does not have access to claim." in caplog.text

    def test_get_claim_as_employer_returns_403(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()
        claim = ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403

        message = response.get_json().get("message")
        assert message == "Employers are not allowed to access claimant claim info"

    def test_get_claim_employee_different_fineos_names(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(
            tax_identifier_id=tax_identifier.tax_identifier_id,
            first_name="Foo",
            last_name="Bar",
            middle_name="Baz",
            fineos_employee_first_name="Foo2",
            fineos_employee_last_name="Bar2",
            fineos_employee_middle_name="Baz2",
        )

        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        claim_data = response_body.get("data")

        assert claim_data["employee"]["first_name"] == "Foo2"
        assert claim_data["employee"]["middle_name"] == "Baz2"
        assert claim_data["employee"]["last_name"] == "Bar2"

    def test_get_claim_employee_no_fineos_names(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(
            tax_identifier_id=tax_identifier.tax_identifier_id,
            first_name="Foo",
            last_name="Bar",
            middle_name="Baz",
            fineos_employee_first_name=None,
            fineos_employee_last_name=None,
            fineos_employee_middle_name=None,
        )

        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        claim_data = response_body.get("data")

        assert claim_data["employee"]["first_name"] == "Foo"
        assert claim_data["employee"]["middle_name"] == "Baz"
        assert claim_data["employee"]["last_name"] == "Bar"

    def test_get_claim_user_has_access_as_claimant(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)
        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim)

    def test_get_claim_with_leave_periods(self, caplog, client, auth_token, user, test_db_session):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)
        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )

        application = ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        leave_period = {
            "absence_period_end_date": "2021-01-30",
            "absence_period_start_date": "2021-01-29",
            "evidence_status": None,
            "fineos_leave_request_id": None,
            "period_type": "Continuous",
            "reason": "Child Bonding",
            "reason_qualifier_one": "Foster Care",
            "reason_qualifier_two": "",
            "request_decision": "Pending",
        }

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim, application)
        assert leave_period_response_equal_leave_period_query(
            claim_data["absence_periods"][0], leave_period
        )

    @mock.patch("massgov.pfml.api.claims.get_claim_detail")
    def test_withdrawn_claim_returns_403(
        self, mock_get_claim_detail, claim, client, auth_token, setup_db
    ):
        mock_get_claim_detail.side_effect = ClaimWithdrawnError()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403

        response_body = response.get_json()
        issues = response_body.get("errors")
        assert issues[0].get("type") == "fineos_claim_withdrawn"

    @mock.patch("massgov.pfml.api.claims.get_claim_detail")
    def test_with_get_claim_detail_error_returns_500(
        self, mock_get_claim_detail, claim, client, auth_token, setup_db, caplog
    ):
        error_msg = "oops :("
        mock_get_claim_detail.side_effect = Exception(error_msg)

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 500
        assert "get_claim failure" in caplog.text
        assert error_msg in caplog.text

    def test_get_claim_with_managed_requirements(self, client, auth_token, user, test_db_session):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)

        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )

        managed_requirement: ManagedRequirement = ManagedRequirementFactory.create(
            claim=claim, claim_id=claim.claim_id
        )
        ManagedRequirementFactory.create(claim=claim, claim_id=claim.claim_id)

        application = ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim, application)
        managed_requirement_response = claim_data["managed_requirements"]
        assert len(managed_requirement_response) == 2
        assert (
            managed_requirement.follow_up_date.strftime("%Y-%m-%d")
            == managed_requirement_response[0]["follow_up_date"]
        )
        assert (
            managed_requirement.managed_requirement_status.managed_requirement_status_description
            == managed_requirement_response[0]["status"]
        )
        assert (
            managed_requirement.managed_requirement_type.managed_requirement_type_description
            == managed_requirement_response[0]["type"]
        )
        assert (
            managed_requirement.managed_requirement_category.managed_requirement_category_description
            == managed_requirement_response[0]["category"]
        )

    def test_get_claim_with_paid_payments(self, test_db_session, client, auth_token, user):
        payment_factory = DelegatedPaymentFactory(
            test_db_session, fineos_absence_id="NTN-304363-ABS-01"
        )
        claim = payment_factory.get_or_create_claim()
        payment_factory.get_or_create_payment_with_state(
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )
        ApplicationFactory.create(user=user, claim=claim)

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert claim_data["has_paid_payments"] is True


class TestGetClaimsEndpoint:
    def test_get_claims_as_leave_admin(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employerA = EmployerFactory.create()
        employee = EmployeeFactory.create()

        generated_claims = [
            ClaimFactory.create(
                employer=employerA, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )
            for _ in range(3)
        ]

        # Create another employer and claim that should not be returned
        employerB = EmployerFactory.create()
        ClaimFactory.create(
            employer=employerB, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employerA.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == len(generated_claims)
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

        # POST /claims/search
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json={"terms": {}},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == len(generated_claims)
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

    def test_get_claims_as_pfml_crm_user(self, client, snow_user_headers):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        employee_with_fineos_customer_number = EmployeeWithFineosNumberFactory.create()

        generated_claims = [
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )
            for _ in range(3)
        ]

        generated_claims.append(
            ClaimFactory.create(employer=employer, employee=employee_with_fineos_customer_number)
        )

        # GET /claims deprecated
        response = client.get("/v1/claims", headers=snow_user_headers)
        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")

        # assert that all created claims are returned
        assert len(claim_data) == len(generated_claims)

        for response_claim, generated_claim in zip(claim_data, reversed(generated_claims)):
            assert_claim_pfml_crm_response_equal_to_claim_query(response_claim, generated_claim)

        # POST /claims/search
        response = client.post("/v1/claims/search", headers=snow_user_headers, json={"terms": {}})
        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")

        # assert that all created claims are returned
        assert len(claim_data) == len(generated_claims)

        for response_claim, generated_claim in zip(claim_data, reversed(generated_claims)):
            assert_claim_pfml_crm_response_equal_to_claim_query(response_claim, generated_claim)

    def test_get_claims_paginated_as_leave_admin(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        for _ in range(30):
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)

        other_employer = EmployerFactory.create()
        other_employee = EmployeeFactory.create()
        for _ in range(5):
            ClaimFactory.create(
                employer=other_employer,
                employee=other_employee,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        test_db_session.commit()
        scenarios = [
            {
                "tag": "Request without paging parameters uses default values",
                "request": {},
                "paging": {
                    "page_size": 25,
                    "page_offset": 1,
                    "total_pages": 2,
                    "total_records": 30,
                    "order_direction": "descending",
                    "order_by": "created_at",
                },
                "real_page_size": 25,
                "status_code": 200,
            },
            {
                "tag": "Use page_size value specified in query parameter",
                "request": {"page_size": 10},
                "paging": {
                    "page_size": 10,
                    "page_offset": 1,
                    "total_pages": 3,
                    "total_records": 30,
                    "order_direction": "descending",
                    "order_by": "created_at",
                },
                "real_page_size": 10,
                "status_code": 200,
            },
            {
                "tag": "page_size must be greater than 0",
                "request": {"page_size": 0},
                "paging": {},
                "status_code": 400,
            },
            {
                "tag": "page_size value larger than total number of records succeeds",
                "request": {"page_size": 100},
                "paging": {
                    "page_size": 100,
                    "page_offset": 1,
                    "total_pages": 1,
                    "total_records": 30,
                    "order_direction": "descending",
                    "order_by": "created_at",
                },
                "real_page_size": 30,
                "status_code": 200,
            },
            {
                "tag": "Unrecognized order_by parameter defaults to created_at",
                "request": {"order_by": "dogecoin"},
                "paging": {},
                "status_code": 400,
            },
            {
                "tag": "Unrecognized order_direction parameter returns 400",
                "request": {"order_direction": "stonks"},
                "paging": {},
                "status_code": 400,
            },
        ]

        for scenario in scenarios:
            tag = scenario["tag"]
            print(f"Running test for pagination scenario: {tag}")

            query_string = "&".join(
                [f"{key}={value}" for key, value in scenario["request"].items()]
            )

            # GET /claims deprecated
            response = client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

            assert (
                response.status_code == scenario["status_code"]
            ), f"tag:{tag}\nUnexpected response status code {response.status_code}"

            if scenario["status_code"] != 200:
                # Do not validate response structure for scenarios where an error response is expected
                continue

            response_body = response.get_json()

            actual_response_page_size = len(response_body["data"])
            expected_page_size = scenario["real_page_size"]
            assert actual_response_page_size == expected_page_size, (
                f"tag:{tag}\nUnexpected data response size {actual_response_page_size},"
                + f"should've been {expected_page_size}"
            )

            actual_page_metadata = response_body["meta"]["paging"]
            expected_page_metadata = scenario["paging"]

            for key, expected_value in expected_page_metadata.items():
                actual_value = actual_page_metadata[key]
                if actual_page_metadata[key] != expected_value:
                    raise AssertionError(
                        f"tag: {tag}\n{key} value was '{actual_value}', not expected {expected_value}"
                    )

            # POST /claims/search
            paging = {
                k.partition("_")[2]: v
                for k, v in scenario["paging"].items()
                if k.startswith("page")
            }
            order = {
                k.partition("_")[2]: v
                for k, v in scenario["paging"].items()
                if k.startswith("order")
            }

            post_body = {"terms": {}, "paging": paging, "order": order}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )

            assert (
                response.status_code == scenario["status_code"]
            ), f"tag:{tag}\nUnexpected response status code {response.status_code}"

            if scenario["status_code"] != 200:
                # Do not validate response structure for scenarios where an error response is expected
                continue

            response_body = response.get_json()

            actual_response_page_size = len(response_body["data"])
            expected_page_size = scenario["real_page_size"]
            assert actual_response_page_size == expected_page_size, (
                f"tag:{tag}\nUnexpected data response size {actual_response_page_size},"
                + f"should've been {expected_page_size}"
            )

            actual_page_metadata = response_body["meta"]["paging"]
            expected_page_metadata = scenario["paging"]

            for key, expected_value in expected_page_metadata.items():
                actual_value = actual_page_metadata[key]
                if actual_page_metadata[key] != expected_value:
                    raise AssertionError(
                        f"tag: {tag}\n{key} value was '{actual_value}', not expected {expected_value}"
                    )

    def test_get_claims_with_paid_payments(
        self, client, test_db_session, employer_user, employer_auth_token, test_verification
    ):
        payment_factory = DelegatedPaymentFactory(test_db_session, fineos_absence_status_id=1)
        claim = payment_factory.get_or_create_claim()
        payment_factory.get_or_create_payment_with_state(
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )

        claim2 = ClaimFactory.create(
            employer=payment_factory.employer,
            employee=payment_factory.employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=payment_factory.employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 2

        # Sort order places most recent claims first
        assert_claim_response_equal_to_claim_query(claim_data[0], claim2, has_paid_payments=False)
        assert_claim_response_equal_to_claim_query(claim_data[1], claim, has_paid_payments=True)

        # POST /claims/search
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json={"terms": {}},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 2

        # Sort order places most recent claims first
        assert_claim_response_equal_to_claim_query(claim_data[0], claim2, has_paid_payments=False)
        assert_claim_response_equal_to_claim_query(claim_data[1], claim, has_paid_payments=True)

    # Inner class for testing Claims With Status Filtering
    class TestClaimsOrder:
        @pytest.fixture()
        def load_test_db_with_managed_requirements(
            self, employer_user, test_verification, test_db_session
        ):
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()

            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)

            other_employer = EmployerFactory.create()
            other_employee = EmployeeFactory.create()

            other_link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=other_employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(other_link)
            claim_one = ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )
            claim_two = ClaimFactory.create(
                employer=other_employer, employee=other_employee, fineos_absence_status_id=2
            )
            claim_three = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            claim_four = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            ManagedRequirementFactory.create(
                claim=claim_three,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date="2022-01-01",
            )
            ManagedRequirementFactory.create(
                claim=claim_three,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date="2022-02-02",
            )
            ManagedRequirementFactory.create(
                claim=claim_four,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date="2021-01-01",
            )
            ManagedRequirementFactory.create(
                claim=claim_one,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=datetime_util.utcnow() + timedelta(days=15),
            )
            ManagedRequirementFactory.create(
                claim=claim_two,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=datetime_util.utcnow() + timedelta(days=30),
            )
            AbsencePeriodFactory.create(
                claim=claim_one,
                absence_period_start_date=date.today() + timedelta(days=5),
                absence_period_end_date=date.today() + timedelta(days=20),
                leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
            )
            AbsencePeriodFactory.create(
                claim=claim_two,
                absence_period_start_date=date.today() + timedelta(days=5),
                absence_period_end_date=date.today() + timedelta(days=20),
                leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
            )
            AbsencePeriodFactory.create(
                claim=claim_three,
                absence_period_start_date=date.today() + timedelta(days=5),
                absence_period_end_date=date.today() + timedelta(days=20),
                leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
            )
            AbsencePeriodFactory.create(
                claim=claim_four,
                absence_period_start_date=date.today() + timedelta(days=5),
                absence_period_end_date=date.today() + timedelta(days=20),
                leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
            )
            test_db_session.commit()

        @pytest.fixture()
        def load_test_db(self, employer_user, test_verification, test_db_session):
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()

            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)

            other_employer = EmployerFactory.create()
            other_employee = EmployeeFactory.create()

            other_link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=other_employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(other_link)

            for _ in range(5):
                ClaimFactory.create(
                    employer=employer,
                    employee=employee,
                    fineos_absence_status_id=1,
                    claim_type_id=1,
                )
                ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    fineos_absence_status_id=2,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    fineos_absence_status_id=7,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                claim = Claim(employer=employer, fineos_absence_status_id=6, claim_type_id=1)
                test_db_session.add(claim)
            self.claims_count = 20
            test_db_session.commit()

        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        def _assert_data_order(self, data, desc=True):
            if desc:
                for i in range(0, len(data) - 1):
                    assert data[i] >= data[i + 1]
            else:
                for i in range(0, len(data) - 1):
                    assert data[i] <= data[i + 1]

        def test_get_claims_with_order_default(self, client, employer_auth_token, load_test_db):
            request = {}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = [d["created_at"] for d in response_body.get("data", [])]
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=True)

        def test_get_claims_with_order_default_asc(self, client, employer_auth_token, load_test_db):
            request = {"order_direction": "ascending"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = [d["created_at"] for d in response_body.get("data", [])]
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=False)

        def test_get_claims_with_order_unsupported_key(
            self, client, employer_auth_token, load_test_db
        ):
            request = {"order_by": "unsupported"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 400

        def _extract_employee_name(self, response_body):
            data = []
            for d in response_body.get("data", []):
                employee = d["employee"] or {}
                name = (
                    employee.get("last_name", " ")
                    + employee.get("first_name", " ")
                    + employee.get("middle_name", " ")
                )
                data.append(name)
            return data

        def test_get_claims_with_order_employee_asc(
            self, client, employer_auth_token, load_test_db
        ):
            request = {"order_direction": "ascending", "order_by": "employee"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = self._extract_employee_name(response_body)
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=False)

        def test_get_claims_with_order_by_follow_up_date_desc(
            self, client, employer_auth_token, load_test_db_with_managed_requirements
        ):
            request = {"order_direction": "descending", "order_by": "latest_follow_up_date"}
            response = self._perform_api_call(request, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()
            claim_one, claim_two, claim_three, claim_four, claim_five = response_body["data"]

            # The first claims are Open, ordered chronologically (e.g. first 2022-02-18 then 2022-03-05)
            assert (
                claim_one["managed_requirements"][0]["follow_up_date"]
                < claim_two["managed_requirements"][0]["follow_up_date"]
            )
            assert claim_one["managed_requirements"][0]["status"] == "Open"
            assert claim_two["managed_requirements"][0]["status"] == "Open"
            # Next are any not-Open claims (or open claims with expired follow up date), ordered reverse chronologically (e.g. first 2022-02-02 then 2021-01-01)
            assert "2022-02-02" in [
                req["follow_up_date"] for req in claim_three["managed_requirements"]
            ]
            assert "2022-01-01" in [
                req["follow_up_date"] for req in claim_three["managed_requirements"]
            ]
            assert claim_three["managed_requirements"][0]["status"] == "Complete"
            assert (
                claim_four["managed_requirements"][0]["status"] == "Open"
            )  # Open but expired follow-up date
            assert claim_four["managed_requirements"][0]["follow_up_date"] == "2021-01-01"
            # Finally, claims without any associated managed requirements are last
            assert claim_five["managed_requirements"] == []

        def test_get_claims_with_order_by_follow_up_date_asc(
            self,
            client,
            employer_auth_token,
            load_test_db_with_managed_requirements,
            test_db_session,
        ):
            request = {"order_direction": "ascending", "order_by": "latest_follow_up_date"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            claim_one, claim_two, claim_three, claim_four, claim_five = response_body["data"]

            # First are not-Open claims (or open claims with expired follow up date), ordered chronologically (e.g. first 2021-01-01 then 2022-01-01)
            assert (
                claim_one["managed_requirements"][0]["status"] == "Open"
            )  # Open but expired follow-up date
            assert claim_two["managed_requirements"][0]["status"] == "Complete"
            assert claim_one["managed_requirements"][0]["follow_up_date"] == "2021-01-01"
            assert (
                claim_one["managed_requirements"][0]["follow_up_date"]
                < claim_two["managed_requirements"][0]["follow_up_date"]
            )

            # Next are open claims, ordered chronologically (e.g. first "2022-01-01" then "2022-03-03")
            assert (
                claim_three["managed_requirements"][0]["follow_up_date"]
                < claim_four["managed_requirements"][0]["follow_up_date"]
            )
            assert claim_three["managed_requirements"][0]["status"] == "Open"
            assert claim_four["managed_requirements"][0]["status"] == "Open"
            # Finally, claims without any associated managed requirements are last
            assert claim_five["managed_requirements"] == []

        def test_get_claims_with_order_by_follow_up_date_asc_and_is_reviewable_yes(
            self,
            client,
            employee,
            employer_auth_token,
            employer_user,
            load_test_db_with_managed_requirements,
            test_verification,
            test_db_session,
        ):
            # Create one more claim, this one with multiple managed requirements, one of which is open.
            # Claims with multiple managed requirements can meet both soonest_open_requirement_date and
            # latest_follow_up_date sort orders, which was throwing off the sort results.
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            claim = ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )
            AbsencePeriodFactory.create(
                claim=claim,
                absence_period_start_date=date.today() + timedelta(days=5),
                absence_period_end_date=date.today() + timedelta(days=20),
                leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
            )
            # follow_up_date of today + 20 should put this between the two other is_reviewable="yes" claims
            ManagedRequirementFactory.create(
                claim=claim,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=datetime_util.utcnow() + timedelta(days=20),
            )
            ManagedRequirementFactory.create(
                claim=claim,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date="2022-02-02",
            )
            test_db_session.commit()

            request = {
                "order_direction": "ascending",
                "order_by": "latest_follow_up_date",
                "is_reviewable": "yes",
            }
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            claim_one, claim_two, claim_three = response_body["data"]

            # They should all be ordered chronologically
            assert (
                claim_one["managed_requirements"][0]["follow_up_date"]
                < claim_two["managed_requirements"][0]["follow_up_date"]
            )
            assert (
                claim_two["managed_requirements"][0]["follow_up_date"]
                < claim_three["managed_requirements"][0]["follow_up_date"]
            )
            # And the claim made above should be in the middle
            assert claim_two["fineos_absence_id"] == claim.fineos_absence_id

        def test_get_claims_with_order_employee_desc(
            self, client, employer_auth_token, load_test_db
        ):
            request = {"order_direction": "descending", "order_by": "employee"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = self._extract_employee_name(response_body)
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=True)

    def test_get_claims_for_employer_id(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)

        other_employer = EmployerFactory.create()
        other_link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=other_employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(other_employer)
        test_db_session.add(other_link)

        for _ in range(5):
            ClaimFactory.create(
                employer=other_employer,
                employee=employee,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        test_db_session.commit()

        # GET /claims deprecated
        response = client.get(
            f"/v1/claims?employer_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(employer.employer_fein)

        # POST /claims/search
        terms = {"employer_id": [employer.employer_id]}
        post_body = {"terms": terms}
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )

        assert response.status_code == 200

    def test_user_claim_access_via_employer_id(
        self, client, user, auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employerB = EmployerFactory.create()
        employerC = EmployerFactory.create()

        employee = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )

        new_claim = ClaimFactory.create(
            employer=employerB, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )
        ApplicationFactory.create(user=user, claim=new_claim)

        new_claim2 = ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )
        ApplicationFactory.create(user=user, claim=new_claim2)

        ClaimFactory.create(
            employer=employerC, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )

        test_db_session.commit()

        # GET /claims to make sure regular user cannot access claims they shouldn't
        response1 = client.get(
            f"/v1/claims?employer_id={employerC.employer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 0

        response2 = client.get(
            f"/v1/claims?employer_id={employerB.employer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 1

        response2 = client.get(
            f"/v1/claims?employer_id={employer.employer_id},{employerB.employer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 2

    def test_get_claims_for_many_employer_ids(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)

        other_employer = EmployerFactory.create()
        other_link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=other_employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(other_employer)
        test_db_session.add(other_link)

        for _ in range(5):
            ClaimFactory.create(
                employer=other_employer,
                employee=employee,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        test_db_session.commit()

        response = client.get(
            f"/v1/claims?employer_id={employer.employer_id},{other_employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_body = response.get_json()

        assert len(response_body["data"]) == 10
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(
                employer.employer_fein
            ) or claim["employer"]["employer_fein"] == format_fein(other_employer.employer_fein)

        # POST /claims/search
        terms = {"employer_id": [employer.employer_id, other_employer.employer_id]}
        post_body = {"terms": terms}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 10
        for claim in response_body1["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(
                employer.employer_fein
            ) or claim["employer"]["employer_fein"] == format_fein(other_employer.employer_fein)

    def test_get_claims_for_employee_id_as_employer(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )
        for _ in range(5):
            ClaimFactory.create(employer=employer, fineos_absence_status_id=1, claim_type_id=1)

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        # Verify we can find the employee in question
        response1 = client.get(
            f"/v1/claims?employee_id={employee.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # POST /claims/search
        terms = {"employee_id": [employee.employee_id]}
        post_body = {"terms": terms}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # Verify we're filtering OUT results if the employee isn't found
        response2 = client.get(
            f"/v1/claims?employee_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 0

        # POST /claims/search
        terms = {"employee_id": [employer.employer_id]}
        post_body = {"terms": terms}
        response2 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 0

    def test_get_claims_valid_employee_id_invalid_employer_id(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )
        for _ in range(5):
            ClaimFactory.create(employer=employer, fineos_absence_status_id=1, claim_type_id=1)

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        # Verify the wrong employer_id fails to find anything
        response1 = client.get(
            f"/v1/claims?employer_id={employee.employee_id}&employee_id={employee.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 0

        # POST /claims/search
        terms = {"employer_id": [employee.employee_id], "employee_id": [employer.employer_id]}
        post_body = {"terms": terms}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 0

        # Verify the right employer_id and employee_id work together
        response2 = client.get(
            f"/v1/claims?employer_id={employer.employer_id}&employee_id={employee.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 1
        assert response_body2["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # POST /claims/search
        terms = {"employer_id": [employer.employer_id], "employee_id": [employee.employee_id]}
        post_body = {"terms": terms}
        response2 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 1
        assert response_body2["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

    def test_get_claims_for_multiple_employee_ids_as_employer(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()
        employee2 = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, employee=employee2, fineos_absence_status_id=1, claim_type_id=1
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        # Verify we can find a single valid employee_id when sending one
        response1 = client.get(
            f"/v1/claims?employee_id={employee.employee_id},{employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # POST /claims/search
        terms = {"employee_id": [employee.employee_id, employer.employer_id]}
        post_body = {"terms": terms}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # Verify we can find both valid employee_ids when sending multiple
        response2 = client.get(
            f"/v1/claims?employee_id={employee.employee_id},{employee2.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 6
        eids_to_find = [str(employee.employee_id), str(employee2.employee_id)]
        for found_employee in response_body2["data"]:
            assert found_employee["employee"]["employee_id"] in eids_to_find

        # POST /claims/search
        terms = {"employee_id": [employee.employee_id, employee2.employee_id]}
        post_body = {"terms": terms}
        response2 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 6
        eids_to_find = [str(employee.employee_id), str(employee2.employee_id)]
        for found_employee in response_body2["data"]:
            assert found_employee["employee"]["employee_id"] in eids_to_find

        # Verify malformed e.g. trailing comma is rejected
        response3 = client.get(
            f"/v1/claims?employee_id={employee.employee_id},",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response3.status_code == 400

        # POST /claims/search
        terms = {"employee_id": f"{employee.employee_id},"}
        post_body = {"terms": terms}
        response3 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response3.status_code == 400

    def test_get_claims_for_employee_id_as_claimant(
        self, client, auth_token, user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employeeA = EmployeeFactory.create()
        generated_claims = []

        for _ in range(3):
            new_claim = ClaimFactory.create(
                employer=employer, employee=employeeA, fineos_absence_status_id=1, claim_type_id=1
            )
            generated_claims.append(new_claim)
            ApplicationFactory.create(user=user, claim=new_claim)

        # Create a claim that is not expected to be returned
        employeeB = EmployeeFactory.create()
        ClaimFactory.create(
            employer=employer, employee=employeeB, fineos_absence_status_id=1, claim_type_id=1
        )

        response1 = client.get(
            f"/v1/claims?employee_id={employeeB.employee_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response1.status_code == 200
        response_body1 = response1.get_json()
        claim_data1 = response_body1.get("data")
        assert len(claim_data1) == 0

        # POST /claims/search
        terms = {"employee_id": [employeeB.employee_id]}
        post_body = {"terms": terms}
        response1 = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {auth_token}"}, json=post_body
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        claim_data1 = response_body1.get("data")
        assert len(claim_data1) == 0

        response2 = client.get(
            f"/v1/claims?employee_id={employeeA.employee_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        claim_data2 = response_body2.get("data")
        assert len(claim_data2) == 3
        for found_claim in response_body2["data"]:
            assert found_claim["employee"]["employee_id"] == str(employeeA.employee_id)

        # POST /claims/search
        terms = {"employee_id": [employeeA.employee_id]}
        post_body = {"terms": terms}
        response2 = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {auth_token}"}, json=post_body
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        claim_data2 = response_body2.get("data")
        assert len(claim_data2) == 3
        for found_claim in response_body2["data"]:
            assert found_claim["employee"]["employee_id"] == str(employeeA.employee_id)

    def test_get_claims_as_claimant(self, client, auth_token, user):
        employer = EmployerFactory.create()
        employeeA = EmployeeFactory.create()
        generated_claims = []

        for _ in range(3):
            new_claim = ClaimFactory.create(
                employer=employer, employee=employeeA, fineos_absence_status_id=1, claim_type_id=1
            )
            generated_claims.append(new_claim)
            ApplicationFactory.create(user=user, claim=new_claim)

        # Create a claim that is not expected to be returned
        employeeB = EmployeeFactory.create()
        ClaimFactory.create(
            employer=employer, employee=employeeB, fineos_absence_status_id=1, claim_type_id=1
        )

        # GET /claims deprecated
        response = client.get("/v1/claims", headers={"Authorization": f"Bearer {auth_token}"})

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 3
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

        # POST /claims/search
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"terms": {}},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 3
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

    def test_get_claims_no_employee(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()

        for _ in range(5):
            ClaimFactory.create(employer=employer, fineos_absence_status_id=1, claim_type_id=1)

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        response = client.get(
            f"/v1/claims?employer_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5

        # POST /claims/search
        terms = {"employer_id": [employer.employer_id]}
        post_body = {"terms": terms}
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5

    def test_get_claims_no_employer(self, client, auth_token, user):
        employee = EmployeeFactory.create()

        for _ in range(5):
            application = ApplicationFactory.create(user=user)
            ClaimFactory.create(
                employee=employee,
                application=application,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        response = client.get("/v1/claims", headers={"Authorization": f"Bearer {auth_token}"})

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5

    # Inner class for testing Claims With Status Filtering
    class TestClaimsWithStatus:
        NUM_CLAIM_PER_STATUS = 2

        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture
        def review_by_claim(self, employer, employee):
            # Approved claim with open managed requirements i.e review by
            claim_review_by = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            AbsencePeriodFactory.create(
                claim=claim_review_by,
                absence_period_start_date=date.today() + timedelta(days=5),
                absence_period_end_date=date.today() + timedelta(days=20),
                leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
            )
            for _ in range(2):
                ManagedRequirementFactory.create(
                    claim=claim_review_by,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                    follow_up_date=date.today() + timedelta(days=10),
                )
            return claim_review_by

        @pytest.fixture
        def review_by_claim_missing_absence_period(self, employer, employee):
            # Approved claim with open managed requirements i.e review by
            claim_review_by = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            for _ in range(2):
                ManagedRequirementFactory.create(
                    claim=claim_review_by,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                    follow_up_date=date.today() + timedelta(days=10),
                )
            return claim_review_by

        @pytest.fixture
        def no_action_claim(self, employer, employee):
            # Approved claim with completed managed requirements
            claim_no_action = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            ManagedRequirementFactory.create(
                claim=claim_no_action,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date=date.today() + timedelta(days=10),
            )
            return claim_no_action

        @pytest.fixture
        def expired_requirements_claim(self, employer, employee):
            # Approved claim with expired managed requirements
            claim_expired = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            ManagedRequirementFactory.create(
                claim=claim_expired,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=date.today() - timedelta(days=2),
            )
            return claim_expired

        @pytest.fixture
        def no_open_requirement_claims(self, employer, employee):
            claims = []
            statuses = [
                AbsenceStatus.APPROVED,
                AbsenceStatus.CLOSED,
                AbsenceStatus.DECLINED,
                AbsenceStatus.COMPLETED,
            ]
            for status in statuses:
                for _ in range(self.NUM_CLAIM_PER_STATUS):
                    claim = ClaimFactory.create(
                        employer=employer,
                        employee=employee,
                        fineos_absence_status_id=status.absence_status_id,
                        claim_type_id=1,
                    )
                    claims.append(claim)
            return claims

        @pytest.fixture
        def pending_claims(self, employer, employee):
            # does not include review by claims
            claims = []
            statuses = [
                AbsenceStatus.INTAKE_IN_PROGRESS,
                AbsenceStatus.IN_REVIEW,
                AbsenceStatus.ADJUDICATION,
            ]
            for status in statuses:
                for _ in range(self.NUM_CLAIM_PER_STATUS):
                    claim = ClaimFactory.create(
                        employer=employer,
                        employee=employee,
                        fineos_absence_status_id=status.absence_status_id,
                        # fineos_absence_status=status,
                        claim_type_id=1,
                    )
                    claims.append(claim)
            for _ in range(self.NUM_CLAIM_PER_STATUS):  # for fineos_absence_status = NULL
                claim = ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)
                claims.append(claim)
            return claims

        @pytest.fixture(autouse=True)
        def load_test_db(
            self,
            employer,
            employee,
            employer_user,
            test_verification,
            test_db_session,
            no_open_requirement_claims,
            pending_claims,
            review_by_claim,
            no_action_claim,
            expired_requirements_claim,
            review_by_claim_missing_absence_period,
        ):
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        def _perform_api_call(self, url, client, employer_auth_token):
            return client.get(url, headers={"Authorization": f"Bearer {employer_auth_token}"})

        def _perform_assertions(self, response, status_code, expected_claims):
            expected_claims_fineos_absence_id = [
                claim.fineos_absence_id for claim in expected_claims
            ]
            assert response.status_code == status_code
            response_body = response.get_json()
            claim_data = response_body.get("data", [])
            for claim in response_body.get("data", []):
                fineos_absence_id = claim.get("fineos_absence_id", None)
                assert fineos_absence_id in expected_claims_fineos_absence_id
            assert len(claim_data) == len(expected_claims)

        def filter_claims_by_status(self, claims, valid_statuses):
            valid_statuses_id = [status.absence_status_id for status in valid_statuses]
            return [
                claim for claim in claims if claim.fineos_absence_status_id in valid_statuses_id
            ]

        def test_get_claims_with_status_filter_is_reviewable_yes(
            self, client, employer_auth_token, review_by_claim
        ):
            resp = self._perform_api_call(
                "/v1/claims?is_reviewable=yes", client, employer_auth_token
            )
            self._perform_assertions(resp, status_code=200, expected_claims=[review_by_claim])

            # POST /claims/search
            terms = {"is_reviewable": "yes"}
            post_body = {"terms": terms}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(response, status_code=200, expected_claims=[review_by_claim])

        def test_get_claims_with_status_filter_is_reviewable_no(
            self,
            client,
            employer_auth_token,
            no_open_requirement_claims,
            pending_claims,
            expired_requirements_claim,
            no_action_claim,
            review_by_claim_missing_absence_period,
        ):
            resp = self._perform_api_call(
                "/v1/claims?is_reviewable=no", client, employer_auth_token
            )
            self._perform_assertions(
                resp,
                status_code=200,
                expected_claims=[
                    *no_open_requirement_claims,
                    *pending_claims,
                    expired_requirements_claim,
                    no_action_claim,
                    review_by_claim_missing_absence_period,
                ],
            )

            # POST /claims/search
            terms = {"is_reviewable": "no"}
            post_body = {"terms": terms}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(
                response,
                status_code=200,
                expected_claims=[
                    *no_open_requirement_claims,
                    *pending_claims,
                    expired_requirements_claim,
                    no_action_claim,
                    review_by_claim_missing_absence_period,
                ],
            )

    # Inner class for testing Claims with Absence Periods
    class TestClaimsWithAbsencePeriods:
        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture()
        def claim(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        @pytest.fixture()
        def claim_no_absence_period(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        ## Note testing w/ None absence_reason_qualifier_two to test field nullability
        @pytest.fixture()
        def absence_periods(self, claim):
            start = date.today() + timedelta(days=5)
            periods = []
            for _ in range(5):
                end = start + timedelta(days=10)
                period = AbsencePeriodFactory.create(
                    claim=claim,
                    absence_period_start_date=start,
                    absence_period_end_date=end,
                    absence_reason_qualifier_two_id=None,
                )
                periods.append(period)
                start = start + timedelta(days=20)
            return periods

        @pytest.fixture()
        def claims(self, employer, employee):
            claims = []
            for _ in range(8):
                claim = ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)
                claims.append(claim)
            return claims

        @pytest.fixture()
        def varied_absence_periods(self, claims):
            start = date.today() + timedelta(days=5)
            periods = []
            num_request_decision_types = 8
            for i in range(num_request_decision_types):
                end = start + timedelta(days=10)
                period = AbsencePeriodFactory.create(
                    claim=claims[i],
                    absence_period_start_date=start,
                    absence_period_end_date=end,
                    leave_request_decision_id=i + 1,
                )
                periods.append(period)
                start = start + timedelta(days=20)
            return periods

        @pytest.fixture(autouse=True)
        def load_test_db(self, claim, test_db_session, employer_user, employer, test_verification):
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        def _find_absence_period_by_fineos_leave_request_id(
            self, fineos_leave_request_id: str, absence_periods: List[AbsencePeriod]
        ) -> Optional[AbsencePeriod]:
            absence_period = [
                period
                for period in absence_periods
                if period.fineos_leave_request_id == fineos_leave_request_id
            ]
            return absence_period[0] if len(absence_period) else None

        def _assert_claim_data(
            self, claim_data: Dict, claim: Claim, absence_periods: List[AbsencePeriod]
        ):
            assert claim_data["fineos_absence_id"] == claim.fineos_absence_id
            assert len(claim_data["absence_periods"]) == len(absence_periods)
            for absence_period_data in claim_data["absence_periods"]:
                absence_period = self._find_absence_period_by_fineos_leave_request_id(
                    absence_period_data["fineos_leave_request_id"], absence_periods
                )
                assert absence_period is not None
                assert (
                    absence_period.absence_period_start_date.isoformat()
                    == absence_period_data["absence_period_start_date"]
                )
                assert (
                    absence_period.absence_period_end_date.isoformat()
                    == absence_period_data["absence_period_end_date"]
                )

        def test_claim_with_absence_periods(
            self, client, employer_auth_token, claim, claim_no_absence_period, absence_periods
        ):
            resp = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 2
            claim_data_with_absence_period = [
                claim for claim in claim_data if claim["absence_periods"]
            ][0]
            claim_data_no_absence_period = [
                claim for claim in claim_data if not claim["absence_periods"]
            ][0]
            self._assert_claim_data(claim_data_with_absence_period, claim, absence_periods)
            self._assert_claim_data(claim_data_no_absence_period, claim_no_absence_period, [])

        @pytest.mark.parametrize(
            "request_decision, num_claims_returned, expected_req_decs_returned",
            [
                ["approved", 1, [LeaveRequestDecision.APPROVED.leave_request_decision_description]],
                ["denied", 1, [LeaveRequestDecision.DENIED.leave_request_decision_description]],
                [
                    "withdrawn",
                    1,
                    [LeaveRequestDecision.WITHDRAWN.leave_request_decision_description],
                ],
                [
                    "pending",
                    3,
                    [
                        LeaveRequestDecision.PENDING.leave_request_decision_description,
                        LeaveRequestDecision.IN_REVIEW.leave_request_decision_description,
                        LeaveRequestDecision.PROJECTED.leave_request_decision_description,
                    ],
                ],
                [
                    "cancelled",
                    2,
                    [
                        LeaveRequestDecision.CANCELLED.leave_request_decision_description,
                        LeaveRequestDecision.VOIDED.leave_request_decision_description,
                    ],
                ],
            ],
        )
        def test_claim_request_decision_filter(
            self,
            request_decision,
            num_claims_returned,
            expected_req_decs_returned,
            client,
            employer_auth_token,
            claims,
            varied_absence_periods,
        ):
            # Note that for this test, our test data puts in the db 1 claim per absence period request decision type
            resp = client.get(
                f"/v1/claims?request_decision={request_decision}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claims_returned = response_body.get("data")
            assert len(claims_returned) == num_claims_returned
            for claim in claims_returned:
                for absence_period in claim["absence_periods"]:
                    assert absence_period["request_decision"] in expected_req_decs_returned

        def test_claim_request_decision_filter_invalid_param(
            self, client, employer_auth_token, claims, varied_absence_periods
        ):
            resp = client.get(
                "/v1/claims?request_decision=foobar",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 400
            response_body = resp.get_json()
            assert "'foobar' is not one of" in response_body["detail"]

    # Inner class for testing Claims with Managed Requirements
    class TestClaimsWithManagedRequirements:
        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture(autouse=True)
        def link(self, test_db_session, employer_user, employer, test_verification):
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        @pytest.fixture()
        def claim(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        @pytest.fixture
        def claim_pending_no_action(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        @pytest.fixture
        def claim_expired_requirements(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        @pytest.fixture
        def third_claim(self, employer, employee):
            return ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.get_id("Adjudication"),
                claim_type_id=1,
            )

        @pytest.fixture
        def completed_claim(self, employer, employee):
            return ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.get_id("Completed"),
                claim_type_id=1,
            )

        def _add_managed_requirements_to_claim(
            self, claim, status: LkManagedRequirementStatus, count=2
        ):
            return [
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=status.managed_requirement_status_id,
                )
                for _ in range(0, count)
            ]

        @pytest.fixture
        def claims_with_managed_requirements(
            self,
            claim,
            claim_pending_no_action,
            claim_expired_requirements,
            third_claim,
            completed_claim,
        ):
            # claim has both open and completed requirements
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.OPEN)
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.COMPLETE)

            # claim_pending_no_action has completed requirements
            self._add_managed_requirements_to_claim(
                claim_pending_no_action, ManagedRequirementStatus.COMPLETE
            )

            # claim_expired_requirements
            ManagedRequirementFactory.create(
                claim=claim_expired_requirements,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=date.today() - timedelta(days=2),
            )
            # third_claim does not have managed requirements

            # completed claim does not have managed requirements and is Completed, should NOT be returned

        @pytest.fixture()
        def old_managed_requirements(self, claim):
            return [
                ManagedRequirementFactory.create(
                    claim=claim, follow_up_date=datetime_util.utcnow() - timedelta(days=3)
                )
                for _ in range(0, 2)
            ]

        def test_claim_managed_requirements(
            self, client, employer_auth_token, claim, old_managed_requirements
        ):
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.OPEN, 2)
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.COMPLETE)
            resp = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1
            claim = response_body["data"][0]
            assert len(claim.get("managed_requirements", [])) == 6

            resp = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json={"terms": {}},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1
            claim = response_body["data"][0]
            assert len(claim.get("managed_requirements", [])) == 6

    # Inner class for testing Claims Search
    class TestClaimsSearch:
        @pytest.fixture()
        def X_NAME(self):
            return "xxxxx"

        @pytest.fixture()
        def XAbsenceCase(self):
            return "NTN-99-ABS-01"

        @pytest.fixture()
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture()
        def other_employer_user(self):
            return UserFactory.create(roles=[Role.EMPLOYER])

        @pytest.fixture
        def other_employer_claims(self, other_employer_user):
            return {
                "exp": datetime.now() + timedelta(days=1),
                "sub": str(other_employer_user.sub_id),
            }

        @pytest.fixture()
        def other_employer_auth_token(self, other_employer_claims, auth_private_key):
            return jwt.encode(other_employer_claims, auth_private_key, algorithm=ALGORITHMS.RS256)

        @pytest.fixture()
        def other_employer(self):
            return EmployerFactory.create()

        @pytest.fixture()
        def first_employee(self, X_NAME):
            return EmployeeFactory.create(
                first_name="FirstName", middle_name=X_NAME, last_name=X_NAME
            )

        @pytest.fixture()
        def middle_employee(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name="InMiddleName", last_name=X_NAME
            )

        @pytest.fixture()
        def last_employee(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name=X_NAME, last_name="AtTheLast"
            )

        @pytest.fixture()
        def id_employee(self, X_NAME):
            return EmployeeFactory.create(first_name=X_NAME, middle_name=X_NAME, last_name=X_NAME)

        @pytest.fixture()
        def john(self, X_NAME):
            return EmployeeFactory.create(first_name="John", middle_name=X_NAME, last_name=X_NAME)

        @pytest.fixture()
        def johnny(self, X_NAME):
            return EmployeeFactory.create(first_name=X_NAME, middle_name="Johnny", last_name=X_NAME)

        @pytest.fixture()
        def middlejohn(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name=X_NAME, last_name="Middlejohn"
            )

        @pytest.fixture()
        def johnson(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name=X_NAME, last_name="Johnson"
            )

        @pytest.fixture()
        def employee_different_fineos_dor_first_name(self, X_NAME):
            return EmployeeFactory.create(
                first_name="Jane",
                middle_name=X_NAME,
                last_name=X_NAME,
                fineos_employee_first_name="Alice",
            )

        @pytest.fixture()
        def employee_different_fineos_dor_middle_name(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME,
                middle_name="Marie",
                last_name=X_NAME,
                fineos_employee_middle_name="Ann",
            )

        @pytest.fixture()
        def employee_different_fineos_dor_last_name(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME,
                middle_name=X_NAME,
                last_name="Doe",
                fineos_employee_last_name="Jones",
            )

        @pytest.fixture(autouse=True)
        def load_test_db(
            self,
            employer_user,
            other_employer_user,
            test_verification,
            test_db_session,
            employer,
            other_employer,
            first_employee,
            middle_employee,
            last_employee,
            id_employee,
            john,
            johnny,
            middlejohn,
            johnson,
            XAbsenceCase,
            employee_different_fineos_dor_first_name,
            employee_different_fineos_dor_middle_name,
            employee_different_fineos_dor_last_name,
        ):
            ClaimFactory.create(employer=employer, employee=first_employee, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=middle_employee, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=last_employee, claim_type_id=1)
            ClaimFactory.create(
                employer=employer,
                employee=id_employee,
                claim_type_id=1,
                fineos_absence_id=XAbsenceCase,
            )
            ClaimFactory.create(employer=employer, employee=john, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=johnny, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=middlejohn, claim_type_id=1)

            ClaimFactory.create(
                employer=employer,
                employee=employee_different_fineos_dor_first_name,
                claim_type_id=1,
            )
            ClaimFactory.create(
                employer=employer,
                employee=employee_different_fineos_dor_middle_name,
                claim_type_id=1,
            )
            ClaimFactory.create(
                employer=employer, employee=employee_different_fineos_dor_last_name, claim_type_id=1
            )

            ClaimFactory.create(employer=other_employer, employee=johnson, claim_type_id=1)

            leave_admin = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            other_leave_admin = UserLeaveAdministrator(
                user_id=other_employer_user.user_id,
                employer_id=other_employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(leave_admin)
            test_db_session.add(other_leave_admin)
            test_db_session.commit()

        def perform_search(self, search_string, client, token):
            return client.get(
                f"/v1/claims?search={search_string}", headers={"Authorization": f"Bearer {token}"}
            )

        def perform_search_with_headers(self, search_string, client, headers):
            return client.get(f"/v1/claims?search={search_string}", headers=headers)

        def test_get_claims_snow_user(self, client, snow_user_headers):
            response = self.perform_search_with_headers("firstn", client, snow_user_headers)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = response_body["data"][0]
            assert "has_paid_payments" not in claim

        def test_get_claims_search_absence_id_snow_user(
            self, XAbsenceCase, client, snow_user_headers
        ):
            response = self.perform_search_with_headers("NTN-99-ABS-01", client, snow_user_headers)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (c for c in response_body["data"] if c["fineos_absence_id"] == XAbsenceCase), None
            )
            assert claim is not None

        def test_get_claims_for_multiple_employee_ids_as_snow_user(
            self, client, snow_user_headers, employer_user, test_db_session
        ):
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()
            employee2 = EmployeeFactory.create()

            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )

            for _ in range(5):
                ClaimFactory.create(
                    employer=employer,
                    employee=employee2,
                    fineos_absence_status_id=1,
                    claim_type_id=1,
                )

            test_db_session.commit()

            # Verify we can find a single valid employee_id when sending one
            response1 = client.get(
                f"/v1/claims?employee_id={employee.employee_id},{employer.employer_id}",
                headers=snow_user_headers,
            )
            assert response1.status_code == 200
            response_body1 = response1.get_json()
            assert len(response_body1["data"]) == 1
            assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

            # Verify we can find both valid employee_ids when sending multiple
            response2 = client.get(
                f"/v1/claims?employee_id={employee.employee_id},{employee2.employee_id}",
                headers=snow_user_headers,
            )
            assert response2.status_code == 200
            response_body2 = response2.get_json()
            assert len(response_body2["data"]) == 6
            eids_to_find = [str(employee.employee_id), str(employee2.employee_id)]
            for found_employee in response_body2["data"]:
                assert found_employee["employee"]["employee_id"] in eids_to_find

        def test_get_claims_search_first_name(self, first_employee, client, employer_auth_token):
            response = self.perform_search("firstn", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["first_name"] == first_employee.first_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_middle_name(self, middle_employee, client, employer_auth_token):
            response = self.perform_search("inmidd", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["middle_name"] == middle_employee.middle_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_last_name(self, last_employee, client, employer_auth_token):
            response = self.perform_search("helast", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["last_name"] == last_employee.last_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_absence_id(self, XAbsenceCase, client, employer_auth_token):
            response = self.perform_search("NTN-99-ABS-01", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (c for c in response_body["data"] if c["fineos_absence_id"] == XAbsenceCase), None
            )
            assert claim is not None

        def test_get_claims_search_common_name_different_employers(
            self,
            client,
            john,
            johnny,
            middlejohn,
            johnson,
            employer_auth_token,
            other_employer_auth_token,
        ):
            response = self.perform_search("john", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            john_claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["first_name"] == john.first_name
                ),
                None,
            )
            assert john_claim is not None

            johnny_claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["middle_name"] == johnny.middle_name
                ),
                None,
            )
            assert johnny_claim is not None

            middlejohn_claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["last_name"] == middlejohn.last_name
                ),
                None,
            )
            assert middlejohn_claim is not None

            empty_response = self.perform_search("johnson", client, employer_auth_token)

            assert empty_response.status_code == 200
            empty_response_body = empty_response.get_json()
            assert len(empty_response_body["data"]) == 0

            other_response = self.perform_search("john", client, other_employer_auth_token)

            assert other_response.status_code == 200
            other_response_body = other_response.get_json()

            johnson_claim = next(
                (
                    c
                    for c in other_response_body["data"]
                    if c["employee"]["last_name"] == johnson.last_name
                ),
                None,
            )
            assert johnson_claim is not None

        def test_get_claims_search_first_name_fineos(
            self, employee_different_fineos_dor_first_name, client, employer_auth_token
        ):
            response = self.perform_search("lice", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["first_name"]
                    == employee_different_fineos_dor_first_name.fineos_employee_first_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_middle_name_fineos(
            self, employee_different_fineos_dor_middle_name, client, employer_auth_token
        ):
            response = self.perform_search("nn", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["middle_name"]
                    == employee_different_fineos_dor_middle_name.fineos_employee_middle_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_last_name_fineos(
            self, employee_different_fineos_dor_last_name, client, employer_auth_token
        ):
            response = self.perform_search("Jon", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["last_name"]
                    == employee_different_fineos_dor_last_name.fineos_employee_last_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_blank_string(self, client, employer_auth_token):
            response = self.perform_search("", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) >= 7

        def test_get_claims_search_not_used(self, client, employer_auth_token):
            response = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
            )
            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) >= 7

        def test_get_claims_search_no_employee(self, client, employer_auth_token, employer):
            claim = ClaimFactory.create(
                employer=employer, employee_id=None, employee=None, claim_type_id=1
            )
            response = self.perform_search(claim.fineos_absence_id, client, employer_auth_token)
            response_body = response.get_json()
            assert len(response_body["data"]) == 1
            assert response_body["data"][0]["fineos_absence_id"] == claim.fineos_absence_id
            assert response_body["data"][0]["employee"] is None

    class TestClaimsSearchFullName:
        @pytest.fixture()
        def X_NAME(self):
            return "xxxxx"

        @pytest.fixture()
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture()
        def full_name_employees(self, X_NAME):
            similar_employees = []
            full_name_employee = EmployeeFactory.create()

            similar_employees.append(full_name_employee)
            similar_employees.append(EmployeeFactory.create())

            # same first_name
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=full_name_employee.first_name, middle_name=X_NAME, last_name=X_NAME
                )
            )
            # same middle_name
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=X_NAME, middle_name=full_name_employee.middle_name, last_name=X_NAME
                )
            )
            # same last_name
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=X_NAME, middle_name=X_NAME, last_name=full_name_employee.last_name
                )
            )
            # same first_name and last_name should be returned in first_last and
            # last_first search, but unique if search terms are the FINEOS names
            # (in this dataset)
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=full_name_employee.first_name,
                    middle_name=X_NAME,
                    last_name=full_name_employee.last_name,
                    fineos_employee_first_name="123",
                    fineos_employee_last_name="456",
                )
            )

            return similar_employees

        @pytest.fixture()
        def full_name_employee(self, full_name_employees):
            return full_name_employees[0]

        @pytest.fixture(autouse=True)
        def load_test_db(
            self, employer_user, employer, test_verification, test_db_session, full_name_employees
        ):

            for employee_full_name in full_name_employees:
                ClaimFactory.create(employer=employer, employee=employee_full_name, claim_type_id=1)

            leave_admin = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(leave_admin)
            test_db_session.commit()

        def perform_search(self, search_string, client, token):
            return client.get(
                f"/v1/claims?search={search_string}", headers={"Authorization": f"Bearer {token}"}
            )

        def test_get_claims_search_full_name(self, client, employer_auth_token, full_name_employee):
            search_string = f"{full_name_employee.first_name} {full_name_employee.middle_name} {full_name_employee.last_name}"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_get_claims_search_full_name_with_extra_spaces(
            self, client, employer_auth_token, full_name_employee
        ):
            search_string = f" {full_name_employee.first_name}     {full_name_employee.middle_name}   {full_name_employee.last_name} "
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_get_claims_search_first_last(
            self, client, employer_auth_token, full_name_employee
        ):
            search_string = f"{full_name_employee.first_name} {full_name_employee.last_name}"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 2

        def test_get_claims_search_last_first(
            self, client, employer_auth_token, full_name_employee
        ):
            search_string = f"{full_name_employee.last_name} {full_name_employee.first_name}"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 2

        def test_get_claims_search_last_first_fineos(self, client, employer_auth_token):
            search_string = "123 456"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_get_claims_search_first_last_fineos(self, client, employer_auth_token):
            search_string = "456 123"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_claims_search_wildcard_input(
            self, client, employer_auth_token, full_name_employee
        ):
            response = self.perform_search("%", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 0

        def test_claims_search_wildcard_input_full_name(
            self, client, employer_auth_token, full_name_employee
        ):
            response = self.perform_search(
                f"{full_name_employee.last_name}%{full_name_employee.first_name}",
                client,
                employer_auth_token,
            )

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 0

    # Test validation of claims/search endpoint request body
    class TestClaimsAPIRequestBodyValidation:
        def _perform_api_call(self, request, client, employer_auth_token):
            return client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json={"terms": request},
            )

        def _assert_400_error_response(self, response):
            assert response.status_code == 400

        def test_claims_invalid_param_field(self, client, employer_auth_token):
            params = {"invalid": "invalid"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_invalid_order_by(self, client, employer_auth_token):
            params = {"order_by": "bad"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_unsupported_column_order_by(self, client, employer_auth_token):
            params = {"order_by": "updated_at"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

    # Test the combination of claims filters and search
    class TestClaimsMultipleParams:
        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create(first_name="Abbie", last_name="Gail")

        @pytest.fixture
        def other_employee(self):
            return EmployeeFactory.create(first_name="John", last_name="Deer")

        @pytest.fixture(autouse=True)
        def load_test_db(
            self, employer_user, test_verification, test_db_session, employee, other_employee
        ):
            employer = EmployerFactory.create()

            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)

            other_employer = EmployerFactory.create()

            other_link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=other_employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(other_link)

            # create 10 claims
            # employee claims are Open, other employee are not Open
            # varied absence periods for employee claims
            # always withdrawn for other employee claims
            for _ in range(5):
                employee_claim = ClaimFactory.create(
                    employer=employer, employee=employee, claim_type_id=1
                )
                other_employee_claim = ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                ManagedRequirementFactory.create(
                    claim=employee_claim,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                )
                ManagedRequirementFactory.create(
                    claim=other_employee_claim,
                    managed_requirement_status_id=ManagedRequirementStatus.SUPPRESSED.managed_requirement_status_id,
                )
                AbsencePeriodFactory.create(
                    claim=employee_claim,
                    absence_period_start_date=date.today() + timedelta(days=5),
                    absence_period_end_date=date.today() + timedelta(days=20),
                    leave_request_decision_id=LeaveRequestDecision.PENDING.leave_request_decision_id,
                )
                AbsencePeriodFactory.create(
                    claim=other_employee_claim,
                    absence_period_start_date=date.today() + timedelta(days=5),
                    absence_period_end_date=date.today() + timedelta(days=20),
                    leave_request_decision_id=LeaveRequestDecision.WITHDRAWN.leave_request_decision_id,
                )

            self.claims_count = 10
            test_db_session.commit()

        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        @pytest.mark.parametrize(
            "is_reviewable, request_decision, expected_output_len",
            [
                ["no", "approved", 0],
                ["no", "pending", 0],
                ["yes", "pending", 5],
            ],
        )
        def test_get_claims_is_reviewable_and_request_decision_filter(
            self, is_reviewable, request_decision, expected_output_len, client, employer_auth_token
        ):
            params = {"is_reviewable": is_reviewable, "request_decision": request_decision}
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == expected_output_len

        def test_get_claims_filter_by_request_decision_with_search(
            self, client, employer_auth_token, other_employee
        ):
            params = {
                "request_decision": "withdrawn",
                "search": other_employee.first_name,
                "order_by": "employee",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == 5

        def test_get_claims_filter_by_request_decision_with_search_no_result(
            self, client, employer_auth_token, other_employee
        ):
            params = {
                "request_decision": "approved",
                "search": other_employee.first_name,
                "order_by": "employee",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == 0

    # Test validation of claims endpoint query param validation
    class TestClaimsAPIInputValidation:
        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        def _assert_400_error_response(self, response):
            assert response.status_code == 400

        def test_claims_invalid_param_field(self, client, employer_auth_token):
            params = {"invalid": "invalid"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_invalid_order_by(self, client, employer_auth_token):
            params = {"order_by": "bad"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_unsupported_column_order_by(self, client, employer_auth_token):
            params = {"order_by": "updated_at"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)


class TestClaimsHelpers:
    @pytest.mark.parametrize(
        "request_decision_param, expected_output",
        [
            ["approved", set([LeaveRequestDecision.APPROVED.leave_request_decision_id])],
            ["denied", set([LeaveRequestDecision.DENIED.leave_request_decision_id])],
            ["withdrawn", set([LeaveRequestDecision.WITHDRAWN.leave_request_decision_id])],
            [
                "pending",
                set(
                    [
                        LeaveRequestDecision.PENDING.leave_request_decision_id,
                        LeaveRequestDecision.IN_REVIEW.leave_request_decision_id,
                        LeaveRequestDecision.PROJECTED.leave_request_decision_id,
                    ]
                ),
            ],
            [
                "cancelled",
                set(
                    [
                        LeaveRequestDecision.CANCELLED.leave_request_decision_id,
                        LeaveRequestDecision.VOIDED.leave_request_decision_id,
                    ]
                ),
            ],
            [None, set()],
        ],
    )
    def test_map_request_decision_param_to_db_columns(
        self, request_decision_param, expected_output
    ):
        assert map_request_decision_param_to_db_columns(request_decision_param) == expected_output

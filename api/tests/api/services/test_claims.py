import json
from datetime import date
from unittest import mock

import pytest

from massgov.pfml.api.services.claims import ClaimWithdrawnError, get_claim_detail
from massgov.pfml.db.models.factories import ManagedRequirementFactory
from massgov.pfml.db.queries.absence_periods import (
    convert_fineos_absence_period_to_claim_response_absence_period,
)
from massgov.pfml.fineos import exception
from massgov.pfml.fineos.models.customer_api.spec import AbsencePeriod as FineosAbsencePeriod
from massgov.pfml.util.pydantic.types import FEINFormattedStr


class TestGetClaimDetail:
    @pytest.fixture
    def fineos_absence_period(self):
        return FineosAbsencePeriod(
            id="PL-14449-0000002237",
            reason="Child Bonding",
            reasonQualifier1="Foster Care",
            reasonQualifier2="",
            startDate=date(2021, 1, 29),
            endDate=date(2021, 1, 30),
            absenceType="Continuous",
        )

    @pytest.fixture
    def managed_requirements(self, claim):
        requirements = []

        for _ in range(2):
            requirement = ManagedRequirementFactory.create(claim=claim, claim_id=claim.claim_id)
            requirements.append(requirement)

        return requirements

    # Run app.preprocess_request before calling method, to ensure we have access to a db_session
    # (set up by a @flask_app.before_request method in app.py)
    def get_claim_detail_with_app_context(self, claim, app):
        with app.app.test_request_context(f"/v1/claims/{claim.fineos_absence_id}"):
            app.app.preprocess_request()

            return get_claim_detail(claim, {})

    @mock.patch("massgov.pfml.api.services.claims.get_absence_periods")
    def test_withdrawn_claim_exception(self, mock_get_absence_periods, app, claim):
        error = {
            "error": "User does not have permission to access the resource or the instance data",
            "correlationId": "foo",
        }
        error_msg = json.dumps(error)

        fineos_response = exception.FINEOSForbidden("get_absence", 200, 403, error_msg)
        mock_get_absence_periods.side_effect = fineos_response

        with pytest.raises(Exception) as exc_info:
            self.get_claim_detail_with_app_context(claim, app)

        error = exc_info.value
        assert type(error) == ClaimWithdrawnError

    @mock.patch("massgov.pfml.api.services.claims.get_absence_periods")
    def test_no_absence_periods_exception(self, mock_get_absence_periods, app, claim):
        mock_get_absence_periods.return_value = []

        with pytest.raises(Exception) as exc_info:
            self.get_claim_detail_with_app_context(claim, app)

        error_msg = str(exc_info.value)
        assert error_msg == "No absence periods found for claim"

    @mock.patch("massgov.pfml.api.services.claims.get_absence_periods")
    def test_success(self, mock_get_absence_periods, app, claim, fineos_absence_period):
        mock_get_absence_periods.return_value = [fineos_absence_period]

        claim_detail = self.get_claim_detail_with_app_context(claim, app)

        assert claim_detail_matches_claim(claim_detail, claim)

        period = claim_detail.absence_periods[0]
        expected_period = convert_fineos_absence_period_to_claim_response_absence_period(
            fineos_absence_period, {}
        )

        assert period == expected_period

    @mock.patch("massgov.pfml.api.services.claims.get_absence_periods")
    def test_success_with_managed_requirements(
        self, mock_get_absence_periods, app, claim, fineos_absence_period, managed_requirements
    ):
        mock_get_absence_periods.return_value = [fineos_absence_period]

        claim_detail = self.get_claim_detail_with_app_context(claim, app)

        assert len(claim_detail.managed_requirements) == 2

        req = claim_detail.managed_requirements[0]
        expected_req = managed_requirements[0]

        assert managed_req_response_matches_managed_req(req, expected_req)


def claim_detail_matches_claim(claim_detail, claim):
    if claim_detail.fineos_absence_id != claim.fineos_absence_id:
        return False
    if claim_detail.fineos_notification_id != claim.fineos_notification_id:
        return False
    if claim_detail.employer.employer_dba != claim.employer.employer_dba:
        return False
    if claim_detail.employer.employer_fein != FEINFormattedStr.validate_type(
        claim.employer.employer_fein
    ):
        return False
    if claim_detail.employer.employer_id != claim.employer.employer_id:
        return False
    if claim_detail.employee.first_name != claim.employee.first_name:
        return False
    if claim_detail.employee.middle_name != claim.employee.middle_name:
        return False
    if claim_detail.employee.last_name != claim.employee.last_name:
        return False
    if claim_detail.employee.other_name != claim.employee.other_name:
        return False

    return True


def managed_req_response_matches_managed_req(req_response, req):
    if str(req_response.follow_up_date) != req.follow_up_date.strftime("%Y-%m-%d"):
        return False

    req_status = req.managed_requirement_status.managed_requirement_status_description
    if req_response.status != req_status:
        return False

    req_type = req.managed_requirement_type.managed_requirement_type_description
    if req_response.type != req_type:
        return False

    req_category = req.managed_requirement_category.managed_requirement_category_description
    if req_response.category != req_category:
        return False

    return True

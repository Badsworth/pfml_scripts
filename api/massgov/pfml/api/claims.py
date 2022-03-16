from typing import Optional, Set, Type, Union
from uuid import UUID

import connexion
import flask
from sqlalchemy_utils import escape_like
from werkzeug.exceptions import Forbidden, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.authorization.flask import READ, can
from massgov.pfml.api.exceptions import ClaimWithdrawn
from massgov.pfml.api.models.applications.common import OrganizationUnit
from massgov.pfml.api.models.claims.requests import ClaimSearchRequest, ClaimSearchTerms
from massgov.pfml.api.models.claims.responses import ClaimForPfmlCrmResponse, ClaimResponse
from massgov.pfml.api.services.claims import (
    ClaimWithdrawnError,
    get_claim_detail,
    get_claim_from_db,
)
from massgov.pfml.api.util.claims import user_has_access_to_claim
from massgov.pfml.api.util.logging.search_request import search_request_log_info
from massgov.pfml.api.util.paginate.paginator import PaginationAPIContext, make_pagination_params
from massgov.pfml.api.validation.exceptions import IssueType
from massgov.pfml.db.models.employees import (
    Claim,
    LeaveRequestDecision,
    Role,
    UserLeaveAdministrator,
)
from massgov.pfml.db.queries.get_claims_query import GetClaimsQuery
from massgov.pfml.util.logging.claims import log_get_claim_metrics
from massgov.pfml.util.logging.employers import get_employer_log_attributes
from massgov.pfml.util.users import has_role_in

logger = massgov.pfml.util.logging.get_logger(__name__)


class VerificationRequired(Forbidden):
    user_leave_admin: UserLeaveAdministrator
    status_code = Forbidden

    def __init__(self, user_leave_admin, description):
        self.user_leave_admin = user_leave_admin
        self.description = description

    def to_api_response(self):
        employer_id = self.user_leave_admin.employer_id
        has_verification_data = self.user_leave_admin.employer.has_verification_data
        return response_util.error_response(
            status_code=self.status_code,
            message=self.description,
            errors=[],
            data={"employer_id": employer_id, "has_verification_data": has_verification_data},
        ).to_api_response()


def get_current_user_leave_admin_record(fineos_absence_id: str) -> UserLeaveAdministrator:
    with app.db_session() as db_session:
        associated_employer_id: Optional[UUID] = None

        current_user = app.current_user()

        claim = get_claim_from_db(fineos_absence_id)

        if claim is not None:
            associated_employer_id = claim.employer_id

        if claim is None or associated_employer_id is None:
            logger.warning(
                "Claim does not exist for given absence ID",
                extra={"absence_case_id": fineos_absence_id},
            )
            raise Forbidden(description="Claim does not exist for given absence ID")

        user_leave_admin = (
            db_session.query(UserLeaveAdministrator)
            .filter(
                (UserLeaveAdministrator.user_id == current_user.user_id)
                & (UserLeaveAdministrator.employer_id == associated_employer_id)
            )
            .one_or_none()
        )

        log_attributes = {
            "absence_case_id": fineos_absence_id,
            "user_id": current_user.user_id,
            "associated_employer_id": associated_employer_id,
        }

        if user_leave_admin is None:
            logger.warning(
                "The leave admin is None",
                extra=log_attributes,
            )
            raise NotAuthorizedForAccess(
                description="User does not have leave administrator record for this employer",
                error_type=IssueType.unauthorized_leave_admin,
            )

        if user_leave_admin.fineos_web_id is None:
            logger.warning(
                "The leave admin has no FINEOS ID",
                extra=log_attributes,
            )
            raise VerificationRequired(
                user_leave_admin, "User has no leave administrator FINEOS ID"
            )

        if not user_leave_admin.verified:
            logger.warning(
                "The leave admin is not verified",
                extra=log_attributes,
            )
            raise VerificationRequired(user_leave_admin, "User is not Verified")

        if not user_has_access_to_claim(claim, current_user):
            logger.warning(
                "The leave admin cannot access claims of this organization unit",
                extra={
                    "has_verification_data": user_leave_admin.employer.has_verification_data,
                    "claim_organization_unit": OrganizationUnit.from_orm(
                        claim.organization_unit
                    ).dict(),
                    "leave_admin_fineos_web_id": user_leave_admin.fineos_web_id,
                    "leave_admin_organization_unit_ids": ",".join(
                        [str(o.organization_unit_id) for o in user_leave_admin.organization_units]
                    ),
                    **log_attributes,
                },
            )
            raise NotAuthorizedForAccess(
                description="The leave admin cannot access claims of this organization unit",
                error_type="unauthorized_leave_admin",
            )

        return user_leave_admin


def get_claim(fineos_absence_id: str) -> flask.Response:
    is_employer = can(READ, "EMPLOYER_API")
    if is_employer:
        error = response_util.error_response(
            Forbidden,
            "Employers are not allowed to access claimant claim info",
            errors=[],
        )
        return error.to_api_response()

    claim = get_claim_from_db(fineos_absence_id)

    if claim is None:
        logger.warning(
            "get_claim failure - Claim not in PFML database.",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = response_util.error_response(NotFound, "Claim not in PFML database.", errors=[])
        return error.to_api_response()

    if not user_has_access_to_claim(claim, app.current_user()):
        logger.warning(
            "get_claim failure - User does not have access to claim.",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = response_util.error_response(
            Forbidden, "User does not have access to claim.", errors=[]
        )
        return error.to_api_response()

    try:
        detailed_claim = get_claim_detail(claim, {"absence_case_id": fineos_absence_id})
    except ClaimWithdrawnError:
        logger.warning(
            "get_claim failure - Claim has been withdrawn. Unable to display claim status.",
            extra={
                "absence_id": claim.fineos_absence_id,
                "absence_case_id": claim.fineos_absence_id,
            },
        )
        return ClaimWithdrawn().to_api_response()
    except Exception as ex:
        logger.warning(
            f"get_claim failure - {str(ex)}",
            extra={
                "absence_id": claim.fineos_absence_id,
                "absence_case_id": claim.fineos_absence_id,
            },
        )
        raise ex  # handled by catch-all error handler in validation/__init__.py

    log_get_claim_metrics(detailed_claim)

    return response_util.success_response(
        message="Successfully retrieved claim",
        data=detailed_claim.dict(),
        status_code=200,
    ).to_api_response()


def retrieve_claims() -> flask.Response:

    body = connexion.request.json
    claim_request = ClaimSearchRequest.parse_obj(body)

    return _process_claims_request(claim_request=claim_request, method_name="retrieve_claims")


def get_claims() -> flask.Response:
    employer_id_str = flask.request.args.get("employer_id")
    employee_id_str = flask.request.args.get("employee_id")
    is_reviewable_str = flask.request.args.get("is_reviewable", type=str)

    terms = ClaimSearchTerms(
        search=flask.request.args.get("search", type=str),
        request_decision=flask.request.args.get("request_decision"),
        is_reviewable=is_reviewable_str,  # type: ignore
    )
    if employer_id_str is not None:
        terms.employer_ids = {UUID(eid.strip()) for eid in employer_id_str.split(",")}
    if employee_id_str is not None:
        terms.employee_ids = {UUID(eid.strip()) for eid in employee_id_str.split(",")}

    pagination_params = make_pagination_params(flask.request)
    claim_request = ClaimSearchRequest(
        terms=terms, order=pagination_params.order, paging=pagination_params.paging
    )

    return _process_claims_request(claim_request=claim_request, method_name="get_claims")


def _process_claims_request(claim_request: ClaimSearchRequest, method_name: str) -> flask.Response:

    claim_request_terms = claim_request.terms
    employee_ids = claim_request_terms.employee_ids
    employer_ids = claim_request_terms.employer_ids
    search_string = claim_request_terms.search
    is_reviewable = claim_request_terms.is_reviewable
    request_decisions = map_request_decision_param_to_db_columns(
        claim_request_terms.request_decision
    )

    current_user = app.current_user()
    is_pfml_crm_user = has_role_in(current_user, [Role.PFML_CRM])
    is_employer = can(READ, "EMPLOYER_API")
    log_attributes = {}
    log_attributes.update(get_employer_log_attributes(current_user))

    with PaginationAPIContext(Claim, request=claim_request) as pagination_context:
        with app.db_session() as db_session:
            query = GetClaimsQuery(db_session)
            # The logic here is similar to that in user_has_access_to_claim (except it is applied to multiple claims)
            # so if something changes there it probably needs to be changed here
            if is_pfml_crm_user:
                # The CRM user should be able to read any claim, so this condition can just pass.
                #
                # The CRM user does not use use /claims/{claim_id} yet, so this logic has explicitly not been added to user_has_access_to_claim
                pass
            elif is_employer and current_user.employers:
                employers_list = list(current_user.employers)

                verified_employers = [
                    employer
                    for employer in employers_list
                    if current_user.verified_employer(employer)
                ]

                # filters claims by employer id - shows all claims of those employers
                # if those employers use org units, then more filters are applied
                query.add_leave_admin_filter(verified_employers, current_user)
            else:
                query.add_user_owns_claim_filter(current_user)

            if employer_ids:
                query.add_employers_filter(employer_ids)

            if employee_ids:
                query.add_employees_filter(employee_ids)

            query.add_managed_requirements_filter()

            if search_string:
                query.add_search_filter(
                    escape_like(search_string)
                )  # escape user input search string

            if is_reviewable is not None:
                log_attributes.update({"filter.is_reviewable": "yes" if is_reviewable else "no"})
                query.add_is_reviewable_filter(is_reviewable)

            if request_decisions:
                # Log values from query param since more familiar to new relic users
                log_attributes.update(
                    {"filter.request_decision": claim_request_terms.request_decision}
                )
                query.add_request_decision_filter(request_decisions)

            query.add_order_by(pagination_context, is_reviewable)

            page = query.get_paginated_results(pagination_context)
            request_log_info = search_request_log_info(claim_request, page)

    logger.info(
        f"{method_name} success",
        extra={**request_log_info, **log_attributes},
    )

    response_model: Union[Type[ClaimForPfmlCrmResponse], Type[ClaimResponse]] = (
        ClaimForPfmlCrmResponse if is_pfml_crm_user else ClaimResponse
    )

    return response_util.paginated_success_response(
        message="Successfully retrieved claims",
        model=response_model,
        page=page,
        context=pagination_context,
        status_code=200,
    ).to_api_response()


def map_request_decision_param_to_db_columns(
    request_decision_str: Optional[str],
) -> Set[int]:
    request_decision_map = {
        "approved": set([LeaveRequestDecision.APPROVED.leave_request_decision_id]),
        "denied": set([LeaveRequestDecision.DENIED.leave_request_decision_id]),
        "withdrawn": set([LeaveRequestDecision.WITHDRAWN.leave_request_decision_id]),
        "pending": set(
            [
                LeaveRequestDecision.PENDING.leave_request_decision_id,
                LeaveRequestDecision.IN_REVIEW.leave_request_decision_id,
                LeaveRequestDecision.PROJECTED.leave_request_decision_id,
            ]
        ),
        "cancelled": set(
            [
                LeaveRequestDecision.CANCELLED.leave_request_decision_id,
                LeaveRequestDecision.VOIDED.leave_request_decision_id,
            ]
        ),
    }

    if not request_decision_str:
        return set()
    return request_decision_map[request_decision_str]

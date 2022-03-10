import base64
from typing import Dict, List, Optional, Set, Type, Union
from uuid import UUID

import connexion
import flask
from sqlalchemy.orm.session import Session
from sqlalchemy_utils import escape_like
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.claim_rules as claim_rules
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.authorization.flask import READ, can, requires
from massgov.pfml.api.exceptions import ClaimWithdrawn, ObjectNotFound
from massgov.pfml.api.models.applications.common import OrganizationUnit
from massgov.pfml.api.models.claims.common import ChangeRequest, EmployerClaimReview
from massgov.pfml.api.models.claims.requests import ClaimSearchRequest, ClaimSearchTerms
from massgov.pfml.api.models.claims.responses import (
    ChangeRequestResponse,
    ClaimForPfmlCrmResponse,
    ClaimResponse,
    ManagedRequirementResponse,
)
from massgov.pfml.api.models.common import OrderData, PagingData
from massgov.pfml.api.services.administrator_fineos_actions import (
    awaiting_leave_info,
    complete_claim_review,
    create_eform,
    download_document_as_leave_admin,
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
)
from massgov.pfml.api.services.claims import (
    ClaimWithdrawnError,
    add_change_request_to_db,
    get_change_requests_from_db,
    get_claim_detail,
)
from massgov.pfml.api.services.managed_requirements import update_employer_confirmation_requirements
from massgov.pfml.api.util.claims import user_has_access_to_claim
from massgov.pfml.api.util.paginate.paginator import (
    PaginationAPIContext,
    make_paging_meta_data_from_paginator,
)
from massgov.pfml.api.validation.exceptions import (
    ContainsV1AndV2Eforms,
    IssueType,
    ValidationErrorDetail,
)
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import ChangeRequest as change_request_db_model
from massgov.pfml.db.models.employees import (
    Claim,
    Employer,
    LeaveRequestDecision,
    ManagedRequirement,
    Role,
    UserLeaveAdministrator,
)
from massgov.pfml.db.queries.absence_periods import upsert_absence_period_from_fineos_period
from massgov.pfml.db.queries.get_claims_query import ActionRequiredStatusFilter, GetClaimsQuery
from massgov.pfml.db.queries.managed_requirements import (
    commit_managed_requirements,
    create_or_update_managed_requirement_from_fineos,
)
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    ManagedRequirementDetails,
    PeriodDecisions,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import (
    EmployerClaimReviewEFormBuilder,
    EmployerClaimReviewV1EFormBuilder,
)
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.logging.claims import (
    get_claim_log_attributes,
    get_claim_review_log_attributes,
    get_managed_requirements_log_attributes,
    log_absence_period,
    log_get_claim_metrics,
    log_managed_requirement,
)
from massgov.pfml.util.logging.employers import get_employer_log_attributes
from massgov.pfml.util.logging.managed_requirements import (
    get_managed_requirements_update_log_attributes,
)
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.users import has_role_in

logger = massgov.pfml.util.logging.get_logger(__name__)

# Added in https://lwd.atlassian.net/browse/PSD-2401
# Modified in https://lwd.atlassian.net/browse/PFMLPB-3276
CLAIMS_DASHBOARD_BLOCKED_FEINS: Set[str] = set([])


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
                "The leave admin is None", extra=log_attributes,
            )
            raise NotAuthorizedForAccess(
                description="User does not have leave administrator record for this employer",
                error_type=IssueType.unauthorized_leave_admin,
            )

        if user_leave_admin.fineos_web_id is None:
            logger.warning(
                "The leave admin has no FINEOS ID", extra=log_attributes,
            )
            raise VerificationRequired(
                user_leave_admin, "User has no leave administrator FINEOS ID"
            )

        if not user_leave_admin.verified:
            logger.warning(
                "The leave admin is not verified", extra=log_attributes,
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


@requires(READ, "EMPLOYER_API")
def employer_update_claim_review(fineos_absence_id: str) -> flask.Response:
    current_user = app.current_user()
    body = connexion.request.json

    claim_review: EmployerClaimReview = EmployerClaimReview.parse_obj(body)

    if issues := claim_rules.get_employer_claim_review_issues(claim_review):
        return response_util.error_response(
            status_code=BadRequest, message="Invalid claim review body", errors=issues, data={},
        ).to_api_response()

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    claim = get_claim_from_db(fineos_absence_id)

    log_attributes: Dict[str, Union[bool, str, int, UUID, None]]

    log_attributes = {
        "absence_case_id": fineos_absence_id,
        "user_leave_admin.employer_id": user_leave_admin.employer_id,
        **get_claim_review_log_attributes(claim_review),
        **get_employer_log_attributes(current_user),
        **get_claim_log_attributes(claim),
    }

    fineos_web_id = user_leave_admin.fineos_web_id

    if fineos_web_id is None:
        raise ValueError("User admin does not have a FINEOS user")

    # can now use `fineos_web_id` as if it was non-None

    if not awaiting_leave_info(fineos_web_id, fineos_absence_id):
        logger.warning("No outstanding information request for claim", extra=log_attributes)
        return response_util.error_response(
            status_code=BadRequest,
            message="No outstanding information request for claim",
            errors=[
                ValidationErrorDetail(
                    type=IssueType.outstanding_information_request_required,
                    message="No outstanding information request for claim",
                )
            ],
        ).to_api_response()

    if (
        claim_review.employer_decision == "Approve"
        and not claim_review.has_amendments
        and not claim_review.comment
        and not claim_review.relationship_inaccurate_reason
    ):
        complete_claim_review(fineos_web_id, fineos_absence_id)
        logger.info("Completed claim review", extra=log_attributes)
    else:
        if claim_review.uses_second_eform_version:
            transformed_eform = EmployerClaimReviewEFormBuilder.build(claim_review)
            create_eform(fineos_web_id, fineos_absence_id, transformed_eform)
            logger.info("Created v2 eform", extra=log_attributes)
        else:
            transformed_eform = EmployerClaimReviewV1EFormBuilder.build(claim_review)
            create_eform(fineos_web_id, fineos_absence_id, transformed_eform)
            logger.info("Created eform", extra=log_attributes)

    logger.info("Updated claim", extra=log_attributes)
    with app.db_session() as db_session:
        # Try updating managed requirements after claim update
        try:
            fineos = massgov.pfml.fineos.create_client()
            fineos_managed_requirements = fineos.get_managed_requirements(
                str(fineos_web_id), fineos_absence_id
            )

            updated_managed_requirements = update_employer_confirmation_requirements(
                db_session, user_leave_admin.user_id, fineos_managed_requirements,
            )

            log_attributes = {
                **log_attributes,
                **get_managed_requirements_update_log_attributes(
                    fineos_managed_requirements, updated_managed_requirements
                ),
            }

        # On exception, log the error and pass so API returns normally
        except Exception as ex:
            logger.warning(
                "Unable to update managed requirements", exc_info=ex, extra=log_attributes
            )
            db_session.rollback()

    claim_response = {"claim_id": fineos_absence_id}
    return response_util.success_response(
        message="Successfully updated claim", data=claim_response,
    ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_get_claim_review(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to retrieve claim data and returns it.
    The requesting user must be of the EMPLOYER role.
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    log_attributes = get_employer_log_attributes(user_leave_admin.user)
    log_attributes = {"absence_case_id": fineos_absence_id, **log_attributes}

    # get_claim_as_leave_admin takes str for the first argument;
    # this effectively unwraps Optional[str] to be used as str,
    # satisfying the type requirement for mypy.
    # It is not expected that this will ever raise an AssertionError.
    assert user_leave_admin.fineos_web_id is not None

    with app.db_session() as db_session:
        employer = get_or_404(db_session, Employer, user_leave_admin.employer_id)

        try:
            (
                fineos_claim_review_response,
                fineos_managed_requirements,
                absence_period_decisions,
            ) = get_claim_as_leave_admin(
                user_leave_admin.fineos_web_id, fineos_absence_id, employer,
            )
        except (ContainsV1AndV2Eforms) as error:
            return response_util.error_response(
                status_code=error.status_code,
                message=error.description,
                errors=[
                    ValidationErrorDetail(
                        message="Claim contains both V1 and V2 eforms.",
                        type=IssueType.contains_v1_and_v2_eforms,
                    )
                ],
                data={},
            ).to_api_response()
        except ClaimWithdrawn as error:
            return error.to_api_response()

        claim_from_db = get_claim_from_db(fineos_absence_id)

        # If claim exists, handle db sync side effects and updates to response object
        if claim_from_db:
            log_attributes.update(get_claim_log_attributes(claim_from_db))

            if claim_from_db.fineos_absence_status:
                fineos_claim_review_response.status = (
                    claim_from_db.fineos_absence_status.absence_status_description
                )
            sync_absence_periods(
                db_session, claim_from_db, absence_period_decisions, log_attributes
            )

            managed_requirements = sync_managed_requirements(
                db_session, claim_from_db, fineos_managed_requirements, log_attributes,
            )
            fineos_claim_review_response.managed_requirements = [
                ManagedRequirementResponse.from_orm(mr) for mr in managed_requirements
            ]

            log_attributes.update(
                get_managed_requirements_log_attributes(
                    fineos_claim_review_response.managed_requirements
                )
            )
            for requirement in fineos_claim_review_response.managed_requirements:
                log_managed_requirement(requirement, fineos_absence_id)

        log_attributes.update(
            {"num_absence_periods": len(fineos_claim_review_response.absence_periods),}
        )

        for period in fineos_claim_review_response.absence_periods:
            log_absence_period(
                fineos_absence_id, period, "get_claim_review - Found absence period for claim"
            )

        logger.info(
            "employer_get_claim_review success", extra=log_attributes,
        )
        return response_util.success_response(
            message="Successfully retrieved claim",
            data=fineos_claim_review_response.dict(),
            status_code=200,
        ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_get_claim_documents(fineos_absence_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to get a list of documents attached to a specified claim.
    The requesting user must be of the EMPLOYER role.
    """
    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    documents = get_documents_as_leave_admin(user_leave_admin.fineos_web_id, fineos_absence_id)  # type: ignore
    documents_list = [doc.dict() for doc in documents]

    log_attributes = get_employer_log_attributes(user_leave_admin.user)

    claim = get_claim_from_db(fineos_absence_id)
    if claim:
        log_attributes.update(get_claim_log_attributes(claim))

    logger.info(
        "employer_get_claim_documents success", extra={**log_attributes},
    )
    return response_util.success_response(
        message="Successfully retrieved documents", data=documents_list, status_code=200
    ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_document_download(fineos_absence_id: str, fineos_document_id: str) -> flask.Response:
    """
    Calls out to the FINEOS Group Client API to download a document for a specified claim.
    The requesting user must be of the EMPLOYER role.
    """

    log_attr: Dict[str, Union[str, int]] = {}

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except NotAuthorizedForAccess as not_authorized:
        logger.error(
            f"employer_document_download failed - {not_authorized.description}", extra=log_attr,
        )
        return not_authorized.to_api_response()
    except VerificationRequired as not_verified:
        logger.error(
            f"employer_document_download failed - {not_verified.description}", extra=log_attr,
        )
        return not_verified.to_api_response()
    log_attr.update(get_employer_log_attributes(user_leave_admin.user))

    try:
        document_data: Base64EncodedFileData = download_document_as_leave_admin(
            user_leave_admin.fineos_web_id, fineos_absence_id, fineos_document_id, log_attr  # type: ignore
        )
    except ObjectNotFound as not_found:
        logger.error(
            f"employer_document_download failed - {not_found.description}", extra=log_attr,
        )
        return not_found.to_api_response()
    except NotAuthorizedForAccess as not_authorized:
        logger.error(
            f"employer_document_download failed - {not_authorized.description}", extra=log_attr,
        )
        return not_authorized.to_api_response()

    file_bytes = base64.b64decode(document_data.base64EncodedFileContents.encode("ascii"))
    content_type = document_data.contentType or "application/octet-stream"
    claim = get_claim_from_db(fineos_absence_id)
    if claim:
        log_attr.update(get_claim_log_attributes(claim))

    logger.info(
        "employer_document_download success", extra=log_attr,
    )
    return flask.Response(
        file_bytes,
        content_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={document_data.fileName}"},
    )


def get_claim(fineos_absence_id: str) -> flask.Response:
    is_employer = can(READ, "EMPLOYER_API")
    if is_employer:
        error = response_util.error_response(
            Forbidden, "Employers are not allowed to access claimant claim info", errors=[],
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
        message="Successfully retrieved claim", data=detailed_claim.dict(), status_code=200,
    ).to_api_response()


def get_claim_from_db(fineos_absence_id: Optional[str]) -> Optional[Claim]:
    if fineos_absence_id is None:
        return None

    with app.db_session() as db_session:
        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

    return claim


def retrieve_claims() -> flask.Response:

    body = connexion.request.json
    claim_request = ClaimSearchRequest.parse_obj(body)

    return _process_claims_request(claim_request=claim_request, method_name="retrieve_claims")


def get_claims() -> flask.Response:
    employer_id_str = flask.request.args.get("employer_id")
    employee_id_str = flask.request.args.get("employee_id")

    terms = ClaimSearchTerms()
    if employer_id_str is not None:
        terms.employer_ids = {UUID(eid.strip()) for eid in employer_id_str.split(",")}
    if employee_id_str is not None:
        terms.employee_ids = {UUID(eid.strip()) for eid in employee_id_str.split(",")}
    terms.search = flask.request.args.get("search", type=str)
    terms.claim_status = flask.request.args.get("claim_status")
    terms.request_decision = flask.request.args.get("request_decision")
    terms.is_reviewable = flask.request.args.get("is_reviewable", type=str)

    request_body = _prepare_request_body(flask.request, terms)
    claim_request = ClaimSearchRequest.parse_obj(request_body)

    return _process_claims_request(claim_request=claim_request, method_name="get_claims")


def _prepare_request_body(request: flask.Request, terms: ClaimSearchTerms) -> Dict:
    order_data = OrderData()
    order = {
        "by": request.args.get("order_by", order_data.by, type=str),
        "direction": request.args.get("order_direction", order_data.direction, type=str),
    }
    paging_data = PagingData()
    paging = {
        "offset": request.args.get("page_offset", paging_data.offset, type=int),
        "size": request.args.get("page_size", paging_data.size, type=int),
    }
    return {"terms": terms, "paging": paging, "order": order}


def _process_claims_request(claim_request: ClaimSearchRequest, method_name: str) -> flask.Response:

    claim_request_terms = claim_request.terms
    employee_ids = claim_request_terms.employee_ids
    employer_ids = claim_request_terms.employer_ids
    search_string = claim_request_terms.search
    absence_statuses = parse_filterable_absence_statuses(claim_request_terms.claim_status)
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
                    if employer.employer_fein.to_formatted_str()
                    not in CLAIMS_DASHBOARD_BLOCKED_FEINS
                    and current_user.verified_employer(employer)
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

            if len(absence_statuses):
                # Log the values from the query params rather than the enum groups they
                # might equate to, since what is sent into the API will be more familiar
                # to New Relic users since it aligns closer to what Portal users see
                log_attributes.update(
                    {"filter.absence_statuses": ", ".join(sorted(absence_statuses))}
                )
                query.add_absence_status_filter(absence_statuses)
            else:
                query.add_managed_requirements_filter()

            if search_string:
                query.add_search_filter(
                    escape_like(search_string)
                )  # escape user input search string

            if is_reviewable:
                log_attributes.update({"filter.is_reviewable": is_reviewable})
                query.add_is_reviewable_filter(is_reviewable)

            if request_decisions:
                # Log values from query param since more familiar to new relic users
                log_attributes.update(
                    {"filter.request_decision": claim_request_terms.request_decision}
                )
                query.add_request_decision_filter(request_decisions)

            query.add_order_by(pagination_context)

            page = query.get_paginated_results(pagination_context)
            page_data_log_attributes = make_paging_meta_data_from_paginator(
                pagination_context, page
            ).to_dict()

    logger.info(
        f"{method_name} success", extra={**page_data_log_attributes, **log_attributes,},
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


def parse_filterable_absence_statuses(absence_status_string: Union[str, None]) -> set:
    if not absence_status_string:
        return set()
    absence_statuses = set(absence_status_string.strip().split(","))
    validate_filterable_absence_statuses(absence_statuses)
    return absence_statuses


def map_request_decision_param_to_db_columns(request_decision_str: Optional[str],) -> Set[int]:
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


def validate_filterable_absence_statuses(absence_statuses: Set[str]) -> None:
    """Confirm the absence statuses match a filterable status"""

    for absence_status in absence_statuses:
        if absence_status in ActionRequiredStatusFilter.all():
            continue

        try:
            AbsenceStatus.get_id(absence_status)
        except KeyError:
            raise BadRequest(f"Invalid claim status {absence_status}.")

    return


def sync_managed_requirements(
    db_session: Session,
    claim: Claim,
    managed_requirements: List[ManagedRequirementDetails],
    log_attributes: dict,
) -> List[ManagedRequirement]:
    """
    Note that commit to db is the responsibility of called functions.
    """
    managed_requirements_from_db = []
    for mr in managed_requirements:
        managed_requirement = create_or_update_managed_requirement_from_fineos(
            db_session, claim.claim_id, mr, log_attributes
        )
        if managed_requirement is not None:
            managed_requirements_from_db.append(managed_requirement)
    commit_managed_requirements(db_session)
    return managed_requirements_from_db


def sync_absence_periods(
    db_session: Session, claim: Claim, decisions: PeriodDecisions, log_attributes: dict
) -> None:
    """
    Note that commit to db is responsibility of the caller
    """
    if not decisions.decisions:
        return
    absence_periods = [
        decision.period for decision in decisions.decisions if decision.period is not None
    ]
    for absence_period in absence_periods:
        upsert_absence_period_from_fineos_period(
            db_session, claim.claim_id, absence_period, log_attributes
        )
    # only commit to db when every absence period has been succesfully synced
    # otherwise rollback changes if any absence period upsert throws an exception
    db_session.commit()


def post_change_request(fineos_absence_id: str) -> flask.Response:
    body = connexion.request.json
    change_request: ChangeRequest = ChangeRequest.parse_obj(body)

    claim = get_claim_from_db(fineos_absence_id)
    if claim is None:
        logger.warning(
            "Claim does not exist for given absence ID",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = response_util.error_response(
            status_code=NotFound,
            message="Claim does not exist for given absence ID",
            errors=[],
            data={},
        )
        return error.to_api_response()

    db_change_request = add_change_request_to_db(change_request, claim.claim_id)

    issues = claim_rules.get_change_request_issues(db_change_request, claim)

    response_data = ChangeRequestResponse.from_orm(db_change_request)

    return response_util.success_response(
        message="Successfully posted change request",
        data=response_data.dict(),
        status_code=201,
        warnings=issues,
    ).to_api_response()


def get_change_requests(fineos_absence_id: str) -> flask.Response:
    claim = get_claim_from_db(fineos_absence_id)

    if claim is None:
        logger.warning(
            "Claim does not exist for given absence ID",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = response_util.error_response(
            NotFound, "Claim does not exist for given absence ID", errors=[],
        )
        return error.to_api_response()

    with app.db_session() as db_session:
        change_requests = get_change_requests_from_db(claim.claim_id, db_session)

    # TODO: (PORTAL-1864) Convert the change_request_type to return the enum value rather than the id
    change_requests_dict = []
    for request in change_requests:
        change_requests_dict.append(request.dict())

    return response_util.success_response(
        message="Successfully retrieved change requests",
        data={"absence_case_id": fineos_absence_id, "change_requests": change_requests_dict},
        status_code=200,
    ).to_api_response()


def submit_change_request(change_request_id: str) -> flask.Response:
    with app.db_session() as db_session:
        change_request = get_or_404(db_session, change_request_db_model, UUID(change_request_id))

    if issues := claim_rules.get_change_request_issues(change_request, change_request.claim):
        return response_util.error_response(
            status_code=BadRequest, message="Invalid change request", errors=issues, data={},
        ).to_api_response()

    # TODO: Post change request to FINEOS - https://lwd.atlassian.net/browse/PORTAL-1710
    change_request.submitted_time = utcnow()

    response_data = ChangeRequestResponse.from_orm(change_request)

    return response_util.success_response(
        message="Successfully submitted Change Request to FINEOS",
        data=response_data.dict(),
        status_code=200,
    ).to_api_response()


def delete_change_request(change_request_id: str) -> flask.Response:
    with app.db_session() as db_session:
        change_request = get_or_404(db_session, change_request_db_model, UUID(change_request_id))

        if change_request.submitted_time is not None:
            error = response_util.error_response(
                BadRequest, "Cannot delete a submitted request", data={}, errors=[],
            )
            return error.to_api_response()

        db_session.delete(change_request)

    return response_util.success_response(
        message="Successfully deleted change request", data={}, status_code=200,
    ).to_api_response()

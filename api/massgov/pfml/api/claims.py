import base64
from typing import Any, Dict, List, Optional, Set, Union

import connexion
import flask
from sqlalchemy.orm.session import Session
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.claim_rules as claim_rules
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.authorization.flask import READ, can, requires
from massgov.pfml.api.exceptions import ObjectNotFound
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.claims.responses import ClaimResponse, DetailedClaimResponse
from massgov.pfml.api.services.administrator_fineos_actions import (
    awaiting_leave_info,
    complete_claim_review,
    create_eform,
    download_document_as_leave_admin,
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
)
from massgov.pfml.api.services.managed_requirements import update_employer_confirmation_requirements
from massgov.pfml.api.validation.exceptions import ContainsV1AndV2Eforms
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    Employer,
    ManagedRequirement,
    ManagedRequirementStatus,
    ManagedRequirementType,
    UserLeaveAdministrator,
)
from massgov.pfml.db.queries.get_claims_query import ActionRequiredStatusFilter, GetClaimsQuery
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
    update_managed_requirement_from_fineos,
)
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    ManagedRequirementDetails,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import (
    EmployerClaimReviewEFormBuilder,
    EmployerClaimReviewV1EFormBuilder,
)
from massgov.pfml.util.paginate.paginator import PaginationAPIContext
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.strings import sanitize_fein

logger = massgov.pfml.util.logging.get_logger(__name__)
# HRD Employer FEIN. See https://lwd.atlassian.net/browse/EMPLOYER-1317
CLAIMS_DASHBOARD_BLOCKED_FEINS = set(["046002284"])


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
        associated_employer_id: Optional[str] = None

        current_user = app.current_user()
        if current_user is None:
            raise Unauthorized()

        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

        if claim is not None:
            associated_employer_id = claim.employer_id

        if associated_employer_id is None:
            raise Forbidden(description="Claim does not exist for given absence ID")

        user_leave_admin = (
            db_session.query(UserLeaveAdministrator)
            .filter(
                (UserLeaveAdministrator.user_id == current_user.user_id)
                & (UserLeaveAdministrator.employer_id == associated_employer_id)
            )
            .one_or_none()
        )

        if user_leave_admin is None:
            raise NotAuthorizedForAccess(
                description="User does not have leave administrator record for this employer",
                error_type="unauthorized_leave_admin",
            )

        if user_leave_admin.fineos_web_id is None:
            raise VerificationRequired(
                user_leave_admin, "User has no leave administrator FINEOS ID"
            )

        if not user_leave_admin.verified:
            raise VerificationRequired(user_leave_admin, "User is not Verified")

        return user_leave_admin


def get_employer_log_attributes(app: connexion.FlaskApp) -> Dict[str, Any]:
    """
    Determine the requesting user's employer relationships & verification status
    """
    current_user = app.current_user()
    if current_user is None:
        raise Unauthorized()

    employers = list(current_user.employers)
    verified_employers = [
        e.employer_id for e in current_user.employers if current_user.verified_employer(e)
    ]
    log_attributes = {
        "num_employers": len(employers),
        "num_verified_employers": len(verified_employers),
        "num_unverified_employers": len(employers) - len(verified_employers),
    }
    return log_attributes


def get_claim_log_attributes(claim: Optional[Claim]) -> Dict[str, Any]:
    if claim is None:
        return {}

    application = claim.application  # type: ignore
    if application is None:
        return {}

    leave_reason = (
        application.leave_reason.leave_reason_description if application.leave_reason else None
    )

    return {"leave_reason": leave_reason}


def get_claim_review_log_attributes(claim_review: Optional[EmployerClaimReview]) -> Dict[str, Any]:
    if claim_review is None:
        return {}

    relationship_accurate_val = (
        claim_review.believe_relationship_accurate.value
        if claim_review.believe_relationship_accurate
        else None
    )

    return {
        "claim_request.believe_relationship_accurate": relationship_accurate_val,
        "claim_request.employer_decision": claim_review.employer_decision,
        "claim_request.fraud": claim_review.fraud,
        "claim_request.has_amendments": claim_review.has_amendments,
        "claim_request.has_comment": str(bool(claim_review.comment)),
        "claim_request.num_previous_leaves": len(claim_review.previous_leaves),
        "claim_request.num_employer_benefits": len(claim_review.employer_benefits),
        "claim_request.num_concurrent_leave": 1 if claim_review.concurrent_leave else 0,
    }


def get_managed_requirements_log_attributes(
    fineos_managed_requirements: List[ManagedRequirementDetails],
    updated_managed_requirements: List[ManagedRequirement],
) -> Dict[str, Any]:
    return {
        "managed_requirements.updated_successfully": len(updated_managed_requirements),
        "managed_requirements.not_updated_successfully": len(fineos_managed_requirements)
        - len(updated_managed_requirements),
        "managed_requirements.received_as_open": len(
            [
                fmr
                for fmr in fineos_managed_requirements
                if str(fmr.status)
                == ManagedRequirementStatus.OPEN.managed_requirement_status_description
            ]
        ),
    }


@requires(READ, "EMPLOYER_API")
def employer_update_claim_review(fineos_absence_id: str) -> flask.Response:
    body = connexion.request.json

    claim_review: EmployerClaimReview = EmployerClaimReview.parse_obj(body)

    if issues := claim_rules.get_employer_claim_review_issues(claim_review):
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid claim review body",
            errors=[response_util.validation_issue(issue) for issue in issues],
            data={},
        ).to_api_response()

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    claim = get_claim_from_db(fineos_absence_id)

    log_attributes: Dict[str, Union[bool, str, int, None]]

    log_attributes = {
        "absence_case_id": fineos_absence_id,
        "user_leave_admin.employer_id": user_leave_admin.employer_id,
        **get_claim_review_log_attributes(claim_review),
        **get_employer_log_attributes(app),
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
                response_util.custom_issue(
                    "outstanding_information_request_required",
                    "No outstanding information request for claim",
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

    # Try updating managed requirements after claim update
    try:
        fineos = massgov.pfml.fineos.create_client()
        fineos_managed_requirements = fineos.get_managed_requirements(
            str(fineos_web_id), fineos_absence_id
        )

        with app.db_session() as db_session:
            updated_managed_requirements = update_employer_confirmation_requirements(
                db_session, user_leave_admin.user_id, fineos_managed_requirements,
            )

            log_attributes = {
                **log_attributes,
                **get_managed_requirements_log_attributes(
                    fineos_managed_requirements, updated_managed_requirements
                ),
            }

    # On exception, log the error and pass so API returns normally
    except Exception as ex:
        logger.warning("Unable to update managed requirements", exc_info=ex, extra=log_attributes)

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
    default_to_v2 = bool(flask.request.headers.get("X-FF-Default-To-V2", False))

    try:
        user_leave_admin = get_current_user_leave_admin_record(fineos_absence_id)
    except (VerificationRequired, NotAuthorizedForAccess) as error:
        return error.to_api_response()

    log_attributes = get_employer_log_attributes(app)

    if not user_leave_admin.fineos_web_id:
        logger.error(
            "employer_get_claim_review failure - user leave administrator does not have a fineos_web_id",
            extra={**log_attributes},
        )
        return response_util.error_response(
            status_code=NotFound, message="ULA does not have a fineos_web_id", errors=[], data={},
        ).to_api_response()

    with app.db_session() as db_session:
        employer = get_or_404(db_session, Employer, user_leave_admin.employer_id)

        try:
            claim_review_response, managed_requirements = get_claim_as_leave_admin(
                user_leave_admin.fineos_web_id,
                fineos_absence_id,
                employer,
                default_to_v2=default_to_v2,
            )
        except (ContainsV1AndV2Eforms) as error:
            return response_util.error_response(
                status_code=error.status_code,
                message=error.description,
                errors=[
                    response_util.custom_issue(
                        message="Claim contains both V1 and V2 eforms.",
                        type="contains_v1_and_v2_eforms",
                    )
                ],
                data={},
            ).to_api_response()

        if claim_review_response is None:
            logger.error(
                "employer_get_claim_review failure - could not get claim for absence id",
                extra={**log_attributes},
            )
            raise NotFound(
                description="Could not fetch Claim from FINEOS with given absence ID {}".format(
                    fineos_absence_id
                )
            )

        claim_from_db = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

        if claim_from_db and claim_from_db.fineos_absence_status:
            claim_review_response.status = (
                claim_from_db.fineos_absence_status.absence_status_description
            )

        if claim_from_db:
            log_attributes.update(get_claim_log_attributes(claim_from_db))

        logger.info(
            "employer_get_claim_review success", extra={**log_attributes},
        )
        try:
            handle_managed_requirements(
                db_session, claim_from_db, managed_requirements, log_attributes,
            )
        except Exception as error:  # catch all exception handler
            logger.error(
                "Failed to handle the claim's managed requirements in employer claim review call",
                extra=log_attributes,
                exc_info=error,
            )
        return response_util.success_response(
            message="Successfully retrieved claim",
            data=claim_review_response.dict(),
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

    log_attributes = get_employer_log_attributes(app)

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
    log_attr.update(get_employer_log_attributes(app))

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

    try:
        document_data: Base64EncodedFileData = download_document_as_leave_admin(
            user_leave_admin.fineos_web_id, fineos_absence_id, fineos_document_id  # type: ignore
        )
    except ObjectNotFound as not_found:
        logger.error(
            f"employer_document_download failed - {not_found.description}", extra=log_attr,
        )
        return not_found.to_api_response()
    except NotAuthorizedForAccess as not_authorized:
        doc_type = not_authorized.data["doc_type"]
        logger.error(
            f"employer_document_download failed - {not_authorized.description}",
            extra={**log_attr, "document_type": doc_type},
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


def user_has_access_to_claim(claim: Claim) -> bool:
    current_user = app.current_user()
    if current_user is None:
        return False

    if can(READ, "EMPLOYER_API") and claim.employer in current_user.employers:
        # User is leave admin for the employer associated with claim
        return current_user.verified_employer(claim.employer)

    application = claim.application  # type: ignore

    if application and application.user == current_user:
        # User is claimant and this is their claim
        return True

    return False


def get_claim(fineos_absence_id: str) -> flask.Response:
    claim = get_claim_from_db(fineos_absence_id)

    if claim is None:
        logger.warning("Claim not in database.")
        return response_util.error_response(
            status_code=BadRequest, message="Claim not in database.", errors=[], data={},
        ).to_api_response()

    if not user_has_access_to_claim(claim):
        logger.warning("User does not have access to claim.")
        return response_util.error_response(
            status_code=Forbidden,
            message="User does not have access to claim.",
            errors=[],
            data={},
        ).to_api_response()

    return response_util.success_response(
        message="Successfully retrieved claim",
        data=DetailedClaimResponse.from_orm(claim).dict(),
        status_code=200,
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


def get_claims() -> flask.Response:
    current_user = app.current_user()
    employer_id = flask.request.args.get("employer_id")
    search_string = flask.request.args.get("search", type=str)
    absence_statuses = parse_filterable_absence_statuses(flask.request.args.get("claim_status"))
    is_employer = can(READ, "EMPLOYER_API")
    log_attributes = get_employer_log_attributes(app)

    with PaginationAPIContext(Claim, request=flask.request) as pagination_context:
        with app.db_session() as db_session:
            query = GetClaimsQuery(db_session)

            # The logic here is similar to that in user_has_access_to_claim (except it is applied to multiple claims)
            # so if something changes there it probably needs to be changed here
            if is_employer and current_user and current_user.employers:
                if employer_id:
                    employers_list = (
                        db_session.query(Employer).filter(Employer.employer_id == employer_id).all()
                    )
                else:
                    employers_list = list(current_user.employers)

                employer_ids_list = [
                    e.employer_id
                    for e in employers_list
                    if sanitize_fein(e.employer_fein or "") not in CLAIMS_DASHBOARD_BLOCKED_FEINS
                    and current_user.verified_employer(e)
                ]

                query.add_employer_ids_filter(employer_ids_list)
            else:
                query.add_user_owns_claim_filter(current_user)

            query.add_managed_requirements_filter()
            if len(absence_statuses):
                # Log the values from the query params rather than the enum groups they
                # might equate to, since what is sent into the API will be more familiar
                # to New Relic users since it aligns closer to what Portal users see
                log_attributes.update(
                    {"filter.absence_statuses": ", ".join(sorted(absence_statuses))}
                )

                query.add_absence_status_filter(absence_statuses)

            if search_string:
                search_string = search_string.strip()
                query.add_search_filter(search_string)

            query.add_order_by(pagination_context)

            page = query.get_paginated_results(pagination_context)

    logger.info(
        "get_claims success",
        extra={
            "is_employer": str(is_employer),
            "pagination.order_by": pagination_context.order_by,
            "pagination.order_direction": pagination_context.order_direction,
            "pagination.page_offset": pagination_context.page_offset,
            "pagination.total_pages": page.total_pages,
            "pagination.total_records": page.total_records,
            "filter.search_string": search_string,
            **log_attributes,
        },
    )

    return response_util.paginated_success_response(
        message="Successfully retrieved claims",
        serializer=ClaimResponse(),
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


def handle_managed_requirements(
    db_session: Session,
    claim: Optional[Claim],
    managed_requirements: List[ManagedRequirementDetails],
    log_attributes: dict,
) -> None:
    if claim is None:
        return
    for mr in managed_requirements:
        db_mr = get_managed_requirement_by_fineos_managed_requirement_id(
            mr.managedReqId, db_session
        )
        if (
            db_mr
            and db_mr.managed_requirement_type_id
            == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id
        ):
            update_managed_requirement_from_fineos(db_session, mr, db_mr, log_attributes)
        elif not db_mr:
            create_managed_requirement_from_fineos(db_session, claim.claim_id, mr, log_attributes)

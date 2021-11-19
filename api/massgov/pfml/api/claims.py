import base64
from typing import Dict, List, Optional, Set, Union
from uuid import UUID

import connexion
import flask
import newrelic.agent
from sqlalchemy.orm.session import Session
from sqlalchemy_utils import escape_like
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.claim_rules as claim_rules
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.authorization.flask import READ, can, requires
from massgov.pfml.api.exceptions import ClaimWithdrawn, ObjectNotFound
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.claims.responses import ClaimResponse
from massgov.pfml.api.services.administrator_fineos_actions import (
    awaiting_leave_info,
    complete_claim_review,
    create_eform,
    download_document_as_leave_admin,
    get_claim_as_leave_admin,
    get_documents_as_leave_admin,
)
from massgov.pfml.api.services.claims import ClaimWithdrawnError, get_claim_detail
from massgov.pfml.api.services.managed_requirements import update_employer_confirmation_requirements
from massgov.pfml.api.util.claims import user_has_access_to_claim
from massgov.pfml.api.util.response import error_response
from massgov.pfml.api.validation.exceptions import (
    ContainsV1AndV2Eforms,
    IssueType,
    ValidationErrorDetail,
)
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    Employer,
    ManagedRequirementType,
    User,
    UserLeaveAdministrator,
)
from massgov.pfml.db.queries.absence_periods import upsert_absence_period_from_fineos_period
from massgov.pfml.db.queries.get_claims_query import ActionRequiredStatusFilter, GetClaimsQuery
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
    update_managed_requirement_from_fineos,
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
from massgov.pfml.util.logging.claims import (
    get_claim_log_attributes,
    get_claim_review_log_attributes,
    log_get_claim_metrics,
)
from massgov.pfml.util.logging.employers import get_employer_log_attributes
from massgov.pfml.util.logging.managed_requirements import (
    get_managed_requirements_update_log_attributes,
)
from massgov.pfml.util.paginate.paginator import PaginationAPIContext
from massgov.pfml.util.sqlalchemy import get_or_404

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


def get_user() -> User:
    current_user = app.current_user()
    if current_user is None:
        raise Unauthorized()
    return current_user


def get_current_user_leave_admin_record(fineos_absence_id: str) -> UserLeaveAdministrator:
    with app.db_session() as db_session:
        associated_employer_id: Optional[UUID] = None

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
                error_type=IssueType.unauthorized_leave_admin,
            )

        if user_leave_admin.fineos_web_id is None:
            raise VerificationRequired(
                user_leave_admin, "User has no leave administrator FINEOS ID"
            )

        if not user_leave_admin.verified:
            raise VerificationRequired(user_leave_admin, "User is not Verified")

        return user_leave_admin


@requires(READ, "EMPLOYER_API")
def employer_update_claim_review(fineos_absence_id: str) -> flask.Response:
    current_user = get_user()
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

    # TODO (PORTAL-1116): This condition can be removed. It's never reached because
    # get_current_user_leave_admin_record does the same check, and raises an
    # `VerificationRequired` exception if its met.
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
            (
                claim_review_response,
                managed_requirements,
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

        if claim_from_db:
            sync_absence_periods(
                db_session, claim_from_db, absence_period_decisions, log_attributes
            )

        try:
            handle_managed_requirements(
                db_session, claim_from_db, managed_requirements, log_attributes,
            )
        except Exception as error:  # catch all exception handler
            db_session.rollback()
            logger.error(
                "Failed to handle the claim's managed requirements in employer claim review call",
                extra=log_attributes,
                exc_info=error,
            )
        logger.info(
            "employer_get_claim_review success", extra=log_attributes,
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
        error = error_response(
            Forbidden, "Employers are not allowed to access claimant claim info", errors=[],
        )
        return error.to_api_response()

    claim = get_claim_from_db(fineos_absence_id)

    if claim is None:
        logger.warning(
            "get_claim failure - Claim not in PFML database.",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = error_response(NotFound, "Claim not in PFML database.", errors=[])
        return error.to_api_response()

    if not user_has_access_to_claim(claim, app.current_user()):
        logger.warning(
            "get_claim failure - User does not have access to claim.",
            extra={"absence_case_id": fineos_absence_id},
        )
        error = error_response(Forbidden, "User does not have access to claim.", errors=[])
        return error.to_api_response()

    try:
        detailed_claim = get_claim_detail(claim)
    except ClaimWithdrawnError:
        logger.warning(
            "get_claim failure - Claim has been withdrawn. Unable to display claim status.",
            extra={"absence_id": claim.fineos_absence_id},
        )
        return ClaimWithdrawn().to_api_response()
    except Exception as ex:
        logger.warning(
            f"get_claim failure - {str(ex)}", extra={"absence_id": claim.fineos_absence_id}
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


def get_claims() -> flask.Response:
    current_user = app.current_user()
    employer_id = flask.request.args.get("employer_id")
    search_string = flask.request.args.get("search", type=str)
    absence_statuses = parse_filterable_absence_statuses(flask.request.args.get("claim_status"))
    is_employer = can(READ, "EMPLOYER_API")
    log_attributes = {}
    if current_user:
        log_attributes.update(get_employer_log_attributes(current_user))

    with PaginationAPIContext(Claim, request=flask.request) as pagination_context:
        with app.db_session() as db_session:
            query = GetClaimsQuery(db_session)

            # The logic here is similar to that in user_has_access_to_claim (except it is applied to multiple claims)
            # so if something changes there it probably needs to be changed here
            if is_employer and current_user and current_user.employers:
                filters = [
                    Employer.employer_fein.notin_(CLAIMS_DASHBOARD_BLOCKED_FEINS),
                    UserLeaveAdministrator.verification_id.isnot(None),
                    User.user_id == current_user.user_id,
                ]
                if employer_id:
                    filters.append(Employer.employer_id == employer_id)

                employer_ids_list = (
                    db_session.query(Employer.employer_id)
                    .join(
                        UserLeaveAdministrator,
                        Employer.employer_id == UserLeaveAdministrator.employer_id,
                    )
                    .join(User, User.user_id == UserLeaveAdministrator.user_id)
                    .filter(*filters)
                    .all()
                )

                # Get list of employers with non-blocked feins with left join for verified
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
                query.add_search_filter(
                    escape_like(search_string)
                )  # escape user input search string

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
        model=ClaimResponse,
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
            update_managed_requirement_from_fineos(db_session, mr, db_mr, log_attributes.copy())
        elif not db_mr:
            create_managed_requirement_from_fineos(
                db_session, claim.claim_id, mr, log_attributes.copy()
            )


def sync_absence_periods(
    db_session: Session, claim: Claim, decisions: PeriodDecisions, log_attributes: dict
) -> None:
    if not decisions.decisions:
        return
    try:
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
    except Exception as e:
        db_session.rollback()
        message = "Failed to update fineos absence periods"
        logger.exception(
            message, extra={"fineos_absence_id": claim.fineos_absence_id, **log_attributes},
        )
        newrelic.agent.record_exception(
            exc=e,
            value=message,
            params={"fineos_absence_id": claim.fineos_absence_id, **log_attributes},
        )

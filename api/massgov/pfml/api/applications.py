import base64
from typing import List, Optional
from uuid import UUID, uuid4

import connexion
from flask import Response, request
from pydantic import ValidationError
from sqlalchemy import asc, desc
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, ServiceUnavailable

import massgov.pfml.api.app as app
import massgov.pfml.api.services.applications as applications_service
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.application_rules as application_rules
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.authorization.flask import CREATE, EDIT, READ, ensure
from massgov.pfml.api.claims import get_claim_from_db
from massgov.pfml.api.exceptions import ClaimWithdrawn
from massgov.pfml.api.models.applications.common import DocumentResponse
from massgov.pfml.api.models.applications.requests import (
    ApplicationImportRequestBody,
    ApplicationRequestBody,
    DocumentRequestBody,
    PaymentPreferenceRequestBody,
    TaxWithholdingPreferenceRequestBody,
)
from massgov.pfml.api.models.applications.responses import ApplicationResponse
from massgov.pfml.api.models.common import OrderDirection
from massgov.pfml.api.services.applications import (
    get_application_split,
    get_document_by_id,
    split_application_by_date,
)
from massgov.pfml.api.services.document_upload import upload_document_to_fineos
from massgov.pfml.api.services.fineos_actions import (
    complete_intake,
    create_other_leaves_and_other_incomes_eforms,
    download_document,
    get_documents,
    mark_documents_as_received,
    register_employee,
    send_tax_withholding_preference,
    send_to_fineos,
    submit_payment_preference,
)
from massgov.pfml.api.util.paginate.paginator import PaginationAPIContext, page_for_api_context
from massgov.pfml.api.validation.exceptions import (
    IssueRule,
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.applications import Application, DocumentType, LeaveReason
from massgov.pfml.db.models.employees import User
from massgov.pfml.fineos.exception import (
    FINEOSClientError,
    FINEOSEntityNotFound,
    FINEOSFatalUnavailable,
)
from massgov.pfml.fineos.models.customer_api import Base64EncodedFileData
from massgov.pfml.util.aws import cognito
from massgov.pfml.util.logging.applications import get_application_log_attributes
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)

UPLOAD_SIZE_CONSTRAINT = 4500000  # bytes

FILE_TOO_LARGE_MSG = "File is too large."
FILE_SIZE_VALIDATION_ERROR = ValidationErrorDetail(
    message=FILE_TOO_LARGE_MSG, type=IssueType.file_size, field="file"
)

LEAVE_REASON_TO_DOCUMENT_TYPE_MAPPING = {
    LeaveReason.CHILD_BONDING.leave_reason_description: DocumentType.CHILD_BONDING_EVIDENCE_FORM,
    LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description: DocumentType.OWN_SERIOUS_HEALTH_CONDITION_FORM,
    LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_description: DocumentType.CARE_FOR_A_FAMILY_MEMBER_FORM,
    LeaveReason.PREGNANCY_MATERNITY.leave_reason_description: DocumentType.PREGNANCY_MATERNITY_FORM,
}


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)
        ensure(READ, existing_application)
        application_response = ApplicationResponse.from_orm(existing_application)

        # Only run these validations if the application hasn't already been submitted. This
        # prevents warnings from showing in the response for rules added after the application
        # was submitted, which would cause a Portal user's Checklist to revert back to showing
        # steps as incomplete, and they wouldn't be able to fix this.
        issues: List[ValidationErrorDetail] = []
        if not existing_application.submitted_time:
            issues, employer_issue = application_rules.get_all_application_issues(
                db_session, existing_application
            )
            if employer_issue:
                issues.append(employer_issue)

    return response_util.success_response(
        message="Successfully retrieved application",
        data=application_response.dict(),
        warnings=issues,
    ).to_api_response()


def applications_get():
    user = app.current_user()
    with PaginationAPIContext(Application, request=request) as pagination_context:
        with app.db_session() as db_session:
            is_asc = pagination_context.order_direction == OrderDirection.asc.value
            sort_fn = asc if is_asc else desc
            application_query = (
                db_session.query(Application)
                .filter(Application.user_id == user.user_id)
                .order_by(sort_fn(pagination_context.order_key))
            )
            page = page_for_api_context(pagination_context, application_query)

    return response_util.paginated_success_response(
        message="Successfully retrieved applications",
        model=ApplicationResponse,
        page=page,
        context=pagination_context,
        status_code=200,
    ).to_api_response()


def application_imports():
    application = Application(application_id=uuid4())
    ensure(CREATE, application)

    user = app.current_user()
    application.user = user

    body = connexion.request.json
    application_import_request = ApplicationImportRequestBody.parse_obj(body)

    logger.info(
        "beginning import for application",
        extra={
            "absence_case_id": application_import_request.absence_case_id,
            "application_id": application.application_id,
        },
    )

    is_cognito_user_mfa_verified = cognito.is_mfa_phone_verified(application.user.email_address, app.get_app_config().cognito_user_pool_id)  # type: ignore
    if not is_cognito_user_mfa_verified:
        logger.info(
            "application import failure - mfa not verified",
            extra={
                "absence_case_id": application_import_request.absence_case_id,
                "user_id": application.user.user_id,
            },
        )
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    field="mfa_delivery_preference",
                    type=IssueType.required,
                    message="User has not opted into MFA delivery preferences",
                )
            ]
        )

    claim = get_claim_from_db(application_import_request.absence_case_id)

    application_rules.validate_application_import_request_for_claim(
        application_import_request, claim
    )
    assert application_import_request.absence_case_id is not None

    with app.db_session() as db_session:
        applications_service.claim_is_valid_for_application_import(db_session, user, claim)

        db_session.add(application)
        fineos = massgov.pfml.fineos.create_client()
        # we have already check that the claim is not None in
        # claim_is_valid_for_application_import
        applications_service.set_application_fields_from_db_claim(
            fineos, application, claim, db_session  # type: ignore
        )
        fineos_web_id = register_employee(
            fineos, claim.employee_tax_identifier, application.employer_fein, db_session  # type: ignore
        )
        applications_service.set_application_absence_and_leave_period(
            fineos, fineos_web_id, application, application_import_request.absence_case_id
        )
        applications_service.set_customer_detail_fields(
            fineos, fineos_web_id, application, db_session
        )
        applications_service.set_customer_contact_detail_fields(
            fineos, fineos_web_id, application, db_session
        )
        applications_service.set_employment_status_and_occupations(
            fineos, fineos_web_id, application
        )
        applications_service.set_payment_preference_fields(
            fineos, fineos_web_id, application, db_session
        )
        eform_cache: applications_service.EFORM_CACHE = {}
        eform_summaries = fineos.customer_get_eform_summary(
            fineos_web_id, application_import_request.absence_case_id
        )
        applications_service.set_other_leaves(
            fineos,
            fineos_web_id,
            application,
            db_session,
            application_import_request.absence_case_id,
            eform_summaries,
            eform_cache,
        )
        applications_service.set_employer_benefits_from_fineos(
            fineos,
            fineos_web_id,
            application,
            db_session,
            application_import_request.absence_case_id,
            eform_summaries,
            eform_cache,
        )
        applications_service.set_other_incomes_from_fineos(
            fineos,
            fineos_web_id,
            application,
            db_session,
            application_import_request.absence_case_id,
            eform_summaries,
            eform_cache,
        )
        db_session.refresh(application)
        db_session.commit()

    log_attributes = get_application_log_attributes(application)
    log_attributes["num_applications_on_account"] = str(
        db_session.query(Application).filter(Application.user_id == user.user_id).count()
    )
    if claim:
        time_elapsed = datetime_util.utcnow() - claim.created_at
        minutes_elapsed = time_elapsed.total_seconds() / 60
        log_attributes["minutes_between_claim_creation_and_import"] = str(minutes_elapsed)
    logger.info("applications_import success", extra=log_attributes)

    return response_util.success_response(
        message="Successfully imported application",
        data=ApplicationResponse.from_orm(application).dict(exclude_none=True),
        status_code=201,
    ).to_api_response()


def applications_start():
    application = Application()

    ensure(CREATE, application)

    application.user = app.current_user()

    with app.db_session() as db_session:
        db_session.add(application)

    log_attributes = get_application_log_attributes(application)
    logger.info("applications_start success", extra=log_attributes)

    return response_util.success_response(
        message="Successfully created application",
        data=ApplicationResponse.from_orm(application).dict(),
        status_code=201,
    ).to_api_response()


def applications_update(application_id):
    body = connexion.request.json
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

    ensure(EDIT, existing_application)

    # The presence of a submitted_time indicates that the application has already been submitted.
    if existing_application.submitted_time:
        log_attributes = get_application_log_attributes(existing_application)
        logger.info(
            "applications_update failure - application already submitted", extra=log_attributes
        )
        message = "Application {} could not be updated. Application already submitted on {}".format(
            existing_application.application_id, existing_application.submitted_time.strftime("%x")
        )
        return response_util.error_response(
            status_code=Forbidden,
            message=message,
            errors=[ValidationErrorDetail(type=IssueType.exists, field="claim", message=message)],
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        ).to_api_response()

    if existing_application.nbr_of_retries >= app.get_config().limit_ssn_fein_max_attempts:
        message = "Application {} could not be updated. Maximum number of attempts reached.".format(
            existing_application.application_id
        )
        return response_util.error_response(
            status_code=BadRequest,
            message=message,
            errors=[
                ValidationErrorDetail(
                    type=IssueType.maximum,
                    rule=IssueRule.max_ssn_fein_update_attempts,
                    message=message,
                )
            ],
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        ).to_api_response()

    updated_body = applications_service.remove_masked_fields_from_request(
        body, existing_application
    )

    application_request = ApplicationRequestBody.parse_obj(updated_body)

    previous_fein = existing_application.employer_fein
    previous_tax_identifier = None
    if existing_application.tax_identifier:
        previous_tax_identifier = existing_application.tax_identifier.tax_identifier

    with app.db_session() as db_session:
        applications_service.update_from_request(
            db_session, application_request, existing_application
        )

        issues, employer_issue = application_rules.get_all_application_issues(
            db_session, existing_application
        )
        if employer_issue:
            issues.append(employer_issue)

    # Set log attributes to the updated attributes rather than the previous attributes
    # Also, calling get_application_log_attributes too early causes the application not to update properly for some reason
    # See https://github.com/EOLWD/pfml/pull/2601
    log_attributes = get_application_log_attributes(existing_application)

    if employer_issue:
        # If either SSN or FEIN have been recently updated
        # and an "employer_issue" occurred, it counts as an attempt
        if (
            application_request.tax_identifier is not None
            and previous_tax_identifier != application_request.tax_identifier
        ) or (
            application_request.employer_fein is not None
            and previous_fein != application_request.employer_fein
        ):
            existing_application.nbr_of_retries += 1
            with app.db_session() as db_session:
                db_session.add(existing_application)
                db_session.commit()
                db_session.refresh(existing_application)
            logger.info("User attempted new combination of SSN/FEIN", extra=log_attributes)

    logger.info("applications_update success", extra=log_attributes)

    return response_util.success_response(
        message="Application updated without errors.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        warnings=issues,
    ).to_api_response()


def get_fineos_submit_issues_response(err, existing_application):
    if isinstance(err, FINEOSEntityNotFound):
        return response_util.error_response(
            status_code=BadRequest,
            message="Application {} could not be submitted".format(
                existing_application.application_id
            ),
            errors=[
                ValidationErrorDetail(
                    IssueType.fineos_case_creation_issues, "register_employee did not find a match"
                )
            ],
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        ).to_api_response()

    elif isinstance(err, FINEOSFatalUnavailable):
        # These errors are usually caught in our error handler and raised with a "fineos_client" issue type.
        # Once the Portal behavior is changed to handle that type, we can remove this special case.
        return response_util.error_response(
            status_code=ServiceUnavailable,
            message="Application {} could not be submitted, try again later".format(
                existing_application.application_id
            ),
            errors=[
                ValidationErrorDetail(
                    IssueType.fineos_case_error,
                    "Unexpected error encountered when submitting to the Claims Processing System",
                )
            ],
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        ).to_api_response()
    else:
        # We don't expect any other errors like 500s. Raise an alarm bell.
        raise err


# TODO: move to service layer
def submit_application_to_fineos(
    application: Application, db_session: db.Session, current_user: User
) -> None:
    log_attributes = get_application_log_attributes(application)
    # Only send to fineos if fineos_absence_id isn't set on the claim. If it is set,
    # assume that just complete_intake needs to be reattempted.
    if not application.claim:
        try:
            send_to_fineos(application, db_session, current_user)
        # TODO (CP-2350): improve handling of FINEOS validation rules
        except ValidationError as e:
            logger.warning(
                "applications_submit failure - application failed FINEOS validation",
                extra=log_attributes,
            )
            raise e

        except Exception as e:
            logger.warning(
                "applications_submit failure - failure sending application to claims processing system",
                extra=log_attributes,
                exc_info=True,
            )

            raise e

        logger.info(
            "applications_submit - application sent to claims processing system",
            extra=log_attributes,
        )

    try:
        complete_intake(application, db_session)
        application.submitted_time = datetime_util.utcnow()
        # Update log attributes now that submitted_time is set
        log_attributes = get_application_log_attributes(application)
        db_session.add(application)
        logger.info(
            "applications_submit - application complete intake success", extra=log_attributes
        )
    except Exception as e:
        logger.warning(
            "applications_submit failure - application complete intake failure",
            extra=log_attributes,
            exc_info=True,
        )

        raise e

    # Send previous leaves, employer benefits, and other incomes as eforms to FINEOS
    create_other_leaves_and_other_incomes_eforms(application, db_session)


def applications_submit(application_id):
    split_claims_across_by_enabled = (
        connexion.request.headers.get("X-FF-Split-Claims-Across-BY") == "true"
    )
    with app.db_session() as db_session:
        current_user = app.current_user()
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        issues, employer_issue = application_rules.get_all_application_issues(
            db_session, existing_application
        )

        if employer_issue and not existing_application.additional_user_not_found_info:
            issues.append(employer_issue)

        if issues:
            logger.info(
                "applications_submit failure - application failed validation", extra=log_attributes
            )
            return response_util.error_response(
                status_code=BadRequest,
                message="Application is not valid for submission",
                errors=issues,
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

        if app.get_config().enable_application_fraud_check:
            # Meta issues are problems with the application beyond just the model itself
            # Includes checks for a potentially fraudulent application.
            meta_issues = application_rules.validate_application_state(
                existing_application, db_session
            )
            if meta_issues:
                logger.info(
                    "applications_submit failure - application flagged for fraud",
                    extra=log_attributes,
                )
                return response_util.error_response(
                    status_code=Forbidden,
                    message="Application unable to be submitted by current user",
                    errors=meta_issues,
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                ).to_api_response()

        # The presence of a submitted_time indicates that the application has already been submitted.
        if existing_application.submitted_time:
            logger.info(
                "applications_submit failure - application already submitted", extra=log_attributes
            )
            message = (
                "Application {} could not be submitted. Application already submitted on {}".format(
                    existing_application.application_id,
                    existing_application.submitted_time.strftime("%x"),
                )
            )
            return response_util.error_response(
                status_code=Forbidden,
                message=message,
                errors=[
                    ValidationErrorDetail(type=IssueType.exists, field="claim", message=message)
                ],
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

        application_split = get_application_split(existing_application, db_session)
        logger.info(
            f"application would have been split: {application_split != None}",
            extra={
                **log_attributes,
                **{"split_claims_across_by_enabled": split_claims_across_by_enabled},
            },
        )

        if not employer_issue and application_split is not None and split_claims_across_by_enabled:
            application_before_split, application_after_split = split_application_by_date(
                db_session, existing_application, application_split.crossed_benefit_year.end_date
            )
            logger.info(
                "successfully split application",
                extra={
                    **log_attributes,
                    **application_split.__dict__,
                    **{"split_claims_across_by_enabled": split_claims_across_by_enabled},
                },
            )
            try:
                submit_application_to_fineos(application_before_split, db_session, current_user)
            except Exception as e:
                if isinstance(e, FINEOSClientError):
                    return get_fineos_submit_issues_response(e, existing_application)
                raise e
            try:
                split_application_log_attributes = get_application_log_attributes(
                    application_after_split
                )
                split_application_issues = application_rules.get_application_submit_issues(
                    application_after_split
                )
                if split_application_issues:
                    logger.info(
                        "split_application was not submitted - split application failed validation",
                        extra={
                            **split_application_log_attributes,
                            **application_split.__dict__,
                            **{"split_claims_across_by_enabled": split_claims_across_by_enabled},
                        },
                    )
                    logger.info(
                        "split_application was not submitted - split application failed validation",
                        extra=split_application_log_attributes,
                    )
                else:
                    submit_application_to_fineos(
                        application_after_split,
                        db_session,
                        current_user,
                    )
            except Exception as e:
                if isinstance(e, FINEOSClientError):
                    return get_fineos_submit_issues_response(e, existing_application)
                raise e
        else:
            if error_response := attempt_application_submission(
                db_session,
                current_user,
                existing_application,
                bool(employer_issue),
            ):
                return error_response

    logger.info("applications_submit success", extra=log_attributes)
    db_session.refresh(existing_application)
    return response_util.success_response(
        message="Application {} submitted without errors".format(
            existing_application.application_id
        ),
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        status_code=201,
    ).to_api_response()


def attempt_application_submission(
    db_session: db.Session,
    current_user: User,
    application: Application,
    has_employer_issue: bool,
) -> Optional[Response]:
    try:
        if has_employer_issue:
            return upload_additional_user_not_found_info_to_fineos(db_session, application)
        else:
            return submit_application_to_fineos(application, db_session, current_user)
    except Exception as e:
        if isinstance(e, FINEOSClientError):
            return get_fineos_submit_issues_response(e, application)
        raise e


def upload_additional_user_not_found_info_to_fineos(
    db_session: db.Session, application: Application
) -> None:
    return None


def applications_complete(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        issues = application_rules.get_application_complete_issues(existing_application, db_session)
        if issues:
            logger.info(
                "applications_complete failure - application failed validation",
                extra=log_attributes,
            )
            return response_util.error_response(
                status_code=BadRequest,
                message="Application is not valid for completion",
                errors=issues,
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

        try:
            mark_documents_as_received(existing_application, db_session)
        except Exception:
            logger.warning(
                "applications_complete failure - application documents failed to be marked as received",
                extra=log_attributes,
                exc_info=True,
            )
            raise

        existing_application.completed_time = datetime_util.utcnow()
        # Update log attributes now that completed_time is set
        log_attributes = get_application_log_attributes(existing_application)

    logger.info(
        "applications_complete - application documents marked as received", extra=log_attributes
    )

    logger.info("applications_complete success", extra=log_attributes)

    return response_util.success_response(
        message="Application {} completed without errors".format(
            existing_application.application_id
        ),
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        status_code=200,
    ).to_api_response()


def document_upload(application_id, body, file):
    with app.db_session() as db_session:
        # Get the referenced application or return 404
        application = get_or_404(db_session, Application, application_id)

    # Parse the document details from the form body
    document_details: DocumentRequestBody = DocumentRequestBody.parse_obj(body)

    try:
        response = upload_document_to_fineos(application, document_details, file)
    except ClaimWithdrawn as err:
        return err.to_api_response()

    return response


def documents_get(application_id):
    with app.db_session() as db_session:
        # Get the referenced application or return 404
        existing_application = get_or_404(db_session, Application, application_id)

        # Check if user can read application
        ensure(READ, existing_application)

        # Check if application has been submitted to fineos
        if not existing_application.claim:
            return response_util.success_response(
                message="Successfully retrieved documents", data=[], status_code=200
            ).to_api_response()

        documents = get_documents(existing_application, db_session)

        documents_list = [doc.dict() for doc in documents]

        return response_util.success_response(
            message="Successfully retrieved documents", data=documents_list, status_code=200
        ).to_api_response()


def document_download(application_id: UUID, document_id: str) -> Response:
    with app.db_session() as db_session:
        # Get the referenced application or return 404
        existing_application = get_or_404(db_session, Application, application_id)

        # Check if user can read application
        ensure(READ, existing_application)

        document = get_document_by_id(db_session, document_id, existing_application)
        if not document:
            raise NotFound(description=f"Could not find Document with ID {document_id}")

        ensure(READ, document)
        if isinstance(document, DocumentResponse):
            document_type = document.document_type
        else:
            document_type = None
        document_data: Base64EncodedFileData = download_document(
            existing_application, document_id, db_session, document_type
        )
        file_bytes = base64.b64decode(document_data.base64EncodedFileContents.encode("ascii"))

        content_type = document_data.contentType or "application/octet-stream"

        return Response(
            file_bytes,
            content_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={document_data.fileName}"},
        )


def payment_preference_submit(application_id: UUID) -> Response:
    body = connexion.request.json

    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        updated_body = applications_service.remove_masked_fields_from_request(
            body, existing_application
        )

        payment_pref_request = PaymentPreferenceRequestBody.parse_obj(updated_body)
        log_attributes["skip_fineos"] = str(payment_pref_request.skip_fineos)

        if not payment_pref_request.payment_preference:
            logger.info(
                "payment_preference_submit failure - payment preference is null",
                extra=log_attributes,
            )
            return response_util.error_response(
                status_code=BadRequest,
                message="Payment Preference cannot be null",
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                errors=[],
            ).to_api_response()

        if not existing_application.has_submitted_payment_preference:
            applications_service.add_or_update_payment_preference(
                db_session, payment_pref_request.payment_preference, existing_application
            )

            db_session.add(existing_application)
            db_session.commit()
            db_session.refresh(existing_application)

            issues = application_rules.get_payments_issues(existing_application)
            if issues:
                logger.info(
                    "payment_preference_submit failure - payment preference failed validation",
                    extra=log_attributes,
                )
                return response_util.error_response(
                    status_code=BadRequest,
                    message="Payment info is not valid for submission",
                    errors=issues,
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                ).to_api_response()

            if existing_application.payment_preference:
                if not payment_pref_request.skip_fineos:
                    try:
                        submit_payment_preference(existing_application, db_session)
                    except Exception:
                        logger.warning(
                            "payment_preference_submit failure - failure submitting payment preference to claims processing system",
                            extra=log_attributes,
                            exc_info=True,
                        )
                        raise

                    existing_application.has_submitted_payment_preference = True
                    db_session.add(existing_application)
                    db_session.commit()
                    db_session.refresh(existing_application)

                logger.info("payment_preference_submit success", extra=log_attributes)

                issues, employer_issue = application_rules.get_all_application_issues(
                    db_session, existing_application
                )
                if employer_issue:
                    issues.append(employer_issue)

                return response_util.success_response(
                    message="Payment Preference for application {} submitted without errors".format(
                        existing_application.application_id
                    ),
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                    status_code=201,
                    warnings=issues,
                ).to_api_response()
            else:
                logger.warning(
                    "payment_preference_submit failure - failure saving payment preference to database",
                    extra=log_attributes,
                )
                return response_util.error_response(
                    status_code=ServiceUnavailable,
                    message="Payment Preference failed to save. Please try again.",
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                    errors=[],
                ).to_api_response()

        logger.info(
            "payment_preference_submit failure - payment preference already submitted",
            extra=log_attributes,
        )
        message = (
            "Application {} could not be updated. Payment preference already submitted".format(
                existing_application.application_id
            )
        )
        return response_util.error_response(
            status_code=Forbidden,
            message=message,
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            errors=[
                ValidationErrorDetail(
                    type=IssueType.exists,
                    field="payment_preference.payment_method",
                    message=message,
                )
            ],
        ).to_api_response()


def validate_tax_withholding_request(db_session, application_id, tax_preference_body):
    """
    Helper to handle validation for tax withholding requests
        1. Must be an existing application
        2. Requesting user must have authorization to edit application
        3. Preference must not already be set
    """
    existing_application = get_or_404(db_session, Application, application_id)
    ensure(EDIT, existing_application)

    if not isinstance(tax_preference_body.is_withholding_tax, bool):
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    type=IssueType.required,
                    message="Tax withholding preference is required",
                    field="is_withholding_tax",
                )
            ]
        )

    allow_multiple_tax_withholding_updates = (
        tax_preference_body.skip_fineos if not existing_application.submitted_time else False
    )

    # only allows multiple updates to tax withholding
    # if we're in the additional user not found flow
    # and the claimant hasn't submitted part 1 yet
    if (
        not allow_multiple_tax_withholding_updates
        and existing_application.is_withholding_tax is not None
    ):
        # otherwise, block further updates to tax withholding
        logger.info(
            "submit_tax_withholding_preference failure - preference already set",
            extra=get_application_log_attributes(existing_application),
        )
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    type=IssueType.duplicate,
                    message="Tax withholding preference is already set",
                    field="is_withholding_tax",
                )
            ]
        )

    return existing_application


def save_tax_preference(db_session, existing_application, tax_preference_body):
    existing_application.is_withholding_tax = tax_preference_body.is_withholding_tax
    db_session.commit()
    db_session.refresh(existing_application)


def send_tax_selection_to_fineos(existing_application, tax_preference_body):
    try:
        send_tax_withholding_preference(
            existing_application, tax_preference_body.is_withholding_tax
        )
    except Exception:
        logger.warning(
            "submit_tax_withholding_preference failure - failure submitting tax withholding preference to claims processing system",
            extra=get_application_log_attributes(existing_application),
            exc_info=True,
        )
        raise


def submit_tax_withholding_preference(application_id: UUID) -> Response:
    body = connexion.request.json
    tax_preference_body = TaxWithholdingPreferenceRequestBody.parse_obj(body)

    with app.db_session() as db_session:
        existing_application = validate_tax_withholding_request(
            db_session, application_id, tax_preference_body
        )
        if not tax_preference_body.skip_fineos:
            send_tax_selection_to_fineos(existing_application, tax_preference_body)
        save_tax_preference(db_session, existing_application, tax_preference_body)

        log_attributes = get_application_log_attributes(existing_application)
        log_attributes["skip_fineos"] = str(tax_preference_body.skip_fineos)

        logger.info(
            "tax_withholding_preference_submit success",
            extra=log_attributes,
        )

        issues, employer_issue = application_rules.get_all_application_issues(
            db_session, existing_application
        )
        if employer_issue:
            issues.append(employer_issue)

        return response_util.success_response(
            message="Tax Withholding Preference for application {} submitted without errors".format(
                existing_application.application_id
            ),
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            warnings=issues,
            status_code=201,
        ).to_api_response()

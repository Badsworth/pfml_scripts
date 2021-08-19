import base64

import connexion
import puremagic
from flask import Response
from puremagic import PureError
from pydantic import ValidationError
from sqlalchemy import desc
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, ServiceUnavailable, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.services.applications as applications_service
import massgov.pfml.api.util.response as response_util
import massgov.pfml.api.validation.application_rules as application_rules
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, EDIT, READ, can, ensure
from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.api.models.applications.common import DocumentType as IoDocumentTypes
from massgov.pfml.api.models.applications.requests import (
    ApplicationRequestBody,
    DocumentRequestBody,
    PaymentPreferenceRequestBody,
)
from massgov.pfml.api.models.applications.responses import ApplicationResponse, DocumentResponse
from massgov.pfml.api.services.applications import get_document_by_id
from massgov.pfml.api.services.fineos_actions import (
    complete_intake,
    create_other_leaves_and_other_incomes_eforms,
    download_document,
    get_documents,
    mark_documents_as_received,
    mark_single_document_as_received,
    send_to_fineos,
    submit_payment_preference,
    upload_document,
)
from massgov.pfml.api.validation.employment_validator import (
    get_contributing_employer_or_employee_issue,
)
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.applications import (
    Application,
    ContentType,
    Document,
    DocumentType,
    EmployerBenefit,
    LeaveReason,
    OtherIncome,
    PreviousLeave,
)
from massgov.pfml.fineos.exception import (
    FINEOSClientBadResponse,
    FINEOSClientError,
    FINEOSFatalUnavailable,
    FINEOSNotFound,
)
from massgov.pfml.util.logging.applications import get_application_log_attributes
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)

LEAVE_REASON_TO_DOCUMENT_TYPE_MAPPING = {
    LeaveReason.CHILD_BONDING.leave_reason_description: DocumentType.CHILD_BONDING_EVIDENCE_FORM,
    LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description: DocumentType.OWN_SERIOUS_HEALTH_CONDITION_FORM,
    LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_description: DocumentType.CARE_FOR_A_FAMILY_MEMBER_FORM,
}

ID_DOCS = [
    DocumentType.PASSPORT.document_type_description,
    DocumentType.DRIVERS_LICENSE_MASS.document_type_description,
    DocumentType.DRIVERS_LICENSE_OTHER_STATE.document_type_description,
    DocumentType.IDENTIFICATION_PROOF.document_type_description,
]


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(READ, existing_application)
        application_response = ApplicationResponse.from_orm(existing_application)

    issues = application_rules.get_application_issues(existing_application)

    return response_util.success_response(
        message="Successfully retrieved application",
        data=application_response.dict(),
        warnings=issues,
    ).to_api_response()


def applications_get():
    if user := app.current_user():
        user_id = user.user_id
    else:
        raise Unauthorized

    with app.db_session() as db_session:
        applications = (
            db_session.query(Application)
            .filter(Application.user_id == user_id)
            .order_by(desc(Application.start_time))
            .limit(50)  # Mitigate slow queries for end-to-end test user
            .all()
        )

        filtered_applications = filter(lambda a: can(READ, a), applications)

    applications_response = list(
        map(
            lambda application: ApplicationResponse.from_orm(application).dict(),
            filtered_applications,
        )
    )
    return response_util.success_response(
        message="Successfully retrieved applications", data=applications_response
    ).to_api_response()


def applications_start():
    application = Application()

    now = datetime_util.utcnow()
    application.start_time = now
    application.updated_time = now

    ensure(CREATE, application)

    # this should always be the case at this point, but the type for
    # current_user is still optional until we require authentication
    if user := app.current_user():
        application.user = user
    else:
        raise Unauthorized

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
        return response_util.error_response(
            status_code=Forbidden,
            message="Application {} could not be updated. Application already submitted on {}".format(
                existing_application.application_id,
                existing_application.submitted_time.strftime("%x"),
            ),
            errors=[],
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        ).to_api_response()

    updated_body = applications_service.remove_masked_fields_from_request(
        body, existing_application
    )

    application_request = ApplicationRequestBody.parse_obj(updated_body)

    with app.db_session() as db_session:
        applications_service.update_from_request(
            db_session, application_request, existing_application
        )

    issues = application_rules.get_application_issues(existing_application)
    employer_issue = get_contributing_employer_or_employee_issue(
        db_session, existing_application.employer_fein, existing_application.tax_identifier
    )

    if employer_issue:
        issues.append(employer_issue)

    # Set log attributes to the updated attributes rather than the previous attributes
    # Also, calling get_application_log_attributes too early causes the application not to update properly for some reason
    # See https://github.com/EOLWD/pfml/pull/2601
    log_attributes = get_application_log_attributes(existing_application)
    logger.info("applications_update success", extra=log_attributes)

    return response_util.success_response(
        message="Application updated without errors.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        warnings=issues,
    ).to_api_response()


def get_fineos_submit_issues_response(err, existing_application):
    if isinstance(err, FINEOSNotFound):
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


def applications_submit(application_id):
    with app.db_session() as db_session:
        current_user = app.current_user()
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        issues = application_rules.get_application_issues(existing_application)
        employer_issue = get_contributing_employer_or_employee_issue(
            db_session, existing_application.employer_fein, existing_application.tax_identifier
        )

        if employer_issue:
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
            return response_util.error_response(
                status_code=Forbidden,
                message="Application {} could not be submitted. Application already submitted on {}".format(
                    existing_application.application_id,
                    existing_application.submitted_time.strftime("%x"),
                ),
                errors=[],
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

        # Only send to fineos if fineos_absence_id isn't set on the claim. If it is set,
        # assume that just complete_intake needs to be reattempted.
        if not existing_application.claim:
            try:
                send_to_fineos(existing_application, db_session, current_user)
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

                if isinstance(e, FINEOSClientError):
                    return get_fineos_submit_issues_response(e, existing_application)

                raise e

            logger.info(
                "applications_submit - application sent to claims processing system",
                extra=log_attributes,
            )

        try:
            complete_intake(existing_application, db_session)
            existing_application.submitted_time = datetime_util.utcnow()
            # Update log attributes now that submitted_time is set
            log_attributes = get_application_log_attributes(existing_application)
            db_session.add(existing_application)
            logger.info(
                "applications_submit - application complete intake success", extra=log_attributes
            )
        except Exception as e:
            logger.warning(
                "applications_submit failure - application complete intake failure",
                extra=log_attributes,
                exc_info=True,
            )

            if not isinstance(e, FINEOSClientError):
                raise e

            return get_fineos_submit_issues_response(e, existing_application)

        # Send previous leaves, employer benefits, and other incomes as eforms to FINEOS
        create_other_leaves_and_other_incomes_eforms(existing_application, db_session)

        logger.info("applications_submit success", extra=log_attributes)

    return response_util.success_response(
        message="Application {} submitted without errors".format(
            existing_application.application_id
        ),
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        status_code=201,
    ).to_api_response()


def applications_complete(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        issues = application_rules.get_application_issues(existing_application)
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
        "applications_complete - application documents marked as received", extra=log_attributes,
    )

    logger.info("applications_complete success", extra=log_attributes)

    return response_util.success_response(
        message="Application {} completed without errors".format(
            existing_application.application_id
        ),
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        status_code=200,
    ).to_api_response()


def validate_content_type(content_type):
    allowed_content_types = [item.value for item in AllowedContentTypes]
    if content_type not in allowed_content_types:
        message = "Incorrect file type: {}".format(content_type)
        logger.warning(message)
        validation_error = ValidationErrorDetail(
            message=message,
            type=IssueType.file_type,
            rule=", ".join(allowed_content_types),
            field="file",
        )
        raise ValidationException(errors=[validation_error], message=message, data={})


# We need custom validation here since we get the content type from the uploaded file
def get_valid_content_type(file):
    """ Use pure magic library to identify file type, use file mimetype as backup"""
    try:
        validate_content_type(file.mimetype)
        content_type = puremagic.from_stream(file.stream, mime=True, filename=file.filename)
        validate_content_type(content_type)
        if content_type != file.mimetype:
            message = "Detected content type and mime type do not match. Detected: {}, mimeType: {}".format(
                content_type, file.mimetype
            )
            logger.warning(message)
            validation_error = ValidationErrorDetail(
                message=message,
                type=IssueType.file_type_mismatch,
                rule="Detected content type and mime type do not match.",
                field="file",
            )
            raise ValidationException(errors=[validation_error], message=message, data={})

        return content_type
    except (ValueError, PureError):
        # return the validated mime type in cases where pure magic can not detect the type
        return file.mimetype


def validate_file_name(file_name):
    """Validate the file name has an extension"""
    extension_index = file_name.rfind(".")
    if extension_index < 1:
        logger.warning("Missing extension on file name.")
        message = "Missing extension on file name: {}".format(file_name)
        validation_error = ValidationErrorDetail(
            message=message,
            type=IssueType.file_name_extension,
            rule="File name extension required.",
            field="file",
        )
        raise ValidationException(errors=[validation_error], message=message, data={})


def has_previous_state_managed_paid_leave(existing_application, db_session):
    # For now, if there are documents previously submitted for the application with the
    # STATE_MANAGED_PAID_LEAVE_CONFIRMATION document type, that document type must also
    # be used for subsequent documents uploaded to the application. If not, the document type
    # from the request should be used instead.
    existing_documents_with_old_doc_type = (
        db_session.query(Document)
        .filter(Document.application_id == existing_application.application_id)
        .filter(
            Document.document_type_id
            == DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_id
        )
    ).all()

    if len(existing_documents_with_old_doc_type) > 0:
        return True

    return False


def document_upload(application_id, body, file):

    with app.db_session() as db_session:
        # Get the referenced application or return 404
        existing_application = get_or_404(db_session, Application, application_id)

        # Check if user can edit application
        ensure(EDIT, existing_application)

        # Check if user can create a document associated with this application before making any API calls or
        # persisting the document to the database.
        document = Document()
        document.user_id = existing_application.user_id
        ensure(CREATE, document)

        # Parse the document details from the form body
        document_details: DocumentRequestBody = DocumentRequestBody.parse_obj(body)

        # Validate the file name and type
        content_type = ""
        try:
            if document_details.name:
                validate_file_name(document_details.name)
            validate_file_name(file.filename)
            content_type = get_valid_content_type(file)
        except ValidationException as ve:
            return response_util.error_response(
                status_code=BadRequest,
                message="File validation error.",
                errors=ve.errors,
                data=document_details.dict(),
            ).to_api_response()

        # Get additional file meta data
        file.seek(0)
        file_content = file.read()
        file_size = len(file_content)
        file_name = document_details.name or file.filename
        file_description = ""
        if document_details.description:
            file_description = document_details.description

        # To accomodate both State managed Paid Leave Confirmation and the new plan proof types, the front end will
        # use Certification Form when the feature flag for caring leave is active, but will otherwise use
        # State manage Paid Leave Confirmation. If the document type is Certification Form,
        # the API will map to the corresponding plan proof based on leave reason
        document_type = document_details.document_type.value

        if document_type == IoDocumentTypes.certification_form.value:
            if existing_application.pregnant_or_recent_birth:
                document_type = DocumentType.PREGNANCY_MATERNITY_FORM.document_type_description
            # For non-pregnancy leave reasons
            else:
                document_type = LEAVE_REASON_TO_DOCUMENT_TYPE_MAPPING[
                    existing_application.leave_reason.leave_reason_description
                ].document_type_description

        if document_type not in ID_DOCS:
            # Check for existing STATE_MANAGED_PAID_LEAVE_CONFIRMATION documents, and reuse the doc type if there are docs
            # Because existng claims where only part 1 has been submitted should continue using old doc type, submitted_time
            # rather than existing docs should be examined

            if has_previous_state_managed_paid_leave(existing_application, db_session) or (
                existing_application.submitted_time
                and existing_application.submitted_time
                < app.get_app_config().new_plan_proofs_active_at
            ):
                document_type = (
                    DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_description
                )

        log_attributes = {
            **get_application_log_attributes(existing_application),
            "document.file_size": file_size,
            "document.content_type": content_type,
            "document.document_type": document_type,
        }

        # Upload document to fineos
        try:
            fineos_document = upload_document(
                existing_application,
                document_type,
                file_content,
                file_name,
                content_type,
                file_description,
                db_session,
            ).dict()
            logger.info(
                "document_upload - document uploaded to claims processing system",
                extra=log_attributes,
            )
        except Exception as err:
            logger.warning(
                "document_upload failure - failure uploading document to claims processing system",
                extra=log_attributes,
                exc_info=True,
            )

            if isinstance(err, FINEOSClientBadResponse) and err.response_status == 422:
                message = "Issue encountered while attempting to upload the document."
                return response_util.error_response(
                    status_code=BadRequest,
                    message=message,
                    errors=[ValidationErrorDetail(type=IssueType.fineos_client, message=message)],
                    data=document_details.dict(),
                ).to_api_response()

            # Bubble any other issues up to the API error handlers
            raise

        # Insert a document metadata row
        document.application_id = existing_application.application_id
        now = datetime_util.utcnow()
        document.created_at = now
        document.updated_at = now
        document.document_type_id = DocumentType.get_id(document_type)
        document.content_type_id = ContentType.get_id(content_type)
        document.size_bytes = file_size
        document.fineos_id = fineos_document["documentId"]
        document.is_stored_in_s3 = False
        document.name = file_name
        document.description = file_description

        db_session.add(document)

        try:
            if document_details.mark_evidence_received:
                mark_single_document_as_received(existing_application, document, db_session)
                logger.info(
                    "document_upload - evidence marked as received", extra=log_attributes,
                )
        except Exception:
            logger.warning(
                "document_upload failure - failure marking evidence as received",
                extra=log_attributes,
                exc_info=True,
            )

            # We don't expect any errors here, raise an error if we get one.
            # FINEOS Unavailability errors will bubble up and be returned as 503
            # with a fineos_client issue type.
            #
            # Note that we expect the DB session to rollback here due to the raised exception,
            # so the document is not saved and the claimant has the opportunity to try again.
            # This behaviour will create multiple documents in FINEOS but will ensure that
            # the evidence can eventually be marked as received without manual intervention.
            raise

        db_session.commit()

        logger.info(
            "document_upload success", extra=log_attributes,
        )

        # Return response
        return response_util.success_response(
            message="Successfully uploaded document",
            data=DocumentResponse.from_orm(document).dict(),
            status_code=200,
        ).to_api_response()


def documents_get(application_id):
    with app.db_session() as db_session:
        # Get the referenced application or return 404
        existing_application = get_or_404(db_session, Application, application_id)

        # Check if user can read application
        ensure(READ, existing_application)

        # Check if application has been submitted to fineos
        if not existing_application.claim:
            return response_util.success_response(
                message="Successfully retrieved documents", data=[], status_code=200,
            ).to_api_response()

        documents = get_documents(existing_application, db_session)

        documents_list = [doc.dict() for doc in documents]

        return response_util.success_response(
            message="Successfully retrieved documents", data=documents_list, status_code=200,
        ).to_api_response()


def document_download(application_id: str, document_id: str) -> Response:
    with app.db_session() as db_session:
        # Get the referenced application or return 404
        existing_application = get_or_404(db_session, Application, application_id)

        # Check if user can read application
        ensure(READ, existing_application)

        document = get_document_by_id(db_session, document_id, existing_application)
        if not document:
            raise NotFound(description=f"Could not find Document with ID {document_id}")

        ensure(READ, document)

        document_data: massgov.pfml.fineos.models.customer_api.Base64EncodedFileData = (
            download_document(existing_application, document_id, db_session)
        )
        file_bytes = base64.b64decode(document_data.base64EncodedFileContents.encode("ascii"))

        content_type = document_data.contentType or "application/octet-stream"

        return Response(
            file_bytes,
            content_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={document_data.fileName}"},
        )


def employer_benefit_delete(application_id: str, employer_benefit_id: str) -> Response:
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        existing_employer_benefit = get_or_404(db_session, EmployerBenefit, employer_benefit_id)
        if existing_employer_benefit.application_id != existing_application.application_id:
            raise NotFound(
                description=f"Could not find EmployerBenefit with ID {employer_benefit_id}"
            )

        applications_service.remove_employer_benefit(db_session, existing_employer_benefit)
        db_session.expire(existing_application, ["employer_benefits"])

    return response_util.success_response(
        message="EmployerBenefit removed.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def other_income_delete(application_id: str, other_income_id: str) -> Response:
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        existing_other_income = get_or_404(db_session, OtherIncome, other_income_id)
        if existing_other_income.application_id != existing_application.application_id:
            raise NotFound(description=f"Could not find OtherIncome with ID {other_income_id}")

        applications_service.remove_other_income(db_session, existing_other_income)
        db_session.expire(existing_application, ["other_incomes"])

    return response_util.success_response(
        message="OtherIncome removed.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def previous_leave_delete(application_id: str, previous_leave_id: str) -> Response:
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        existing_previous_leave = get_or_404(db_session, PreviousLeave, previous_leave_id)
        if existing_previous_leave.application_id != existing_application.application_id:
            raise NotFound(description=f"Could not find PreviousLeave with ID {previous_leave_id}")

        applications_service.remove_previous_leave(db_session, existing_previous_leave)
        db_session.expire(
            existing_application, ["previous_leaves_other_reason", "previous_leaves_same_reason"],
        )

    return response_util.success_response(
        message="PreviousLeave removed.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def payment_preference_submit(application_id: str) -> Response:
    body = connexion.request.json

    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        updated_body = applications_service.remove_masked_fields_from_request(
            body, existing_application
        )

        payment_pref_request = PaymentPreferenceRequestBody.parse_obj(updated_body)

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
            existing_application.updated_time = datetime_util.utcnow()
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

                return response_util.success_response(
                    message="Payment Preference for application {} submitted without errors".format(
                        existing_application.application_id
                    ),
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                    status_code=201,
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
        return response_util.error_response(
            status_code=Forbidden,
            message="Application {} could not be updated. Payment preference already submitted".format(
                existing_application.application_id
            ),
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            errors=[],
        ).to_api_response()

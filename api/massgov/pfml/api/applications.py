import base64
from typing import Dict, Optional, Type, Union

import connexion
import puremagic
from flask import Response
from puremagic import PureError
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, ServiceUnavailable, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.services.application_rules as application_rules
import massgov.pfml.api.services.applications as applications_service
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, EDIT, READ, can, ensure
from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.api.models.applications.requests import (
    ApplicationRequestBody,
    DocumentRequestBody,
    PaymentPreferenceRequestBody,
)
from massgov.pfml.api.models.applications.responses import ApplicationResponse, DocumentResponse
from massgov.pfml.api.services.applications import get_document_by_id
from massgov.pfml.api.services.fineos_actions import (
    complete_intake,
    download_document,
    get_documents,
    mark_documents_as_received,
    mark_single_document_as_received,
    send_to_fineos,
    submit_payment_preference,
    upload_document,
)
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.db.models.applications import (
    Application,
    ContentType,
    Document,
    DocumentType,
    EmployerBenefit,
    OtherIncome,
    PreviousLeave,
)
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


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
        applications = db_session.query(Application).filter(Application.user_id == user_id).all()

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

    return response_util.success_response(
        message="Application updated without errors.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
        warnings=issues,
    ).to_api_response()


def get_fineos_submit_issues_response(issues, existing_application):
    status_code: Union[Type[BadRequest], Type[ServiceUnavailable]]

    if issues[0].type == response_util.IssueType.fineos_case_creation_issues:
        status_code = BadRequest
        message = "Application {} could not be submitted".format(
            existing_application.application_id
        )
    else:
        status_code = ServiceUnavailable
        message = "Application {} could not be submitted, try again later".format(
            existing_application.application_id
        )

    return response_util.error_response(
        status_code=status_code,
        message=message,
        errors=issues,
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def applications_submit(application_id):
    with app.db_session() as db_session:
        current_user = app.current_user()
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        log_attributes = get_application_log_attributes(existing_application)

        issues = application_rules.get_application_issues(existing_application)
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

        # Only send to fineos if fineos_absence_id isn't set. If it is set,
        # assume that just complete_intake needs to be reattempted.
        if not existing_application.fineos_absence_id:
            send_to_fineos_issues = send_to_fineos(existing_application, db_session, current_user)
            if len(send_to_fineos_issues) != 0:
                logger.error(
                    "applications_submit failure - failure sending application to claims processing system",
                    extra=log_attributes,
                )

                return get_fineos_submit_issues_response(
                    send_to_fineos_issues, existing_application
                )

            logger.info(
                "applications_submit - application sent to claims processing system",
                extra=log_attributes,
            )

        complete_intake_issues = complete_intake(existing_application, db_session)
        if len(complete_intake_issues) == 0:
            existing_application.submitted_time = datetime_util.utcnow()
            db_session.add(existing_application)
            logger.info(
                "applications_submit - application complete intake success", extra=log_attributes
            )
        else:
            logger.error(
                "applications_submit failure - application complete intake failure",
                extra=log_attributes,
            )
            return get_fineos_submit_issues_response(complete_intake_issues, existing_application)

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

        if mark_documents_as_received(existing_application, db_session):
            existing_application.completed_time = datetime_util.utcnow()
            logger.info(
                "applications_complete - application documents marked as received",
                extra=log_attributes,
            )
        else:
            logger.error(
                "applications_complete failure - application documents failed to be marked as received",
                extra=log_attributes,
            )
            return response_util.error_response(
                status_code=ServiceUnavailable,
                message="Application {} could not be completed (failed to mark associated documents as received), try again later".format(
                    existing_application.application_id
                ),
                errors=[],
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

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
        logger.error(message)
        validation_error = ValidationErrorDetail(
            message=message, type="file_type", rule=allowed_content_types, field="file",
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
            logger.error(message)
            validation_error = ValidationErrorDetail(
                message=message,
                type="file_type_mismatch",
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
        logger.error("Missing extension on file name.")
        message = "Missing extension on file name: {}".format(file_name)
        validation_error = ValidationErrorDetail(
            message=message,
            type="file_name_extension",
            rule="File name extension required.",
            field="file",
        )
        raise ValidationException(errors=[validation_error], message=message, data={})


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
                errors=[response_util.validation_issue(error) for error in ve.errors],
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
        document_type = document_details.document_type.value

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
        except ValueError as ve:
            logger.error(
                "document_upload failure - failure uploading document to claims processing system",
                extra=log_attributes,
            )
            return response_util.error_response(
                status_code=BadRequest,
                message=str(ve),
                errors=[response_util.custom_issue("fineos_client", str(ve))],
                data=document_details.dict(),
            ).to_api_response()

        # Insert a document metadata row
        document.application_id = existing_application.application_id
        now = datetime_util.utcnow()
        document.created_at = now
        document.updated_at = now
        document.document_type_id = DocumentType.get_id(document_details.document_type.value)
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
        except ValueError as ve:
            logger.error(
                "document_upload failure - failure marking evidence as received",
                extra=log_attributes,
            )

            # Do not save the document in the database if we failed to mark the associated evidence as received in
            # FINEOS because we want the claimant to have the opportunity to try again. This behaviour will create
            # mutliple documents in FINEOS but will also ensure that the evidence can eventually be marked as received.
            db_session.rollback()

            return response_util.error_response(
                status_code=BadRequest,
                message=str(ve),
                errors=[response_util.custom_issue("fineos_client", str(ve))],
                data=document_details.dict(),
            ).to_api_response()

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
        if existing_application.fineos_absence_id is None:
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

        document_data: massgov.pfml.fineos.models.customer_api.Base64EncodedFileData = download_document(
            existing_application, document_id, db_session
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

    return response_util.success_response(
        message="PreviousLeave removed.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def payment_preference_submit(application_id: str) -> Response:
    body = connexion.request.json
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        updated_body = applications_service.remove_masked_fields_from_request(
            body, existing_application
        )

        payment_pref_request = PaymentPreferenceRequestBody.parse_obj(updated_body)

        if not payment_pref_request.payment_preference:
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
                return response_util.error_response(
                    status_code=BadRequest,
                    message="Payment info is not valid for submission",
                    errors=issues,
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                ).to_api_response()

            if existing_application.payment_preference:
                try:
                    submit_payment_preference(existing_application, db_session)
                    existing_application.has_submitted_payment_preference = True
                    db_session.add(existing_application)
                    db_session.commit()
                    db_session.refresh(existing_application)

                    return response_util.success_response(
                        message="Payment Preference for application {} submitted without errors".format(
                            existing_application.application_id
                        ),
                        data=ApplicationResponse.from_orm(existing_application).dict(
                            exclude_none=True
                        ),
                        status_code=201,
                    ).to_api_response()
                except ValueError as ve:
                    return response_util.error_response(
                        status_code=BadRequest,
                        message=str(ve),
                        errors=[response_util.custom_issue("fineos_client", str(ve))],
                        data=ApplicationResponse.from_orm(existing_application).dict(
                            exclude_none=True
                        ),
                    ).to_api_response()
            else:
                return response_util.error_response(
                    status_code=ServiceUnavailable,
                    message="Payment Preference failed to save. Please try again.",
                    data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
                    errors=[],
                ).to_api_response()
        return response_util.error_response(
            status_code=Forbidden,
            message="Application {} could not be updated. Payment preference already submitted".format(
                existing_application.application_id
            ),
            data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            errors=[],
        ).to_api_response()


def get_application_log_attributes(application: Application) -> Dict[str, Optional[str]]:
    attributes_to_log = [
        "application_id",
        "employer_id",
        "leave_type",
        "has_state_id",
        "has_continuous_leave_periods",
        "has_employer_benefits",
        "has_future_child_date",
        "has_intermittent_leave_periods",
        "has_mailing_address",
        "has_other_incomes",
        "has_reduced_schedule_leave_periods",
        "has_submitted_payment_preference",
        "start_time",
        "updated_time",
        "completed_time",
        "submitted_time",
    ]

    result = {}
    for name in attributes_to_log:
        value = getattr(application, name)
        result[f"application.{name}"] = str(value) if value is not None else None

    # Use a different attribute name for other_incomes_awaiting_approval to be consistent with other booleans
    has_other_incomes_awaiting_approval = application.other_incomes_awaiting_approval
    result["application.has_other_incomes_awaiting_approval"] = (
        str(has_other_incomes_awaiting_approval)
        if has_other_incomes_awaiting_approval is not None
        else None
    )

    # Use a different attribute name for fineos_absence_id to avoid using vendor specific names
    result["application.absence_case_id"] = application.fineos_absence_id

    # leave_reason and leave_reason_qualifier are objects, so get the underlying string description
    result["application.leave_reason"] = (
        application.leave_reason.leave_reason_description if application.leave_reason else None
    )
    result["application.leave_reason_qualifier"] = (
        application.leave_reason_qualifier.leave_reason_qualifier_description
        if application.leave_reason_qualifier
        else None
    )

    result["work_pattern.work_pattern_type"] = (
        application.work_pattern.work_pattern_type.work_pattern_type_description
        if application.work_pattern and application.work_pattern.work_pattern_type
        else None
    )

    return result

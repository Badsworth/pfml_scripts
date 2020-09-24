from datetime import datetime

import connexion
import puremagic
from puremagic import PureError
from werkzeug.exceptions import BadRequest, ServiceUnavailable, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.services.applications as applications_service
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, EDIT, READ, can, ensure
from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.api.models.applications.requests import (
    ApplicationRequestBody,
    DocumentRequestBody,
)
from massgov.pfml.api.models.applications.responses import ApplicationResponse, DocumentResponse
from massgov.pfml.api.services.fineos_actions import (
    complete_intake,
    get_documents,
    send_to_fineos,
    upload_document,
)
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.db.models.applications import (
    Application,
    ContentType,
    Document,
    DocumentCategory,
    DocumentType,
)
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


def application_get(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(READ, existing_application)
        application_response = ApplicationResponse.from_orm(existing_application)

    return response_util.success_response(
        message="Successfully retrieved application", data=application_response.dict(),
    ).to_api_response()


def applications_get():
    with app.db_session() as db_session:
        applications = db_session.query(Application).all()

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

    now = datetime.now()
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

    application_request = ApplicationRequestBody.parse_obj(body)

    with app.db_session() as db_session:
        applications_service.update_from_request(
            db_session, application_request, existing_application
        )

    return response_util.success_response(
        message="Application updated without errors.",
        data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
    ).to_api_response()


def applications_submit(application_id):
    with app.db_session() as db_session:
        existing_application = get_or_404(db_session, Application, application_id)

        ensure(EDIT, existing_application)

        if send_to_fineos(existing_application, db_session):
            existing_application.submitted_time = datetime.now()
            db_session.add(existing_application)

        else:
            return response_util.error_response(
                status_code=ServiceUnavailable,
                message="Application {} could not be submitted, try again later".format(
                    existing_application.application_id
                ),
                errors=[],
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

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

        if complete_intake(existing_application, db_session):
            existing_application.completed_time = datetime.now()
            db_session.add(existing_application)

        else:
            return response_util.error_response(
                status_code=ServiceUnavailable,
                message="Application {} could not be completed, try again later".format(
                    existing_application.application_id
                ),
                errors=[],
                data=ApplicationResponse.from_orm(existing_application).dict(exclude_none=True),
            ).to_api_response()

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
        except ValueError as ve:
            return response_util.error_response(
                status_code=BadRequest,
                message=str(ve),
                errors=[response_util.custom_issue("fineos_client", str(ve))],
                data=document_details.dict(),
            ).to_api_response()

        # Insert a document metadata row
        document = Document()
        document.user_id = existing_application.user_id
        document.application_id = existing_application.application_id
        now = datetime.now()
        document.created_at = now
        document.updated_at = now
        document.document_category_id = DocumentCategory.get_id(
            document_details.document_category.value
        )
        document.document_type_id = DocumentType.get_id(document_details.document_type.value)
        document.content_type_id = ContentType.get_id(content_type)
        document.size_bytes = file_size
        document.fineos_id = fineos_document["documentId"]
        document.is_stored_in_s3 = False
        document.name = file_name
        document.description = file_description

        # Check if user can create this document, then persistence
        ensure(CREATE, document)

        db_session.add(document)
        db_session.commit()

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

        documents = get_documents(existing_application, db_session)

        documents_list = [doc.dict() for doc in documents]

        return response_util.success_response(
            message="Successfully retrieved documents", data=documents_list, status_code=200,
        ).to_api_response()

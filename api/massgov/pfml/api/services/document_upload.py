import tempfile
from typing import Any, Dict

import flask
import newrelic.agent
import puremagic
from puremagic import PureError
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
import massgov.pfml.util.pdf as pdf_util
from massgov.pfml.api.authorization.flask import CREATE, EDIT, ensure
from massgov.pfml.api.constants.application import ID_DOC_TYPES
from massgov.pfml.api.models.applications.common import ContentType as AllowedContentTypes
from massgov.pfml.api.models.applications.common import DocumentType as IoDocumentTypes
from massgov.pfml.api.models.applications.requests import DocumentRequestBody
from massgov.pfml.api.models.applications.responses import DocumentResponse
from massgov.pfml.api.services.fineos_actions import (
    mark_single_document_as_received,
    upload_document,
)
from massgov.pfml.api.validation.exceptions import (
    IssueRule,
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.applications import Application, Document, DocumentType, LeaveReason
from massgov.pfml.fineos.exception import FINEOSUnprocessableEntity
from massgov.pfml.util.logging.applications import get_application_log_attributes

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


def upload_document_to_fineos(
    application: Application, document_details: DocumentRequestBody, file: FileStorage
) -> flask.Response:
    log_attributes: Dict[str, Any] = get_application_log_attributes(application)

    with app.db_session() as db_session:
        # Check if user can edit application
        ensure(EDIT, application)

        # To upload documents, an application needs to have a corresponding claim in FINEOS
        claim = application.claim
        if not claim:
            logger.warning(
                "document_upload - No claim for application",
                extra=log_attributes,
            )

        # Check if user can create a document associated with this application before making any API calls or
        # persisting the document to the database.
        document = Document()
        document.user_id = application.user_id
        ensure(CREATE, document)

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

        try:
            # If the file is a PDF larger than the upload size constraint,
            # attempt to compress the PDF and update file meta data.
            # A size constraint of 10MB is still enforced by the API gateway,
            # so the API should not expect to receive anything above this size
            if content_type == AllowedContentTypes.pdf.value and file_size > UPLOAD_SIZE_CONSTRAINT:
                # tempfile.SpooledTemporaryFile writes the compressed file in-memory
                with tempfile.SpooledTemporaryFile(mode="wb+") as compressed_file:
                    file_size = pdf_util.compress_pdf(file, compressed_file)  # type: ignore
                    file_name = f"Compressed_{file_name}"

                    compressed_file.seek(0)
                    file_content = compressed_file.read()

            # Validate file size, regardless of processing
            validate_file_size(file_size)

        except (pdf_util.PDFSizeError):
            logger.warning("document_upload - file too large", extra=log_attributes, exc_info=True)
            return response_util.error_response(
                status_code=BadRequest,
                message="File validation error.",
                errors=[FILE_SIZE_VALIDATION_ERROR],
                data=document_details.dict(),
            ).to_api_response()

        except (pdf_util.PDFCompressionError):
            newrelic.agent.notice_error(attributes={"document_id": document.document_id})
            raise ValidationException(errors=[FILE_SIZE_VALIDATION_ERROR])

        # use Certification Form when the feature flag for caring leave is active, but will otherwise use
        # State manage Paid Leave Confirmation. If the document type is Certification Form,
        # the API will map to the corresponding plan proof based on leave reason
        document_type = document_details.document_type.value

        if document_type == IoDocumentTypes.certification_form.value:
            document_type = LEAVE_REASON_TO_DOCUMENT_TYPE_MAPPING[
                application.leave_reason.leave_reason_description
            ].document_type_description

        if document_type not in [doc_type.document_type_description for doc_type in ID_DOC_TYPES]:
            # Check for existing STATE_MANAGED_PAID_LEAVE_CONFIRMATION documents, and reuse the doc type if there are docs
            # Because existing claims where only part 1 has been submitted should continue using old doc type, submitted_time
            # rather than existing docs should be examined

            if has_previous_state_managed_paid_leave(application, db_session) or (
                application.submitted_time
                and application.submitted_time < app.get_app_config().new_plan_proofs_active_at
            ):
                document_type = (
                    DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_description
                )

        log_attributes.update(
            {
                "document.file_size": file_size,
                "document.content_type": content_type,
                "document.document_type": document_type,
            }
        )

        # Upload document to FINEOS
        try:
            fineos_document = upload_document(
                application,
                document_type,
                file_content,
                file_name,  # type: ignore
                content_type,
                file_description,
                db_session,
                with_multipart=app.get_config().enable_document_multipart_upload,
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

            if isinstance(err, FINEOSUnprocessableEntity):
                message = "Issue encountered while attempting to upload the document."
                return response_util.error_response(
                    status_code=BadRequest,
                    message=message,
                    errors=[
                        ValidationErrorDetail(
                            type=IssueType.fineos_client,
                            message=message,
                            rule=IssueRule.document_requirement_already_satisfied
                            if "is not required for the case provided" in err.message  # noqa: B306
                            else None,
                        )
                    ],
                    data=document_details.dict(),
                ).to_api_response()

            # Bubble any other issues up to the API error handlers
            raise

        # Insert a document metadata row
        document.application_id = application.application_id
        now = datetime_util.utcnow()
        document.created_at = now
        document.updated_at = now
        document.document_type_id = DocumentType.get_id(document_type)
        document.size_bytes = file_size
        document.fineos_id = fineos_document["documentId"]
        document.is_stored_in_s3 = False
        document.name = file_name  # type: ignore
        document.description = file_description

        db_session.add(document)

        try:
            if document_details.mark_evidence_received:
                mark_single_document_as_received(application, document, db_session)
                logger.info("document_upload - evidence marked as received", extra=log_attributes)
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

        logger.info("document_upload success", extra=log_attributes)
        document_response = DocumentResponse.from_orm(document)
        document_response.content_type = content_type
        # Return response
        return response_util.success_response(
            message="Successfully uploaded document", data=document_response.dict(), status_code=200
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
    """Use pure magic library to identify file type, use file mimetype as backup"""
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


def validate_file_size(file_size_bytes: int) -> None:
    """Validate the file size is below the known upload size constraint for files in FINEOS."""
    if file_size_bytes > UPLOAD_SIZE_CONSTRAINT:
        raise ValidationException(
            errors=[FILE_SIZE_VALIDATION_ERROR], message=FILE_TOO_LARGE_MSG, data={}
        )


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

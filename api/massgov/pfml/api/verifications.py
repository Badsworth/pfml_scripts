import json
from typing import Any, Dict, Optional, Tuple

import connexion
from flask.wrappers import Response
from sqlalchemy.orm.session import Session
from werkzeug.exceptions import BadRequest, Conflict, ServiceUnavailable

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.fineos as fineos
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.verifications.requests import VerificationRequest
from massgov.pfml.api.services.administrator_fineos_actions import generate_fineos_web_id
from massgov.pfml.api.users import user_response
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.db.models.employees import (
    EmployerQuarterlyContribution,
    User,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.verifications import Verification, VerificationType
from massgov.pfml.fineos.models.leave_admin_creation import CreateOrUpdateLeaveAdmin

logger = logging.get_logger(__name__)

WITHHOLDING_THRESHOLD = 0.10


def verifications():
    body = connexion.request.json
    verification_request = VerificationRequest.parse_obj(body)
    current_user = app.current_user()

    log_attributes: Dict[str, Any] = {
        "employer_id": verification_request.employer_id,
        "withholding_quarter": verification_request.withholding_quarter,
    }

    if current_user is None:
        logger.error("No authenticated user", extra=log_attributes)
        return response_util.error_response(
            status_code=BadRequest,
            message="No authenticated user",
            errors=[],
            data=verification_request.dict(exclude_none=True),
        ).to_api_response()

    with app.db_session() as db_session:
        user_leave_administrator = (
            db_session.query(UserLeaveAdministrator)
            .join(User)
            .filter(
                User.user_id == current_user.user_id,
                UserLeaveAdministrator.employer_id == verification_request.employer_id,
            )
            .one_or_none()
        )

        if user_leave_administrator is None:
            logger.error(
                "User not associated with this employer.", extra=log_attributes,
            )

            return response_util.error_response(
                status_code=BadRequest,
                message="User not associated with this employer.",
                errors=[],
                data=verification_request.dict(exclude_none=True),
            ).to_api_response()

        if user_leave_administrator.verification is not None:
            logger.error("User has already been verified", extra=log_attributes)
            return response_util.error_response(
                status_code=Conflict, message="User has already been verified.", errors=[]
            ).to_api_response()

        err_response, employer_quarterly_contribution = verify_quarterly_contribution(
            db_session, verification_request, log_attributes
        )

        if err_response is not None:
            return err_response

        verification = Verification(
            verification_type_id=VerificationType.PFML_WITHHOLDING.verification_type_id
        )

        verification_metadata = {
            "request_body": body,
            **employer_quarterly_contribution.for_json(),  # type: ignore
        }

        verification.verification_metadata = json.dumps(verification_metadata)  # type: ignore
        user_leave_administrator.verification = verification

        err_response = register_verified_leave_admin_with_fineos(user_leave_administrator)
        if err_response is not None:
            db_session.rollback()
            return err_response

        db_session.add(verification)
        db_session.add(user_leave_administrator)
        db_session.commit()
    logger.info(
        "Successfully verified user.",
        extra={
            "employer_id": verification_request.employer_id,
            "withholding_amount": verification_request.withholding_amount,
            "withholding_quarter": verification_request.withholding_quarter,
        },
    )

    return response_util.success_response(
        message="Successfully verified user.", status_code=201, data=user_response(current_user),
    ).to_api_response()


def verify_quarterly_contribution(
    db_session: Session, verification_request: VerificationRequest, log_attributes: dict
) -> Tuple[Optional[Response], Optional[EmployerQuarterlyContribution]]:
    employer_quarterly_contribution = (
        db_session.query(EmployerQuarterlyContribution)
        .filter(
            EmployerQuarterlyContribution.employer_id == verification_request.employer_id,
            EmployerQuarterlyContribution.filing_period == verification_request.withholding_quarter,
        )
        .one_or_none()
    )

    if employer_quarterly_contribution is None:
        logger.error(
            "Employer has no quarterly contribution data.", extra=log_attributes,
        )

        return (
            response_util.error_response(
                status_code=BadRequest,
                message="Employer has no quarterly contribution data.",
                errors=[],
                data=verification_request.dict(exclude_none=True),
            ).to_api_response(),
            None,
        )

    withholding_amount_delta = (
        verification_request.withholding_amount
        - employer_quarterly_contribution.employer_total_pfml_contribution
    )
    log_attributes = {**log_attributes, "withholding_amount_delta": withholding_amount_delta}
    if abs(withholding_amount_delta) > WITHHOLDING_THRESHOLD:
        logger.info(
            "Withholding amount is incorrect.", extra=log_attributes,
        )

        return (
            response_util.error_response(
                status_code=BadRequest,
                message="Withholding amount is incorrect.",
                errors=[
                    ValidationErrorDetail(
                        message="Withholding amount is incorrect",
                        type=IssueType.incorrect,
                        field="withholding_amount",
                    )
                ],
                data=verification_request.dict(exclude_none=True),
            ).to_api_response(),
            None,
        )
    return None, employer_quarterly_contribution


def register_verified_leave_admin_with_fineos(
    user_leave_administrator: UserLeaveAdministrator,
) -> Optional[Response]:
    if user_leave_administrator.employer.fineos_employer_id is None:
        logger.error(
            "Employer does not have a fineos_employer_id, registration to fineos cancelled",
            extra={
                "employer_id": user_leave_administrator.employer_id,
                "user_id": user_leave_administrator.user_id,
            },
        )
        return response_util.error_response(
            status_code=Conflict, errors=[], message="Employer does not have a fineos_employer_id.",
        ).to_api_response()

    if not user_leave_administrator.fineos_web_id:
        fineos_client = fineos.create_client()
        user_leave_administrator.fineos_web_id = generate_fineos_web_id()

        email_address = user_leave_administrator.user.email_address
        if email_address is None:
            logger.error(
                "Leave Admin user does not have an email address.",
                extra={
                    "employer_id": user_leave_administrator.employer_id,
                    "user_id": user_leave_administrator.user_id,
                },
            )
            return response_util.error_response(
                status_code=ServiceUnavailable,
                errors=[],
                message="Fineos Leave admin registration failed, Leave Admin user does not have an email address",
            ).to_api_response()
        leave_admin_create_payload = CreateOrUpdateLeaveAdmin(
            fineos_web_id=user_leave_administrator.fineos_web_id,
            fineos_employer_id=user_leave_administrator.employer.fineos_employer_id,
            # TODO: Set a real admin full name - https://lwd.atlassian.net/browse/EMPLOYER-540
            admin_full_name="Leave Administrator",
            admin_area_code=None,
            admin_phone_number=None,
            admin_email=email_address,
        )
        try:
            fineos_error, fineos_error_message = fineos_client.create_or_update_leave_admin(
                leave_admin_create_payload
            )
        except Exception as error:
            logger.error(
                "Failed to verify user, fineos error.",
                extra={
                    "employer_id": user_leave_administrator.employer_id,
                    "user_id": user_leave_administrator.user_id,
                },
                exc_info=error,
            )
            return response_util.error_response(
                status_code=ServiceUnavailable,
                errors=[],
                message="Fineos Leave admin registration failed.",
            ).to_api_response()

        if fineos_error or fineos_error_message:
            logger.error(
                "Failed to verify user, fineos error.",
                extra={
                    "fineos_error_code": fineos_error,
                    "fineos_error_message": fineos_error_message,
                    "employer_id": user_leave_administrator.employer_id,
                    "user_id": user_leave_administrator.user_id,
                },
            )
            return response_util.error_response(
                status_code=ServiceUnavailable,
                errors=[],
                message="Fineos Leave admin registration failed.",
            ).to_api_response()
    return None

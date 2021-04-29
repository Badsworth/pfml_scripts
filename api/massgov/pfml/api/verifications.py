import json

import connexion
from werkzeug.exceptions import BadRequest, Conflict

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.verifications.requests import VerificationRequest
from massgov.pfml.api.users import user_response
from massgov.pfml.db.models.employees import (
    EmployerQuarterlyContribution,
    User,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.verifications import Verification, VerificationType

logger = logging.get_logger(__name__)


def verifications():
    body = connexion.request.json
    verification_request = VerificationRequest.parse_obj(body)
    current_user = app.current_user()

    if current_user is None:
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
                "User not associated with this employer.", extra=verification_request.dict()
            )

            return response_util.error_response(
                status_code=BadRequest,
                message="User not associated with this employer.",
                errors=[],
                data=verification_request.dict(exclude_none=True),
            ).to_api_response()

        if user_leave_administrator.verification is not None:
            return response_util.error_response(
                status_code=Conflict, message="User has already been verified.", errors=[]
            ).to_api_response()

        employer_quarterly_contribution = (
            db_session.query(EmployerQuarterlyContribution)
            .filter(
                EmployerQuarterlyContribution.employer_id == verification_request.employer_id,
                EmployerQuarterlyContribution.filing_period
                == verification_request.withholding_quarter,
            )
            .one_or_none()
        )

        if employer_quarterly_contribution is None:
            logger.error(
                "Employer has no quarterly contribution data.", extra=verification_request.dict()
            )

            return response_util.error_response(
                status_code=BadRequest,
                message="Employer has no quarterly contribution data.",
                errors=[],
                data=verification_request.dict(exclude_none=True),
            ).to_api_response()

        if (
            employer_quarterly_contribution.employer_total_pfml_contribution
            != verification_request.withholding_amount
        ):
            logger.warning("Withholding amount is incorrect.", extra=verification_request.dict())

            return response_util.error_response(
                status_code=BadRequest,
                message="Withholding amount is incorrect.",
                errors=[
                    response_util.custom_issue(
                        message="Withholding amount is incorrect",
                        type="incorrect",
                        field="withholding_amount",
                    )
                ],
                data=verification_request.dict(exclude_none=True),
            ).to_api_response()

        verification = Verification(
            verification_type_id=VerificationType.PFML_WITHHOLDING.verification_type_id
        )

        verification_metadata = {
            "request_body": body,
            **employer_quarterly_contribution.for_json(),
        }

        verification.verification_metadata = json.dumps(verification_metadata)  # type: ignore
        db_session.add(verification)
        user_leave_administrator.verification = verification
        db_session.add(user_leave_administrator)
        db_session.commit()

    logger.info("Successfully verified user.", extra=verification_request.dict())

    return response_util.success_response(
        message="Successfully verified user.", status_code=201, data=user_response(current_user),
    ).to_api_response()

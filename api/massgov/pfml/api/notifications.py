import json

import connexion
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.api.services.service_now_actions import send_notification_to_service_now
from massgov.pfml.db.models.applications import Notification
from massgov.pfml.db.models.employees import Claim, Employer

logger = massgov.pfml.util.logging.get_logger(__name__)


def notifications_post():
    # Bounce them out if they do not have access
    ensure(CREATE, Notification)

    body = connexion.request.json
    # Use the pydantic models for validation
    notification_request = NotificationRequest.parse_obj(body)

    with app.db_session() as db_session:
        # Persist the notification to the DB
        notification = Notification()

        now = datetime_util.utcnow()
        notification.created_at = now
        notification.updated_at = now

        notification.request_json = json.dumps(body)  # type: ignore

        db_session.add(notification)
        db_session.commit()

        # Find or create an associated claim
        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == notification_request.absence_case_id)
            .one_or_none()
        )

        try:
            employer = (
                db_session.query(Employer)
                .filter(Employer.employer_fein == notification_request.fein.replace("-", ""))
                .one_or_none()
            )

        except MultipleResultsFound as exc:
            logger.error("Multiple employers found for specified FEIN", exc_info=exc)

            return response_util.error_response(
                status_code=BadRequest,
                message="Multiple employers found for specified FEIN",
                errors=[],
            )

        if employer is None:
            return response_util.error_response(
                status_code=BadRequest,
                message="Failed to lookup the specified FEIN to add Claim record on Notification POST request",
                errors=[],
            )

        if claim is None:
            new_claim = Claim(
                employer_id=employer.employer_id,
                fineos_absence_id=notification_request.absence_case_id,
            )

            db_session.add(new_claim)
            db_session.commit()

    # Send the request to Service Now
    send_notification_to_service_now(notification_request, employer)

    return response_util.success_response(
        message="Successfully started notification process.", status_code=201, data={}
    ).to_api_response()

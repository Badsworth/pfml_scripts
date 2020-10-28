import json

import connexion

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.datetime as datetime_util
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.api.services.service_now_actions import send_notification_to_service_now
from massgov.pfml.db.models.applications import Notification


def notifications_post():
    # Bounce them out if they do not have access
    ensure(CREATE, Notification)

    body = connexion.request.json
    # Use the pydantic models for validation
    notification_request = NotificationRequest.parse_obj(body)

    # Send the request to Service Now
    send_notification_to_service_now(notification_request)

    # Persist the notification to the DB
    with app.db_session() as db_session:
        notification = Notification()

        now = datetime_util.utcnow()
        notification.created_at = now
        notification.updated_at = now

        notification.request_json = json.dumps(body)  # type: ignore

        db_session.add(notification)

    return response_util.success_response(
        message="Successfully started notification process.", status_code=201, data={}
    ).to_api_response()

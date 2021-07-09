import json
from typing import Optional

import connexion
import flask
import newrelic.agent
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.api.services.service_now_actions import send_notification_to_service_now
from massgov.pfml.db.models.applications import Notification
from massgov.pfml.db.models.employees import Claim, Employee, Employer

logger = massgov.pfml.util.logging.get_logger(__name__)


def notifications_post():
    # Bounce them out if they do not have access
    ensure(CREATE, Notification)

    body = connexion.request.json
    # Use the pydantic models for validation
    notification_request = NotificationRequest.parse_obj(body)
    log_attributes = {
        "notification.absence_case_id": notification_request.absence_case_id,
        "notification.recipient_type": notification_request.recipient_type,
        "notification.source": notification_request.source,
        "notification.trigger": notification_request.trigger,
        "notification_request.claimant_info.customer_id": notification_request.claimant_info.customer_id,
    }
    for k, v in log_attributes.items():
        newrelic.agent.add_custom_parameter(k, v)

    with app.db_session() as db_session:
        # Persist the notification to the DB
        notification = Notification()

        now = datetime_util.utcnow()
        notification.created_at = now
        notification.updated_at = now
        notification.fineos_absence_id = notification_request.absence_case_id

        notification.request_json = json.dumps(body)  # type: ignore

        db_session.add(notification)
        db_session.commit()

        # Find or create an associated claim
        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == notification_request.absence_case_id)
            .one_or_none()
        )
        if claim:
            log_attributes = {**log_attributes, "claim_id": str(claim.claim_id)}
            newrelic.agent.add_custom_parameter("claim_id", str(claim.claim_id))

        try:
            employer = (
                db_session.query(Employer)
                .filter(Employer.employer_fein == notification_request.fein.replace("-", ""))
                .one_or_none()
            )

            if employer:
                log_attributes = {
                    **log_attributes,
                    "employer_id": employer.employer_id,
                }
                newrelic.agent.add_custom_parameter("employer_id", employer.employer_id)
        except MultipleResultsFound:
            return _err400_multiple_employer_feins_found(notification_request, log_attributes)

        if employer is None:
            return _err400_employer_fein_not_found(notification_request, log_attributes)

        employee_id = get_employee_id_from_fineos_customer_number(
            db_session, log_attributes, notification_request.claimant_info.customer_id
        )
        if employee_id:
            log_attributes = {**log_attributes, "employee_id": employee_id}
            newrelic.agent.add_custom_parameter("employee_id", employee_id)

        if claim is None:
            new_claim = Claim(
                employer_id=employer.employer_id,
                employee_id=employee_id,
                fineos_absence_id=notification_request.absence_case_id,
            )
            db_session.add(new_claim)
            db_session.commit()

            log_attributes = {**log_attributes, "claim_id": str(new_claim.claim_id)}
            newrelic.agent.add_custom_parameter("claim_id", str(new_claim.claim_id))

            logger.info("Created Claim from a Notification", extra=log_attributes)
        else:
            db_changed = False
            if claim.employer_id is None:
                db_changed = True
                claim.employer_id = employer.employer_id
                logger.info("Associated Employer to Claim", extra=log_attributes)
            if claim.employee_id is None and employee_id is not None:
                db_changed = True
                claim.employee_id = employee_id
                logger.info("Associated Employee to Claim", extra=log_attributes)
            if db_changed:
                db_session.add(claim)
                db_session.commit()
    # Send the request to Service Now
    send_notification_to_service_now(notification_request, employer)

    logger.info("Sent notification", extra=log_attributes)
    return response_util.success_response(
        message="Successfully started notification process.", status_code=201, data={}
    ).to_api_response()


def get_employee_id_from_fineos_customer_number(
    db_session: db.Session, log_attributes: dict, fineos_customer_number: str
) -> Optional[str]:
    """Get employee ID by fineos_customer_number. Fails without raising an exception since an Employee ID isn't required for sending a notification."""
    try:
        employee = (
            db_session.query(Employee)
            .filter(Employee.fineos_customer_number == fineos_customer_number)
            .one_or_none()
        )
        if employee:
            return employee.employee_id
        logger.warning(
            "Failed to lookup the specified Employee Fineos Customer Number to associate Claim record",
            extra=log_attributes,
        )
    except MultipleResultsFound:
        # TODO (EMPLOYER-1417): Remove this exception handler once the `fineos_customer_number` field is unique
        logger.exception(
            "Multiple employees found for specified Claimant Fineos Customer Number",
            extra=log_attributes,
        )
    except Exception:
        logger.exception(
            "Unexpected error while searching employees for specified Claimant Fineos Customer Number",
            extra=log_attributes,
        )
    return None


def _err400_employer_fein_not_found(notification_request, log_attributes):
    logger.warning(
        "Failed to lookup the specified FEIN to add Claim record on Notification POST request",
        extra=log_attributes,
    )

    newrelic.agent.record_custom_event(
        "FineosError",
        {
            **log_attributes,
            "error.class": "FINEOSNotificationInvalidFEIN",
            "error.message": "Failed to lookup the specified FEIN to add Claim record on Notification POST request",
            "request.method": flask.request.method if flask.has_request_context() else None,
            "request.uri": flask.request.path if flask.has_request_context() else None,
            "request.headers.x-amzn-requestid": flask.request.headers.get("x-amzn-requestid", None),
            "absence-id": notification_request.absence_case_id
            if flask.has_request_context()
            else None,
        },
    )

    return response_util.error_response(
        status_code=BadRequest,
        message="Failed to lookup the specified FEIN to add Claim record on Notification POST request",
        errors=[],
        data={},
    ).to_api_response()


def _err400_multiple_employer_feins_found(notification_request, log_attributes):
    logger.exception("Multiple employers found for specified FEIN", extra=log_attributes)

    newrelic.agent.record_custom_event(
        "FineosError",
        {
            **log_attributes,
            "error.class": "FINEOSNotificationMultipleResults",
            "error.message": "Multiple employers found for specified FEIN",
            "request.method": flask.request.method if flask.has_request_context() else None,
            "request.uri": flask.request.path if flask.has_request_context() else None,
            "request.headers.x-amzn-requestid": flask.request.headers.get("x-amzn-requestid", None),
            "absence-id": notification_request.absence_case_id
            if flask.has_request_context()
            else None,
        },
    )

    return response_util.error_response(
        status_code=BadRequest,
        message="Multiple employers found for specified FEIN",
        errors=[],
        data={},
    ).to_api_response()

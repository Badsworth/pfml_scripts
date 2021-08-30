from enum import Enum
from typing import Optional
from uuid import UUID

import connexion
import flask
import newrelic.agent
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.session import Session
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.api.services.managed_requirements import (
    get_fineos_managed_requirements_from_notification,
)
from massgov.pfml.api.services.service_now_actions import send_notification_to_service_now
from massgov.pfml.db.models.applications import Notification
from massgov.pfml.db.models.employees import Claim, Employee, Employer, ManagedRequirementType
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    create_or_update_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
)
from massgov.pfml.types import Fein
from massgov.pfml.util.logging.managed_requirements import (
    get_fineos_managed_requirement_log_attributes,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


class FineosNotificationTrigger(str, Enum):
    DESIGNATION_NOTICE = "Designation Notice"
    LEAVE_REQUEST_DECLINED = "Leave Request Declined"
    EMPLOYER_CONFIRMATION_OF_LEAVE_DATA = "Employer Confirmation of Leave Data"


class FineosRecipientType(str, Enum):
    LEAVE_ADMINISTRATOR = "Leave Administrator"


def notifications_post():
    # Bounce them out if they do not have access
    ensure(CREATE, Notification)

    body = connexion.request.json
    # Use the pydantic models for validation
    notification_request = NotificationRequest.parse_obj(body)
    log_attributes = {
        "absence_case_id": notification_request.absence_case_id,
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

        notification.fineos_absence_id = notification_request.absence_case_id

        notification.request_json = body

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
                .filter(Employer.employer_fein == Fein(notification_request.fein.replace("-", "")))
                .one_or_none()
            )

            if employer:
                log_attributes = {
                    **log_attributes,
                    "employer_id": str(employer.employer_id),
                }
                newrelic.agent.add_custom_parameter("employer_id", employer.employer_id)
        except MultipleResultsFound:
            return _err400_multiple_employer_feins_found(notification_request, log_attributes)
        except ValueError:
            return _err400_employer_fein_not_found(notification_request, log_attributes)

        if employer is None:
            return _err400_employer_fein_not_found(notification_request, log_attributes)

        employee_id = get_employee_id_from_fineos_customer_number(
            db_session, log_attributes, notification_request.claimant_info.customer_id
        )
        if employee_id:
            log_attributes = {**log_attributes, "employee_id": str(employee_id)}
            newrelic.agent.add_custom_parameter("employee_id", employee_id)

        if claim is None:
            claim = Claim(
                employer_id=employer.employer_id,
                employee_id=employee_id,
                fineos_absence_id=notification_request.absence_case_id,
            )
            db_session.add(claim)
            db_session.commit()

            log_attributes = {**log_attributes, "claim_id": str(claim.claim_id)}
            newrelic.agent.add_custom_parameter("claim_id", str(claim.claim_id))

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

        try:
            handle_managed_requirements(
                notification_request, claim.claim_id, db_session, log_attributes
            )
        except Exception as error:  # catch all exception handler
            logger.error(
                "Failed to handle the claim's managed requirements in notification call",
                extra=log_attributes,
                exc_info=error,
            )
            db_session.rollback()  # handle insert errors

    # Send the request to Service Now
    send_notification_to_service_now(notification_request, employer)

    logger.info("Sent notification", extra=log_attributes)
    return response_util.success_response(
        message="Successfully started notification process.", status_code=201, data={}
    ).to_api_response()


def get_employee_id_from_fineos_customer_number(
    db_session: db.Session, log_attributes: dict, fineos_customer_number: str
) -> Optional[UUID]:
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


def handle_managed_requirements_create(
    notification: NotificationRequest, claim_id: UUID, db_session: Session, log_attributes: dict
) -> None:
    fineos_requirements = get_fineos_managed_requirements_from_notification(
        notification, log_attributes
    )

    if len(fineos_requirements) == 0:
        logger.info("No managed requirements returned by Fineos", extra=log_attributes)
        return

    for fineos_requirement in fineos_requirements:
        log_attr = {
            **log_attributes.copy(),
            **get_fineos_managed_requirement_log_attributes(fineos_requirement),
        }
        try:
            type_id = ManagedRequirementType.get_id(fineos_requirement.type)
        except KeyError:
            logger.warning(
                "Managed Requirement unsupported lookup from Fineos Manged Requirement Creation aborted",
                extra=log_attr,
            )
            continue
        existing_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_requirement.managedReqId, db_session
        )
        if existing_requirement is None:
            create_managed_requirement_from_fineos(
                db_session, claim_id, fineos_requirement, log_attr
            )
        elif existing_requirement.managed_requirement_type_id != type_id:
            logger.warning("Managed Requirement type mismatch", extra=log_attr)
        else:
            logger.info("Managed Requirement already exists, no record created", extra=log_attr)
    return


def handle_managed_requirements_update(
    notification: NotificationRequest, claim_id: UUID, db_session: Session, log_attributes: dict
) -> None:
    fineos_requirements = get_fineos_managed_requirements_from_notification(
        notification, log_attributes
    )

    if len(fineos_requirements) == 0:
        logger.info("No managed requirements returned by Fineos", extra=log_attributes)
        return

    for fineos_requirement in fineos_requirements:
        log_attr = {
            **log_attributes.copy(),
            **get_fineos_managed_requirement_log_attributes(fineos_requirement),
        }
        create_or_update_managed_requirement_from_fineos(
            db_session, claim_id, fineos_requirement, log_attr
        )
    return


def handle_managed_requirements(
    notification: NotificationRequest, claim_id: UUID, db_session: Session, log_attributes: dict
) -> None:
    update_triggers = [
        FineosNotificationTrigger.DESIGNATION_NOTICE,
        FineosNotificationTrigger.LEAVE_REQUEST_DECLINED,
    ]

    should_update_managed_requirements = notification.trigger in update_triggers and (
        notification.recipient_type == FineosRecipientType.LEAVE_ADMINISTRATOR
    )
    should_create_managed_requirements = (
        notification.trigger == FineosNotificationTrigger.EMPLOYER_CONFIRMATION_OF_LEAVE_DATA
        and notification.recipient_type == FineosRecipientType.LEAVE_ADMINISTRATOR
    )
    if should_update_managed_requirements:
        handle_managed_requirements_update(notification, claim_id, db_session, log_attributes)
    elif should_create_managed_requirements:
        handle_managed_requirements_create(notification, claim_id, db_session, log_attributes)

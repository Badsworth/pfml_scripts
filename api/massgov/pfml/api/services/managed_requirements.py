from typing import List, Optional

from sqlalchemy import exc

import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging
from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.db import Session
from massgov.pfml.db.models.employees import (
    ManagedRequirement,
    ManagedRequirementStatus,
    ManagedRequirementType,
)
from massgov.pfml.db.queries.managed_requirements import (
    commit_managed_requirement_update,
    get_managed_requirement_by_fineos_managed_requirement_id,
)
from massgov.pfml.fineos import create_client, exception
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails
from massgov.pfml.util.logging.managed_requirements import (
    get_fineos_managed_requirement_log_attributes,
    get_managed_requirement_log_attributes,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_contact_id(notification: NotificationRequest) -> Optional[str]:
    for recipient in notification.recipients:
        if recipient.contact_id is not None:
            return recipient.contact_id

    return None


def get_fineos_managed_requirements_from_notification(
    notification: NotificationRequest, log_attributes: dict
) -> List[ManagedRequirementDetails]:
    if not notification.recipients:
        logger.warning("No Recipient in notification request", extra=log_attributes)
        return []
    fineos_client = create_client()
    contact_id = get_contact_id(notification)
    if contact_id is None:
        logger.warning("No contact_id in any recipient", extra=log_attributes)
        return []
    try:
        return fineos_client.get_managed_requirements(contact_id, notification.absence_case_id)
    except exception.FINEOSClientError:
        # the error is already logged by get_managed_requirements
        return []


def update_employer_confirmation_requirements(
    db_session: Session, admin_user_id: str, fineos_managed_reqs: List[ManagedRequirementDetails],
) -> List[ManagedRequirement]:

    employer_confirmation_requirements = select_employer_confirmation_requirements(
        fineos_managed_reqs
    )

    managed_req_updates = [
        employer_confirmation_req_to_managed_req_update(db_session, admin_user_id, req)
        for req in employer_confirmation_requirements
    ]

    records = [
        commit_managed_requirement_update(db_session, valid_update)
        for valid_update in managed_req_updates
        if valid_update
    ]

    updated_records = [updated for updated in records if updated]

    return updated_records


def employer_confirmation_req_to_managed_req_update(
    db_session: Session, admin_user_id: str, fineos_managed_req: ManagedRequirementDetails,
) -> Optional[ManagedRequirement]:

    managed_req: Optional[ManagedRequirement]
    try:
        managed_req_id = str(fineos_managed_req.managedReqId)
        managed_req = get_managed_requirement_by_fineos_managed_requirement_id(
            int(managed_req_id), db_session
        )

        if managed_req:
            managed_req.respondent_user_id = admin_user_id
            managed_req.managed_requirement_status_id = ManagedRequirementStatus.get_id(
                fineos_managed_req.status
            )
            managed_req.responded_at = datetime_util.utcnow()
        else:
            logger.warning(
                "ManagedRequirement record not found",
                extra={**get_fineos_managed_requirement_log_attributes(fineos_managed_req)},
            )

    except exc.SQLAlchemyError as ex:
        logger.warning(
            "Unable to get ManagedRequirement record",
            exc_info=ex,
            extra={**get_fineos_managed_requirement_log_attributes(fineos_managed_req)},
        )
        return None

    except KeyError as ex:
        logger.warning(
            "Managed requirement failed to update. Unsupported Fineos Managed Requirement status received.",
            exc_info=ex,
            extra={**get_fineos_managed_requirement_log_attributes(fineos_managed_req)},
        )
        return None

    return managed_req


def is_managed_req_status_outdated(
    managed_req: ManagedRequirement, fineos_managed_req: ManagedRequirementDetails
) -> bool:
    is_outdated = (
        managed_req.managed_requirement_status.managed_requirement_status_description
        != fineos_managed_req.status
    )
    if not is_outdated:
        logger.info(
            "Received managed requirement details with no status change",
            extra={
                **get_fineos_managed_requirement_log_attributes(fineos_managed_req),
                **get_managed_requirement_log_attributes(managed_req),
            },
        )

    return is_outdated


def is_employer_confirmation_requirement(fineos_managed_req: ManagedRequirementDetails) -> bool:
    is_confirmation = (
        fineos_managed_req.type
        == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_description
    )
    if not is_confirmation:
        # We currently only sync this type of managed requirement, and don't expect any others
        logger.info(
            "Received unexpected managed requirement type",
            extra={**get_fineos_managed_requirement_log_attributes(fineos_managed_req)},
        )

    return is_confirmation


def select_employer_confirmation_requirements(
    fineos_managed_reqs: List[ManagedRequirementDetails],
) -> List[ManagedRequirementDetails]:
    employer_confirmation_requirements = [
        req for req in fineos_managed_reqs if is_employer_confirmation_requirement(req)
    ]

    return employer_confirmation_requirements

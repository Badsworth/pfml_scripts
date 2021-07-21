from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm.session import Session

import massgov.pfml.util.logging
from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.db.models.employees import (
    ManagedRequirement,
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
)
from massgov.pfml.fineos import create_client, exception
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_contact_id(notification: NotificationRequest) -> Optional[str]:
    for recipient in notification.recipients:
        if recipient.contact_id is not None:
            return recipient.contact_id

    return None


# TODO: move to api/massgov/pfml/api/services/managed_requirements.py
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


def get_managed_requirement_by_fineos_managed_requirement_id(
    fineos_managed_requirement_id: int, db_session: Session
) -> Optional[ManagedRequirement]:
    return (
        db_session.query(ManagedRequirement)
        .filter(
            ManagedRequirement.fineos_managed_requirement_id == str(fineos_managed_requirement_id)
        )
        .one_or_none()
    )


def update_managed_requirement_from_fineos(
    db_session: Session,
    fineos_requirement: ManagedRequirementDetails,
    db_requirement: ManagedRequirement,
    log_attributes: dict,
) -> Optional[ManagedRequirement]:
    log_attributes.update(
        {"managed_requirement.id": str(db_requirement.managed_requirement_id), **log_attributes,}
    )
    try:
        db_requirement.managed_requirement_status_id = ManagedRequirementStatus.get_id(
            fineos_requirement.status
        )
    except KeyError:
        logger.warning(
            "Managed requirement failed to update. Unsupported Fineos Managed Requirement status received.",
            extra=log_attributes,
        )
        return None

    fineos_follow_up_date = fineos_requirement.followUpDate
    if fineos_follow_up_date != db_requirement.follow_up_date:
        log_attributes.update(
            {"managed_requirement.follow_up_date": db_requirement.follow_up_date, **log_attributes,}
        )
        logger.warning("Managed Requirement follow_up_date Mismatch", extra=log_attributes)
    db_requirement.follow_up_date = fineos_follow_up_date
    db_session.add(db_requirement)
    db_session.commit()
    logger.info("Managed requirement successfully updated", extra=log_attributes)
    return db_requirement


def create_managed_requirement_from_fineos(
    db_session: Session,
    claim_id: UUID,
    fineos_requirement: ManagedRequirementDetails,
    log_attributes: dict,
) -> Optional[ManagedRequirement]:
    try:
        status_id = ManagedRequirementStatus.get_id(fineos_requirement.status)
        category_id = ManagedRequirementCategory.get_id(fineos_requirement.category)
        type_id = ManagedRequirementType.get_id(fineos_requirement.type)
    except KeyError:
        logger.warning(
            "Managed requirement failed to create. Unsupported Fineos Managed Requirement lookup received.",
            extra=log_attributes,
            exc_info=True,
        )
        return None
    managed_requirement = ManagedRequirement(
        claim_id=claim_id,  # type: ignore
        fineos_managed_requirement_id=str(fineos_requirement.managedReqId),
        follow_up_date=fineos_requirement.followUpDate,
        managed_requirement_status_id=status_id,
        managed_requirement_category_id=category_id,
        managed_requirement_type_id=type_id,
    )
    db_session.add(managed_requirement)
    db_session.commit()
    logger.info("Managed requirement successfully created", extra=log_attributes)
    return managed_requirement


def create_or_update_managed_requirement_from_fineos(
    db_session: Session,
    claim_id: UUID,
    fineos_requirement: ManagedRequirementDetails,
    log_attributes: dict,
) -> Optional[ManagedRequirement]:
    db_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
        fineos_requirement.managedReqId, db_session
    )
    if db_requirement is None:
        return create_managed_requirement_from_fineos(
            db_session, claim_id, fineos_requirement, log_attributes
        )
    else:
        return update_managed_requirement_from_fineos(
            db_session, fineos_requirement, db_requirement, log_attributes
        )

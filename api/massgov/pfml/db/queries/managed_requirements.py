from typing import Optional
from uuid import UUID

from sqlalchemy import exc
from sqlalchemy.orm.session import Session

import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    ManagedRequirement,
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
)
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails
from massgov.pfml.util.logging.managed_requirements import (
    get_fineos_managed_requirement_log_attributes,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


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
) -> ManagedRequirement:
    log_attributes = {
        **log_attributes,
        **get_fineos_managed_requirement_log_attributes(fineos_requirement),
    }
    db_requirement.managed_requirement_status_id = ManagedRequirementStatus.get_id(
        fineos_requirement.status
    )

    fineos_follow_up_date = fineos_requirement.followUpDate
    if fineos_follow_up_date != db_requirement.follow_up_date:
        log_attributes.update(
            {"managed_requirement.follow_up_date": db_requirement.follow_up_date, **log_attributes,}
        )
        logger.warning("Managed Requirement follow_up_date Mismatch", extra=log_attributes)
    db_requirement.follow_up_date = fineos_follow_up_date
    db_session.add(db_requirement)
    return db_requirement


def create_managed_requirement_from_fineos(
    db_session: Session, claim_id: UUID, fineos_requirement: ManagedRequirementDetails,
) -> ManagedRequirement:
    status_id = ManagedRequirementStatus.get_id(fineos_requirement.status)
    category_id = ManagedRequirementCategory.get_id(fineos_requirement.category)
    type_id = ManagedRequirementType.get_id(fineos_requirement.type)

    managed_requirement = ManagedRequirement(
        claim_id=claim_id,
        fineos_managed_requirement_id=str(fineos_requirement.managedReqId),
        follow_up_date=fineos_requirement.followUpDate,
        managed_requirement_status_id=status_id,
        managed_requirement_category_id=category_id,
        managed_requirement_type_id=type_id,
    )
    db_session.add(managed_requirement)
    return managed_requirement


def create_or_update_managed_requirement_from_fineos(
    db_session: Session,
    claim_id: UUID,
    fineos_requirement: ManagedRequirementDetails,
    log_attributes: dict,
) -> ManagedRequirement:
    db_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
        fineos_requirement.managedReqId, db_session
    )
    if db_requirement is None:
        return create_managed_requirement_from_fineos(db_session, claim_id, fineos_requirement)
    else:
        return update_managed_requirement_from_fineos(
            db_session, fineos_requirement, db_requirement, log_attributes
        )


def commit_managed_requirements(db_session: Session) -> None:

    try:
        db_session.commit()
    except exc.SQLAlchemyError as ex:
        db_session.rollback()
        logger.warning("Unable to commit Managed Requirement records to database", exc_info=ex)

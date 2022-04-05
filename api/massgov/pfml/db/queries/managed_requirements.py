from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import exc
from sqlalchemy.orm.session import Session

import massgov.pfml.util.logging
import massgov.pfml.util.newrelic.events as newrelic_util
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
) -> Optional[ManagedRequirement]:
    log_attributes = {
        **log_attributes,
        **get_fineos_managed_requirement_log_attributes(fineos_requirement),
    }
    db_requirement.managed_requirement_status_id = ManagedRequirementStatus.get_id(
        fineos_requirement.status
    )

    try:
        type_id = ManagedRequirementType.get_id(fineos_requirement.type)
    except KeyError:
        logger.warning(
            "Unsupported type lookup from Fineos Managed Requirement Creation - aborted",
            extra=log_attributes,
        )
        return None

    if db_requirement.managed_requirement_type_id != type_id:
        newrelic_util.log_and_capture_exception(
            "Managed Requirement type mismatch",
            extra={
                **log_attributes,
                "managed_requirement_type": db_requirement.managed_requirement_type.managed_requirement_type_description,
                "fineos.managed_requirement_type": fineos_requirement.type,
            },
        )

    fineos_follow_up_date = fineos_requirement.followUpDate
    if fineos_follow_up_date != db_requirement.follow_up_date:
        newrelic_util.log_and_capture_exception(
            "Managed Requirement follow_up_date Mismatch",
            extra={
                **log_attributes,
                "managed_requirement.follow_up_date": db_requirement.follow_up_date,
                "fineos.follow_up_date": fineos_follow_up_date,
            },
        )
    db_requirement.follow_up_date = fineos_follow_up_date
    db_session.add(db_requirement)
    return db_requirement


def create_managed_requirement_from_fineos(
    db_session: Session, claim_id: UUID, fineos_requirement: ManagedRequirementDetails
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
) -> Tuple[Optional[ManagedRequirement], bool]:
    """
    Returns a boolean to indicate if the requirement is created or updated
    """
    db_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
        fineos_requirement.managedReqId, db_session
    )
    if db_requirement is None:
        return (
            create_managed_requirement_from_fineos(db_session, claim_id, fineos_requirement),
            True,
        )
    else:
        return (
            update_managed_requirement_from_fineos(
                db_session, fineos_requirement, db_requirement, log_attributes
            ),
            False,
        )


def sync_managed_requirements_to_db(
    fineos_requirements: List[ManagedRequirementDetails],
    claim_id: UUID,
    db_session: Session,
    log_attributes: dict,
) -> Tuple[List[ManagedRequirement], dict]:
    num_created_requirements = 0
    num_updated_requirements = 0
    managed_requirements_from_db = []
    for fineos_requirement in fineos_requirements:
        log_attr = {
            **log_attributes.copy(),
            **get_fineos_managed_requirement_log_attributes(fineos_requirement),
        }
        (managed_requirement, is_created) = create_or_update_managed_requirement_from_fineos(
            db_session, claim_id, fineos_requirement, log_attr
        )

        if managed_requirement is not None:
            managed_requirements_from_db.append(managed_requirement)
            if is_created:
                num_created_requirements += 1
            else:
                num_updated_requirements += 1
    log_attributes.update(
        {
            "num_created_requirements": num_created_requirements,
            "num_updated_requirements": num_updated_requirements,
        }
    )
    return (managed_requirements_from_db, log_attributes)


def commit_managed_requirements(db_session: Session, log_attributes: Optional[dict]) -> None:

    try:
        db_session.commit()
        if log_attributes:
            logger.info("Successfully synced Managed requirements", extra=log_attributes)
    except exc.SQLAlchemyError as ex:
        db_session.rollback()
        logger.warning("Unable to commit Managed Requirement records to database", exc_info=ex)

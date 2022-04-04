from typing import Any, Dict, List, Optional

import massgov
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    ManagedRequirement,
    ManagedRequirementStatus,
)
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_managed_requirements_update_log_attributes(
    fineos_managed_requirements: List[ManagedRequirementDetails],
    updated_managed_requirements: List[ManagedRequirement],
) -> Dict[str, Any]:
    return {
        "managed_requirements.updated_successfully": len(updated_managed_requirements),
        "managed_requirements.not_updated_successfully": len(fineos_managed_requirements)
        - len(updated_managed_requirements),
        "managed_requirements.received_as_open": len(
            [
                fmr
                for fmr in fineos_managed_requirements
                if str(fmr.status)
                == ManagedRequirementStatus.OPEN.managed_requirement_status_description
            ]
        ),
    }


def get_fineos_managed_requirement_log_attributes(
    fineos_managed_req: ManagedRequirementDetails,
) -> Dict[str, Any]:
    return {
        "fineos_managed_requirement.managedReqId": fineos_managed_req.managedReqId,
        "fineos_managed_requirement.status": fineos_managed_req.status,
        "fineos_managed_requirement.category": fineos_managed_req.category,
        "fineos_managed_requirement.type": fineos_managed_req.type,
        "fineos_managed_requirement.followUpDate": fineos_managed_req.followUpDate,
    }


def get_managed_requirement_log_attributes(managed_req: ManagedRequirement) -> Dict[str, Any]:
    return {
        "managed_requirement.id": managed_req.managed_requirement_id,
        "managed_requirement.fineos_managed_requirement_id": managed_req.fineos_managed_requirement_id,
        "managed_requirement.status": managed_req.managed_requirement_status.managed_requirement_status_description,
    }


def log_db_managed_requirements_not_in_fineos(
    fineos_managed_requirements: List[ManagedRequirementDetails],
    db_managed_requirements: List[ManagedRequirement],
    log_attributes: Dict,
) -> None:
    db_requirement_ids = {
        str(requirement.fineos_managed_requirement_id) for requirement in db_managed_requirements
    }

    fineos_requirement_ids = {
        str(requirement.managedReqId) for requirement in fineos_managed_requirements
    }

    db_requirements_not_in_fineos_ids = db_requirement_ids - fineos_requirement_ids

    if len(db_requirements_not_in_fineos_ids) > 0:
        logger.warning(
            "Claim has managed requirements not present in the data received from fineos.",
            extra={
                **log_attributes,
                "managed_requirements.fineos_id": db_requirements_not_in_fineos_ids,
            },
        )


def log_managed_requirement_issues(
    fineos_managed_requirements: List[ManagedRequirementDetails],
    managed_requirements: List[ManagedRequirement],
    db_absence_periods: Optional[List[AbsencePeriod]],
    log_attributes: Dict,
) -> None:
    """
    This method logs any potential unexpected scenarios related to managed requirements, such as:
    - An open requirement in the DB, even though all absence periods have a decision.
    - More than one open requirement in the DB on a claim
    - Requirements that exist in our DB that are not found in FINEOS.

    This should only be called using data that is confirmed to be up to date, e.g. right after
    syncing managed requirements and absence periods, using the freshest data from the DB.
    """
    open_requirements = [req for req in managed_requirements if req.is_open]
    open_requirement_ids = [req.fineos_managed_requirement_id for req in open_requirements]

    # Check if we have an open requirement and no pending absence period decisions.
    if db_absence_periods:
        decisions_finalized = all([d.has_final_decision for d in db_absence_periods])

        if len(open_requirement_ids) > 0 and decisions_finalized:
            logger.warning(
                "Claim has open managed requirement but all absence periods already have a final decision.",
                extra=log_attributes,
            )

    # Check if we have more than one open requirement.
    if len(open_requirement_ids) > 1:
        logger.warning(
            "Multiple open managed requirements were found.",
            extra={**log_attributes, "fineos_managed_requirements_ids": open_requirement_ids},
        )

    # Check if we have any "ghost" requirements in the DB.
    log_db_managed_requirements_not_in_fineos(
        fineos_managed_requirements, managed_requirements, log_attributes
    )

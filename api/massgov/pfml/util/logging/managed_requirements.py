from typing import Any, Dict, List

from massgov.pfml.db.models.employees import ManagedRequirement, ManagedRequirementStatus
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails


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

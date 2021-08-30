from typing import Any, Dict

from massgov.pfml.db.models.employees import User


def get_employer_log_attributes(current_user: User) -> Dict[str, Any]:
    """
    Determine the requesting user's employer relationships & verification status
    """

    employers = list(current_user.employers)
    verified_employers = [
        e.employer_id for e in current_user.employers if current_user.verified_employer(e)
    ]
    log_attributes = {
        "num_employers": len(employers),
        "num_verified_employers": len(verified_employers),
        "num_unverified_employers": len(employers) - len(verified_employers),
    }
    return log_attributes

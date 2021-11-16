from typing import Optional

from massgov.pfml.api.authorization.flask import READ, can
from massgov.pfml.db.models.employees import Claim, User


def user_has_access_to_claim(claim: Claim, current_user: Optional[User]) -> bool:
    if current_user is None:
        return False

    if can(READ, "EMPLOYER_API") and claim.employer in current_user.employers:
        # User is leave admin for the employer associated with claim
        return current_user.verified_employer(claim.employer)

    application = claim.application  # type: ignore

    if application and application.user == current_user:
        # User is claimant and this is their claim
        return True

    return False

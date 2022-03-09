from massgov.pfml.api.authorization.flask import READ, can
from massgov.pfml.db.models.employees import Claim, User


def user_has_access_to_claim(claim: Claim, current_user: User) -> bool:

    # When user is LA for the employer associated with claim
    if can(READ, "EMPLOYER_API") and claim.employer in current_user.employers:
        leave_admin = current_user.get_user_leave_admin_for_employer(claim.employer)

        # If LA is not verified, deny access
        if not leave_admin.verified:
            return False

        # The leave admin is verified
        # If their employer does NOT use organization units, allow access
        if not claim.employer.uses_organization_units:
            return True

        # If the employer uses organization units
        # check if LA has access to this claim's org unit
        can_view_org_unit = False
        # or if LA has been notified about this claim
        has_been_notified = False

        if claim.organization_unit is not None and len(leave_admin.organization_units) > 0:
            can_view_org_unit = claim.organization_unit in leave_admin.organization_units

        if not can_view_org_unit:
            # we'll only check notifications as a "last resort"/override
            notification_absence_ids = current_user.get_leave_admin_notifications()
            has_been_notified = claim.fineos_absence_id in notification_absence_ids

        return can_view_org_unit or has_been_notified

    application = claim.application  # type: ignore

    if application and application.user == current_user:
        # User is claimant and this is their claim
        return True

    return False

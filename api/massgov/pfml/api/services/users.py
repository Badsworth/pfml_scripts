from datetime import datetime, timezone
from typing import Optional, cast

import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.mfa as mfa
import massgov.pfml.util.logging
from massgov.pfml.api.models.common import Phone
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.services.administrator_fineos_actions import update_leave_admin_with_fineos
from massgov.pfml.db.models.employees import (
    LkMFADeliveryPreference,
    LkMFADeliveryPreferenceUpdatedBy,
    MFADeliveryPreference,
    Role,
    User,
)
from massgov.pfml.mfa import MFAUpdatedBy
from massgov.pfml.util.users import has_role_in

logger = massgov.pfml.util.logging.get_logger(__name__)


def update_user(
    db_session: db.Session,
    user: User,
    update_request: UserUpdateRequest,
    # TODO (PORTAL-1828): Remove X-FF-Sync-Cognito-Preferences feature flag header
    save_mfa_preference_to_cognito: bool,
    cognito_auth_token: str,
) -> User:

    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "mfa_delivery_preference":
            _update_mfa_preference(
                db_session,
                user,
                value,
                save_mfa_preference_to_cognito,
                cognito_auth_token,
            )
            continue

        if key == "mfa_phone_number":
            if value is not None:
                value = value.e164
        if key == "phone_number":
            if value is not None:
                _maybe_set_extension(user, value)
                value = value.e164
        setattr(user, key, value)

    return user


def _maybe_set_extension(user: User, phone: Phone) -> None:
    if phone and phone.extension:
        user.phone_extension = phone.extension


def _update_mfa_preference(
    db_session: db.Session,
    user: User,
    value: Optional[str],
    save_mfa_preference_to_cognito: bool,
    cognito_auth_token: str,
) -> None:
    existing_mfa_preference = user.mfa_preference_description()
    if value == existing_mfa_preference:
        return

    mfa_preference = (
        db_lookups.by_value(db_session, LkMFADeliveryPreference, value)
        if value is not None
        else None
    )
    # the type checker doesn't know that user.mfa_delivery_preference can be None so
    # ignore the type warning
    user.mfa_delivery_preference = mfa_preference  # type: ignore

    # Keep a copy of the last updated timestamp before we update it. This is used later for logging
    # feature metrics
    updated_by = MFAUpdatedBy.USER
    last_updated_at = user.mfa_delivery_preference_updated_at

    _update_mfa_preference_audit_trail(db_session, user, updated_by)

    log_attributes = {
        "mfa_preference": value,
        "save_mfa_preference_to_cognito": save_mfa_preference_to_cognito,
    }
    logger.info("MFA preference updated for user in DB", extra=log_attributes)

    if save_mfa_preference_to_cognito:
        _update_mfa_in_cognito(value, cognito_auth_token)

    if value == "Opt Out" and existing_mfa_preference is not None:
        # Try to handle MFA side-effects but don't fail the API request if there is a problem. This allows
        # the DB changes to be committed even if we fail to send the MFA disabled email so that the DB stays
        # consistent with Cognito
        try:
            mfa.handle_mfa_disabled(user, last_updated_at)
        except Exception as error:
            logger.error(
                "Error handling expected side-effects of disabling MFA. MFA is still disabled, and the API request is still successful.",
                exc_info=error,
            )


def _update_mfa_in_cognito(value, cognito_auth_token):
    if value == "SMS":
        mfa.enable_mfa(cognito_auth_token)
    elif value == "Opt Out":
        mfa.disable_mfa(cognito_auth_token)
    else:
        logger.error("Unexpected value for MFA option. Should be SMS or Opt Out.")


def _update_mfa_preference_audit_trail(
    db_session: db.Session, user: User, updated_by: MFAUpdatedBy
) -> None:
    # when a user changes their security preferences
    # we want to record an audit trail of who made the change, and when
    now = datetime.now(timezone.utc)
    user.mfa_delivery_preference_updated_at = now

    if updated_by == MFAUpdatedBy.ADMIN:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "Admin")
    else:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "User")

    mfa_updated_by = cast(LkMFADeliveryPreferenceUpdatedBy, mfa_updated_by)
    user.mfa_delivery_preference_updated_by = mfa_updated_by


def admin_disable_mfa(
    db_session: db.Session,
    user: User,
) -> None:
    """API administrator action for disabling MFA on a user's account. This is used to unlock users who have
    been locked out of their account due to MFA but should be used carefully and only after a user has had their
    identity verified"""
    existing_mfa_preference = user.mfa_preference_description()
    if MFADeliveryPreference.OPT_OUT.description == existing_mfa_preference:
        return

    opt_out = cast(
        LkMFADeliveryPreference, db_lookups.by_value(db_session, LkMFADeliveryPreference, "Opt Out")
    )
    user.mfa_delivery_preference = opt_out

    # Keep a copy of the last updated timestamp before we update it. This is used later for logging
    # feature metrics
    updated_by = MFAUpdatedBy.ADMIN
    last_updated_at = user.mfa_delivery_preference_updated_at

    _update_mfa_preference_audit_trail(db_session, user, updated_by)

    log_attributes = {
        "mfa_preference": "Opt Out",
        "updated_by": updated_by.value,
    }
    logger.info("MFA disabled for user", extra=log_attributes)

    mfa.handle_mfa_disabled_by_admin(user, last_updated_at)


def handle_user_patch_fineos_side_effects(user: User, request_body: UserUpdateRequest) -> None:
    if (
        has_role_in(user, [Role.EMPLOYER])
        and request_body.first_name
        and request_body.last_name
        and request_body.phone_number
    ):
        try:
            for leave_admin in user.user_leave_administrators:
                update_leave_admin_with_fineos(user, request_body, leave_admin)
        except Exception:
            logger.warning(
                "leave_admin_update - fineos sync failed",
                extra={"user_id": user.user_id, "fineos_web_id": leave_admin.fineos_web_id},
                exc_info=True,
            )

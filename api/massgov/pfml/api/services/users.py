from datetime import datetime, timezone
from typing import Optional

import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.util.logging
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.db.models.employees import (
    LkMFADeliveryPreference,
    LkMFADeliveryPreferenceUpdatedBy,
    MFADeliveryPreference,
    User,
)
from massgov.pfml.mfa import handle_mfa_disabled, handle_mfa_enabled

logger = massgov.pfml.util.logging.get_logger(__name__)


def update_user(
    db_session: db.Session,
    user: User,
    update_request: UserUpdateRequest,
    sync_cognito_preferences: bool,
    cognito_auth_token: str,
) -> User:
    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "mfa_delivery_preference":
            _update_mfa_preference(
                db_session, user, key, value, sync_cognito_preferences, cognito_auth_token,
            )
            continue

        if key == "mfa_phone_number":
            if value is not None:
                value = value.e164

        setattr(user, key, value)

    return user


def _update_mfa_preference(
    db_session: db.Session,
    user: User,
    key: str,
    value: Optional[str],
    sync_cognito_preferences: bool,
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
    setattr(user, key, mfa_preference)

    # Keep a copy of the last updated timestamp before we update it. This is used later for logging
    # feature metrics
    updated_by = "user"
    last_updated_at = user.mfa_delivery_preference_updated_at

    _update_mfa_preference_audit_trail(db_session, user, updated_by)

    log_attributes = {
        "mfa_preference": value,
        "sync_cognito_preferences": sync_cognito_preferences,
    }
    logger.info("MFA updated for user", extra=log_attributes)

    if value == "Opt Out" and existing_mfa_preference is not None:
        handle_mfa_disabled(user, last_updated_at, sync_cognito_preferences, cognito_auth_token)
    elif value == "SMS" and sync_cognito_preferences:
        handle_mfa_enabled(user, cognito_auth_token)


def _update_mfa_preference_audit_trail(db_session: db.Session, user: User, updated_by: str) -> None:
    # when a user changes their security preferences
    # we want to record an audit trail of who made the change, and when
    now = datetime.now(timezone.utc)
    mfa_delivery_preference_updated_at = "mfa_delivery_preference_updated_at"
    setattr(user, mfa_delivery_preference_updated_at, now)

    if updated_by == "admin":
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "Admin")
    else:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "User")

    mfa_delivery_preference_updated_by = "mfa_delivery_preference_updated_by"
    setattr(user, mfa_delivery_preference_updated_by, mfa_updated_by)


# todo: add comment
def admin_disable_mfa(db_session: db.Session, user: User,) -> None:
    existing_mfa_preference = user.mfa_preference_description()
    if MFADeliveryPreference.OPT_OUT.mfa_delivery_preference_description == existing_mfa_preference:
        return

    setattr(user, "mfa_delivery_preference", MFADeliveryPreference.OPT_OUT)

    # Keep a copy of the last updated timestamp before we update it. This is used later for logging
    # feature metrics
    updated_by = "admin"

    _update_mfa_preference_audit_trail(db_session, user, updated_by)

    log_attributes = {
        "mfa_preference": "Opt Out",
        "updated_by": updated_by,
    }
    logger.info("MFA disabled for user", extra=log_attributes)

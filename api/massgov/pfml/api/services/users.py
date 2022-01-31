from datetime import datetime, timezone
from typing import Optional

import massgov.pfml.db as db
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.util.logging
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.util.phone import convert_to_E164
from massgov.pfml.db.models.employees import (
    LkMFADeliveryPreference,
    LkMFADeliveryPreferenceUpdatedBy,
    User,
)
from massgov.pfml.util.users import send_mfa_disabled_email

logger = massgov.pfml.util.logging.get_logger(__name__)


def update_user(
    db_session: db.Session, user: User, update_request: UserUpdateRequest, updated_by: str = "User"
) -> User:
    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "mfa_delivery_preference":
            _update_mfa_preference(db_session, user, key, value, updated_by)
            continue

        if key == "mfa_phone_number":
            if value is not None:
                value = convert_to_E164(value)

        setattr(user, key, value)

    return user


def _update_mfa_preference(
    db_session: db.Session, user: User, key: str, value: Optional[str], updated_by: str
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
    last_updated_at = user.mfa_delivery_preference_updated_at
    _update_mfa_preference_audit_trail(db_session, user, updated_by)

    log_attributes = {"mfa_preference": value, "updated_by": updated_by}
    logger.info("MFA updated for user", extra=log_attributes)

    if value == "Opt Out" and existing_mfa_preference is not None:
        _handle_mfa_disabled(user, last_updated_at)


def _update_mfa_preference_audit_trail(db_session: db.Session, user: User, updated_by: str) -> None:
    # when a user changes their security preferences
    # we want to record an audit trail of who made the change, and when
    now = datetime.now(timezone.utc)
    mfa_delivery_preference_updated_at = "mfa_delivery_preference_updated_at"
    setattr(user, mfa_delivery_preference_updated_at, now)

    if updated_by.lower() == "admin":
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "Admin")
    else:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "User")

    mfa_delivery_preference_updated_by = "mfa_delivery_preference_updated_by"
    setattr(user, mfa_delivery_preference_updated_by, mfa_updated_by)


def _handle_mfa_disabled(user: User, last_enabled_at: Optional[datetime]) -> None:
    """Helper method for handling necessary actions after MFA is disabled for a user (send email, logging, etc)"""
    # These values should always be set by the time a user disables MFA but the
    # linter doesn't know that. This prevents a linter failure
    assert last_enabled_at
    assert user.email_address
    assert user.mfa_phone_number_last_four()

    now = datetime.now(timezone.utc)
    diff = now - last_enabled_at
    time_since_enabled_in_sec = round(diff.total_seconds())

    log_attributes = {
        "last_enabled_at": last_enabled_at,
        "time_since_enabled_in_sec": time_since_enabled_in_sec,
    }
    logger.info("MFA disabled for user", extra=log_attributes)
    try:
        send_mfa_disabled_email(user.email_address, user.mfa_phone_number_last_four())
    except Exception as error:
        logger.error("Error sending MFA disabled email", exc_info=error)
        raise error

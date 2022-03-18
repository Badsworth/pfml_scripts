from datetime import datetime, timezone
from typing import Optional, cast

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
from massgov.pfml.mfa import MFAUpdatedBy, handle_mfa_disabled, handle_mfa_disabled_by_admin

logger = massgov.pfml.util.logging.get_logger(__name__)


def update_user(
    db_session: db.Session,
    user: User,
    update_request: UserUpdateRequest,
    updated_by: MFAUpdatedBy = MFAUpdatedBy.USER,
) -> User:
    for key in update_request.__fields_set__:
        value = getattr(update_request, key)

        if key == "mfa_delivery_preference":
            _update_mfa_preference(db_session, user, key, value, updated_by)
            continue

        if key == "mfa_phone_number":
            if value is not None:
                value = value.e164

        setattr(user, key, value)

    return user


def _update_mfa_preference(
    db_session: db.Session, user: User, key: str, value: Optional[str], updated_by: MFAUpdatedBy
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

    log_attributes = {"mfa_preference": value, "updated_by": updated_by.value}
    logger.info("MFA updated for user", extra=log_attributes)

    if value == "Opt Out" and existing_mfa_preference is not None:
        handle_mfa_disabled(user, last_updated_at, updated_by)


def _update_mfa_preference_audit_trail(
    db_session: db.Session, user: User, updated_by: MFAUpdatedBy
) -> None:
    # when a user changes their security preferences
    # we want to record an audit trail of who made the change, and when
    now = datetime.now(timezone.utc)
    mfa_delivery_preference_updated_at = "mfa_delivery_preference_updated_at"
    setattr(user, mfa_delivery_preference_updated_at, now)

    if updated_by == MFAUpdatedBy.ADMIN:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "Admin")
    else:
        mfa_updated_by = db_lookups.by_value(db_session, LkMFADeliveryPreferenceUpdatedBy, "User")

    mfa_delivery_preference_updated_by = "mfa_delivery_preference_updated_by"
    setattr(user, mfa_delivery_preference_updated_by, mfa_updated_by)


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

    handle_mfa_disabled_by_admin(user, last_updated_at)

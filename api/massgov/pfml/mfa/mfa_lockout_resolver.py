import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.services.users import update_user
from massgov.pfml.db.models.employees import User
from massgov.pfml.db.queries.users import get_user_by_email
from massgov.pfml.util.aws.cognito import disable_user_mfa
from massgov.pfml.util.aws.sns import check_phone_number_opt_out, opt_in_phone_number

logger = logging.get_logger(__name__)


class MfaLockoutResolver:
    user_email: str
    log_attr: dict
    should_commit_changes: bool

    def __init__(
        self,
        user_email,
        psd_number,
        reason_for_disabling,
        agent_email,
        verification_method,
        dry_run,
        db_session=None,
    ):
        self.user_email = user_email
        self.log_attr = {
            "dry_run": dry_run,
            "psd_ticket_number": psd_number,
            "reason_for_disabling": reason_for_disabling,
            "contact_center_agent": agent_email,
            "identity_verification_method": verification_method,
        }

        if dry_run:
            self._log_info("***DRY RUN MODE ENABLED***")
        else:
            self._log_info("***DRY RUN MODE DISABLED***")

        self.db_session_raw = db.init(sync_lookups=True) if not db_session else db_session

        self.should_commit_changes = not dry_run

    def run(self):
        user = self._get_user()

        self._log_info("Starting MFA lockout resolution")

        self._resolve_lockout(user)

        self._log_info("Completed MFA lockout resolution!")

    def _resolve_lockout(self, user: User) -> None:

        self._disable_mfa_cognito()
        self._disable_mfa_pfml(user)
        self._set_sns_opt_in(user)

    def _get_user(self) -> User:
        self._log_info("Getting user from PFML API")

        with db.session_scope(self.db_session_raw) as db_session:
            user = get_user_by_email(db_session, self.user_email)

        if user is None:
            e = Exception("Unable to find user with the given email")
            self._log_error("Error finding user in PFML database", e)
            raise e

        self.log_attr["user_id"] = user.user_id

        self._log_info("...Done!")
        return user

    def _disable_mfa_cognito(self) -> None:
        self._log_info("Disabling user MFA in Cognito")

        try:
            if self.should_commit_changes:
                disable_user_mfa(self.user_email)
            else:
                self._log_info("(DRY RUN: Skipping API call to disable user MFA)")
        except Exception as e:
            self._log_error("Error disabling user MFA in Cognito", e)
            raise e

        self._log_info("...Done!")

    def _set_sns_opt_in(self, user: User) -> None:
        self._log_info("Checking user opt-in in SNS")

        if not user.mfa_phone_number:
            return

        # Check if a user has opted out of text messages with their phone number.
        try:
            user_opted_out = check_phone_number_opt_out(user.mfa_phone_number)
        except Exception as e:
            self._log_error("Error pulling opt-in status from SNS", e)
            raise e

        # Note: this can only be successfully run for a user once every 30 days!
        if user_opted_out:
            self._log_info("Setting user opt-in in SNS")
            try:
                if self.should_commit_changes:
                    opt_in_phone_number(user.mfa_phone_number)
                else:
                    self._log_info("(DRY RUN: Skipping API call to opt user into SNS)")
            except Exception as e:
                self._log_error("Error setting user opt-in in SNS", e)
                raise e

        self._log_info("...Done!")

    def _disable_mfa_pfml(self, user: User) -> None:
        self._log_info("Disabling user MFA in PFML db")

        update_request = UserUpdateRequest(mfa_delivery_preference="Opt Out")

        with db.session_scope(self.db_session_raw) as db_session:
            try:
                if self.should_commit_changes:
                    update_user(db_session, user, update_request, "Admin")
                else:
                    self._log_info("(DRY RUN: Skipping API call to disable MFA in PFML DB)")
            except Exception as e:
                self._log_error("Error disabling user MFA in PFML db", e)
                raise e

        self._log_info("...Done!")

    def _log_info(self, message: str) -> None:
        """Helper for adding metadata to each log statement"""
        logger.info(message, extra=self.log_attr)

    def _log_error(self, message: str, error: Exception) -> None:
        """Helper for adding metadata to each log statement"""
        logger.error(message, exc_info=error, extra=self.log_attr)

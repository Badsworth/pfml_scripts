import argparse
import sys

import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.services.users import update_user
from massgov.pfml.db.models.employees import User
from massgov.pfml.db.queries.users import get_user_by_email
from massgov.pfml.util.aws.cognito import disable_user_mfa
from massgov.pfml.util.bg import background_task

db_session_raw = db.init(sync_lookups=True)
logger = logging.get_logger(__name__)


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fixes users locked out of their accounts via MFA")
    parser.add_argument(
        "--email", type=str, required=True, help="(Required) The user's email address"
    )
    parser.add_argument(
        "--dry_run",
        type=str,
        default="True",
        help="(Optional) If enabled, this script will not make any changes to Cognito or the PFML db",
    )

    return parser


def _get_user(email: str) -> User:
    logger.info("Getting user from PFML API")

    with db.session_scope(db_session_raw) as db_session:
        user = get_user_by_email(db_session, email)

    if user is None:
        raise Exception("Unable to find user with the given email")

    logger.info("...Done!")
    return user


def _disable_mfa_cognito(email: str, dry_run: bool) -> None:
    logger.info("Disabling user MFA in Cognito")

    try:
        if dry_run:
            logger.info("(DRY RUN: Skipping API call)")
        else:
            disable_user_mfa(email)
    except Exception as e:
        logger.error("Error disabling user MFA in Cognito", exc_info=e)
        raise e

    logger.info("...Done!")


def _disable_mfa_pfml(user: User, dry_run: bool) -> None:
    logger.info("Disabling user MFA in PFML db")

    update_request = UserUpdateRequest(mfa_delivery_preference="Opt Out")

    with db.session_scope(db_session_raw) as db_session:
        try:
            if dry_run:
                logger.info("(DRY RUN: Skipping API call)")
            else:
                update_user(db_session, user, update_request, "Admin")
        except Exception as e:
            logger.error("Error disabling user MFA in PFML db", exc_info=e)
            raise e

    logger.info("...Done!")


def fix_mfa_lockout(email: str, dry_run: bool) -> None:
    logger.info("Starting MFA lockout resolution")
    logger.info(f"dry_run mode is: {dry_run}")

    user = _get_user(email)

    _disable_mfa_cognito(email, dry_run)
    _disable_mfa_pfml(user, dry_run)

    logger.info("Completed MFA lockout resolution!")


@background_task("mfa-lockout-resolution")
def main() -> None:
    args = sys.argv[1:]
    parser = _create_parser()
    parsed_args = parser.parse_args(args)

    email = parsed_args.email
    dry_run = parsed_args.dry_run.lower() == "true"

    fix_mfa_lockout(email, dry_run)

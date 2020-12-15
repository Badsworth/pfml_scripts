import boto3

import massgov.pfml.util.config as config
import massgov.pfml.util.logging
from massgov.pfml import db, fineos
from massgov.pfml.api.services.administrator_fineos_actions import register_leave_admin_with_fineos
from massgov.pfml.db.models.employees import UserLeaveAdministrator

logger = massgov.pfml.util.logging.get_logger(__name__)


def find_user_and_register(
    db_session: db.Session,
    leave_admin: UserLeaveAdministrator,
    fineos_client: fineos.AbstractFINEOSClient,
) -> None:
    if leave_admin.user is None:
        logger.error(
            "No user found for record: ",
            extra={"user_id": leave_admin.user_id, "employer_id": leave_admin.employer_id},
        )
        return

    if leave_admin.employer is None:
        logger.error(
            "No employer found for record: ",
            extra={"user_id": leave_admin.user_id, "employer_id": leave_admin.employer_id},
        )
        return

    if leave_admin.employer.fineos_employer_id is None:
        logger.error(
            "No FINEOS employer ID found for record: ",
            extra={"user_id": leave_admin.user_id, "employer_id": leave_admin.employer_id},
        )
        return

    register_leave_admin_with_fineos(
        # TODO: Set a real admin full name - https://lwd.atlassian.net/browse/EMPLOYER-540
        admin_full_name="Leave Administrator",
        admin_email=leave_admin.user.email_address,
        admin_area_code=None,
        admin_phone_number=None,
        employer=leave_admin.employer,
        user=leave_admin.user,
        db_session=db_session,
        fineos_client=fineos_client,
    )


def find_admins_without_registration(db_session: db.Session):
    # Get records with no fineos_web_id
    # For each record, lookup the user and employer
    # Register with fineos
    leave_admins_without_fineos = (
        db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.fineos_web_id == None)  # noqa: E711
        .all()
    )

    if len(leave_admins_without_fineos) > 0:
        fineos_client_config = fineos.factory.FINEOSClientConfig.from_env()
        if fineos_client_config.oauth2_client_secret is None:
            aws_ssm = boto3.client("ssm", region_name="us-east-1")
            fineos_client_config.oauth2_client_secret = config.get_secret_from_env(
                aws_ssm, "FINEOS_CLIENT_OAUTH2_CLIENT_SECRET"
            )

        fineos_client = fineos.create_client(fineos_client_config)

    logger.info(
        "Leave admin records to process", extra={"To process": len(leave_admins_without_fineos)}
    )

    for leave_admin in leave_admins_without_fineos:
        find_user_and_register(db_session, leave_admin, fineos_client)

    leave_admins_without_fineos_count = (
        db_session.query(UserLeaveAdministrator)
        .filter(UserLeaveAdministrator.fineos_web_id == None)  # noqa: E711
        .count()
    )

    logger.info(
        "Leave admin records left unprocessed",
        extra={"Left unprocessed": leave_admins_without_fineos_count},
    )

    logger.info("Completed FINEOS Leave Admin Creation Script")


def main():
    massgov.pfml.util.logging.init("register_leave_admins_with_fineos")
    logger.info("Beginning FINEOS Leave Admin Creation Script")
    db_session_raw = db.init()

    with db.session_scope(db_session_raw) as db_session:
        find_admins_without_registration(db_session)


if __name__ == "__main__":
    main()

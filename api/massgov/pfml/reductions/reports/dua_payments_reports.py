import os
from typing import List

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.reductions.config as reductions_config
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType, State
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

logger = logging.get_logger(__name__)


def send_dua_reductions_report(db_session: db.Session) -> None:
    s3_config = reductions_config.get_s3_config()

    dfml_outbound_directory = os.path.join(
        s3_config.s3_bucket_uri, s3_config.s3_dfml_outbound_directory_path
    )
    error_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dfml_error_directory_path)

    reductions_ref_files = _get_dua_reductions_ref_files(dfml_outbound_directory, db_session)
    if len(reductions_ref_files) == 0:
        raise NoResultFound("No results returned for ReferenceFile query.")
    elif len(reductions_ref_files) > 1:
        raise MultipleResultsFound(
            "Multiple results returned for ReferenceFile query. Exactly one is expected"
        )
    else:
        reductions_ref_file = reductions_ref_files[0]

    try:
        # Temporarily stop sending the DUA payments email, as it is redundant with a separate
        # process set up in https://lwd.atlassian.net/browse/OPSS-120 to separately send a zipped
        # version of this file.
        # See https://lwd.atlassian.net/browse/API-2587 for more details.
        # TODO (API-1858) turn this back on once we add support for compressing attachments
        # _send_dua_payments_email(reductions_ref_file, db_session, reductions_ref_file.file_location)

        _update_ref_file(reductions_ref_file, db_session)
        _update_state_log(reductions_ref_file, db_session)

    except Exception:
        # Move to error directory and update ReferenceFile.
        filename = os.path.basename(reductions_ref_file.file_location)
        dest_path = os.path.join(error_dir, filename)
        payments_util.move_file_and_update_ref_file(db_session, dest_path, reductions_ref_file)

        state_log_util.create_finished_state_log(
            associated_model=reductions_ref_file,
            end_state=State.DUA_REDUCTIONS_REPORT_ERROR,
            outcome=state_log_util.build_outcome(
                "Error emailing new DUA reductions payments to DFML"
            ),
            db_session=db_session,
        )

        logger.exception("Error emailing new DUA reductions payments to DFML")

        db_session.commit()

        raise


def _get_dua_reductions_ref_files(
    dfml_outbound_directory: str, db_session: db.Session
) -> List[ReferenceFile]:

    return (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DUA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
            ReferenceFile.file_location.like(dfml_outbound_directory + "%"),
        )
        .all()
    )


def _update_ref_file(ref_file: ReferenceFile, db_session: db.Session) -> None:
    s3_config = reductions_config.get_s3_config()

    source_dir = s3_config.s3_dfml_outbound_directory_path
    destination_dir = s3_config.s3_dfml_archive_directory_path

    payments_util.move_reference_file(db_session, ref_file, source_dir, destination_dir)


def _update_state_log(ref_file: ReferenceFile, db_session: db.Session) -> None:
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DUA_REDUCTIONS_REPORT_SENT,
        outcome=state_log_util.build_outcome("Emailed new DUA reductions payments to DFML"),
        db_session=db_session,
    )

    db_session.commit()


def _send_dua_payments_email(
    ref_file: ReferenceFile, db_session: db.Session, report_file_path: str
) -> None:

    email_config = reductions_config.get_email_config()
    sender = email_config.pfml_email_address
    recipient = email_config.agency_reductions_email_address
    subject = f"DUA reductions payments as of {datetime_util.get_now_us_eastern():%m/%d/%Y}"
    body = "Attached please find a report that includes all DUA reductions payments for PFML claimants to date"
    bounce_forwarding_email_address_arn = email_config.bounce_forwarding_email_address_arn

    email_recipient = EmailRecipient(to_addresses=[recipient])

    send_email(
        recipient=email_recipient,
        subject=subject,
        body_text=body,
        sender=sender,
        bounce_forwarding_email_address_arn=bounce_forwarding_email_address_arn,
        attachments=[report_file_path],
    )

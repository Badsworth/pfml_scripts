import os
from typing import Optional

from sqlalchemy.orm.exc import NoResultFound

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.reductions.config as reductions_config
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType, State
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

logger = logging.get_logger(__name__)


def send_consolidated_dia_reductions_report(db_session: db.Session) -> None:
    s3_config = reductions_config.get_s3_config()

    dfml_outbound_directory = os.path.join(
        s3_config.s3_bucket_uri, s3_config.s3_dfml_outbound_directory_path
    )
    error_dir = os.path.join(s3_config.s3_bucket_uri, s3_config.s3_dfml_error_directory_path)

    reductions_ref_file = _get_ref_file(
        db_session,
        dfml_outbound_directory,
        ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id,
    )

    if reductions_ref_file is None:
        raise NoResultFound

    error_ref_file = _get_ref_file(
        db_session,
        dfml_outbound_directory,
        ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT_ERRORS.reference_file_type_id,
    )

    try:
        error_file_path = error_ref_file and error_ref_file.file_location or None
        _send_consolidated_dia_payments_email(
            reductions_ref_file.file_location, error_file_path=error_file_path
        )

        _update_ref_file(db_session, reductions_ref_file)
        if error_ref_file:
            _update_ref_file(db_session, error_ref_file)

        _update_state_log(db_session, reductions_ref_file)

    except Exception:
        # Move to error directory and update ReferenceFile.
        filename = os.path.basename(reductions_ref_file.file_location)
        dest_path = os.path.join(error_dir, filename)
        payments_util.move_file_and_update_ref_file(db_session, dest_path, reductions_ref_file)

        if error_ref_file:
            error_filename = os.path.basename(error_ref_file.file_location)
            error_dest_path = os.path.join(error_dir, error_filename)
            payments_util.move_file_and_update_ref_file(db_session, error_dest_path, error_ref_file)

        state_log_util.create_finished_state_log(
            associated_model=reductions_ref_file,
            end_state=State.DIA_CONSOLIDATED_REPORT_ERROR,
            outcome=state_log_util.build_outcome(
                "Error emailing consolidated DIA reductions payments to DFML"
            ),
            db_session=db_session,
        )

        logger.exception("Error emailing consolidated DIA reductions payments to DFML")

        db_session.commit()

        raise


def _get_ref_file(
    db_session: db.Session, dfml_outbound_directory: str, reference_file_type_id: int
) -> Optional[ReferenceFile]:
    return (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id == reference_file_type_id,
            ReferenceFile.file_location.like(dfml_outbound_directory + "%"),
        )
        .one_or_none()
    )


def _update_ref_file(db_session: db.Session, ref_file: ReferenceFile) -> None:
    s3_config = reductions_config.get_s3_config()
    source_dir = s3_config.s3_dfml_outbound_directory_path
    destination_dir = s3_config.s3_dfml_archive_directory_path

    payments_util.move_reference_file(
        db_session, ref_file, source_dir, destination_dir,
    )


def _update_state_log(db_session: db.Session, ref_file: ReferenceFile) -> None:
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DIA_CONSOLIDATED_REPORT_SENT,
        outcome=state_log_util.build_outcome(
            "Emailed consolidated DIA reductions payments to DFML"
        ),
        db_session=db_session,
    )

    db_session.commit()


def _send_consolidated_dia_payments_email(
    report_file_path: str, error_file_path: Optional[str] = None
) -> None:
    email_config = reductions_config.get_email_config()
    sender = email_config.pfml_email_address
    recipient = email_config.agency_reductions_email_address
    subject = f"Consolidated DIA reductions payments as of {payments_util.get_now():%m/%d/%Y}"
    body = "Attached please find a report that includes the consolidated DIA reductions payments."
    error_report_text = " See records which could not be merged in a separately attached file."
    bounce_forwarding_email_address_arn = email_config.bounce_forwarding_email_address_arn

    attachments = [report_file_path]

    if error_file_path is not None:
        body = body + error_report_text
        attachments.append(error_file_path)

    email_recipient = EmailRecipient(to_addresses=[recipient])
    send_email(
        recipient=email_recipient,
        subject=subject,
        body_text=body,
        sender=sender,
        bounce_forwarding_email_address_arn=bounce_forwarding_email_address_arn,
        attachments=attachments,
    )

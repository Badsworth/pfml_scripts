import os
from typing import List

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.reductions.config as reductions_config
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType, State
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

logger = logging.get_logger(__name__)


def send_dia_reductions_report(db_session: db.Session) -> None:
    s3_config = reductions_config.get_s3_config()

    dfml_outbound_directory = os.path.join(
        s3_config.s3_bucket_uri, s3_config.s3_dfml_outbound_directory_path
    )

    reductions_ref_files = _get_dia_reductions_ref_files(dfml_outbound_directory, db_session)
    if len(reductions_ref_files) == 0:
        raise NoResultFound("No results returned for ReferenceFile query.")
    elif len(reductions_ref_files) > 1:
        raise MultipleResultsFound(
            "Multiple results returned for ReferenceFile query. Exactly one is expected"
        )
    else:
        reductions_ref_file = reductions_ref_files[0]

    _send_dia_payments_email(reductions_ref_file, db_session, reductions_ref_file.file_location)
    _update_ref_file(reductions_ref_file, db_session)
    _update_state_log(reductions_ref_file, db_session)


def _get_dia_reductions_ref_files(
    dfml_outbound_directory: str, db_session: db.Session
) -> List[ReferenceFile]:

    return (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DIA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
            ReferenceFile.file_location.like(dfml_outbound_directory + "%"),
        )
        .all()
    )


def _update_ref_file(ref_file: ReferenceFile, db_session: db.Session) -> None:
    s3_config = reductions_config.get_s3_config()
    source_dir = s3_config.s3_dfml_outbound_directory_path
    destination_dir = s3_config.s3_dfml_archive_directory_path

    payments_util.move_reference_file(
        db_session, ref_file, source_dir, destination_dir,
    )


def _update_state_log(ref_file: ReferenceFile, db_session: db.Session) -> None:
    state_log_util.create_finished_state_log(
        associated_model=ref_file,
        end_state=State.DIA_REDUCTIONS_REPORT_SENT,
        outcome=state_log_util.build_outcome("Emailed new DIA reductions payments to DFML"),
        db_session=db_session,
    )

    db_session.commit()


def _send_dia_payments_email(
    ref_file: ReferenceFile, db_session: db.Session, report_file_path: str
) -> None:
    email_config = reductions_config.get_email_config()
    sender = email_config.pfml_email_address
    recipient = email_config.agency_reductions_email_address
    subject = f"DIA reductions payments as of {payments_util.get_now():%m/%d/%Y}"
    body = "Attached please find a report that includes all DIA reductions payments for PFML claimants to date"
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

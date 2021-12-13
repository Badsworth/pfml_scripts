import os

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.util import logging
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)


def make_db_session() -> db.Session:
    return db.init(sync_lookups=True)


@background_task("copy-audit-report")
def main():
    with db.session_scope(make_db_session(), close=True) as db_session:
        _copy_audit_report_to_inbound_path(db_session)


def _copy_audit_report_to_inbound_path(db_session: db.Session) -> None:
    if os.getenv("ENVIRONMENT", None) in ["prod", None]:
        logger.exception("Unable to run copy-audit-report task in production or when env not set")
        raise Exception("Unable to run copy-audit-report task in production or when env not set")

    latest_report = (
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id
        )
        .order_by(ReferenceFile.created_at.desc())
        .first()
    )

    if not latest_report:
        logger.warning("No file found, unable to copy. Exiting task")
        return

    s3_config = payments_config.get_s3_config()

    # Copy the report to the dfml-responses s3 folder
    outgoing_file_name = f"{payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT}.csv"
    dfml_responses_path = os.path.join(s3_config.dfml_response_inbound_path, outgoing_file_name)
    file_util.copy_file(latest_report.file_location, str(dfml_responses_path))

    logger.info(
        "Done copying Payment Audit Report file to inbound folder",
        extra={"source": latest_report.file_location, "destination": str(dfml_responses_path)},
    )

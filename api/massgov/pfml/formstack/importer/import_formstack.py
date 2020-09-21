import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from pytz import timezone
from sqlalchemy import and_, desc
from sqlalchemy.orm.session import Session

import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.formstack.formstack_client import FormstackClient
from massgov.pfml.util.config import get_secret_from_env

logger = logging.get_logger("massgov.pfml.formstack.importer.import_formstack")

MANUAL_RUN_SOURCE_ID = "Formstack-Manual"
LAMBDA_RUN_SOURCE_ID = "Formstack-Lambda"


@dataclass
class ImportReport:
    status: str = ""
    query_start_time: Optional[str] = None
    query_end_time: Optional[str] = None
    total_submission_count: int = 0
    invalid_verification: int = 0
    unknown_fein: int = 0
    created_verifications: int = 0
    submissions_by_form: List[Dict] = field(default_factory=list)


def handler(event: Dict, context: Dict) -> None:
    """
    Formstack import lambda handler function that imports data from Formstack
    and uploads it in JSON files to AWS S3
    """
    logging.init(__name__)
    import_start_time = datetime.now()
    report_status = "success"
    submissions_by_form = []
    config = db.get_config()
    db_session_raw = db.init(config)

    if "is_daily_lambda" in event:
        source = LAMBDA_RUN_SOURCE_ID
    else:
        source = MANUAL_RUN_SOURCE_ID

    with db.session_scope(db_session_raw) as db_session:
        try:
            client = FormstackClient()

            if "form_id" in event:
                form_id = event["form_id"]
            elif os.getenv("form_id") is not None:
                form_id = os.getenv("form_id")
            else:
                form_id = None

            logger.info("Starting Formstack import run", extra={"form_id": form_id})

            query_start_time = (
                datetime.strptime(event["start_time"], "%Y-%m-%d %H:%M:%S")
                if "start_time" in event
                else get_last_successful_import_end_time(db_session)
            )
            query_end_time = (
                datetime.strptime(event["end_time"], "%Y-%m-%d %H:%M:%S")
                if "end_time" in event
                else import_start_time
            )

            form_ids = get_form_ids(client, form_id)

            submissions_by_form = process_submissions(
                client, form_ids, query_start_time, query_end_time
            )
        except Exception as error:
            logger.exception("Formstack Import exception while processing", extra={"error": error})
            report_status = "error"
        finally:
            write_to_import_log(
                db_session,
                submissions_by_form or [],
                source,
                import_start_time,
                query_start_time,
                query_end_time,
                report_status,
            )


def get_last_successful_import_end_time(db_session: Session) -> datetime:
    default_end_time = datetime.now() - timedelta(hours=24)

    import_log_row = (
        db_session.query(ImportLog)
        .filter(and_(ImportLog.source == LAMBDA_RUN_SOURCE_ID, ImportLog.status == "success"))
        .order_by(desc("start"))
        .first()
    )
    if import_log_row is None:
        logger.info(
            "Failed to retrieve ImportLog record for last import time -- using default of 24 hours ago"
        )
        end_time = default_end_time
    else:
        if import_log_row.report is not None:
            import_report = json.loads(import_log_row.report)
            end_time = datetime.fromisoformat(import_report["query_end_time"])
        else:
            logger.info(
                "ImportLog record did not contain last import time -- using default of 24 hours ago"
            )
            end_time = default_end_time

    return end_time


def get_form_ids(client: FormstackClient, form_id: str = "") -> List[str]:
    """
    Returns a list of form IDs to be processed.  If one is specified via the triggering event, the list
    will only contain that form ID.
    """
    if not form_id:
        forms = client.get_forms()
        return list(map(lambda form_dict: form_dict["id"], forms))
    else:
        return [form_id]


def process_submissions(
    client: FormstackClient,
    form_ids: List[str],
    query_start_time: datetime,
    query_end_time: datetime,
) -> List[Dict]:
    """
    Given a list of form IDs, each form ID's submission data will be retrieved based on the start
    and end times.  The submission data will then be saved in S3. A list of dictionaries containing the form_id
    and the total submissions collected will be returned.  Formstack APIs require timestamps to be of the US/Eastern
    timezone.
    """
    tz = timezone("America/New_York")
    start_time_est = tz.fromutc(query_start_time).strftime("%Y-%m-%d %H:%M:%S")
    end_time_est = tz.fromutc(query_end_time).strftime("%Y-%m-%d %H:%M:%S")
    submission_counts = []
    for form_id in form_ids:
        total_submissions = 0
        submissions = []
        for submission in client.get_submissions(form_id, start_time_est, end_time_est):
            total_submissions += 1
            submissions.append(submission.dict())
        if submissions:
            write_to_s3(
                submissions,
                form_id,
                query_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                query_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            )
        submission_counts.append({"form_id": form_id, "total_submissions": total_submissions})
    return submission_counts


def write_to_s3(submissions: List[Dict], form_id: str, start_time: str, end_time: str) -> None:
    """
    Writes submission data to the S3 bucket.
    """
    aws_ssm = boto3.client("ssm", region_name="us-east-1")
    s3 = boto3.resource("s3", region_name="us-east-1")
    bucket_name = get_secret_from_env(aws_ssm, "FORMSTACK_DATA_BUCKET_NAME")
    key = f"{form_id}_{start_time.replace(' ', '_')}_{end_time.replace(' ', '_')}.json"
    report_body = json.dumps(submissions, indent=2)
    s3.Bucket(bucket_name).put_object(Key=key, Body=report_body)
    logger.info(
        "Formstack Import wrote all submissions to S3",
        extra={"num_form_submissions_written": len(submissions)},
    )


def write_to_import_log(
    db_session: Session,
    submissions_by_form: List[Dict],
    source: str,
    import_start_time: datetime,
    query_start_time: Optional[datetime],
    query_end_time: Optional[datetime],
    status: str,
) -> ImportLog:
    """
    Writes to the import_log table in the DB.
    """
    total_submission_count = functools.reduce(
        lambda a, b: a + b["total_submissions"], submissions_by_form, 0
    )
    report = ImportReport(
        query_start_time=query_start_time.isoformat() if query_start_time is not None else None,
        query_end_time=query_end_time.isoformat() if query_end_time is not None else None,
        total_submission_count=total_submission_count,
        submissions_by_form=submissions_by_form,
        status=status,
    )

    logger.info("Adding Formstack import report to import log", extra={"source": source})
    import_log = ImportLog(
        source=source,
        import_type="Initial",
        status=report.status,
        report=json.dumps(asdict(report), indent=2),
        start=import_start_time,
        end=datetime.now(),
    )
    db_session.add(import_log)
    db_session.flush()
    db_session.refresh(import_log)
    logger.info("Formstack Import wrote report to the import log")

    return import_log

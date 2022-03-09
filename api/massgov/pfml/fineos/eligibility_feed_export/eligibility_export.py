#
# Executable functionality to export Eligibility Feed to FINEOS.
#
import dataclasses

import boto3

import massgov.pfml.fineos.eligibility_feed as eligibility_feed
import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.batch.log
import massgov.pfml.util.logging as logging
from massgov.pfml import db, fineos
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)


def make_fineos_client() -> fineos.AbstractFINEOSClient:
    return fineos.create_client()


def make_db_session() -> db.Session:
    return db.init()


def make_fineos_boto_session(config: eligibility_feed.EligibilityFeedExportConfig) -> boto3.Session:
    return aws_sts.assume_session(
        role_arn=config.fineos_aws_iam_role_arn,
        external_id=config.fineos_aws_iam_role_external_id,
        role_session_name="eligibility_feed",
        region_name="us-east-1",
    )


@background_task("fineos-eligibility-feed-export")
def main():
    """Entry point for ECS task

    For an ECS task, the return value is taken as a status code, so should not
    return anything (or anything non-zero) from this function.
    """
    main_with_return()
    return 0


def main_with_return():
    logger.info("Starting FINEOS eligibility feed export run")

    config = eligibility_feed.EligibilityFeedExportConfig()

    with db.session_scope(make_db_session(), close=True) as db_session:
        report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
            db_session, "Eligibility export", config.mode.name.lower()
        )

    output_transport_params = None
    output_directory_path = f"{config.output_directory_path}/absence-eligibility/upload"

    # Note that the IAM role for the Eligibility Feed Export Lambda/ECS Task
    # does not have access to any S3 bucket in the PFML account by default. So
    # in order to test the functionality by writing to a non-FINEOS S3 location,
    # the IAM role needs updated for the test as well.
    if eligibility_feed.is_fineos_output_location(output_directory_path):
        session = make_fineos_boto_session(config)
        output_transport_params = dict(session=session)

    fineos_client = make_fineos_client()

    if config.mode is eligibility_feed.EligibilityFeedExportMode.UPDATES:
        with db.session_scope(make_db_session(), close=True) as db_session:
            process_result = eligibility_feed.process_employee_updates(
                db_session,
                fineos_client,
                output_directory_path,
                output_transport_params,
                export_file_number_limit=config.export_file_number_limit,
            )
    elif config.mode is eligibility_feed.EligibilityFeedExportMode.LIST:
        employer_ids = config.employer_ids.split(",")
        if config and len(employer_ids) > 0:
            with db.session_scope(make_db_session(), close=True) as db_session:
                process_result = eligibility_feed.process_a_list_of_employers(
                    employer_ids,
                    db_session,
                    fineos_client,
                    output_directory_path,
                    output_transport_params,
                )
        else:
            logger.info(
                "Task started in 'LIST' mode but no list of employers provided. "
                "If you intended to start task in this mode please provide a list of "
                "employers to process in the ELIGIBILITY_FEED_LIST_OF_EMPLOYER_IDS environment variable."
            )
    else:
        process_result = eligibility_feed.process_all_employers(
            make_db_session, make_fineos_client, make_fineos_boto_session, config
        )

    with db.session_scope(make_db_session(), close=True) as db_session:
        massgov.pfml.util.batch.log.update_log_entry(
            db_session, report_log_entry, "success", process_result
        )

    logger.info(
        "Finished writing all eligibility feeds",
        extra={"report": dataclasses.asdict(process_result)},
    )

    return dataclasses.asdict(process_result)

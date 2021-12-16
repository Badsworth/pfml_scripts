#
# Copies certain FINEOS files into an appropriate table structure in the BI warehouse so they
# can be easily ingested by AWS Glue or Qlik.
#

import argparse
import os
from datetime import datetime, timedelta

from pydantic import BaseSettings, Field

import massgov.pfml.util.aws.sts
import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.util.bg import background_task

logger = massgov.pfml.util.logging.get_logger(__name__)

# These extracts use a 'SELECT * FROM FINEOS.TABLENAME' query so we treat their contents as a full table in the
# warehouse and overwrite the contents each day.
fineos_warehouse_full_extracts = [
    "Employee_feed.csv",
    "VBI_BENEFIT.csv",
    "VBI_BENEFITADJUSTMENT.csv",
    "VBI_BENEFITPAYMENTLINK.csv",
    "VBI_BENEFITPAYMENTPARAMETERS.csv",
    "VBI_BENEFITPERIOD.csv",
    "VBI_CALCULATEDBENEFITAMOUNTS.csv",
    "VBI_PROCESSSTEPVISIT.csv",
    "VBI_ABSENCECASE.csv",
    "VBI_ABSENCEEMPLOYMENT.csv",
    "VBI_ABSENCEPERIODREPORTINGINFO.csv",
    "VBI_ABSENCETIMESPAN.csv",
    "VBI_EPISODICABSENCEPERIOD.csv",
    "VBI_CANCELLEDDATEOFABSENCE.csv",
    "VBI_LEAVEPLANREQUESTEDABSENCE.csv",
    "VBI_LEAVESUMMARY.csv",
    "VBI_REDUCEDSCHEDABSENCEPERIOD.csv",
    "VBI_REPORTEDDATEOFABSENCE.csv",
    "VBI_REQUESTEDABSENCE.csv",
    "VBI_REQUESTEDDATEOFABSENCE.csv",
    "VBI_REQ_ABSENCE_SUBSEQDECISION.csv",
    "VBI_NEW_REQUESTEDABSENCE_SOM.csv",
    "VBI_TIMEOFFABSENCEPERIOD.csv",
    "VBI_SCHEDULEDDAY.csv",
    "VBI_CASE.csv",
    "VBI_CLAIM.csv",
    "VBI_CLAIMOCCUPATION.csv",
    "VBI_CLASSDIVISIONSNAPSHOT.csv",
    "VBI_CONTACT.csv",
    "VBI_CONTRACTSTUB.csv",
    "VBI_COVERAGE.csv",
    "VBI_DIAGNOSISCODE.csv",
    "VBI_DISABILITYDETAILS.csv",
    "VBI_DOCUMENT.csv",
    "VBI_EARNINGS.csv",
    "VBI_EMAIL.csv",
    "VBI_EMAILCONTACT.csv",
    "VBI_EMAILDOCUMENT.csv",
    "VBI_EXTRADATA.csv",
    "VBI_MANAGEDREQUIREMENT.csv",
    "VBI_MEDICAL.csv",
    "VBI_OCCUPATION.csv",
    "VBI_ORGANISATION.csv",
    "VBI_OTHERINCOME.csv",
    "VBI_OVERPAYMENTCASE.csv",
    "VBI_PARTIALPERIOD.csv",
    "VBI_PARTYADDRESSTYPE.csv",
    "VBI_PARTYADDRESSVERSION.csv",
    "VBI_PARTYCASEROLE.csv",
    "VBI_PARTYCONTRACTROLE.csv",
    "VBI_PAYMENTMETHOD.csv",
    "VBI_PAYMENTPREFERENCE.csv",
    "VBI_PERCENTAGEADJUSTMENT.csv",
    "VBI_POLICYSNAPSHOT.csv",
    "VBI_POSTALADDRESS.csv",
    "VBI_PROCESSINSTANCE.csv",
    "VBI_PROCESSSTEP.csv",
    "VBI_ROLE.csv",
    "VBI_ROLEHOLDER.csv",
    "VBI_SUPPRESSCASEVALIDATION.csv",
    "VBI_TASK.csv",
    "vtaskreport.csv",
    "vpeipurchasedetails.csv",
    "vpeipaymentdetails.csv",
    "vpeiexplanationofbenefit.csv",
    "vpeiclaimdetails.csv",
    "vpeipaymentline.csv",
    "vpei.csv",
    "LeavePlan_info.csv",
    "VBI_REQUESTEDABSENCE_SOM.csv",
    "CPS_AbsenceCasesWithGT1LeavePlan.csv",
    "CPS_ServiceAgreementsWithGT3LeavePlans.csv",
    "OrphanedCases_list.csv",
]

# These extracts use a WHERE clause of records that have some date column > THE_LAST_RUN_START_TIME. So we will
# store these in a YYYY/MM/DD/extract.csv folder structure which can easily be partitioned by AWS Glue.
fineos_warehouse_daily_extracts = [
    "VBI_ABSENCEAPPEALCASES.csv",
    "VBI_PERSON_SOM.csv",
    "VBI_ABSENCECASEByOrg.csv",
    "VBI_ABSENCECASEByStage.csv",
    "EmployeeDataLoad_feed.csv",
    "VBI_TASKREPORT_SOM.csv",
]


class BucketConfig(BaseSettings):
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)
    fineos_data_export_path: str = Field(..., min_length=1)
    bi_warehouse_path: str = Field(..., min_length=1)


@background_task("import-fineos-to-warehouse")
def handler():
    """ECS task handler."""
    config = BucketConfig()

    fineos_boto_session = massgov.pfml.util.aws.sts.assume_session(
        role_arn=config.fineos_aws_iam_role_arn,
        external_id=config.fineos_aws_iam_role_external_id,
        role_session_name="import_fineos_to_warehouse",
        region_name="us-east-1",
    )

    s3_fineos = fineos_boto_session.resource("s3")

    parser = argparse.ArgumentParser(
        description="Import data from FINEOS into BI warehouse in a structured format. If a start_date is provided, only the daily extracts will be processed to avoid overwriting current data."
    )
    parser.add_argument(
        "-s", "--start_date", type=valid_date, help="Date to start backfilling - format YYYY-MM-DD"
    )
    parser.add_argument(
        "-e",
        "--end_date",
        type=valid_date,
        help="Date to end backfilling. NOTE: This is not inclusive. The backfilling will go up to, but not include this date. - format YYYY-MM-DD",
    )

    args = parser.parse_args()

    # If we have no start_date, then we are doing today only with full extracts since it is the latest
    # version of the extracts, which are at the root of the remote S3 bucket.
    # This is the default behaviour of this task used by ECS that runs at 10pm EST.
    # Extracts are generated by FINEOS at 7pm Eastern and take about an hour to finish so
    # we run this script at 10pm Eastern on the same day and know the file prefix.
    # Note we subtract a day as Cloudwatch scheduled events run in UTC.
    if not args.start_date:
        start_date = datetime.now() - timedelta(1)
        process_date(
            start_date, s3_fineos, config.fineos_data_export_path, config.bi_warehouse_path, True
        )
    else:
        # If we don't have an end date, then we will do just the one day
        if not args.end_date:
            args.end_date = args.start_date + timedelta(1)

        # In the case of backfills, we will not process the full extracts. We need to get a list of the folders in the remote S3 bucket
        # which are named YYYY-MM-DD-HH-MM-SS corresponding with when it was generated. Since we do not know the seconds, we can match
        # on the date portion and then use the full path to get the files inside.
        # NOTE: this list_folders command has a limit of 1000 as it currently does not use pagination.
        fineos_day_folders = massgov.pfml.util.files.list_folders(
            config.fineos_data_export_path, fineos_boto_session
        )

        for date in daterange(args.start_date, args.end_date):
            date_string = date.strftime("%Y-%m-%d")

            # Look for folders that starts with the date_string. Could be multiple for same day? Since we are doing
            # daily extracts with timestamps in filename, it shouldn't matter
            day_folder = [i for i in fineos_day_folders if i.startswith(date_string)]
            if day_folder:
                for day in day_folder:
                    process_date(
                        date,
                        s3_fineos,
                        os.path.join(config.fineos_data_export_path, day),
                        config.bi_warehouse_path,
                        False,
                    )
            else:
                logger.info(
                    "Could not find backfill date (%s) in remote FINEOS bucket", date_string
                )


def process_date(date, s3_fineos, fineos_s3_path, bi_warehouse_path, include_full_extracts=False):
    current_date_string = date.strftime("%Y-%m-%d")
    logger.info("Processing FINEOS extracts for %s", current_date_string)

    # Get files in remote S3. Top level files are todays extracts generated at 7pm EST.
    # The next day, FINEOS moves them into a folder when the next day is generated.
    all_fineos_extracts = massgov.pfml.util.files.list_files(fineos_s3_path, s3_fineos)

    # Get the full daily extracts we care about
    for fineos_extract in all_fineos_extracts:
        # Ensure we are staying with files not in a folder
        if "/" not in fineos_extract:
            if include_full_extracts:
                # Handle the extracts that are a SELECT * query generated each day
                for wanted_extract in fineos_warehouse_full_extracts:
                    if (
                        fineos_extract.startswith(current_date_string)
                        and ("-" + wanted_extract) in fineos_extract
                    ):
                        warehouse_table_name = os.path.splitext(wanted_extract)[0].lower()
                        source_file = os.path.join(fineos_s3_path, fineos_extract)
                        dest_file = os.path.join(
                            bi_warehouse_path, warehouse_table_name, wanted_extract,
                        )

                        logger.info("Copying %s to %s", source_file, dest_file)

                        # We knowingly overwrite the warehouse file to ensure all updated rows are included
                        massgov.pfml.util.files.copy_file(source_file, dest_file)

            # Handle the extracts that need a YYYY/MM/DD folder structure.
            for daily_extract in fineos_warehouse_daily_extracts:
                if (
                    fineos_extract.startswith(current_date_string)
                    and daily_extract in fineos_extract
                ):
                    warehouse_table_name = os.path.splitext(daily_extract)[0].lower()
                    source_file = os.path.join(fineos_s3_path, fineos_extract)
                    dest_file = os.path.join(
                        bi_warehouse_path,
                        warehouse_table_name,
                        date.strftime("%Y/%m/%d"),
                        fineos_extract,
                    )

                    logger.info("Copying %s to %s", source_file, dest_file)

                    # In this case we do not overwrite and are able to use the date/time in the filename
                    massgov.pfml.util.files.copy_file(source_file, dest_file)


# This is used to ensure the date arguments are correctly provided
def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


# This is used to loop through the dates
# Note for consistency with the built-in range() function this iteration stops before reaching the end_date.
# So for inclusive iteration use the next day, as you would with range()
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

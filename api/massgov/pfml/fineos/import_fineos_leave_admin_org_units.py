import sys
from dataclasses import asdict, dataclass
from itertools import groupby
from operator import itemgetter
from typing import Optional

import boto3
from pydantic import Field
from sqlalchemy import or_
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov
import massgov.pfml.db as db
import massgov.pfml.fineos as fineos
import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.batch.log
import massgov.pfml.util.files as file_utils
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Employer,
    OrganizationUnit,
    User,
    UserLeaveAdministrator,
    UserLeaveAdministratorOrgUnit,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.csv import CSVSourceWrapper
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.logging import log_every
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = logging.get_logger(__name__)


class ImportFineosOrganizationUnitUpdatesConfig(PydanticBaseSettings):
    fineos_folder_path: str = Field(..., min_length=1)
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)


@dataclass
class ImportFineosOrganizationUnitUpdatesReport:
    organization_unit_file: str = ""
    # total count of rows in extract
    total_rows_received_count: int = 0
    # when a row in the extract doesn't have enough info to proceed
    missing_required_fields_count: int = 0
    # when new fineos organization units are added to the database
    created_employer_org_units_count: int = 0
    # when an organization unit is updated in the database
    updated_employer_org_units_count: int = 0
    # when we could not add a new organization unit to the database due to any conflicts
    errored_employer_org_units_count: int = 0
    # when a leave admin is servicing an org unit that the employer does not have
    employer_org_unit_discrepancy_count: int = 0
    # when multiple leave admins records are found for the same email/fein combo
    duplicate_leave_admins_count: int = 0
    # when an employer searched by fein is not found in the database
    missing_employer_count: int = 0
    # when multiple employer records have the same fein in the database
    duplicate_employer_count: int = 0
    # when the leave admin record is missing from database
    missing_leave_admins_count: int = 0
    # when the leave admin has been associated with an org unit
    created_leave_admin_org_units_count: int = 0
    # when we could not add a new leave admin organization unit to the database due to any conflicts
    errored_leave_admin_org_units_count: int = 0
    # when a leave admin is not enabled this script ignores them
    disabled_leave_admins_count: int = 0
    # when a fineos employer is not found in this fineos environment
    missing_fineos_employer_count: int = 0
    # when the fineos employer does not have organization units
    missing_fineos_org_units_count: int = 0


@dataclass
class LeaveAdmin:
    email_address: str
    departments: list[str]


@background_task("fineos-import-la-units")
def handler():
    """ECS handler function. Creates Org Units for the given employer"""
    logger.info("Starting import of organization unit updates from FINEOS.")

    db_session_raw = db.init(sync_lookups=True)

    config = ImportFineosOrganizationUnitUpdatesConfig()

    fineos_boto_session = None
    if config.fineos_folder_path.startswith("s3://fin-som"):
        fineos_boto_session = aws_sts.assume_session(
            role_arn=config.fineos_aws_iam_role_arn,
            external_id=config.fineos_aws_iam_role_external_id,
            role_session_name="import_fineos_leave_admin_org_units",
            region_name="us-east-1",
        )

    try:
        with massgov.pfml.util.batch.log.LogEntry(
            db_session_raw, "FINEOS Organization Unit Update", ""
        ) as log_entry, db.session_scope(db_session_raw) as db_session:
            report = process_fineos_updates(
                db_session, config.fineos_folder_path, fineos_boto_session
            )
            log_entry.set_metrics(asdict(report))
    except Exception:
        logger.exception("Error importing organization unit updates from FINEOS")
        sys.exit(1)

    logger.info(
        "Finished importing organization unit updates from FINEOS.",
        extra={"report": asdict(report)},
    )


def get_file_to_process(
    folder_path: str, boto_session: Optional[boto3.Session] = None
) -> Optional[str]:
    files_for_import = file_utils.list_files(str(folder_path), boto_session=boto_session)

    update_files = []
    for update_file in files_for_import:
        if update_file.endswith("-VBI_ORGUNIT_DETAILS_SOM.csv"):
            update_files.append(update_file)

    if len(update_files) == 0:
        logger.info("No daily FINEOS organization unit update file found.")
        return None

    if len(update_files) > 1:
        logger.error(
            "More than one FINEOS organization unit update extract file found in S3 bucket folder. Expect only one daily."
        )
        return None

    return update_files[0]


def process_fineos_updates(
    db_session: db.Session, folder_path: str, boto_session: Optional[boto3.Session] = None
) -> ImportFineosOrganizationUnitUpdatesReport:
    # Get CSV file and initiate report
    report = ImportFineosOrganizationUnitUpdatesReport()
    file = get_file_to_process(folder_path, boto_session)
    if file is None:
        return report
    else:
        logger.info(
            f"Processing daily FINEOS organization unit update extract with filename: {file}"
        )

    file_path = f"{folder_path}/{file}"
    report.organization_unit_file = file_path
    csv_input = CSVSourceWrapper(file_path, transport_params={"session": boto_session})

    # For each employer fein, keep a list of leave admins
    employers: dict[str, list[LeaveAdmin]] = {}
    # Process CSV data into a simpler format
    rows = []
    REQUIRED_KEYS = ("USERENABLED", "FEIN", "EMAIL", "ORGUNIT_NAME")
    for row in log_every(logger, csv_input, count=10000, item_name="CSV row", start_time=utcnow()):
        report.total_rows_received_count += 1
        if all(row.get(key) for key in REQUIRED_KEYS):
            rows.append(row)
        else:
            report.missing_required_fields_count += 1
    # Sort so the groupby works.
    rows.sort(key=itemgetter("FEIN"))
    rows.sort(key=itemgetter("EMAIL"))
    for key, group in groupby(
        rows, lambda a: (a.get("EMAIL"), a.get("FEIN"), a.get("USERENABLED"))
    ):
        email_address = key[0]
        employer_fein = key[1]
        user_enabled = key[2]
        # Just to appease mypy.
        if not email_address or not employer_fein or not user_enabled:
            continue
        is_enabled = int(user_enabled) == 1
        if not is_enabled:
            report.disabled_leave_admins_count += 1
            continue
        if employer_fein not in employers:
            employers[employer_fein] = []
        employers[employer_fein].append(
            LeaveAdmin(
                email_address=email_address,
                departments=[entry.get("ORGUNIT_NAME") for entry in group],  # type: ignore
            )
        )

    # Start the import process
    cps = fineos.create_client()
    for employer_fein, leave_admins in employers.items():
        try:
            employer: Employer = (
                db_session.query(Employer).filter(Employer.employer_fein == employer_fein).one()
            )
        except NoResultFound:
            logger.error("No query results for employer.", extra={"employer_fein": employer_fein})
            report.missing_employer_count += 1
            continue
        except MultipleResultsFound:
            logger.error(
                "Multiple query results for employer.", extra={"employer_fein": employer_fein}
            )
            report.duplicate_employer_count += 1
            continue

        try:
            cps_employer = cps.read_employer(employer.employer_fein)
            fineos_org_units = cps_employer.get_organization_units()
            if not fineos_org_units:
                logger.warning(
                    "Did not find org units in FINEOS as expected.",
                    extra={
                        "internal_employer_id": employer.employer_id,
                        "fineos_employer_id": employer.fineos_employer_id,
                    },
                )
                report.missing_fineos_org_units_count += 1
                continue
        except fineos.exception.FINEOSNotFound:
            logger.warning(
                "Did not find employer in FINEOS as expected.",
                extra={
                    "internal_employer_id": employer.employer_id,
                    "fineos_employer_id": employer.fineos_employer_id,
                },
            )
            report.missing_fineos_employer_count += 1
            continue

        for f_org_unit in fineos_org_units:
            fineos_id = f_org_unit.OID
            name = f_org_unit.Name

            # Create OrganizationUnit record if it doesn't exist.
            org_unit = (
                db_session.query(OrganizationUnit)
                .filter(or_(OrganizationUnit.name == name, OrganizationUnit.fineos_id == fineos_id))
                .filter(OrganizationUnit.employer_id == employer.employer_id)
                .one_or_none()
            )
            # When the org unit does not yet exist
            if org_unit is None:
                try:
                    # Create a new one
                    org_unit_model = OrganizationUnit(
                        fineos_id=fineos_id, name=name, employer_id=employer.employer_id
                    )
                    db_session.add(org_unit_model)
                    db_session.commit()
                    org_unit = org_unit_model
                    report.created_employer_org_units_count += 1
                except Exception:
                    logger.error(
                        "Unable to add Organization Unit.",
                        extra={
                            "fineos_id": fineos_id,
                            "name": name,
                            "employer_id": employer.employer_id,
                        },
                    )
                    report.errored_employer_org_units_count += 1
                    continue
            # When the org unit exists but needs to be updated
            elif org_unit.fineos_id is None or org_unit.name != name:
                try:
                    # Update fineos_id and name
                    org_unit.fineos_id = fineos_id
                    org_unit.name = name
                    db_session.add(org_unit)
                    db_session.commit()
                    report.updated_employer_org_units_count += 1
                except Exception:
                    logger.error(
                        "Unable to update Organization Unit.",
                        extra={
                            "organization_unit_id": org_unit.organization_unit_id,
                            "name": name,
                            "employer_id": employer.employer_id,
                        },
                    )
                    report.errored_employer_org_units_count += 1
                    continue

        # Create a map of agencies for this employer w/ UUID.
        org_units = {
            org_unit.name: org_unit.organization_unit_id
            for org_unit in db_session.query(OrganizationUnit).filter(
                OrganizationUnit.employer_id == employer.employer_id
            )
        }

        for la in leave_admins:
            try:
                leave_admin_id = (
                    db_session.query(UserLeaveAdministrator.user_leave_administrator_id)
                    .join(User)
                    .filter(
                        User.email_address == la.email_address,
                        UserLeaveAdministrator.employer_id == employer.employer_id,
                    )
                    .one()
                )
            except NoResultFound:
                logger.error(
                    "No query results for Leave Admin.",
                    extra={"email_address": la.email_address, "employer_id": employer.employer_id},
                )
                report.missing_leave_admins_count += 1
                continue
            except MultipleResultsFound:
                logger.error(
                    "Multiple query results for Leave Admin.",
                    extra={"email_address": la.email_address, "employer_id": employer.employer_id},
                )
                report.duplicate_leave_admins_count += 1
                continue

            # Ensure that the Leave Admin to department link is removed if it isn't in extract
            db_session.query(UserLeaveAdministratorOrgUnit).filter(
                UserLeaveAdministratorOrgUnit.user_leave_administrator_id == leave_admin_id
            ).delete()
            for organization_unit_name in la.departments:
                org_unit_id = org_units.get(organization_unit_name)
                if org_unit_id is None:
                    logger.error(
                        "Org unit listed for Leave Admin, but not in employer.",
                        extra={
                            "email_address": la.email_address,
                            "employer_id": employer.employer_id,
                            "organization_unit_id": org_unit_id,
                            "organization_unit_name": organization_unit_name,
                        },
                    )
                    report.employer_org_unit_discrepancy_count += 1
                    continue
                try:
                    link_leave_admin = UserLeaveAdministratorOrgUnit(leave_admin_id, org_unit_id)
                    db_session.add(link_leave_admin)
                    db_session.commit()
                    report.created_leave_admin_org_units_count += 1
                except Exception:
                    logger.error(
                        "Unable to add Leave Admin Organization Unit.",
                        extra={"leave_admin_id": leave_admin_id, "org_unit_id": org_unit_id},
                    )
                    report.errored_leave_admin_org_units_count += 1
                    continue

    # Ended import process

    return report

import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

import boto3
from pydantic import BaseSettings, Field, parse_obj_as, validator

import massgov
import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.batch.log
import massgov.pfml.util.files as file_utils
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.api.util.phone import convert_to_E164
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeeOccupation,
    Employer,
    LkGender,
    LkMaritalStatus,
    LkOccupation,
    LkTitle,
    OrganizationUnit,
    TaxIdentifier,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.csv import CSVSourceWrapper
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.logging import log_every
from massgov.pfml.util.pydantic import PydanticBaseModelEmptyStrIsNone

logger = logging.get_logger(__name__)


class ImportFineosEmployeeUpdatesConfig(BaseSettings):
    fineos_folder_path: str = Field(..., min_length=1)
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)


@dataclass
class ImportFineosEmployeeUpdatesReport:
    start: str = utcnow().isoformat()
    total_employees_received_count: int = 0
    created_employees_count: int = 0
    updated_employees_count: int = 0
    emp_id_discrepancies_count: int = 0
    no_ssn_present_count: int = 0
    errored_employees_count: int = 0
    errored_employee_occupation_count: int = 0
    end: Optional[str] = None
    process_duration_in_seconds: float = 0


class EmployeeDataLoadFeedLine(PydanticBaseModelEmptyStrIsNone):
    EMPLOYEEIDENTIFIER: Optional[UUID] = None
    EMPLOYEETITLE: Optional[str] = None
    EMPLOYEEDATEOFBIRTH: Optional[date] = None
    EMPLOYEEGENDER: Optional[str] = None
    EMPLOYEEMARITALSTATUS: Optional[str] = None
    TELEPHONEINTCODE: Optional[str] = None
    TELEPHONEAREACODE: Optional[str] = None
    TELEPHONENUMBER: Optional[str] = None
    CELLINTCODE: Optional[str] = None
    CELLAREACODE: Optional[str] = None
    CELLNUMBER: Optional[str] = None
    EMPLOYEEEMAIL: Optional[str] = None
    EMPLOYEEID: Optional[str] = None
    EMPLOYEECLASSIFICATION: Optional[str] = None
    EMPLOYEEJOBTITLE: Optional[str] = None
    EMPLOYEEDATEOFHIRE: Optional[date] = None
    EMPLOYEEENDDATE: Optional[date] = None
    EMPLOYMENTSTATUS: Optional[str] = None
    EMPLOYEEORGUNITNAME: Optional[str] = None
    # these "worked per week" fields seem to come through with "0" instead of ""
    # if FINEOS doesn't have the data available, so will generally always have a
    # value for these, i.e., they will never be `None``
    EMPLOYEEHOURSWORKEDPERWEEK: Optional[Decimal] = None
    EMPLOYEEDAYSWORKEDPERWEEK: Optional[Decimal] = None
    MANAGERIDENTIFIER: Optional[str] = None
    QUALIFIERDESCRIPTION: Optional[str] = None
    EMPLOYEEWORKSITEID: Optional[str] = None
    ORG_CUSTOMERNO: Optional[str] = None
    ORG_NAME: Optional[str] = None
    EMPLOYEENATIONALID: Optional[str] = None
    EMPLOYEEFIRSTNAME: Optional[str] = None
    EMPLOYEELASTNAME: Optional[str] = None
    CUSTOMERNO: Optional[str] = None

    @validator("EMPLOYEEDATEOFBIRTH", "EMPLOYEEDATEOFHIRE", "EMPLOYEEENDDATE", pre=True)
    def datetime_to_date(cls, v):  # noqa: B902
        if isinstance(v, date):
            return v

        if isinstance(v, str) and v:
            as_datetime = parse_obj_as(datetime, v)

            return as_datetime.date()


@background_task("fineos-import-employee-updates")
def handler():
    """ECS handler function."""
    logger.info("Starting import of employee updates from FINEOS.")

    db_session_raw = db.init(sync_lookups=True)

    config = ImportFineosEmployeeUpdatesConfig()

    fineos_boto_session = None
    if config.fineos_folder_path.startswith("s3://fin-som"):
        fineos_boto_session = aws_sts.assume_session(
            role_arn=config.fineos_aws_iam_role_arn,
            external_id=config.fineos_aws_iam_role_external_id,
            role_session_name="import_fineos_updates",
            region_name="us-east-1",
        )

    try:
        with massgov.pfml.util.batch.log.log_entry(
            db_session_raw, "FINEOS Employee Update", ""
        ) as log_entry, db.session_scope(db_session_raw) as db_session:
            report = process_fineos_updates(
                db_session, config.fineos_folder_path, fineos_boto_session
            )
            log_entry.report = json.dumps(asdict(report), indent=2)
    except Exception:
        logger.exception("Error importing employee updates from FINEOS")
        sys.exit(1)

    logger.info(
        "Finished importing employee updates from FINEOS.", extra={"report": asdict(report)}
    )


def get_file_to_process(
    folder_path: str, boto_session: Optional[boto3.Session] = None
) -> Optional[str]:
    files_for_import = file_utils.list_files(str(folder_path), boto_session=boto_session)

    update_files = []
    for update_file in files_for_import:
        if update_file.endswith("-EmployeeDataLoad_feed.csv"):
            update_files.append(update_file)

    if len(update_files) == 0:
        logger.info("No daily FINEOS employee update file found.")
        return None

    if len(update_files) > 1:
        logger.error(
            "More than one FINEOS employee update extract file found in S3 bucket folder. Expect only one daily."
        )
        return None

    return update_files[0]


def process_fineos_updates(
    db_session: db.Session, folder_path: str, boto_session: Optional[boto3.Session] = None
) -> ImportFineosEmployeeUpdatesReport:
    start_time = utcnow()
    report = ImportFineosEmployeeUpdatesReport(start=start_time.isoformat())

    file = get_file_to_process(folder_path, boto_session)
    if file is None:
        end_time = utcnow()
        report.end = end_time.isoformat()
        report.process_duration_in_seconds = (end_time - start_time).total_seconds()
        return report
    else:
        logger.info(f"Processing daily FINEOS employee update extract with filename: {file}")

    file_path = f"{folder_path}/{file}"
    csv_input = CSVSourceWrapper(file_path, transport_params={"session": boto_session})

    line_count = 0
    for row in log_every(logger, csv_input, count=10, item_name="CSV row"):
        line_count += 1

        report.total_employees_received_count += 1
        try:
            process_csv_row(db_session, row, report)
        except Exception:
            logger.exception(
                f"Unhandled issue processing CSV row with file: {file} at line {line_count}. Continuing processing."
            )
            db_session.rollback()

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def process_csv_row(
    db_session: db.Session, row_dict: Dict[Any, Any], report: ImportFineosEmployeeUpdatesReport
) -> None:
    is_new_employee = False

    row = EmployeeDataLoadFeedLine.parse_obj(row_dict)

    employee_id = row.EMPLOYEEIDENTIFIER
    if not employee_id:
        raise ValueError("Employee ID is required to process row")

    employee: Optional[Employee] = db_session.query(Employee).get(employee_id)

    if employee is None:
        # Find employee by SSN
        employee_tax_id = row.EMPLOYEENATIONALID
        if employee_tax_id:
            employee = (
                db_session.query(Employee)
                .join(TaxIdentifier)
                .filter(TaxIdentifier.tax_identifier == employee_tax_id)
                .one_or_none()
            )
        else:
            logger.info(
                f"Employee not found in PFML DB and no SSN provided."
                f" FINEOS employee_id is {employee_id}."
            )
            report.no_ssn_present_count += 1
            report.errored_employees_count += 1
            return

        if employee is None:
            is_new_employee = True
            employee = Employee(employee_id=employee_id)

            tax_identifier = (
                db_session.query(TaxIdentifier)
                .filter(TaxIdentifier.tax_identifier == employee_tax_id)
                .one_or_none()
            )
            employee.tax_identifier = (
                tax_identifier if tax_identifier else TaxIdentifier(tax_identifier=employee_tax_id)
            )

            employee.first_name = row.EMPLOYEEFIRSTNAME or ""
            employee.last_name = row.EMPLOYEELASTNAME or ""

            db_session.add(employee)
            report.created_employees_count += 1
        else:
            # Employee found but with a different employee_id value (UUID)
            logger.info(
                f"Employee found in PFML DB by SSN with different emp_id."
                f" PFML employee_id is {employee.employee_id},"
                f" FINEOS employee_id is {employee_id}."
            )
            report.emp_id_discrepancies_count += 1
            report.errored_employees_count += 1
            report.errored_employee_occupation_count += 1
            return

    customer_no = row.CUSTOMERNO
    if customer_no:
        employee.fineos_customer_number = customer_no

    title = row.EMPLOYEETITLE
    title_id = (
        db_session.query(LkTitle.title_id).filter(LkTitle.title_description == title).scalar()
    )
    if title_id is not None:
        employee.title_id = title_id

    date_of_birth = row.EMPLOYEEDATEOFBIRTH
    if date_of_birth:
        employee.date_of_birth = date_of_birth

    gender = row.EMPLOYEEGENDER
    gender_id = (
        db_session.query(LkGender.gender_id)
        .filter(LkGender.fineos_gender_description == gender)
        .scalar()
    )
    if gender_id is not None:
        employee.gender_id = gender_id

    marital_status = row.EMPLOYEEMARITALSTATUS
    marital_status_id = (
        db_session.query(LkMaritalStatus.marital_status_id)
        .filter(LkMaritalStatus.marital_status_description == marital_status)
        .scalar()
    )
    if marital_status_id is not None:
        employee.marital_status_id = marital_status_id

    employee.phone_number = parse_fineos_phone_number(
        row.TELEPHONEINTCODE,
        row.TELEPHONEAREACODE,
        row.TELEPHONENUMBER,
        {"employee_id": employee_id, "fineos_customer_number": customer_no},
    )

    employee.cell_phone_number = parse_fineos_phone_number(
        row.CELLINTCODE,
        row.CELLAREACODE,
        row.CELLNUMBER,
        {"employee_id": employee_id, "fineos_customer_number": customer_no},
    )

    employee_email = row.EMPLOYEEEMAIL
    if employee_email is not None:
        employee.email_address = employee_email

    # Map to employee.occupation??
    employee_classification = row.EMPLOYEECLASSIFICATION
    employee_classification_id = (
        db_session.query(LkOccupation.occupation_id)
        .filter(LkOccupation.occupation_description == employee_classification)
        .scalar()
    )
    if employee_classification_id is not None:
        employee.occupation_id = employee_classification_id

    employer_fineos_id = row.ORG_CUSTOMERNO
    if not employer_fineos_id or not employer_fineos_id.isdecimal():
        logger.warning(
            f"Employer has non-numeric FINEOS Customer Nbr {employer_fineos_id} for employee_id {employee_id}."
        )
        report.errored_employees_count += 1
        return

    employer_id: Optional[UUID] = (
        db_session.query(Employer.employer_id)
        .filter(Employer.fineos_employer_id == employer_fineos_id)
        .scalar()
    )

    if employer_id is None:
        fineos_employer_name = row.ORG_NAME
        logger.info(f"Cannot create EmployerOccupation record for employee_id {employee_id}.")
        logger.info(
            f"Employer with FINEOS Customer Nbr {employer_fineos_id} and Org Name of {fineos_employer_name} not found."
        )
        report.errored_employee_occupation_count += 1
        return

    employee_occupation: Optional[EmployeeOccupation] = (
        db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == employee.employee_id,
            EmployeeOccupation.employer_id == employer_id,
        )
        .one_or_none()
    )

    if employee_occupation is None:
        employee_occupation = EmployeeOccupation()
        employee_occupation.employee_id = employee.employee_id
        employee_occupation.employer_id = employer_id

        db_session.add(employee_occupation)

    job_title = row.EMPLOYEEJOBTITLE
    if job_title is not None:
        employee_occupation.job_title = job_title

    date_of_hire = row.EMPLOYEEDATEOFHIRE
    if date_of_hire:
        employee_occupation.date_of_hire = date_of_hire

    end_date = row.EMPLOYEEENDDATE
    if end_date:
        employee_occupation.date_job_ended = end_date

    emp_status = row.EMPLOYMENTSTATUS
    if emp_status is not None:
        employee_occupation.employment_status = emp_status

    org_unit_name = row.EMPLOYEEORGUNITNAME

    if org_unit_name:
        org_unit = (
            db_session.query(OrganizationUnit)
            .filter(
                OrganizationUnit.name == org_unit_name, OrganizationUnit.employer_id == employer_id
            )
            .one_or_none()
        )

        if org_unit is None:
            org_unit = OrganizationUnit(name=str(org_unit_name), employer_id=employer_id)
            db_session.add(org_unit)

        employee_occupation.organization_unit = org_unit

    hours_per_week = row.EMPLOYEEHOURSWORKEDPERWEEK
    if hours_per_week is not None:
        employee_occupation.hours_worked_per_week = hours_per_week

    days_per_week = row.EMPLOYEEDAYSWORKEDPERWEEK
    if days_per_week is not None:
        employee_occupation.days_worked_per_week = days_per_week

    manager_id = row.MANAGERIDENTIFIER
    if manager_id is not None:
        employee_occupation.manager_id = manager_id

    worksite_id = row.EMPLOYEEWORKSITEID
    if worksite_id is not None:
        employee_occupation.worksite_id = worksite_id

    occupation_qualifier = row.QUALIFIERDESCRIPTION
    if occupation_qualifier is not None:
        employee_occupation.occupation_qualifier = occupation_qualifier

    db_session.commit()

    if not is_new_employee:
        report.updated_employees_count += 1


def parse_fineos_phone_number(
    intl_code: Optional[str],
    area_code: Optional[str],
    phone_nbr: Optional[str],
    log_attrs: Optional[Dict] = None,
) -> Optional[str]:
    try:
        return convert_to_E164(f"{area_code}{phone_nbr}", intl_code, True)
    except ValueError:
        log_attrs = {} if log_attrs is None else log_attrs
        log_attrs["int_code_len"] = len(intl_code) if intl_code else 0
        log_attrs["area_code_len"] = len(area_code) if area_code else 0
        log_attrs["telephone_num_len"] = len(phone_nbr) if phone_nbr else 0
        logger.warning("Could not parse a valid phone number from input", extra=log_attrs)

        return None

import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from uuid import UUID

import boto3
from pydantic import BaseSettings, Field

import massgov
import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.batch.log
import massgov.pfml.util.files as file_utils
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeeOccupation,
    Employer,
    LkGender,
    LkMaritalStatus,
    LkOccupation,
    LkTitle,
    TaxIdentifier,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.csv import CSVSourceWrapper
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.logging import log_every

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

    end_time = utcnow()
    report.end = end_time.isoformat()
    report.process_duration_in_seconds = (end_time - start_time).total_seconds()

    return report


def process_csv_row(
    db_session: db.Session, row: Dict[Any, Any], report: ImportFineosEmployeeUpdatesReport
) -> None:
    is_new_employee = False

    employee_id = row.get("EMPLOYEEIDENTIFIER")
    if not employee_id:
        raise ValueError("Employee ID is required to process row")

    employee: Optional[Employee] = db_session.query(Employee).get(employee_id)

    if employee is None:
        # Find employee by SSN
        employee_tax_id: str = row.get("EMPLOYEENATIONALID", None)
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

            first_name = row.get("EMPLOYEEFIRSTNAME", "")
            employee.first_name = first_name
            last_name = row.get("EMPLOYEELASTNAME", "")
            employee.last_name = last_name

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

    customer_no = row.get("CUSTOMERNO")
    if customer_no is not None and customer_no != "":
        employee.fineos_customer_number = customer_no

    title = row.get("EMPLOYEETITLE")
    title_id = (
        db_session.query(LkTitle.title_id).filter(LkTitle.title_description == title).one_or_none()
    )
    if title_id is not None:
        employee.title_id = title_id

    date_of_birth = row.get("EMPLOYEEDATEOFBIRTH")
    if date_of_birth is not None and date_of_birth != "":
        employee.date_of_birth = date_of_birth

    gender = row.get("EMPLOYEEGENDER")
    gender_id = (
        db_session.query(LkGender.gender_id)
        .filter(LkGender.fineos_gender_description == gender)
        .one_or_none()
    )
    if gender_id is not None:
        employee.gender_id = gender_id

    marital_status = row.get("EMPLOYEEMARITALSTATUS")
    marital_status_id = (
        db_session.query(LkMaritalStatus.marital_status_id)
        .filter(LkMaritalStatus.marital_status_description == marital_status)
        .one_or_none()
    )
    if marital_status_id is not None:
        employee.marital_status_id = marital_status_id

    phone_intl_code = row.get("TELEPHONEINTCODE")
    phone_area_code = row.get("TELEPHONEAREACODE")
    phone_nbr = row.get("TELEPHONENUMBER")

    if phone_area_code is None:
        employee.phone_number = f"+{phone_intl_code}{phone_nbr}"
    else:
        employee.phone_number = f"+{phone_intl_code}{phone_area_code}{phone_nbr}"

    cell_intl_code = row.get("CELLINTCODE")
    cell_area_code = row.get("CELLAREACODE")
    cell_nbr = row.get("CELLNUMBER")

    if cell_area_code is None:
        employee.cell_phone_number = f"+{cell_intl_code}{cell_nbr}"
    else:
        employee.cell_phone_number = f"+{cell_intl_code}{cell_area_code}{cell_nbr}"

    employee_email = row.get("EMPLOYEEEMAIL")
    if employee_email is not None:
        employee.email_address = employee_email

    # Map to employee.occupation??
    employee_classification = row.get("EMPLOYEECLASSIFICATION")
    employee_classification_id = (
        db_session.query(LkOccupation.occupation_id)
        .filter(LkOccupation.occupation_description == employee_classification)
        .one_or_none()
    )
    if employee_classification_id is not None:
        employee.occupation_id = employee_classification_id

    employer_fineos_id = row.get("ORG_CUSTOMERNO", None)
    if not employer_fineos_id.isdecimal():
        logger.warning(
            f"Employer has non-numeric FINEOS Customer Nbr {employer_fineos_id} for employee_id {employee_id}."
        )
        report.errored_employees_count += 1
        return

    employer_id: Optional[UUID] = (
        db_session.query(Employer.employer_id)
        .filter(Employer.fineos_employer_id == employer_fineos_id)
        .one_or_none()
    )

    if employer_id is None:
        fineos_employer_name = row.get("ORG_NAME")
        logger.info(f"Cannot create EmployerOccupation record for employee_id {employee_id}.")
        logger.info(
            f"Employer with FINEOS Customer Nbr {employer_fineos_id} and Org Name of {fineos_employer_name} not found."
        )
        report.errored_employee_occupation_count += 1
        return

    employee_occupation: Optional[EmployeeOccupation] = db_session.query(EmployeeOccupation).filter(
        EmployeeOccupation.employee_id == employee.employee_id,
        EmployeeOccupation.employer_id == employer_id,
    ).one_or_none()

    if employee_occupation is None:
        employee_occupation = EmployeeOccupation()
        employee_occupation.employee_id = employee.employee_id
        employee_occupation.employer_id = employer_id

        db_session.add(employee_occupation)

    job_title = row.get("EMPLOYEEJOBTITLE")
    if job_title is not None:
        employee_occupation.job_title = job_title

    date_of_hire = row.get("EMPLOYEEDATEOFHIRE")
    if date_of_hire is not None and date_of_hire != "":
        employee_occupation.date_of_hire = date_of_hire

    end_date = row.get("EMPLOYEEENDDATE")
    if end_date is not None and end_date != "":
        employee_occupation.date_job_ended = end_date

    emp_status = row.get("EMPLOYMENTSTATUS")
    if emp_status is not None:
        employee_occupation.employment_status = emp_status

    org_unit_name = row.get("EMPLOYEEORGUNITNAME")
    if org_unit_name is not None:
        employee_occupation.org_unit_name = org_unit_name

    hours_per_week = row.get("EMPLOYEEHOURSWORKEDPERWEEK")
    if hours_per_week is not None:
        employee_occupation.hours_worked_per_week = hours_per_week

    days_per_week = row.get("EMPLOYEEDAYSWORKEDPERWEEK")
    if days_per_week is not None:
        employee_occupation.days_worked_per_week = days_per_week

    manager_id = row.get("MANAGERIDENTIFIER")
    if manager_id is not None:
        employee_occupation.manager_id = manager_id

    worksite_id = row.get("EMPLOYEEWORKSITEID")
    if worksite_id is not None:
        employee_occupation.worksite_id = worksite_id

    occupation_qualifier = row.get("QUALIFIERDESCRIPTION")
    if occupation_qualifier is not None:
        employee_occupation.occupation_qualifier = occupation_qualifier

    db_session.commit()

    if not is_new_employee:
        report.updated_employees_count += 1

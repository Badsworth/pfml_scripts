import concurrent.futures
import csv
import dataclasses
import enum
import itertools
import math
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import cached_property
from typing import Any, Callable, Dict, Iterable, List, Optional, TextIO, Tuple, TypeVar, Union

import boto3
import smart_open
from pydantic import BaseSettings, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Query

import massgov.pfml.db as db
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employee, EmployeeLog, Employer, WagesAndContributions
from massgov.pfml.fineos.exception import FINEOSNotFound
from massgov.pfml.util.datetime import utcnow

logger = massgov.pfml.util.logging.get_logger(__name__)


class EligibilityFeedExportMode(Enum):
    FULL = "full"
    UPDATES = "updates"


class EligibilityFeedExportConfig(BaseSettings):
    output_directory_path: str = Field(..., min_length=1)
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)
    mode: EligibilityFeedExportMode = Field(
        EligibilityFeedExportMode.FULL, env="ELIGIBILITY_FEED_MODE"
    )


DEFAULT_DATE = date(1753, 1, 1)
DEFAULT_HIRE_DATE = date(2020, 1, 1)
DEFAULT_EMPLOYMENT_WORK_STATE = "MA"


class AddressType(Enum):
    home = "Home"
    business = "Business"


class Gender(Enum):
    male = "Male"
    female = "Female"
    other = "Other"


class MaritalStatus(Enum):
    single = "Single"
    married = "Married"
    divorced = "Divorced"
    widowed = "Widowed"


class EarningFrequency(Enum):
    hourly = "Hourly"
    weekly = "Weekly"
    bi_weekly = "Bi-weekly"
    monthly = "Monthly"
    semi_monthly = "Semi-monthly"
    yearly = "Yearly"


class NationalIdType(Enum):
    ssn = "Social Security Number"
    itin = "Individual Taxpayer Identification Number"


def determine_national_id_type(tax_id: str) -> NationalIdType:
    if tax_id[0] == "9":
        return NationalIdType.itin

    return NationalIdType.ssn


@dataclass
class NoneMeansDefault:
    """A dataclass that uses an attributes default value if it is set to None

    A convenience to keep defaults defined in one place, and cut down on the
    number of distinct if blocks/conditionals required to set attributes from
    optional sources.
    """

    # something like this would also work, at least for things set while
    # constructing the dataclass, __setattr__ works when attributes are set
    # after the fact as well
    #
    # def __post_init__(self):
    #     for field in dataclasses.fields(self):
    #         if field.default is not None:
    #             field_val = getattr(self, field.name)
    #             if field_val is None:
    #                 setattr(self, field.name, field.default)

    def __setattr__(self, attr, value):
        if value is None:
            if attr in self.fields_with_non_none_default:
                value = self.fields_with_non_none_default[attr].default

        super().__setattr__(attr, value)

    @cached_property
    def fields_with_non_none_default(self) -> Dict[str, dataclasses.Field]:
        return {f.name: f for f in dataclasses.fields(self) if f.default is not None}


@dataclass
class EligibilityFeedRecord(NoneMeansDefault):
    # FINEOS required fields, without a general default we can set
    employeeIdentifier: str
    employeeFirstName: str
    employeeLastName: str

    # FINEOS required fields, but with an agreed upon default
    employeeDateOfBirth: Union[date, None] = DEFAULT_DATE
    employeeJobTitle: Union[str, None] = "DEFAULT"
    employeeDateOfHire: Union[date, None] = DEFAULT_HIRE_DATE
    employmentStatus: Union[str, None] = "Active"
    # FINOES DB type is DECIMAL(5,2)
    # 5 digits of precision overall, 2 digits past the decimal if needed
    employeeHoursWorkedPerWeek: Union[float, None] = 0

    # all other fields are (usually) optional
    employeeTitle: Optional[str] = None
    # if employeeThirdName is specified, employeeSecondName is then required
    employeeSecondName: Optional[str] = None
    employeeThirdName: Optional[str] = None
    employeeDateOfDeath: Optional[date] = None
    employeeGender: Optional[Gender] = None
    employeeMaritalStatus: Optional[MaritalStatus] = None
    employeeNationalID: Optional[str] = None
    employeeNationalIDType: Optional[NationalIdType] = None
    spouseIdentifier: Optional[str] = None
    spouseReasonForChange: Optional[str] = None
    spouseDateOfChange: Optional[date] = None
    spouseTitle: Optional[str] = None
    spouseFirstName: Optional[str] = None
    spouseSecondName: Optional[str] = None
    spouseThirdName: Optional[str] = None
    spouseLastName: Optional[str] = None
    spouseDateOfBirth: Optional[date] = None
    spouseDateOfDeath: Optional[date] = None
    spouseGender: Optional[Gender] = None
    spouseNationalID: Optional[str] = None
    spouseNationalIDType: Optional[str] = None
    # if any address information is included, these fields are then all required
    addressType: Optional[AddressType] = None
    addressState: Optional[str] = None
    addressCity: Optional[str] = None
    addressAddressLine1: Optional[str] = None
    addressZipCode: Optional[str] = None
    # these address fields never required
    addressEffectiveDate: Optional[date] = None
    addressCountry: Optional[str] = None
    addressAddressLine2: Optional[str] = None
    addressCounty: Optional[str] = None
    telephoneIntCode: Optional[str] = None
    telephoneAreaCode: Optional[str] = None
    telephoneNumber: Optional[str] = None
    cellIntCode: Optional[str] = None
    cellAreaCode: Optional[str] = None
    cellNumber: Optional[str] = None
    employeeEmail: Optional[str] = None
    employeeId: Optional[str] = None
    employeeClassification: Optional[str] = None
    employeeAdjustedDateOfHire: Optional[date] = None
    employeeEndDate: Optional[date] = None
    employmentStrength: Optional[str] = None
    employmentCategory: Optional[str] = None
    employmentType: Optional[str] = None
    employeeOrgUnitName: Optional[str] = None
    employeeCBACode: Optional[str] = None
    keyEmployee: Optional[bool] = None
    employeeWorkAtHome: Optional[bool] = None
    # FINOES DB type is DECIMAL(5,2)
    # 5 digits of precision overall, 2 digits past the decimal if needed
    employeeDaysWorkedPerWeek: Optional[Decimal] = None
    employeeHoursWorkedPerYear: Optional[int] = None
    employee50EmployeesWithin75Miles: Optional[bool] = None
    employmentWorkState: Optional[str] = DEFAULT_EMPLOYMENT_WORK_STATE
    managerIdentifier: Optional[str] = None
    # note, there can be multiple of these starting with occupationQualifier*,
    # which we don't support in this data structure
    occupationQualifier: Optional[str] = None
    employeeWorkSiteId: Optional[str] = None
    employeeEffectiveFromDate: Optional[date] = None
    employeeEffectiveToDate: Optional[date] = None
    # FINEOS DB type is DECIMAL(28,6)
    # 28 digits of precision overall, up to 6 digits past the decimal
    employeeSalary: Optional[Decimal] = None
    employeeEarningFrequency: Optional[EarningFrequency] = None


@dataclass
class EligibilityFeedExportReport:
    started_at: str
    completed_at: Optional[str] = None
    employers_total_count: int = 0
    employers_success_count: int = 0
    employers_skipped_count: int = 0
    employers_error_count: int = 0
    employee_and_employer_pairs_total_count: int = 0


OutputTransportParams = Dict[str, Any]


_T = TypeVar("_T")


def query_employees_for_employer(query: "Query[_T]", employer: Employer) -> "Query[_T]":
    return (
        query.select_from(WagesAndContributions)
        .join(WagesAndContributions.employee)
        .filter(WagesAndContributions.employer_id == employer.employer_id)
        .group_by(Employee.employee_id)
        .distinct(Employee.employee_id)
    )


def query_employees_and_most_recent_wages_for_employer(
    query: "Query[_T]", employer: Employer
) -> "Query[_T]":
    return (
        query.select_from(WagesAndContributions)
        .join(WagesAndContributions.employee)
        .filter(WagesAndContributions.employer_id == employer.employer_id)
        .order_by(
            WagesAndContributions.employer_id,
            WagesAndContributions.employee_id,
            WagesAndContributions.filing_period.desc(),
        )
        .distinct(WagesAndContributions.employer_id, WagesAndContributions.employee_id)
    )


def get_latest_employer_for_updates(employer_employee_list: List) -> List:
    latest_employer_employee_list: List[Any] = []
    employee_filing_dates: Dict[str, Optional[date]] = {}
    for employer_employee_pair in employer_employee_list:
        filing_date = employee_filing_dates.setdefault(employer_employee_pair.employee_id, None)
        if filing_date is None:
            employee_filing_dates[
                employer_employee_pair.employee_id
            ] = employer_employee_pair.maxdate
            latest_employer_employee_list.append(employer_employee_pair)

    return latest_employer_employee_list


# When loading employers to FINEOS the API we use requires us to
# generate a unique key which we pass in the attribute CustomerNo.
#
# The API returns the FINEOS primary key for the organization it
# created in the response as attribute CUSTOMER_NUMBER. We store
# this value in the fineos_employer_id field in the employer model.
# The fineos_employer_id is the value that should be used to identify
# an employer in the Eligibility Feed.
def get_fineos_employer_id(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient, employer: Employer
) -> Optional[int]:
    if employer.fineos_employer_id:
        return employer.fineos_employer_id

    try:
        fineos_employer_id = fineos.find_employer(employer.employer_fein)
        return int(fineos_employer_id)
    except FINEOSNotFound:
        return None


def process_employee_updates(
    db_session: db.Session,
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    output_dir_path: str,
    output_transport_params: Optional[OutputTransportParams] = None,
) -> EligibilityFeedExportReport:
    report = EligibilityFeedExportReport(started_at=utcnow().isoformat())

    logger.info("Starting eligibility feeds generation for employee updates.")

    # We may modify this code to spawn more than one process to consume the
    # updates similar to what has been done for all employers process.
    # When doing so we should use the same sequence of process identifiers
    # so that at recovery the process knows what incomplete rows to pick from
    # EmployeeLog.
    process_id = 1

    # Recovery. Check for unprocessed rows. There should never be more than
    # the batch size in normal processing.
    unprocessed_employees = (
        db_session.query(EmployeeLog.employee_id)
        .filter(EmployeeLog.process_id == process_id)
        .distinct(EmployeeLog.employee_id)
        .all()
    )

    if len(unprocessed_employees) > 0:
        recovery_employee_ids = process_employee_batch(
            db_session, fineos, output_dir_path, unprocessed_employees, report
        )

        db_session.begin_nested()
        delete_processed_batch(db_session, recovery_employee_ids, process_id)
        db_session.commit()

    # After recovery proceed with normal flow.
    while "batch not empty":
        updated_employee_ids = (
            db_session.query(EmployeeLog.employee_id)
            .filter(
                and_(EmployeeLog.action.in_(["INSERT", "UPDATE"]), EmployeeLog.process_id.is_(None))
            )
            .distinct(EmployeeLog.employee_id)
            .limit(1000)
            .all()
        )

        if not updated_employee_ids or len(updated_employee_ids) == 0:
            break

        with db_session.begin_nested():
            update_batch_to_processing(db_session, updated_employee_ids, process_id)

        successfully_processed_employee_ids = process_employee_batch(
            db_session, fineos, output_dir_path, updated_employee_ids, report
        )

        with db_session.begin_nested():
            delete_processed_batch(db_session, successfully_processed_employee_ids, process_id)

    if report.employers_total_count == 0:
        logger.info("Eligibility Feed: No updates found to process.")

    report.completed_at = utcnow().isoformat()

    return report


def process_employee_batch(
    db_session: db.Session,
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    output_dir_path: str,
    batch_of_employee_ids: Iterable,
    report: EligibilityFeedExportReport,
) -> List:
    # Get the latest wages record for modified employee to get
    # employer associated with it.
    employer_employee_pairs = (
        db_session.query(
            WagesAndContributions.employer_id,
            WagesAndContributions.employee_id,
            func.max(WagesAndContributions.filing_period).label("maxdate"),
        )
        .filter(WagesAndContributions.employee_id.in_(batch_of_employee_ids))
        .group_by(WagesAndContributions.employer_id, WagesAndContributions.employee_id)
        .order_by(WagesAndContributions.employee_id, WagesAndContributions.employer_id)
        .all()
    )

    latest_employer_for_employee = get_latest_employer_for_updates(employer_employee_pairs)

    # Organize pairs into a structured class
    employer_id_to_employee_ids: Dict[str, List] = {}
    for employer_employee_pair in latest_employer_for_employee:
        employer_id_to_employee_ids.setdefault(employer_employee_pair.employer_id, []).append(
            employer_employee_pair.employee_id
        )

    # Process list of employers
    successfully_processed_employee_ids: List = []
    for employer_id, employee_ids in employer_id_to_employee_ids.items():
        try:
            report.employers_total_count += 1

            employer = db_session.query(Employer).filter(Employer.employer_id == employer_id).one()

            # Find FINEOS employer id using employer FEIN
            fineos_employer_id = get_fineos_employer_id(fineos, employer)
            if fineos_employer_id is None:
                logger.info(
                    "FINEOS employer id not in API DB. Continuing.",
                    extra={
                        "internal_employer_id": employer.employer_id,
                        "account_key": employer.account_key,
                    },
                )
                report.employers_skipped_count += 1
                continue

            number_of_employees = len(employee_ids)
            report.employee_and_employer_pairs_total_count += number_of_employees

            employees_and_most_recent_wages: Iterable[
                Tuple[Employee, WagesAndContributions]
            ] = query_employees_and_most_recent_wages_for_employer(
                db_session.query(Employee, WagesAndContributions), employer
            ).filter(
                Employee.employee_id.in_(employee_ids)
            ).yield_per(
                1000
            )

            open_and_write_to_eligibility_file(
                output_dir_path,
                fineos_employer_id,
                employer,
                number_of_employees,
                employees_and_most_recent_wages,
            )

            report.employers_success_count += 1
            successfully_processed_employee_ids.extend(employee_ids)
        except Exception:
            logger.exception(
                "Error generating FINEOS Eligibility Feed for Employer",
                extra={"internal_employer_id": employer.employer_id},
            )
            report.employers_error_count += 1
            continue

    return successfully_processed_employee_ids


def update_batch_to_processing(db_session, employee_ids, process_id):
    db_session.query(EmployeeLog).filter(EmployeeLog.employee_id.in_(employee_ids)).update(
        {EmployeeLog.process_id: process_id}, synchronize_session=False
    )


def delete_processed_batch(db_session, employee_ids, process_id):
    db_session.query(EmployeeLog).filter(
        EmployeeLog.employee_id.in_(employee_ids), EmployeeLog.process_id == process_id
    ).delete(synchronize_session=False)


class TaskResultStatus(Enum):
    SUCCESS = enum.auto()
    SKIPPED = enum.auto()
    ERROR = enum.auto()


# per-process globals for concurrent runs
db_session: Optional[db.Session] = None
fineos: Optional[massgov.pfml.fineos.AbstractFINEOSClient] = None
output_transport_params: Optional[Dict[str, Any]] = None


def is_fineos_output_location(path: str) -> bool:
    return path.startswith("s3://fin-som")


def process_all_worker_initializer(
    make_db_session: Callable[[], db.Session],
    make_fineos_client: Callable[[], massgov.pfml.fineos.AbstractFINEOSClient],
    make_fineos_boto_session: Callable[[EligibilityFeedExportConfig], boto3.Session],
    config: EligibilityFeedExportConfig,
) -> None:
    global db_session, fineos, output_transport_params

    db_session = make_db_session()
    fineos = make_fineos_client()

    output_transport_params = {}

    if is_fineos_output_location(config.output_directory_path):
        session = make_fineos_boto_session(config)
        output_transport_params = dict(session=session)


def process_all_worker(
    config: EligibilityFeedExportConfig, employer: Employer, index: int, total_employers_count: int
) -> Tuple[TaskResultStatus, Optional[int]]:
    global db_session, fineos, output_transport_params
    output_dir_path = config.output_directory_path

    if not db_session or not fineos:
        logger.error("Database session and FINEOS client not initialized for task")
        return (TaskResultStatus.ERROR, None)

    try:
        # Find FINEOS employer id using employer FEIN
        fineos_employer_id = get_fineos_employer_id(fineos, employer)
        if fineos_employer_id is None:
            logger.info(
                "FINEOS employer id not in Portal DB. Continuing.",
                extra={"account_key": employer.account_key},
            )
            return (TaskResultStatus.SKIPPED, None)

        number_of_employees = query_employees_for_employer(
            db_session.query(Employee.employee_id), employer
        ).count()

        employees_and_most_recent_wages: Iterable[
            Tuple[Employee, WagesAndContributions]
        ] = query_employees_and_most_recent_wages_for_employer(
            db_session.query(Employee, WagesAndContributions), employer
        ).yield_per(
            1000
        )

        output_bundle_dir_path = determine_bundle_path(
            output_dir_path, index, total_employers_count
        )

        open_and_write_to_eligibility_file(
            output_bundle_dir_path,
            fineos_employer_id,
            employer,
            number_of_employees,
            employees_and_most_recent_wages,
            output_transport_params,
        )
        return (TaskResultStatus.SUCCESS, number_of_employees)
    except Exception:
        logger.exception(
            "Error creating employer export", extra={"employer_id": employer.employer_id}
        )
        return (TaskResultStatus.ERROR, None)
    finally:
        db_session.close()


def process_all_employers(
    make_db_session: Callable[[], db.Session],
    make_fineos_client: Callable[[], massgov.pfml.fineos.AbstractFINEOSClient],
    make_fineos_boto_session: Callable[[EligibilityFeedExportConfig], boto3.Session],
    config: EligibilityFeedExportConfig,
) -> EligibilityFeedExportReport:
    db_session = make_db_session()

    start_time = utcnow()
    report = EligibilityFeedExportReport(started_at=start_time.isoformat())

    logger.info("Starting eligibility feeds generation for all employers")

    employers = db_session.query(Employer).yield_per(1000)
    employers_count = db_session.query(Employer.employer_id).count()

    employers_with_logging = massgov.pfml.util.logging.log_every(
        logger,
        employers,
        count=1000,
        start_time=start_time,
        item_name="Employer",
        total_count=employers_count,
    )

    employers_with_logging_and_index = enumerate(employers_with_logging, 0)

    max_workers: Optional[int] = None

    # this should be big enough to keep all workers fed, any more doesn't
    # necessarily have an impact, unless the query to fetch new records is
    # particularly costly, and the smaller keeps `log_every` more accurate
    work_queue_size: int = 100

    if cpu_count := os.cpu_count():
        max_workers = cpu_count * 2

    if max_workers:
        work_queue_size = max_workers * 2

    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=process_all_worker_initializer,
        initargs=(make_db_session, make_fineos_client, make_fineos_boto_session, config),
    ) as executor:
        futures = {
            executor.submit(process_all_worker, config, employer, index, employers_count)
            for index, employer in itertools.islice(
                employers_with_logging_and_index, work_queue_size
            )
        }

        while futures:
            done, futures = concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_COMPLETED
            )

            for r in done:
                report.employers_total_count += 1
                status, count = r.result()

                if status is TaskResultStatus.SUCCESS:
                    if count is None:
                        logger.error(
                            "Task reported success but returned no employee count, using 0"
                        )
                        count = 0

                    report.employers_success_count += 1
                    report.employee_and_employer_pairs_total_count += count
                elif status is TaskResultStatus.SKIPPED:
                    report.employers_skipped_count += 1
                elif status is TaskResultStatus.ERROR:
                    report.employers_error_count += 1

            for index, employer in itertools.islice(employers_with_logging_and_index, len(done)):
                futures.add(
                    executor.submit(process_all_worker, config, employer, index, employers_count)
                )

    db_session.close()

    end_time = utcnow()
    report.completed_at = end_time.isoformat()

    return report


ELIGIBILITY_FEED_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
    Decimal: lambda n: str(round(n, 6)),
}


def determine_bundle_path(
    output_dir_path: str, index: int, total: int, total_bundles: int = 12
) -> str:
    bundle_size_initial = 1000
    bundle_size_after_initial = math.ceil((total - bundle_size_initial) / (total_bundles - 1))

    if index >= total:
        raise ValueError("Item count is greater than expected total")

    if index < bundle_size_initial:
        bundle_num = 1
    else:
        minus_initial = index - bundle_size_initial
        bundle_num_calculated = (minus_initial // bundle_size_after_initial) + 2
        # just in case something is off in the calculation, clamp it to a valid
        # batch number, i.e., after the initial one and no more than the
        # total_bundles limit
        bundle_num = max(min(bundle_num_calculated, 12), 2)

    # the first bundle directory is not numbered
    bundle_num_path_part = "" if bundle_num == 1 else str(bundle_num)

    return f"{output_dir_path}/absence-eligibility{bundle_num_path_part}/upload"


def open_and_write_to_eligibility_file(
    output_dir_path: str,
    fineos_employer_id: int,
    employer: Employer,
    number_of_employees: int,
    employees: Iterable[Tuple[Employee, WagesAndContributions]],
    output_transport_params: Optional[OutputTransportParams] = None,
) -> str:
    output_file_path = (
        f"{output_dir_path}/{datetime.now().strftime('%Y%m%dT%H%M%S')}_{fineos_employer_id}.csv"
    )

    logger.info(
        "Opening destination to write eligibility feed",
        extra={
            "internal_employer_id": employer.employer_id,
            "fineos_employer_id": fineos_employer_id,
            "number_of_employees": number_of_employees,
            "output_file": output_file_path,
        },
    )

    try:
        s3_obj = None

        with smart_open.open(
            output_file_path, "w", transport_params=output_transport_params
        ) as output_file:
            if file_util.is_s3_path(output_file_path):
                s3_obj = output_file.to_boto3()

            write_employees_to_csv(
                employer, str(fineos_employer_id), number_of_employees, employees, output_file,
            )
    except Exception:
        logger.info(
            "Error writing eligibility feed. Deleting partial export file.",
            extra={
                "internal_employer_id": employer.employer_id,
                "fineos_employer_id": fineos_employer_id,
                "number_of_employees": number_of_employees,
                "output_file": output_file_path,
            },
        )

        if s3_obj:
            s3_obj.delete()
        else:
            file_util.remove_if_exists(output_file_path)

        raise

    return output_file_path


def write_employees_to_csv(
    employer: Employer,
    fineos_employer_id: str,
    number_of_employees: int,
    employees_with_most_recent_wages: Iterable[Tuple[Employee, WagesAndContributions]],
    output_file: TextIO,
) -> None:
    start_time = utcnow()

    logger.info(
        "Starting to write eligibility feed",
        extra={
            "internal_employer_id": employer.employer_id,
            "fineos_employer_id": fineos_employer_id,
            "number_of_employees": number_of_employees,
            "output_file": output_file.name,
        },
    )

    # write datablock section
    logger.debug("Writing DATABLOCK section")
    output_file.write(f"EMPLOYER_ID:{fineos_employer_id}\n")
    output_file.write(f"NUMBER_OF_RECORDS:{number_of_employees}\n")
    output_file.write("@DATABLOCK\n")

    # write CSV parts
    logger.debug("Writing CSV header")
    writer = csv.DictWriter(
        output_file,
        fieldnames=list(map(lambda f: f.name, dataclasses.fields(EligibilityFeedRecord))),
    )
    writer.writeheader()

    employees_with_most_recent_wages_with_logging = massgov.pfml.util.logging.log_every(
        logger,
        employees_with_most_recent_wages,
        count=1000,
        start_time=start_time,
        total_count=number_of_employees,
        item_name="Employee",
        extra={
            "internal_employer_id": employer.employer_id,
            "fineos_employer_id": fineos_employer_id,
            "output_file": output_file.name,
        },
    )

    logger.debug("Writing CSV rows")
    processed_employee_count = 0
    for (employee, most_recent_wages) in employees_with_most_recent_wages_with_logging:
        logger.debug("Writing row for employee", extra={"employee_id": employee.employee_id})
        try:
            writer.writerow(
                csv_util.encode_row(
                    employee_to_eligibility_feed_record(employee, most_recent_wages, employer),
                    ELIGIBILITY_FEED_CSV_ENCODERS,
                )
            )
        except Exception:
            logger.error(
                "Error processing employee entry",
                extra={
                    "internal_employer_id": employer.employer_id,
                    "fineos_employer_id": fineos_employer_id,
                    "number_of_employees": number_of_employees,
                    "output_file": output_file.name,
                    "processed_employee_count": processed_employee_count,
                    "employee_id": employee.employee_id,
                },
            )
            raise

        processed_employee_count += 1

    logger.info(
        "Finished writing eligibility feed",
        extra={
            "internal_employer_id": employer.employer_id,
            "fineos_employer_id": fineos_employer_id,
            "number_of_employees": number_of_employees,
            "output_file": output_file.name,
            "processed_employee_count": processed_employee_count,
        },
    )

    # TODO: how to actually handle this properly? throw exception here? delete file?
    if processed_employee_count != number_of_employees:
        logger.error(
            f"Eligibility feed count mismatch, expected to process {number_of_employees}, actually processed {processed_employee_count}",
            extra={
                "internal_employer_id": employer.employer_id,
                "fineos_employer_id": fineos_employer_id,
                "number_of_employees": number_of_employees,
                "output_file": output_file.name,
                "processed_employee_count": processed_employee_count,
            },
        )


def employee_to_eligibility_feed_record(
    employee: Employee, most_recent_wages: WagesAndContributions, employer: Employer
) -> Optional[EligibilityFeedRecord]:
    record = EligibilityFeedRecord(
        # FINEOS required fields, without a general default we can set
        employeeIdentifier=employee.employee_id,
        employeeFirstName=employee.first_name,
        employeeLastName=employee.last_name,
        # FINEOS required fields, but with an agreed upon default we can fall
        # back on
        employeeDateOfBirth=employee.date_of_birth,
        # FINEOS optional params
        employeeSecondName=employee.middle_name,
        employeeGender=(Gender(employee.gender.gender_description) if employee.gender else None),
        employeeMaritalStatus=(
            MaritalStatus(employee.marital_status.marital_status_description)
            if employee.marital_status
            else None
        ),
        # TODO: use Pydantic TaxIdUnformattedStr? Or otherwise create a type for
        # TaxId that can be formatted appropriately in the encoder?
        employeeNationalID=(
            employee.tax_identifier.tax_identifier.replace("-", "")
            if employee.tax_identifier
            else None
        ),
        employeeNationalIDType=(
            determine_national_id_type(str(employee.tax_identifier.tax_identifier))
            if employee.tax_identifier
            else None
        ),
        employeeEmail=employee.email_address,
    )

    employee_address = employee.addresses.first()
    if employee_address:
        address = employee_address.address
        record.addressType = AddressType(address.address_type.address_description)
        record.addressAddressLine1 = address.address_line_one
        record.addressCity = address.city
        record.addressState = address.geo_state.geo_state_description
        record.addressZipCode = address.zip_code

    if employee.phone_number:
        # TODO: pull in phonenumber lib to parse numbers properly here and in
        # request handlers so values are stored in standard format in DB
        phone_parts = employee.phone_number.split("-")

        # TODO: if there's an indication that the number is a cell phone, set
        # cell* attributes instead, unless it's the only number we have, then
        # still set telephone* attrs? Both attribute sets seem to feed into the
        # same place, OCPhone, but maybe extra flag is set if cell*
        if len(phone_parts) == 3:
            record.telephoneIntCode = "1"
            record.telephoneAreaCode = phone_parts[0]
            record.telephoneNumber = "".join(phone_parts[1:])

    return record

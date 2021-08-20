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
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, TextIO, Tuple, TypeVar, Union
from uuid import UUID

import boto3
import phonenumbers
import smart_open
from pydantic import BaseSettings, Field, PositiveInt
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Query

import massgov.pfml.db as db
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeeLog,
    EmployeeOccupation,
    Employer,
    WagesAndContributions,
)
from massgov.pfml.fineos import AbstractFINEOSClient
from massgov.pfml.fineos.exception import FINEOSNotFound
from massgov.pfml.util.datetime import utcnow

logger = massgov.pfml.util.logging.get_logger(__name__)

EmployerId = UUID
EmployeeId = UUID


class EligibilityFeedExportMode(Enum):
    FULL = "full"
    UPDATES = "updates"
    LIST = "list"


class EligibilityFeedExportConfig(BaseSettings):
    output_directory_path: str = Field(..., min_length=1)
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)
    mode: EligibilityFeedExportMode = Field(
        EligibilityFeedExportMode.FULL, env="ELIGIBILITY_FEED_MODE"
    )
    update_batch_size: int = Field(1000, env="ELIGIBILITY_FEED_UPDATE_BATCH_SIZE")
    export_file_number_limit: Optional[int] = Field(
        None, env="ELIGIBILITY_FEED_EXPORT_FILE_NUMBER_LIMIT"
    )  # Only applies to "updates" mode
    bundle_count: PositiveInt = PositiveInt(1)  # Only applies to "full" mode currently
    employer_ids: str = Field(
        None, env="ELIGIBILITY_FEED_LIST_OF_EMPLOYER_IDS"
    )  # Applies to "list" mode only. Pass a list of employer Id's to process.


DEFAULT_DATE = date(1753, 1, 1)
DEFAULT_HIRE_DATE = date(2020, 1, 1)
DEFAULT_EMPLOYMENT_WORK_STATE = "MA"


class AddressType(Enum):
    home = "Home"
    business = "Business"


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
class PhoneNumber:
    country_code: str
    number: str
    area_code: Optional[str] = None


# parse E.164 format phone number
def parse_phone_number(phone_number: str) -> Optional[PhoneNumber]:
    try:
        parsed_phone_number = phonenumbers.parse(phone_number)
        national_number = str(parsed_phone_number.national_number)
        if parsed_phone_number.country_code == 1:  # get area code for US number
            return PhoneNumber(
                country_code=str(parsed_phone_number.country_code),
                number=national_number[3:],
                area_code=national_number[0:3],
            )
        else:
            return PhoneNumber(
                country_code=str(parsed_phone_number.country_code), number=national_number
            )
    except phonenumbers.NumberParseException:
        return None


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
    # FINEOS DB type is DECIMAL(5,2)
    # 5 digits of precision overall, 2 digits past the decimal if needed
    employeeHoursWorkedPerWeek: Union[Decimal, None] = Decimal(0)

    # all other fields are (usually) optional
    employeeTitle: Optional[str] = None
    # if employeeThirdName is specified, employeeSecondName is then required
    employeeSecondName: Optional[str] = None
    employeeThirdName: Optional[str] = None
    employeeDateOfDeath: Optional[date] = None
    employeeGender: Optional[str] = None
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
    spouseGender: Optional[str] = None
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
    # FINEOS DB type is DECIMAL(5,2)
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
    start: str
    end: Optional[str] = None
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


class EmployerEmployeeLogPairQueryResult(db.RowProxy):
    employer_id: EmployerId
    employee_id: EmployeeId


class EmployerEmployeePairQueryResult(db.RowProxy):
    employer_id: EmployerId
    employee_id: EmployeeId
    maxdate: date


def get_most_recent_employer_and_employee_log_employers_to_employee_info(
    db_session: db.Session, employee_ids: Iterable[EmployeeId]
) -> Dict[EmployerId, List[EmployeeId]]:
    employer_employee_pairs: List[EmployerEmployeePairQueryResult] = (
        db_session.query(
            WagesAndContributions.employer_id,
            WagesAndContributions.employee_id,
            func.max(WagesAndContributions.filing_period).label("maxdate"),
        )
        .filter(WagesAndContributions.employee_id.in_(employee_ids))
        .group_by(WagesAndContributions.employer_id, WagesAndContributions.employee_id)
        .order_by(
            desc("maxdate"), WagesAndContributions.employee_id, WagesAndContributions.employer_id
        )
        .all()
    )

    # since the query is ordered first by maxdate, the first employer-employee
    # pair will be the most recent one
    most_recent_employer_employee_pairs = filter_to_first_employer_employee_pair(
        employer_employee_pairs
    )

    employee_log_employers: List[EmployerEmployeeLogPairQueryResult] = (
        db_session.query(EmployeeLog.employee_id, EmployeeLog.employer_id)
        .filter(EmployeeLog.employer_id.isnot(None), EmployeeLog.employee_id.in_(employee_ids))
        .group_by(EmployeeLog.employer_id, EmployeeLog.employee_id)
        .all()
    )

    # Organize pairs into the structure we want
    employer_id_to_employee_ids: Dict[EmployerId, List[EmployeeId]] = {}
    for employer_employee_pair in most_recent_employer_employee_pairs:
        employer_id_to_employee_ids.setdefault(employer_employee_pair.employer_id, []).append(
            employer_employee_pair.employee_id
        )

    for employee_log_employer in employee_log_employers:
        if employee_log_employer.employee_id not in employer_id_to_employee_ids.setdefault(
            employee_log_employer.employer_id, []
        ):
            employer_id_to_employee_ids.setdefault(employee_log_employer.employer_id, []).append(
                employee_log_employer.employee_id
            )

    return employer_id_to_employee_ids


def filter_to_first_employer_employee_pair(
    employer_employee_list: List[EmployerEmployeePairQueryResult],
) -> List[EmployerEmployeePairQueryResult]:
    """Filter input list to only contain the first reference for an employee.

    This could be done in SQL, but isn't currently in order to keep core query
    simple until there is a chance to focus on optimization.
    """
    seen_employee_ids = set()
    first_employee_records = []

    for employer_employee_pair in employer_employee_list:
        if employer_employee_pair.employee_id not in seen_employee_ids:
            seen_employee_ids.add(employer_employee_pair.employee_id)
            first_employee_records.append(employer_employee_pair)

    return first_employee_records


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


# When loading employers to FINEOS the API we use requires us to
# generate a unique key which we pass in the attribute CustomerNo.
#
# The API returns the FINEOS primary key for the organization it
# created in the response as attribute CUSTOMER_NUMBER. We store
# this value in the fineos_employer_id field in the employer model.
# The fineos_employer_id is the value that should be used to identify
# an employer in the Eligibility Feed.
def get_fineos_employer_id(fineos: AbstractFINEOSClient, employer: Employer) -> Optional[int]:
    if employer.fineos_employer_id:
        return employer.fineos_employer_id

    try:
        fineos_employer_id = fineos.find_employer(employer.employer_fein)
        return int(fineos_employer_id)
    except FINEOSNotFound:
        return None


def process_employee_updates(
    db_session: db.Session,
    fineos: AbstractFINEOSClient,
    output_dir_path: str,
    output_transport_params: Optional[OutputTransportParams] = None,
    batch_size: int = 1000,
    export_file_number_limit: Optional[int] = None,
) -> EligibilityFeedExportReport:
    report = EligibilityFeedExportReport(start=utcnow().isoformat())

    logger.info(
        "Starting eligibility feeds generation for employee updates.",
        extra={
            "output_dir_path": output_dir_path,
            "batch_size": batch_size,
            "export_file_number_limit": export_file_number_limit,
        },
    )

    # We may modify this code to spawn more than one process to consume the
    # updates similar to what has been done for all employers process.
    # When doing so we should use the same sequence of process identifiers
    # so that at recovery the process knows what incomplete rows to pick from
    # EmployeeLog.
    process_id = 1

    unsuccessful_employee_ids: Set[EmployeeId] = set()
    while "batch not empty":
        updated_employee_ids: Set[EmployeeId] = set(
            row[0]
            for row in db_session.query(EmployeeLog.employee_id)
            .filter(
                EmployeeLog.action.in_(["INSERT", "UPDATE", "UPDATE_NEW_EMPLOYER"]),
                or_(EmployeeLog.process_id.is_(None), EmployeeLog.process_id == process_id),
                EmployeeLog.employee_id.notin_(unsuccessful_employee_ids),
            )
            .distinct(EmployeeLog.employee_id)
            .limit(batch_size)
            .all()
        )

        if not updated_employee_ids or len(updated_employee_ids) == 0:
            break

        update_batch_to_processing(db_session, updated_employee_ids, process_id)
        db_session.commit()

        successfully_processed_employee_ids = process_employee_batch(
            db_session,
            fineos,
            output_dir_path,
            updated_employee_ids,
            report,
            output_transport_params,
            export_file_number_limit=export_file_number_limit,
        )

        unsuccessful_employee_ids.update(
            updated_employee_ids.difference(successfully_processed_employee_ids)
        )

        delete_processed_batch(db_session, successfully_processed_employee_ids, process_id)
        db_session.commit()

        # process_employee_batch() will stop processing if it hits the limit,
        # but need to break out of this loop grabbing the batches as well
        if export_file_number_limit and report.employers_success_count >= export_file_number_limit:
            logger.info("Export file number limit was hit. Finishing task.")
            break

    if report.employers_total_count == 0:
        logger.info("Eligibility Feed: No updates found to process.")

    report.end = utcnow().isoformat()

    return report


def process_employee_batch(
    db_session: db.Session,
    fineos: AbstractFINEOSClient,
    output_dir_path: str,
    batch_of_employee_ids: Iterable[EmployeeId],
    report: EligibilityFeedExportReport,
    output_transport_params: Optional[OutputTransportParams] = None,
    export_file_number_limit: Optional[int] = None,
) -> Set[EmployeeId]:
    # Want information for the only most recent Employer for a given Employee
    employer_id_to_employee_ids = get_most_recent_employer_and_employee_log_employers_to_employee_info(
        db_session, batch_of_employee_ids
    )

    # Process list of employers
    successfully_processed_employee_ids: List[EmployeeId] = []
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
                output_transport_params,
            )

            report.employers_success_count += 1
            successfully_processed_employee_ids.extend(employee_ids)

            if (
                export_file_number_limit
                and report.employers_success_count >= export_file_number_limit
            ):
                logger.info(
                    "Hit export file number limit while processing batch. Stopping batch processing."
                )
                break
        except Exception:
            logger.exception(
                "Error generating FINEOS Eligibility Feed for Employer",
                extra={"internal_employer_id": employer.employer_id},
            )
            report.employers_error_count += 1
            continue

    return set(successfully_processed_employee_ids)


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
fineos: Optional[AbstractFINEOSClient] = None
output_transport_params: Optional[Dict[str, Any]] = None


def is_fineos_output_location(path: str) -> bool:
    return path.startswith("s3://fin-som")


def process_all_worker_initializer(
    make_db_session: Callable[[], db.Session],
    make_fineos_client: Callable[[], AbstractFINEOSClient],
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
            output_dir_path, index, total_employers_count, total_bundles=config.bundle_count
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
    make_fineos_client: Callable[[], AbstractFINEOSClient],
    make_fineos_boto_session: Callable[[EligibilityFeedExportConfig], boto3.Session],
    config: EligibilityFeedExportConfig,
) -> EligibilityFeedExportReport:
    db_session = make_db_session()

    start_time = utcnow()
    report = EligibilityFeedExportReport(start=start_time.isoformat())

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
    report.end = end_time.isoformat()

    return report


# Used by Prod Support to fix a small number of employers.
# This method is not meant to be used for high volumes.
def process_a_list_of_employers(
    employer_ids: List[str],
    db_session: db.Session,
    fineos_client: AbstractFINEOSClient,
    output_dir_path: str,
    output_transport_params: Optional[OutputTransportParams] = None,
) -> EligibilityFeedExportReport:
    start_time = utcnow()
    report = EligibilityFeedExportReport(start=start_time.isoformat())

    logger.info(f"Starting eligibility feeds generation for a list of employers: {employer_ids}")

    employers_to_process: List[Employer] = db_session.query(Employer).filter(
        Employer.employer_id.in_(employer_ids)
    ).all()
    employers_to_process_count = len(employers_to_process)

    if employers_to_process_count != len(employer_ids):
        logger.error("Not all employers in input list found in the database. Exiting.")
        return report

    # Process list of employers
    for employer in employers_to_process:
        try:
            report.employers_total_count += 1

            # Find FINEOS employer id using employer FEIN
            fineos_employer_id = get_fineos_employer_id(fineos_client, employer)
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

            open_and_write_to_eligibility_file(
                output_dir_path,
                fineos_employer_id,
                employer,
                number_of_employees,
                employees_and_most_recent_wages,
                output_transport_params,
            )

            report.employers_success_count += 1
            report.employee_and_employer_pairs_total_count += number_of_employees
        except Exception:
            logger.exception(
                "Error generating FINEOS Eligibility Feed for Employer",
                extra={"internal_employer_id": employer.employer_id},
            )
            report.employers_error_count += 1
            continue

    end_time = utcnow()
    report.end = end_time.isoformat()

    return report


ELIGIBILITY_FEED_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
    Decimal: lambda n: str(round(n, 2)),
}


def determine_bundle_path(
    output_dir_path: str, index: int, total: int, total_bundles: int = 12
) -> str:
    if total_bundles <= 1:
        bundle_num = 1
    else:
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
            bundle_num = max(min(bundle_num_calculated, total_bundles), 2)

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
        employeeGender=(employee.gender.fineos_gender_description if employee.gender else None),
        employeeMaritalStatus=(
            MaritalStatus(employee.marital_status.marital_status_description)
            if employee.marital_status
            else None
        ),
        employeeNationalID=(
            employee.tax_identifier.tax_identifier.to_unformatted_str().replace("-", "")
            if employee.tax_identifier
            else None
        ),
        employeeNationalIDType=(
            determine_national_id_type(
                employee.tax_identifier.tax_identifier.to_unformatted_str().replace("-", "")
            )
            if employee.tax_identifier
            else None
        ),
        employeeEmail=employee.email_address,
        employeeTitle=(employee.title.title_description if employee.title else None),
        employeeDateOfDeath=employee.date_of_death,
    )

    employee_occupation_for_employer: Optional[
        EmployeeOccupation
    ] = employee.employee_occupations.filter(
        EmployeeOccupation.employer_id == employer.employer_id
    ).one_or_none()

    if employee_occupation_for_employer:
        occupation: EmployeeOccupation = employee_occupation_for_employer
        record.employeeJobTitle = occupation.job_title
        record.employeeDateOfHire = occupation.date_of_hire
        record.employeeEndDate = occupation.date_job_ended
        record.employmentStatus = occupation.employment_status
        record.employeeOrgUnitName = occupation.org_unit_name
        record.employeeHoursWorkedPerWeek = (
            Decimal(occupation.hours_worked_per_week) if occupation.hours_worked_per_week else None
        )
        record.employeeDaysWorkedPerWeek = (
            Decimal(occupation.days_worked_per_week) if occupation.days_worked_per_week else None
        )
        record.managerIdentifier = occupation.manager_id
        record.occupationQualifier = occupation.occupation_qualifier
        record.employeeWorkSiteId = occupation.worksite_id

    if employee.phone_number:
        phone_number: Optional[PhoneNumber] = parse_phone_number(employee.phone_number)
        if phone_number:
            record.telephoneIntCode = phone_number.country_code
            record.telephoneAreaCode = phone_number.area_code
            record.telephoneNumber = phone_number.number

    if employee.cell_phone_number:
        cell_phone_number: Optional[PhoneNumber] = parse_phone_number(employee.cell_phone_number)
        if cell_phone_number:
            record.cellIntCode = cell_phone_number.country_code
            record.cellAreaCode = cell_phone_number.area_code
            record.cellNumber = cell_phone_number.number

    return record

import csv
import dataclasses
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, TextIO, TypeVar, Union

import smart_open
from sqlalchemy import func
from sqlalchemy.orm import Query

import massgov.pfml.db as db
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employee, EmployeeLog, Employer, WagesAndContributions
from massgov.pfml.fineos.exception import FINEOSNotFound

logger = massgov.pfml.util.logging.get_logger(__name__)

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
    # def __post_init__(self):db_session
    #     for field in dataclasses.fields(self):
    #         if field.default is not None:
    #             field_val = getattr(self, field.name)
    #             if field_val is None:
    #                 setattr(self, field.name, field.default)

    def __setattr__(self, attr, value):
        if value is None:
            # TODO: pretty wasteful to iterate over the entire field list every
            # time something is getting set to None
            fields_with_non_none_default = {
                f.name: f for f in dataclasses.fields(self) if f.default is not None
            }

            if attr in fields_with_non_none_default:
                value = fields_with_non_none_default[attr].default

        super().__setattr__(attr, value)


@dataclass
class EligibilityFeedRecord(NoneMeansDefault):
    # FINEOS required fields, without a general default we can set
    employeeIdentifier: str
    employeeFirstName: str
    employeeLastName: str
    employeeEffectiveFromDate: date
    # FINEOS DB type is DECIMAL(28,6)
    # 28 digits of precision overall, up to 6 digits past the decimal
    employeeSalary: Decimal
    employeeEarningFrequency: EarningFrequency

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
    # TODO: there can be multiple of these starting with occupationQualifier*
    occupationQualifier: Optional[str] = None
    employeeWorkSiteId: Optional[str] = None
    employeeEffectiveToDate: Optional[date] = None


@dataclass
class ProcessUpdatesResult:
    employers_total_count: int
    employee_and_employer_pairs_total_count: int


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
# We store that value in fineos_customer_nbr in the employer model.
# FINEOS uses this key to determine if a request is a create or an
# update.
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
) -> ProcessUpdatesResult:
    employers_total_count = 0
    employee_and_employer_pairs_total_count = 0

    logger.info("Starting eligibility feeds generation for employee updates.")
    # Get employee changes from log table in batches
    # TODO Add a process date to process only items since last run.
    # https://lwd.atlassian.net/browse/API-710
    updated_employees_query = (
        db_session.query(EmployeeLog.employee_id)
        .filter(EmployeeLog.action.in_(["INSERT", "UPDATE"]))
        .distinct(EmployeeLog.employee_id)
        .yield_per(1000)
    )

    if updated_employees_query.count() == 0:
        logger.info("Eligibility Feed: No updates to process.")
        return ProcessUpdatesResult(
            employers_total_count=0, employee_and_employer_pairs_total_count=0,
        )

    # Get the latest wages record for modified employee to get
    # employer associated with it.
    employer_employee_pairs = (
        db_session.query(
            WagesAndContributions.employer_id,
            WagesAndContributions.employee_id,
            func.max(WagesAndContributions.filing_period).label("maxdate"),
        )
        .filter(WagesAndContributions.employee_id.in_(updated_employees_query))
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
    for employer_id, employee_ids in employer_id_to_employee_ids.items():
        employer = db_session.query(Employer).filter(Employer.employer_id == employer_id).one()
        # Find FINEOS employer id using employer FEIN
        fineos_employer_id = get_fineos_employer_id(fineos, employer)
        if fineos_employer_id is None:
            logger.info(
                "FINEOS employer id not in Portal DB. Continuing.",
                extra={"account_key": employer.account_key},
            )
            continue

        number_of_employees = len(employee_ids)
        employee_and_employer_pairs_total_count += number_of_employees

        employees = (
            db_session.query(Employee)
            .filter(Employee.employee_id.in_(employee_ids))
            .yield_per(1000)
        )

        open_and_write_to_eligibility_file(
            output_dir_path, fineos_employer_id, employer, number_of_employees, employees
        )

        employers_total_count += 1

    logger.info(
        "Finished writing all eligibility feeds",
        extra={
            "employers_total_count": employers_total_count,
            "employee_and_employer_pairs_total_count": employee_and_employer_pairs_total_count,
        },
    )

    return ProcessUpdatesResult(
        employers_total_count=employers_total_count,
        employee_and_employer_pairs_total_count=employee_and_employer_pairs_total_count,
    )


def process_all_employers(
    db_session: db.Session,
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    output_dir_path: str,
    output_transport_params: Optional[OutputTransportParams] = None,
) -> ProcessUpdatesResult:
    employers_total_count = 0
    employee_and_employer_pairs_total_count = 0

    logger.info("Starting eligibility feeds generation for all employers")

    employers = db_session.query(Employer).yield_per(1000)

    for employer in employers:
        # Find FINEOS employer id using employer FEIN
        fineos_employer_id = get_fineos_employer_id(fineos, employer)
        if fineos_employer_id is None:
            logger.info(
                "FINEOS employer id not in Portal DB. Continuing.",
                extra={"account_key": employer.account_key},
            )
            continue

        employers_total_count += 1

        number_of_employees = query_employees_for_employer(
            db_session.query(Employee.employee_id), employer
        ).count()

        # TODO: use result of write_employees_to_csv instead?
        employee_and_employer_pairs_total_count += number_of_employees

        employees = query_employees_for_employer(db_session.query(Employee), employer).yield_per(
            1000
        )

        open_and_write_to_eligibility_file(
            output_dir_path,
            fineos_employer_id,
            employer,
            number_of_employees,
            employees,
            output_transport_params,
        )

    logger.info(
        "Finished writing all eligibility feeds",
        extra={
            "employers_total_count": employers_total_count,
            "employee_and_employer_pairs_total_count": employee_and_employer_pairs_total_count,
        },
    )

    return ProcessUpdatesResult(
        employers_total_count=employers_total_count,
        employee_and_employer_pairs_total_count=employee_and_employer_pairs_total_count,
    )


ELIGIBILITY_FEED_CSV_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%m/%d/%Y"),
    Decimal: lambda n: str(round(n, 6)),
}


def open_and_write_to_eligibility_file(
    output_dir_path: str,
    fineos_employer_id: int,
    employer: Employer,
    number_of_employees: int,
    employees: Iterable[Employee],
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

    with smart_open.open(
        output_file_path, "w", transport_params=output_transport_params
    ) as output_file:
        write_employees_to_csv(
            employer, str(fineos_employer_id), number_of_employees, employees, output_file,
        )

    return output_file_path


def write_employees_to_csv(
    employer: Employer,
    fineos_employer_id: str,
    number_of_employees: int,
    employees: Iterable[Employee],
    output_file: TextIO,
) -> None:
    logger.info(
        "Starting to write eligibility feed",
        extra={
            "employer_id": employer.employer_id,
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

    logger.debug("Writing CSV rows")
    processed_employee_count = 0
    for employee in employees:
        logger.debug("Writing row for employee", extra={"employee_id": employee.employee_id})
        writer.writerow(
            csv_util.encode_row(
                employee_to_eligibility_feed_record(employee, employer),
                ELIGIBILITY_FEED_CSV_ENCODERS,
            )
        )
        processed_employee_count += 1

    logger.info(
        "Finished writing eligibility feed",
        extra={
            "employer_id": employer.employer_id,
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
                "employer_id": employer.employer_id,
                "number_of_employees": number_of_employees,
                "output_file": output_file.name,
                "processed_employee_count": processed_employee_count,
            },
        )


def employee_to_eligibility_feed_record(
    employee: Employee, employer: Employer
) -> Optional[EligibilityFeedRecord]:
    most_recent_wages = (
        employee.wages_and_contributions.order_by(WagesAndContributions.filing_period.desc())
        .filter(WagesAndContributions.employer_id == employer.employer_id)
        .first()
    )

    if most_recent_wages is None:
        # TODO: should we throw exception instead?
        logger.warning(
            "Employee does have wage records for the specified employer, can not export for eligibility feed",
            extra={"employee_id": employee.employee_id, "employer_id": employer.employer_id},
        )
        return None

    record = EligibilityFeedRecord(
        # FINEOS required fields, without a general default we can set
        employeeIdentifier=employee.employee_id,
        employeeFirstName=employee.first_name,
        employeeLastName=employee.last_name,
        employeeEffectiveFromDate=most_recent_wages.filing_period,
        employeeSalary=most_recent_wages.employee_ytd_wages,
        employeeEarningFrequency=EarningFrequency.yearly,
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

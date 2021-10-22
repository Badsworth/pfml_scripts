import argparse
import sys
from enum import Enum
from typing import Any, Dict, List

from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.db as db
from massgov.pfml.db.models.employees import Employee, EmployeePushToFineosQueue, Gender
from massgov.pfml.util import logging
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.csv import CSVSourceWrapper

logger = logging.get_logger(__name__)

DUAColumns = {
    "fineos_id": "FINEOS",
    "fein": "FEIN",
    "birthdate": "BirthDt",
    "gender": "GenderCd",
    "occupation_code": "OccupationCode",
    "occupation_description": "OccupationDesc",
    "employer_unit_number": "EmployerUnitNumber",
}

DUA_TO_FINEOS_GENDER_MAP = {
    "M": Gender.MAN,
    "F": Gender.WOMAN,
    "U": Gender.NOT_LISTED,
}


class Metrics(str, Enum):
    EMPLOYEES_TOTAL_COUNT = "employees_total_count"
    DUA_NO_GENDER_COUNT = "dua_no_gender_count"
    DUA_INVALID_GENDER_VALUE_COUNT = "dua_invalid_gender_count"
    EMPLOYEES_UPDATED_COUNT = "employees_updated_count"
    EMPLOYEE_NOT_FOUND_OR_SKIPPED_COUNT = "employees_not_found_or_skipped_count"


class Configuration:
    source_file_path: str

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Update employee gender demographics from DUA file"
        )
        parser.add_argument("file", help="Local paths and S3 URIs supported")
        args = parser.parse_args(input_args)

        self.source_file_path = args.file


@background_task("dua_backfill_employee_gender")
def main():
    config = Configuration(sys.argv[1:])

    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with LogEntry(log_entry_db_session, "DUA update_employee_demographics") as log_entry:
            logger.info(
                "Processing DUA employee demographics file",
                extra={"employee_demographic_filename": config.source_file_path},
            )
            for dua_employee_row in CSVSourceWrapper(config.source_file_path):
                try:
                    backfill_employee_gender(db_session, log_entry, dua_employee_row)
                except Exception:
                    log_entry.increment(Metrics.EMPLOYEE_NOT_FOUND_OR_SKIPPED_COUNT)
                    logger.exception("Hit error processing gender update")


def backfill_employee_gender(
    db_session: db.Session, log_entry: LogEntry, dua_employee_row: Dict[Any, Any]
) -> None:
    log_entry.increment(Metrics.EMPLOYEES_TOTAL_COUNT)

    fineos_customer_number = dua_employee_row[DUAColumns["fineos_id"]]
    dua_gender_code = dua_employee_row[DUAColumns["gender"]]

    if not dua_gender_code:
        log_entry.increment(Metrics.DUA_NO_GENDER_COUNT)
        return

    gender = DUA_TO_FINEOS_GENDER_MAP.get(dua_gender_code, None)

    if not gender:
        log_entry.increment(Metrics.DUA_INVALID_GENDER_VALUE_COUNT)
        logger.warning(
            "Invalid gender value from input file",
            extra={
                "dua_gender_code": dua_gender_code,
                "fineos_customer_id": fineos_customer_number,
            },
        )
        return

    try:
        employee = (
            db_session.query(Employee)
            .filter(
                Employee.fineos_customer_number == fineos_customer_number,
                Employee.gender_id.is_(None),
            )
            .one_or_none()
        )
    except MultipleResultsFound:
        logger.exception(
            "Found multiple Employees with same fineos id and null gender, expected 1",
            extra={"fineos_customer_id": fineos_customer_number},
        )
        raise

    if not employee:
        log_entry.increment(Metrics.EMPLOYEE_NOT_FOUND_OR_SKIPPED_COUNT)
        return

    employee.gender_id = gender.gender_id
    db_session.add(EmployeePushToFineosQueue(employee_id=employee.employee_id, action="UPDATE"))
    db_session.commit()
    log_entry.increment(Metrics.EMPLOYEES_UPDATED_COUNT)

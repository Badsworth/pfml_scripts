import os
from datetime import date, datetime
from typing import IO, List, Set, Tuple
from uuid import UUID

from pydantic import Field
from pydantic.main import BaseModel
from sqlalchemy import distinct, func
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.selectable import Alias

import massgov.pfml.db as db
import massgov.pfml.util.files as file_util
import massgov.pfml.util.pydantic.csv as pydantic_csv_util
from massgov.pfml.db.models.employees import Claim, Employee, WagesAndContributions
from massgov.pfml.report.config import ReportsS3Config
from massgov.pfml.util import logging
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.datetime.quarter import Quarter

logger = logging.get_logger(__name__)


class SequentialEmploymentReportRow(BaseModel):
    row_name: str = Field(None, alias="ROW_NAME")
    group_total: int = Field(None, alias="GROUP_TOTAL")
    group_total_applicants: int = Field(None, alias="GROUP_TOTAL_APPLICANTS")
    percent_total_employees: float = Field(None, alias="PERCENT_TOTAL_EMPLOYEES")
    percent_total_applicants: float = Field(None, alias="PERCENT_TOTAL_APPLICANTS")
    total_employees: int = Field(None, alias="TOTAL_EMPLOYEES")
    total_applicants: int = Field(None, alias="TOTAL_APPLICANTS")


@background_task("report-sequential-employment")
def main():
    with db.session_scope(db.init(), close=True) as db_session:
        create_report(db_session)


def create_report(db_session: db.Session) -> None:
    logger.info("Creating sequential employment report")

    wages_1_of_2_prev_quarters, wages_both_prev_quarters = get_scenario_groups(db_session)

    total_applicants = total_applicant_count(db_session)
    total_employees = total_employee_count(db_session)

    def make_row(group: Set[UUID], group_name: str):
        applicant_count = group_applicant_count(db_session, group)
        group_total = len(group)
        row = SequentialEmploymentReportRow()

        row.row_name = group_name
        row.group_total = group_total
        row.group_total_applicants = applicant_count
        # Prevent divide by 0 error - could happen in lower envs.
        row.percent_total_employees = (
            round(group_total / total_employees, 5) if total_employees > 0 else 0
        )
        row.percent_total_applicants = (
            round(applicant_count / total_applicants, 5) if total_applicants > 0 else 0
        )
        row.total_employees = total_employees
        row.total_applicants = total_applicants

        report_row_dict = row.dict()
        logger.info("Created sequential employment report row", extra=report_row_dict)

        return row

    row1 = make_row(wages_1_of_2_prev_quarters, "Wages one of two quarters")
    row2 = make_row(wages_both_prev_quarters, "Wages both quarters")

    location = s3_location()
    logger.info("Writing sequential employment report to s3", extra={"s3_location": location})

    with file_util.open_stream(location, mode="w") as output_file:
        write_report_to_s3(output_file, [row1, row2])

    logger.info("Finished writing sequential employment report to s3")


def get_scenario_groups(db_session: db.Session) -> Tuple[Set[UUID]]:
    """
    Scenario One:
        - Subset of employee_ids that match an employee having non-zero wages reported in ONLY one of the last two quarters
    Scenario Two:
        - Subset of employee_ids that match an employee having non-zero wages reported in BOTH of the last two quarters
    """
    employees_matching_base_criteria = base_query(db_session).all()

    wages_one_quarter_ago_subquery = non_zero_wages_between_quarters(db_session, 1, 1)
    wages_two_quarters_ago_subquery = non_zero_wages_between_quarters(db_session, 2, 2)

    employee_query = db_session.query(Employee.employee_id)

    def get_ids(results):
        return {r.employee_id for r in results}

    one_quarter_ago_group = get_ids(
        employee_query.join(
            wages_one_quarter_ago_subquery,
            wages_one_quarter_ago_subquery.c.employee_id == Employee.employee_id,
        )
        .filter(Employee.employee_id.in_(employees_matching_base_criteria))
        .all()
    )

    two_quarters_ago_group = get_ids(
        employee_query.join(
            wages_two_quarters_ago_subquery,
            wages_two_quarters_ago_subquery.c.employee_id == Employee.employee_id,
        )
        .filter(Employee.employee_id.in_(employees_matching_base_criteria))
        .all()
    )

    # Symmetrical difference - elements in one of two groups but not in both
    scenario_one_group = one_quarter_ago_group ^ two_quarters_ago_group
    # Intersection - elements found in both groups
    scenario_two_group = one_quarter_ago_group & two_quarters_ago_group

    return (scenario_one_group, scenario_two_group)


def base_query(db_session: db.Session) -> Query:
    """
    Employees with no reported wages from any employer 3 quarters and 4 quarters ago,
    who did report wages from multiple employers in either the last or 2nd to last completed quarter.
    """
    wages_3_and_4_quarters_ago_subquery = non_zero_wages_between_quarters(db_session, 4, 3)

    wages_previous_2_quarters_subquery = non_zero_wages_between_quarters(db_session, 2, 1)

    multiple_employers_subquery = multiple_employers(db_session)

    employee_query = db_session.query(Employee.employee_id)

    return (
        employee_query.join(
            wages_previous_2_quarters_subquery,
            wages_previous_2_quarters_subquery.c.employee_id == Employee.employee_id,
        )
        .join(
            multiple_employers_subquery,
            multiple_employers_subquery.c.employee_id == Employee.employee_id,
        )
        .filter(Employee.employee_id.notin_(db_session.query(wages_3_and_4_quarters_ago_subquery)))
    )


def non_zero_wages_between_quarters(
    db_session: db.Session, quarters_ago_start: int, quarters_ago_end: int
) -> Alias:
    start_date = Quarter.from_date(date.today()).subtract_quarters(quarters_ago_start).start_date()
    end_date = Quarter.from_date(date.today()).subtract_quarters(quarters_ago_end).as_date()

    return (
        db_session.query(WagesAndContributions.employee_id)
        .filter(WagesAndContributions.filing_period.between(start_date, end_date))
        .filter(WagesAndContributions.employee_qtr_wages > 0)
        .distinct()
        .subquery()
    )


def multiple_employers(db_session: db.Session) -> Alias:
    two_quarters_ago_start = Quarter.from_date(date.today()).subtract_quarters(2).start_date()
    previous_quarter_end = Quarter.from_date(date.today()).previous_quarter().as_date()

    # Get the number of employers for each employee and add a label
    num_employers_query = (
        db_session.query(
            WagesAndContributions.employee_id,
            func.count(distinct(WagesAndContributions.employer_id)).label("employer_count"),
        )
        .filter(WagesAndContributions.filing_period >= two_quarters_ago_start)
        .filter(WagesAndContributions.filing_period <= previous_quarter_end)
        .filter(WagesAndContributions.employee_qtr_wages > 0)
        .group_by(WagesAndContributions.employee_id)
        .subquery()
    )

    # Filter by the label we added above
    return (
        db_session.query(num_employers_query)
        .filter(num_employers_query.c.employer_count > 1)
        .subquery()
    )


def total_employee_count(db_session: db.Session) -> int:
    return db_session.query(func.count(Employee.employee_id)).scalar()


def total_applicant_count(db_session) -> int:
    return db_session.query(func.count(Claim.employee_id)).distinct().scalar()


def group_applicant_count(db_session: db.Session, group: Set[UUID]) -> int:
    return (
        db_session.query(func.count(Claim.employee_id))
        .filter(Claim.employee_id.in_(group))
        .distinct()
        .scalar()
    )


def write_report_to_s3(
    output_file: IO[str], report_rows: List[SequentialEmploymentReportRow]
) -> None:
    writer = pydantic_csv_util.DataWriter(output_file, row_type=SequentialEmploymentReportRow)
    writer.writeheader()
    writer.writerows(report_rows)


def s3_location():
    report_config = ReportsS3Config()
    now = datetime.now()
    s3_path = os.path.join(
        report_config.sequential_employment_s3_path,
        report_config.environment + "/" + now.strftime("%Y%m%d%H%M%S"),
    )
    return os.path.join(report_config.s3_bucket, s3_path)

#!/usr/bin/env python3
#
# Generate fake Fineos daily extract file.
#
# Run via `make fineos-daily-generate`.
#

import argparse
import csv
import os
import random
import uuid
from datetime import date, datetime

import faker

import massgov.pfml.db
import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employee

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.fineos.mock.generate")

OUTPUT_CSV_FIELDS = (
    "EMPLOYEEIDENTIFIER",
    "EMPLOYEETITLE",
    "EMPLOYEEDATEOFBIRTH",
    "EMPLOYEEGENDER",
    "EMPLOYEEMARITALSTATUS",
    "TELEPHONEINTCODE",
    "TELEPHONEAREACODE",
    "TELEPHONENUMBER",
    "CELLINTCODE",
    "CELLAREACODE",
    "CELLNUMBER",
    "EMPLOYEEEMAIL",
    "EMPLOYEEID",
    "EMPLOYEECLASSIFICATION",
    "EMPLOYEEJOBTITLE",
    "EMPLOYEEDATEOFHIRE",
    "EMPLOYEEENDDATE",
    "EMPLOYMENTSTATUS",
    "EMPLOYEEORGUNITNAME",
    "EMPLOYEEHOURSWORKEDPERWEEK",
    "EMPLOYEEDAYSWORKEDPERWEEK",
    "MANAGERIDENTIFIER",
    "QUALIFIERDESCRIPTION",
    "EMPLOYEEWORKSITEID",
    "C",
    "I",
    "LASTUPDATEDATE",
    "REFERENCENO",
    "EMPLOYEEFIRSTNAME",
    "EMPLOYEELASTNAME",
    "EMPLOYEENATIONALID",
    "CUSTOMERNO",
    "UNVERIFIED",
    "STAFF",
    "GROUPCLIENT",
    "SECUREDCLIENT",
    "EMPLOYEEADJUSTEDDATEOFHIRE",
    "EMPLOYMENTSTRENGTH",
    "EMPLOYMENTCATEGORY",
    "EMPLOYMENTTYPE",
    "EMPLOYEECBACODE",
    "KEYEMPLOYEE",
    "EMPLOYEEWORKATHOME",
    "EMPLOYEEHOURSWORKEDPERYEAR",
    "EMPLOYEE50EMPLOYEESWITHIN75MILES",
    "EMPLOYMENTWORKSTATE",
    "ORG_CUSTOMERNO",
    "ORG_NAME",
)

fake = faker.Faker()

parser = argparse.ArgumentParser(description="Generate fake DOR data")
parser.add_argument(
    "--count", type=int, default=100, help="Number of employers to generate data for"
)
parser.add_argument(
    "--folder", type=str, default="generated_files", help="Output folder for generated files"
)


def main():
    """Fineos Daily Mock File Generator"""
    massgov.pfml.util.logging.init(__name__)

    db_session_raw = massgov.pfml.db.init()

    args = parser.parse_args()
    employer_count = args.count

    output_folder = args.folder
    if not output_folder.startswith("s3:"):
        os.makedirs(output_folder, exist_ok=True)

    employee_file_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-EmployeeDataLoad_feed.csv")
    employee_path = "{}/{}".format(output_folder, employee_file_name)
    employee_file = massgov.pfml.util.files.open_stream(employee_path, "w")

    with massgov.pfml.db.session_scope(db_session_raw, close=True) as db_session:
        generate_employee_file(employer_count, employee_file, db_session)

    employee_file.close()

    logger.info(
        "DONE: output file %s", employee_path,
    )


def generate_employee_file(employee_count, employees_file, db_session):
    """Generate employees rows, print rows to file"""
    csv_output = csv.DictWriter(
        employees_file,
        fieldnames=OUTPUT_CSV_FIELDS,
        lineterminator="\n",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    )

    csv_output.writeheader()

    employees = (
        db_session.query(Employee)
        .order_by(Employee.last_name, Employee.first_name)
        .limit(employee_count)
    )

    employee_generate_id = 1
    for employee_row in employees:
        employee = generate_single_employee(employee_generate_id, employee_row)
        csv_output.writerow(employee)
        employee_generate_id += 1


def generate_single_employee(employee_generate_id: int, employee_row: Employee):
    """
      Generate a single employee.

      This is intended to always generate the same fake values for a given employee_generate_id.
    """
    fake.seed_instance(employee_generate_id)
    random.seed(employee_generate_id)

    first_name = employee_row.first_name
    last_name = employee_row.last_name

    # Simulate updated first and/or last name.
    if (employee_generate_id % 10) == 1:
        first_name = fake.first_name()
    elif (employee_generate_id % 10) == 2:
        last_name = fake.last_name()
    elif (employee_generate_id % 10) == 3:
        first_name = fake.first_name()
        last_name = fake.last_name()

    if (employee_generate_id % 3) == 1:
        date_of_birth = fake.date_between(date(1930, 1, 1), date(2010, 1, 1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        date_of_birth = ""

    if (employee_generate_id % 5) == 1:
        employee_title = fake.random_element(("Ms", "Mr"))
    else:
        employee_title = "Unknown"

    if (employee_generate_id % 7) <= 2:
        employee_gender = fake.random_element(("Male", "Female"))
    else:
        employee_gender = "Unknown"

    return dict(
        EMPLOYEEIDENTIFIER=employee_row.employee_id,
        EMPLOYEETITLE=employee_title,
        EMPLOYEEDATEOFBIRTH=date_of_birth,
        EMPLOYEEGENDER=employee_gender,
        EMPLOYEEMARITALSTATUS="Unknown",
        TELEPHONEINTCODE="1",
        TELEPHONEAREACODE="212",
        TELEPHONENUMBER="4900487",
        CELLINTCODE="1",
        CELLAREACODE="212",
        CELLNUMBER="4900487",
        EMPLOYEEEMAIL="{}{}@example.com".format(first_name, last_name),
        EMPLOYEEID="847847847",
        EMPLOYEECLASSIFICATION="Unknown",
        EMPLOYEEJOBTITLE="DEFAULT",
        EMPLOYEEDATEOFHIRE=fake.date_object().strftime("%Y-%m-%d %H:%M:%S"),
        EMPLOYEEENDDATE=fake.date_object().strftime("%Y-%m-%d %H:%M:%S"),
        EMPLOYMENTSTATUS="Active",
        EMPLOYEEORGUNITNAME="Testing Department",
        EMPLOYEEHOURSWORKEDPERWEEK="37.5",
        EMPLOYEEDAYSWORKEDPERWEEK="0",
        MANAGERIDENTIFIER="",
        QUALIFIERDESCRIPTION="",
        EMPLOYEEWORKSITEID="",
        C=11536,
        I=12000 + employee_generate_id,
        LASTUPDATEDATE=fake.date_time_between(start_date="-24h").strftime("%Y-%m-%d %H:%M:%S"),
        REFERENCENO=str(uuid.uuid4()),
        EMPLOYEEFIRSTNAME=first_name,
        EMPLOYEELASTNAME=last_name,
        EMPLOYEENATIONALID="758108516",
        CUSTOMERNO=11536,
        UNVERIFIED="0",
        STAFF="0",
        GROUPCLIENT="0",
        SECUREDCLIENT="0",
        EMPLOYEEADJUSTEDDATEOFHIRE="",
        EMPLOYMENTSTRENGTH="Unknown",
        EMPLOYMENTCATEGORY="Unknown",
        EMPLOYMENTTYPE="Unknown",
        EMPLOYEECBACODE="",
        KEYEMPLOYEE="0",
        EMPLOYEEWORKATHOME="0",
        EMPLOYEEHOURSWORKEDPERYEAR="0",
        EMPLOYEE50EMPLOYEESWITHIN75MILES="0",
        EMPLOYMENTWORKSTATE="MA",
        ORG_CUSTOMERNO=144000055,
        ORG_NAME="Sampson Inc",
    )


if __name__ == "__main__":
    main()

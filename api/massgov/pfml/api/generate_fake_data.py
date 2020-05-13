import random
import uuid
from datetime import timedelta

from faker import Faker

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)
fake = Faker()

# since there is no DB connection, using dictionaries to hold fake employee and wage data
wages = {}
employees = {}
employers = {}
applications = {}

# Period ID possibilities
q1 = "2019-03-31"
q2 = "2019-06-30"
q3 = "2019-09-30"
q4 = "2019-12-31"


# this method will create a fake user when valid data is sent to POST /users
def create_user(email, auth_id):
    user = {}

    user["user_id"] = str(uuid.uuid4())
    user["auth_id"] = auth_id
    user["email_address"] = email
    user["status"] = "unverified"

    return user


def create_employee():
    employee = {}

    employee["employee_id"] = str(uuid.uuid4())
    employee["first_name"] = fake.first_name()
    employee["middle_name"] = fake.first_name()
    employee["last_name"] = fake.last_name()
    employee["date_of_birth"] = fake.date_of_birth(tzinfo=None, minimum_age=14, maximum_age=115)
    employee["ssn_or_itin"] = fake.ssn()

    return employee


def create_employer():
    employer = {}

    employer["employer_id"] = str(uuid.uuid4())
    employer["employer_fein"] = fake.ein()
    employer["employer_dba"] = fake.company()

    return employer


def create_wages(employee_id, employer_id, period_id=None):
    wages_object = {}
    period_id_list = [q1, q2, q3, q4]

    wages_object["employee_id"] = employee_id
    wages_object["period_id"] = period_id or random.choice(period_id_list)
    wages_object["employer_id"] = employer_id
    wages_object["independent_contractor"] = random.choice([True, False])
    wages_object["opt_in"] = random.choice([True, False])
    wages_object["employer_ytd_wages"] = fake.random_int(min=0, max=150000, step=1)
    wages_object["employer_qtr_wages"] = fake.random_int(min=0, max=35000, step=1)
    wages_object["employer_med_contribution"] = fake.random_int(min=0, max=10000, step=1)
    wages_object["employee_med_contribution"] = fake.random_int(min=0, max=4000, step=1)
    wages_object["employer_fam_contribution"] = fake.random_int(min=0, max=10000, step=1)
    wages_object["employee_fam_contribution"] = fake.random_int(min=0, max=4000, step=1)

    return wages_object


def create_application(employee):
    application = {}
    leave_types = ["bonding", "medical", "accident"]
    occupations = ["Sales Clerk", "Administrative", "Engineer", "Doctor"]

    employee_id = employee.get("employee_id")
    wage_employers = wages.get(employee_id)
    employer_id = wage_employers[0]["employer_id"]

    leave_type = random.choice(leave_types)

    application["application_nickname"] = "My " + leave_type + " leave application"
    application["application_id"] = str(uuid.uuid4())
    application["employee_id"] = employee["employee_id"]
    application["employer_id"] = employer_id
    application["first_name"] = fake.first_name()
    application["last_name"] = fake.last_name()
    application["occupation"] = random.choice(occupations)

    application["leave_details"] = create_leave_details(leave_type)
    application["payment_preferences"] = create_payment_preferences(
        application.get("first_name"), application.get("last_name")
    )

    return application


def create_leave_details(leave_type):
    leave_details = {}
    leave_periods = []
    leave_period = {}
    status = ["Known", "Estimated"]
    employer_notification = ["In Writing", "In Person", "By Telephone", "Other"]

    start_date = fake.date_this_month()
    end_date = start_date + timedelta(fake.random_int(min=1, max=12, step=1))

    leave_period["start_date"] = start_date
    leave_period["end_date"] = end_date

    if leave_type.find("bonding") > 0:
        leave_details["reason"] = "Child Bonding"
        leave_details["reason_qualifier"] = "Newborn"
        leave_period["status"] = random.choice(status)
        continuous_leave_period = create_continuous_leave_period(leave_period)
        leave_periods.append(continuous_leave_period)
        leave_details["continuous_leave_periods"] = leave_periods
        leave_details["relationship_to_caregiver"] = "Parent"
        leave_details["relationship_qualifier"] = "Biological"
    elif leave_type.find("medical") > 0:
        leave_details["reason"] = "Care For A Family Member"
        leave_details["reason_qualifier"] = "Serious Health Condition"
        leave_period["status"] = random.choice(status)
        reduced_leave_period = create_reduced_leave_period(leave_period)
        leave_periods.append(reduced_leave_period)
        leave_details["reduced_schedule_leave_periods"] = leave_periods
    else:
        leave_details["reason"] = "Serious Health Condition - Employee"
        leave_details["reason_qualifier"] = "Work Related Accident/Injury"
        intermittent_leave_period = create_intermittent_leave_period(leave_period)
        leave_periods.append(intermittent_leave_period)
        leave_details["intermittent_leave_periods"] = leave_periods

    leave_details["employer_notified"] = True
    leave_details["employer_notification_date"] = start_date - timedelta(
        fake.random_int(min=1, max=120, step=1)
    )
    leave_details["employer_notification_method"] = random.choice(employer_notification)

    return leave_details


def create_payment_preferences(first_name, last_name):
    payment_preferences = []
    payment_preference = {}
    payment_types = ["Elec Funds Transfer", "Check"]
    account_type = ["Checking", "Savings"]
    routing_numbers = ["021202337", "021200025"]

    payment_type = random.choice(payment_types)
    payment_preference["payment_method"] = payment_type
    payment_preference["is_default"] = True

    if payment_type == "Elec Funds Transfer":
        account_details = {
            "account_name": fake.sentence(),
            "account_no": str(fake.random_number(digits=12)),
            "routing_number": random.choice(routing_numbers),
            "account_type": random.choice(account_type),
        }
        payment_preference["account_details"] = account_details
    else:
        full_name = first_name + " " + last_name
        check_details = {"name_to_print_on_check": full_name}
        payment_preference["cheque_details"] = check_details

    payment_preferences.append(payment_preference)

    return payment_preferences


def create_continuous_leave_period(leave_period):
    # No attempt to determine if previous or next dates are business days.
    leave_period["last_day_worked"] = leave_period["start_date"] - timedelta(1)
    leave_period["expected_return_to_work_date"] = leave_period["end_date"] + timedelta(1)
    leave_period["start_date_full_day"] = True
    leave_period["start_date_off_hours"] = 0
    leave_period["start_date_off_minutes"] = 0
    leave_period["end_date_off_hours"] = 0
    leave_period["end_date_off_minutes"] = 0
    leave_period["end_date_full_day"] = True

    return leave_period


def create_reduced_leave_period(leave_period):
    off_hours = fake.random_int(min=1, max=7, step=1)
    off_minutes = fake.random_int(min=5, max=55, step=5)

    leave_period["thursday_off_hours"] = off_hours
    leave_period["thursday_off_minutes"] = off_minutes
    leave_period["friday_off_hours"] = off_hours
    leave_period["friday_off_minutes"] = off_minutes
    leave_period["saturday_off_hours"] = off_hours
    leave_period["saturday_off_minutes"] = off_minutes
    leave_period["sunday_off_hours"] = off_hours
    leave_period["sunday_off_minutes"] = off_minutes
    leave_period["monday_off_hours"] = off_hours
    leave_period["monday_off_minutes"] = off_minutes
    leave_period["tuesday_off_hours"] = off_hours
    leave_period["tuesday_off_minutes"] = off_minutes
    leave_period["wednesday_off_hours"] = off_hours
    leave_period["wednesday_off_minutes"] = off_minutes

    return leave_period


def create_intermittent_leave_period(leave_period):
    interval_basis = ["Days", "Weeks", "Months"]
    duration_choices = ["Minutes", "Hours", "Days"]

    # Random combinations may not yield logical results. There is
    # an opportunity to fine tune.

    # Occurs <frequency> times
    leave_period["frequency"] = fake.random_int(min=1, max=10, step=1)
    # Every <frequency_interval> <frequency_interval_basis
    leave_period["frequency_interval"] = fake.random_int(min=1, max=5, step=1)
    leave_period["frequency_interval_basis"] = random.choice(interval_basis)

    # For <duration> <duration_basis>
    # e.g. Occurs 4 times every 2 weeks for 3 days
    duration_basis = random.choice(duration_choices)

    if duration_basis == "Minutes":
        leave_period["duration"] = fake.random_int(min=1, max=60, step=1)
    elif duration_basis == "Hours":
        leave_period["duration"] = fake.random_int(min=1, max=24, step=1)
    else:
        leave_period["duration"] = fake.random_int(min=1, max=30, step=1)

    leave_period["duration_basis"] = duration_basis

    return leave_period


def build_fake_data_dictionaries():
    employer_id_list = []
    # create fake employers
    for _x in range(1, 50):
        employer = create_employer()
        employer_id = employer["employer_id"]
        employers[employer_id] = employer
        employer_id_list.append(employer_id)

    # create wage records where employee only has wages for one quarter and one employer
    for _x in range(1, 25):
        employee = create_employee()
        employee_id = employee["employee_id"]
        ssn_or_itin = employee["ssn_or_itin"]

        # put newly built employee into employees dictionary
        employees[ssn_or_itin] = employee

        fake_wages = create_wages(employee_id, random.choice(employer_id_list))
        # put newly built wages array into wages dictionary, where employee id is the key
        wages[employee_id] = [fake_wages]

    # create wage records where employee has wages from multiple employers for multiple quarters
    for _x in range(1, 25):
        employee = create_employee()
        employee_id = employee["employee_id"]
        ssn_or_itin = employee["ssn_or_itin"]

        # put newly built employee into employees dictionary
        employees[ssn_or_itin] = employee

        fake_wages = create_wages(employee_id, random.choice(employer_id_list), q1)
        employer_id = fake_wages["employer_id"]

        # put newly built wages into an array and then put that array into wages dictionary where employee id is the key
        fake_wages2 = create_wages(employee_id, employer_id, q2)
        fake_wages3 = create_wages(employee_id, random.choice(employer_id_list), q3)
        fake_wages4 = create_wages(employee_id, employer_id, q3)

        wages[employee_id] = [fake_wages, fake_wages2, fake_wages3, fake_wages4]

    # create wage records where employee has wages for each quarter, all from same employer
    for _x in range(1, 25):
        employee = create_employee()
        employee_id = employee["employee_id"]
        ssn_or_itin = employee["ssn_or_itin"]

        # put newly built employee into employees dictionary
        employees[ssn_or_itin] = employee

        fake_wages = create_wages(employee_id, random.choice(employer_id_list))
        employer_id = fake_wages["employer_id"]
        fake_wages["period_id"] = q1

        # put newly built wages into an array and then that array into wages dictionary
        fake_wages2 = create_wages(employee_id, employer_id, q2)
        fake_wages3 = create_wages(employee_id, employer_id, q3)
        fake_wages4 = create_wages(employee_id, employer_id, q4)

        wages[employee_id] = [fake_wages, fake_wages2, fake_wages3, fake_wages4]

    for app_employee in employees.values():
        # Create one application per employee
        application = create_application(app_employee)
        applications[application["application_id"]] = application

    logger.info(
        "generated employers %i, employees %i, wages %i", len(employers), len(employees), len(wages)
    )

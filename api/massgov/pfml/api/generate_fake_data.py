import random
import uuid

from faker import Faker

fake = Faker()

# since there is no DB connection, using dictionaries to hold fake employee and wage data
wages = {}
employees = {}
employers = {}

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
    user["email"] = email
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

    return

# Factories for generating mock data and inserting it into the database.
# This should be used for seeding tables in development and testing.
#
import random
from datetime import datetime, timedelta
from decimal import Decimal

import factory  # this is from the factory_boy package
from sqlalchemy.orm import scoped_session

import massgov.pfml.db as db
import massgov.pfml.db.models.applications as application_models
import massgov.pfml.db.models.employees as employee_models

db_session = None


def get_db_session():
    global db_session

    if db_session is None:
        db_session = db.init()

    return db_session


Session = scoped_session(lambda: get_db_session(), scopefunc=lambda: get_db_session())


class Generators:
    AccountKey = factory.Sequence(lambda n: "%011d" % n)
    Tin = factory.LazyFunction(lambda: factory.Faker("ssn").generate().replace("-", ""))
    Fein = Tin
    Money = factory.LazyFunction(lambda: Decimal(round(random.uniform(0, 50000), 2)))
    Now = factory.LazyFunction(lambda: datetime.now())
    UuidObj = factory.Faker("uuid4", cast_to=None)


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    class Meta:
        model = employee_models.User

    user_id = Generators.UuidObj
    active_directory_id = factory.Faker("uuid4")
    email_address = factory.Faker("email")


class EmployerFactory(BaseFactory):
    class Meta:
        model = employee_models.Employer

    employer_id = Generators.UuidObj
    employer_fein = Generators.Fein
    employer_dba = factory.Faker("company")


class EmployeeFactory(BaseFactory):
    class Meta:
        model = employee_models.Employee

    employee_id = Generators.UuidObj
    tax_identifier = Generators.Tin
    first_name = factory.Faker("first_name")
    middle_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    other_name = None
    email_address = factory.Faker("email")
    phone_number = "942-529-0727"


class WagesAndContributionsFactory(BaseFactory):
    class Meta:
        model = employee_models.WagesAndContributions

    wage_and_contribution_id = Generators.UuidObj
    account_key = Generators.AccountKey
    filing_period = factory.Faker("date_object")
    is_independent_contractor = False
    is_opted_in = False
    employee_ytd_wages = Generators.Money
    employee_qtr_wages = Generators.Money
    employee_med_contribution = Generators.Money
    employer_med_contribution = Generators.Money
    employee_fam_contribution = Generators.Money
    employer_fam_contribution = Generators.Money

    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda w: w.employer.employer_id)

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda w: w.employee.employee_id)


class ApplicationFactory(BaseFactory):
    class Meta:
        model = application_models.Application

    application_id = Generators.UuidObj
    nickname = "My leave application"
    requestor = None
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    middle_initial = None
    employer_notified = False
    employer_notification_date = None
    start_time = Generators.Now
    updated_time = Generators.Now
    completed_time = None
    submitted_time = None
    fineos_absence_id = None
    fineos_notification_case_id = None

    # Relationships
    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda a: a.user.user_id)

    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda a: a.employer.employer_id)

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda a: a.employee.employee_id)

    # Lookups
    occupation_id = None
    employment_status_id = None
    relationship_to_caregiver_id = None
    relationship_qualifier_id = None
    employer_notification_method_id = None
    leave_type_id = None
    leave_reason_id = application_models.LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id
    leave_reason_qualifier_id = None

    start_time = factory.Faker("date_time")
    updated_time = factory.LazyAttribute(lambda a: a.start_time + timedelta(days=1))


class AddressFactory(BaseFactory):
    class Meta:
        model = employee_models.Address

    address_type_id = 1
    address_line_one = factory.Faker("street_address")
    city = factory.Faker("city")
    zip_code = factory.Faker("postcode")

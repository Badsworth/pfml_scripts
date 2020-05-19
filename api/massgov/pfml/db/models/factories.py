# Factories for generating mock data and inserting it into the database.
# This should be used for seeding tables in development and testing.
#
import random

import factory
from sqlalchemy.orm import scoped_session

import massgov.pfml.db as db
import massgov.pfml.db.models.employees as models

db_session = None


def get_db_session():
    global db_session

    if db_session is None:
        db_session = db.init()

    return db_session


Session = scoped_session(lambda: get_db_session(), scopefunc=lambda: get_db_session())


class Generators:
    Tin = factory.Sequence(lambda n: "000%06d" % n)
    Fein = Tin
    Money = factory.LazyFunction(lambda: round(random.uniform(0, 50000), 2))


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    class Meta:
        model = models.User

    user_id = factory.Faker("uuid4")
    active_directory_id = factory.Sequence(lambda n: n)
    email_address = factory.Faker("email")

    # Use iterator for now, to allow us to lazily load the status_type when needed.
    @factory.lazy_attribute
    def status_type(self):  # noqa: B902
        active_status = (
            UserFactory._meta.sqlalchemy_session.query(models.Status)
            .filter_by(status_description="Active")
            .one()
        )

        return active_status.status_type


class EmployerFactory(BaseFactory):
    class Meta:
        model = models.Employer

    employer_id = factory.Faker("uuid4")
    employer_fein = Generators.Fein
    employer_dba = factory.Faker("company")


class EmployeeFactory(BaseFactory):
    class Meta:
        model = models.Employee

    employee_id = factory.Faker("uuid4")
    tax_identifier = Generators.Tin
    first_name = factory.Faker("first_name")
    middle_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    other_name = None
    email_address = factory.Faker("email")
    phone_number = "942-529-0727"


class WagesAndContributionsFactory(BaseFactory):
    class Meta:
        model = models.WagesAndContributions

    wage_and_contribution_id = factory.Faker("uuid4")
    filing_period = factory.Faker("date")
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

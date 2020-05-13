# Factories for generating mock data and inserting it into the database.
# This should be used for seeding tables in development and testing.
#
import factory
from sqlalchemy.orm import scoped_session

import massgov.pfml.api.db as db
import massgov.pfml.api.db.models.employees as models

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


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = Session


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

# Factories for generating mock data and inserting it into the database.
# This should be used for seeding tables in development and testing.
#
import factory
from sqlalchemy.orm import scoped_session

import massgov.pfml.api.db as db
import massgov.pfml.api.db.models as models

Session = scoped_session(lambda: db.get_session(), scopefunc=lambda: db.get_session(),)


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
        with db.session_scope() as db_session:
            active_status = (
                db_session.query(models.Status).filter_by(status_description="Active").one()
            )

        return [active_status.status_type]


class EmployerFactory(BaseFactory):
    class Meta:
        model = models.Employer

    employer_id = factory.Faker("uuid4")
    employer_fein = Generators.Fein
    employer_dba = factory.Faker("company")

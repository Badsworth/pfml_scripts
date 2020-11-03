# Factories for generating mock data and inserting it into the database.
# This should be used for seeding tables in development and testing.
#

import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from math import floor

import factory  # this is from the factory_boy package
import pytz
from sqlalchemy.orm import scoped_session

import massgov.pfml.db as db
import massgov.pfml.db.models.applications as application_models
import massgov.pfml.db.models.employees as employee_models
import massgov.pfml.db.models.verifications as verification_models
import massgov.pfml.util.datetime as datetime_util

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
    Now = factory.LazyFunction(datetime.now)
    # A reproducible datetime that might represent a database creation, modification, or other
    # transaction datetime.
    TransactionDateTime = factory.Faker(
        "date_time_between_dates",
        datetime_start=pytz.UTC.localize(datetime(2020, 1, 1)),
        datetime_end=pytz.UTC.localize(datetime(2022, 1, 1)),
    )
    UtcNow = factory.LazyFunction(datetime_util.utcnow)
    UuidObj = factory.Faker("uuid4", cast_to=None)
    VerificationCode = factory.Faker("pystr", max_chars=6, min_chars=6)


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

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for role in extracted:
                lk_role = employee_models.Role.get_instance(db_session, template=role)
                user_role = employee_models.UserRole(role=lk_role, user=self)
                self.roles.append(user_role)
                get_db_session().commit()


class EmployerOnlyRequiredFactory(BaseFactory):
    class Meta:
        model = employee_models.Employer

    employer_id = Generators.UuidObj
    employer_fein = Generators.Fein
    employer_dba = factory.Faker("company")


class EmployerOnlyDORDataFactory(EmployerOnlyRequiredFactory):
    account_key = Generators.AccountKey
    employer_name = factory.Faker("company")
    family_exemption = factory.Faker("boolean", chance_of_getting_true=0.1)
    medical_exemption = factory.Faker("boolean", chance_of_getting_true=0.1)

    # Address info not implemented

    exemption_commence_date = factory.LazyAttribute(
        lambda e: factory.Faker(
            "date_between_dates", start_date=date(2020, 1, 1), end_date="next year"
        )
        if e.family_exemption or e.medical_exemption
        else None
    )
    exemption_cease_date = factory.LazyAttribute(
        lambda e: factory.Faker(
            "date_between_dates",
            start_date=e.exemption_commence_date,
            end_date=e.exemption_commence_date + timedelta(weeks=52),
        )
        if e.exemption_commence_date
        else None
    )


class EmployerFactory(EmployerOnlyDORDataFactory):
    fineos_customer_nbr = f"pfml_api_{str(Generators.UuidObj)}"
    fineos_employer_id = random.randint(100, 1000)


class TaxIdentifierFactory(BaseFactory):
    class Meta:
        model = employee_models.TaxIdentifier

    tax_identifier_id = Generators.UuidObj
    tax_identifier = Generators.Tin


class EmployeeFactory(BaseFactory):
    class Meta:
        model = employee_models.Employee

    employee_id = Generators.UuidObj

    tax_identifier = factory.SubFactory(TaxIdentifierFactory)
    tax_identifier_id = factory.LazyAttribute(lambda t: t.tax_identifier.tax_identifier_id)
    first_name = factory.Faker("first_name")
    middle_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    other_name = None
    email_address = factory.Faker("email")
    phone_number = "942-529-0727"


class VerificationTypeFactory(BaseFactory):
    class Meta:
        model = verification_models.VerificationType

    verification_type_id = factory.Sequence(lambda n: n)
    verification_type_description = factory.Faker("pystr")


class VerificationFactory(BaseFactory):
    class Meta:
        model = verification_models.Verification

    verified_at = Generators.UtcNow
    verification_code_id = Generators.UuidObj
    verification_id = Generators.UuidObj
    verification_type = factory.SubFactory(VerificationTypeFactory)
    verification_type_id = factory.LazyAttribute(lambda a: a.verification_type.verification_type_id)


class VerificationCodeFactory(BaseFactory):
    class Meta:
        model = verification_models.VerificationCode

    verification_code_id = Generators.UuidObj

    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda a: a.employer.employer_fein)
    employer_fein = factory.LazyAttribute(lambda a: a.employer.employer_id)
    verification_code = Generators.VerificationCode

    issued_at = Generators.UtcNow
    expires_at = factory.LazyAttribute(lambda a: a.issue_ts + timedelta(minutes=5))
    remaining_uses = 1


class VerificationCodeLogs(BaseFactory):
    class Meta:
        model = verification_models.VerificationCodeLogs

    verification_code_log_id = Generators.UuidObj
    verification_code_id = Generators.UuidObj
    result = factory.Faker("sentence")
    message = factory.Faker("paragraph")
    created_at = Generators.UtcNow


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
    middle_name = None
    date_of_birth = factory.Faker("date_of_birth", minimum_age=14, maximum_age=100)
    has_state_id = False
    mass_id = None
    has_mailing_address = False
    pregnant_or_recent_birth = False
    child_birth_date = None
    child_placement_date = None
    employer_notified = False
    employer_notification_date = None
    completed_time = None
    submitted_time = None
    fineos_absence_id = None
    fineos_notification_case_id = None

    # Leave Periods
    has_continuous_leave_periods = False
    has_intermittent_leave_periods = False
    has_reduced_schedule_leave_periods = False

    # Relationships
    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda a: a.user.user_id)

    employer = factory.SubFactory(EmployerFactory)
    hours_worked_per_week = None
    employer_id = factory.LazyAttribute(lambda a: a.employer.employer_id)

    tax_identifier = factory.SubFactory(TaxIdentifierFactory)
    tax_identifier_id = factory.LazyAttribute(lambda t: t.tax_identifier.tax_identifier_id)

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda a: a.employee.employee_id)

    employer_fein = "22-7777777"

    # Lookups
    occupation_id = None
    employment_status_id = None
    relationship_to_caregiver_id = None
    relationship_qualifier_id = None
    employer_notification_method_id = None
    leave_type_id = None
    leave_reason_id = (
        application_models.LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
    )
    leave_reason_qualifier_id = None

    start_time = Generators.TransactionDateTime
    updated_time = factory.LazyAttribute(lambda a: a.start_time + timedelta(days=1))


class AddressFactory(BaseFactory):
    class Meta:
        model = employee_models.Address

    address_type_id = 1
    address_line_one = factory.Faker("street_address")
    city = factory.Faker("city")
    zip_code = factory.Faker("postcode")
    geo_state_id = employee_models.GeoState.MA.geo_state_id


class PaymentPreferenceFactory(BaseFactory):
    class Meta:
        model = application_models.ApplicationPaymentPreference

    payment_pref_id = Generators.UuidObj
    description = "My checking account"
    payment_type_id = employee_models.PaymentType.ACH.payment_type_id
    is_default = True
    account_name = ""
    account_number = "123456789"
    routing_number = "234567890"
    type_of_account = "Checking"
    name_in_check = None


class ContinuousLeavePeriodFactory(BaseFactory):
    class Meta:
        model = application_models.ContinuousLeavePeriod

    leave_period_id = Generators.UuidObj
    start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 1), date_end=date(2021, 1, 15)
    )
    end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 16), date_end=date(2021, 1, 28)
    )
    is_estimated = True
    last_day_worked = factory.Faker("date_object")
    expected_return_to_work_date = factory.Faker("date_object")
    start_date_full_day = None
    start_date_off_hours = None
    start_date_off_minutes = None
    end_date_full_day = None
    end_date_off_hours = None
    end_date_off_minutes = None


class IntermittentLeavePeriodFactory(BaseFactory):
    class Meta:
        model = application_models.IntermittentLeavePeriod

    leave_period_id = Generators.UuidObj
    start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 2, 1), date_end=date(2021, 2, 15)
    )
    end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 2, 16), date_end=date(2021, 2, 28)
    )
    frequency = None
    frequency_interval = None
    frequency_interval_basis = None
    duration = None
    duration_basis = None


class ReducedScheduleLeavePeriodFactory(BaseFactory):
    class Meta:
        model = application_models.ReducedScheduleLeavePeriod

    leave_period_id = Generators.UuidObj
    start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 1), date_end=date(2021, 3, 15)
    )
    end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 16), date_end=date(2021, 3, 28)
    )
    is_estimated = True
    thursday_off_hours = None
    thursday_off_minutes = None
    friday_off_hours = None
    friday_off_minutes = None
    saturday_off_hours = None
    saturday_off_minutes = None
    sunday_off_hours = None
    sunday_off_minutes = None
    monday_off_hours = None
    monday_off_minutes = None
    tuesday_off_hours = None
    tuesday_off_minutes = None
    wednesday_off_hours = None
    wednesday_off_minutes = None


class StateMetricFactory(BaseFactory):
    class Meta:
        model = application_models.StateMetric

    state_metric_id = Generators.UuidObj
    effective_date = datetime(2019, 10, 1)
    unemployment_minimum_earnings = Decimal(5000)
    average_weekly_wage = Decimal(1331.66)


class WorkPatternFixedFactory(BaseFactory):
    """A single week work pattern for someone working a fixed (consistent) schedule"""

    class Meta:
        model = application_models.WorkPattern

    work_pattern_id = Generators.UuidObj

    work_pattern_type_id = application_models.WorkPatternType.FIXED.work_pattern_type_id
    work_week_starts_id = application_models.DayOfWeek.SUNDAY.day_of_week_id
    work_pattern_days = factory.LazyAttribute(
        lambda w: [
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.SUNDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.MONDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.TUESDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.WEDNESDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.THURSDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.FRIDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.SATURDAY.day_of_week_id,
                week_number=1,
                minutes=8 * 60,
            ),
        ]
    )


class WorkPatternVariableFactory(WorkPatternFixedFactory):
    work_pattern_type_id = application_models.WorkPatternType.VARIABLE.work_pattern_type_id


class WorkPatternRotatingFactory(WorkPatternFixedFactory):
    work_pattern_type_id = application_models.WorkPatternType.ROTATING.work_pattern_type_id
    pattern_start_date = "2021-01-03"
    work_pattern_days = factory.LazyAttribute(
        lambda w: [
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=i % 7 + 1,
                week_number=floor(i / 7) + 1,
                minutes=8 * 60,
            )
            for i in range(28)
        ]
    )

# Factories for generating mock data and inserting it into the database.
# This should be used for seeding tables in development and testing.
#

import os
import random
import string
import unittest.mock
from datetime import date, datetime, timedelta
from decimal import Decimal

import factory  # this is from the factory_boy package
import faker
import pytz
from sqlalchemy.orm import scoped_session

import massgov.pfml.db as db
import massgov.pfml.db.models.applications as application_models
import massgov.pfml.db.models.employees as employee_models
import massgov.pfml.db.models.geo as geo_models
import massgov.pfml.db.models.payments as payment_models
import massgov.pfml.db.models.verifications as verification_models
import massgov.pfml.fineos.mock.field
import massgov.pfml.util.datetime as datetime_util
from massgov.pfml.api.authentication.azure import AzureUser

db_session = None

fake = faker.Faker()


def get_db_session():
    global db_session

    if os.getenv("DB_FACTORIES_DISABLE_DB_ACCESS", "0") == "1":
        alert_db_session = unittest.mock.MagicMock()
        alert_db_session.add.side_effect = Exception(
            """DB_FACTORIES_DISABLE_DB_ACCESS is set, refusing database action.

            If your tests don't need to cover database behavior, consider
            calling the `build()` method instead of `create()` on the factory to
            not persist the generated model.

            If running tests that actually need data in the DB, pull in the
            `initialize_factories_session` fixture.

            If running factories outside of the tests and you see this, unset
            the DB_FACTORIES_DISABLE_DB_ACCESS env var.
            """
        )

        return alert_db_session

    if db_session is None:
        db_session = db.init()

    return db_session


Session = scoped_session(lambda: get_db_session(), scopefunc=lambda: get_db_session())


class Generators:
    AccountKey = factory.Sequence(lambda n: "%011d" % n)
    EmailAddress = factory.Sequence(lambda n: f"example-{n}@example.com")
    Tin = factory.LazyFunction(lambda: fake.ssn().replace("-", ""))
    Fein = Tin
    Money = factory.LazyFunction(lambda: Decimal(round(random.uniform(0, 50000), 2)))
    Now = factory.LazyFunction(datetime.now)
    ThisYear = factory.LazyFunction(datetime.now().year)
    # A reproducible datetime that might represent a database creation, modification, or other
    # transaction datetime.
    TransactionDateTime = factory.Faker(
        "date_time_between_dates",
        datetime_start=pytz.UTC.localize(datetime(2020, 1, 1)),
        datetime_end=pytz.UTC.localize(datetime(2022, 1, 1)),
    )
    UtcNow = factory.LazyFunction(datetime_util.utcnow)
    UuidObj = factory.Faker("uuid4", cast_to=None)
    S3Path = factory.LazyFunction(
        lambda: os.path.join(
            "s3://bucket/path/to/",
            "".join(random.choices(string.ascii_letters + string.digits, k=8)) + ".txt",
        )
    )
    CtrDocumentIdentifier = factory.LazyFunction(
        lambda: "INTFDFML" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    )
    FineosAbsenceId = factory.Sequence(lambda n: "NTN-{:02d}-ABS-01".format(n))
    VccDocCounter = factory.Sequence(lambda n: n)
    VccDocId = factory.Sequence(
        lambda n: "INTFDFML{}{}".format(datetime.now().strftime("%d%m%Y"), f"{n:04}")
    )
    VccBatchCounter = factory.Sequence(lambda n: n)
    VccBatchId = factory.Sequence(lambda n: "EOL{}VCC{}".format(datetime.now().strftime("%m%d"), n))


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


class AzureUserFactory(factory.Factory):
    class Meta:
        model = AzureUser

    sub_id = factory.Faker("uuid4")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email_address = Generators.EmailAddress
    groups = fake.pylist(3, True, "uuid4")
    permissions = fake.pylist(10, True, "int")


class UserFactory(BaseFactory):
    class Meta:
        model = employee_models.User

    user_id = Generators.UuidObj
    sub_id = factory.Faker("uuid4")
    email_address = Generators.EmailAddress

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for role in extracted:
                lk_role = employee_models.Role.get_instance(db_session, template=role)
                self.roles.append(lk_role)
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
    fineos_employer_id = factory.LazyAttribute(
        lambda e: massgov.pfml.fineos.mock.field.fake_customer_no(e.employer_fein)
    )


class TaxIdentifierFactory(BaseFactory):
    class Meta:
        model = employee_models.TaxIdentifier

    tax_identifier_id = Generators.UuidObj
    tax_identifier = Generators.Tin


class EftFactory(BaseFactory):
    class Meta:
        model = employee_models.EFT

    eft_id = Generators.UuidObj
    account_nbr = "123456789"
    routing_nbr = "234567890"
    bank_account_type_id = employee_models.BankAccountType.CHECKING.bank_account_type_id


class PubEftFactory(BaseFactory):
    class Meta:
        model = employee_models.PubEft

    pub_eft_id = Generators.UuidObj
    routing_nbr = factory.Sequence(lambda n: "%09d" % n)
    account_nbr = factory.Sequence(lambda n: "%011d" % n)
    bank_account_type_id = employee_models.BankAccountType.CHECKING.bank_account_type_id
    prenote_state_id = employee_models.PrenoteState.PENDING_PRE_PUB.prenote_state_id
    prenote_response_at = Generators.UtcNow


class EmployeeOnlyDORDataFactory(BaseFactory):
    class Meta:
        model = employee_models.Employee

    employee_id = Generators.UuidObj

    tax_identifier = factory.SubFactory(TaxIdentifierFactory)
    tax_identifier_id = factory.LazyAttribute(lambda t: t.tax_identifier.tax_identifier_id)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class EmployeeFactory(EmployeeOnlyDORDataFactory):
    middle_name = factory.Faker("first_name")
    other_name = None
    email_address = factory.Faker("email")
    phone_number = "+19425290727"
    ctr_vendor_customer_code = "VC0001201168"
    gender_id = None
    fineos_employee_first_name = factory.LazyAttribute(lambda e: e.first_name)
    fineos_employee_last_name = factory.LazyAttribute(lambda e: e.last_name)


class EmployeeWithFineosNumberFactory(EmployeeFactory):
    date_of_birth = factory.Faker("date_of_birth", minimum_age=14, maximum_age=100)
    fineos_customer_number = factory.Faker("numerify", text="####")


class EmployeePubEftPairFactory(BaseFactory):
    class Meta:
        model = employee_models.EmployeePubEftPair

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)

    pub_eft = factory.SubFactory(PubEftFactory)
    pub_eft_id = factory.LazyAttribute(lambda p: p.pub_eft.pub_eft_id)


class CtrBatchIdentifierFactory(BaseFactory):
    class Meta:
        model = employee_models.CtrBatchIdentifier

    ctr_batch_identifier_id = Generators.UuidObj
    ctr_batch_identifier = Generators.VccBatchId
    year = datetime.now().year
    batch_date = datetime.now()
    batch_counter = Generators.VccBatchCounter
    inf_data = {
        "NewMmarsBatchID": "EOL0101GAX11",
        "NewMmarsBatchDeptCode": "EOL",
        "NewMmarsUnitCode": "8770",
        "NewMmarsImportDate": "2020-01-01",
        "NewMmarsTransCode": "GAX",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": "2",
        "NewMmarsTransDollarAmount": "2500.00",
    }


class CtrDocumentIdentifierFactory(BaseFactory):
    class Meta:
        model = employee_models.CtrDocumentIdentifier

    ctr_document_identifier_id = Generators.UuidObj
    ctr_document_identifier = Generators.VccDocId
    document_counter = Generators.VccDocCounter
    document_date = Generators.Now


class ReferenceFileFactory(BaseFactory):
    class Meta:
        model = employee_models.ReferenceFile

    reference_file_id = Generators.UuidObj
    file_location = Generators.S3Path
    reference_file_type_id = (
        employee_models.ReferenceFileType.PAYMENT_EXTRACT.reference_file_type_id
    )


class EmployeeReferenceFileFactory(BaseFactory):
    class Meta:
        model = employee_models.EmployeeReferenceFile

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)

    reference_file = factory.SubFactory(ReferenceFileFactory)
    reference_file_id = factory.LazyAttribute(lambda e: e.reference_file.reference_file_id)
    reference_file.reference_file_type_id = (
        employee_models.ReferenceFileType.VCC.reference_file_type_id
    )

    ctr_document_identifier = factory.SubFactory(CtrDocumentIdentifierFactory)
    ctr_document_identifier_id = factory.LazyAttribute(
        lambda e: e.ctr_document_identifier.ctr_document_identifier_id
    )


class VerificationTypeFactory(BaseFactory):
    class Meta:
        model = verification_models.LkVerificationType

    verification_type_id = factory.Sequence(lambda n: n)
    verification_type_description = factory.Faker("pystr")


class VerificationFactory(BaseFactory):
    class Meta:
        model = verification_models.Verification

    created_at = Generators.UtcNow
    updated_at = Generators.UtcNow
    verification_id = Generators.UuidObj
    verification_type = factory.SubFactory(VerificationTypeFactory, __sequence=100)
    verification_type_id = factory.LazyAttribute(lambda w: w.verification_type.verification_type_id)
    verification_metadata = factory.Faker("json")


class EmployerQuarterlyContributionFactory(BaseFactory):
    class Meta:
        model = employee_models.EmployerQuarterlyContribution

    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda w: w.employer.employer_id)
    filing_period = datetime.now().strftime("%Y-%m-%d")
    employer_total_pfml_contribution = factory.Faker("random_int", min=1)
    pfm_account_id = factory.Faker("random_int")


class EmployeePushToFineosQueueFactory(BaseFactory):
    class Meta:
        model = employee_models.EmployeePushToFineosQueue

    employee_push_to_fineos_queue_id = Generators.UuidObj
    employee_id = None
    employer_id = None
    action = "UPDATE_NEW_EMPLOYER"
    modified_at = Generators.UtcNow
    process_id = 1


class EmployerPushToFineosQueueFactoryFactory(BaseFactory):
    class Meta:
        model = employee_models.EmployerPushToFineosQueue

    employer_push_to_fineos_queue_id = Generators.UuidObj
    employer_id = None
    action = "INSERT"
    modified_at = Generators.UtcNow
    process_id = 1
    family_exemption = None
    medical_exemption = None
    exemption_commence_date = None
    exemption_cease_date = None


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


class OrganizationUnitFactory(BaseFactory):
    class Meta:
        model = employee_models.OrganizationUnit

    organization_unit_id = Generators.UuidObj

    fineos_id = factory.Faker("numerify", text="PE:#####:##########")
    name = factory.Faker("company")
    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda c: c.employer.employer_id)


class ClaimFactory(BaseFactory):
    class Meta:
        model = employee_models.Claim

    claim_id = Generators.UuidObj

    authorized_representative_id = None
    claim_type_id = None
    benefit_amount = 100
    benefit_days = 60
    fineos_absence_id = Generators.FineosAbsenceId
    fineos_notification_id = None
    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda w: w.employee.employee_id)
    organization_unit = None
    organization_unit_id = factory.LazyAttribute(
        lambda w: w.organization_unit.organization_unit_id if w.organization_unit else None
    )


class AbsencePeriodFactory(BaseFactory):
    class Meta:
        model = employee_models.AbsencePeriod

    absence_period_id = Generators.UuidObj
    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda w: w.claim.claim_id)
    fineos_leave_request_id = factory.Faker("random_int")
    absence_period_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 1), date_end=date(2021, 1, 15)
    )
    absence_period_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 16), date_end=date(2021, 1, 28)
    )
    leave_request_decision_id = (
        employee_models.LeaveRequestDecision.APPROVED.leave_request_decision_id
    )
    absence_period_type_id = 1
    absence_reason_id = 1
    absence_reason_qualifier_one_id = 1
    absence_reason_qualifier_two_id = 1
    is_id_proofed = False
    created_at = datetime.now()
    updated_at = datetime.now()
    fineos_absence_period_class_id = factory.Faker("random_int")
    fineos_absence_period_index_id = factory.Faker("random_int")


class ManagedRequirementFactory(BaseFactory):
    class Meta:
        model = employee_models.ManagedRequirement

    managed_requirement_id = Generators.UuidObj
    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda w: w.claim.claim_id)
    respondent_user = factory.SubFactory(UserFactory)
    respondent_user_id = factory.LazyAttribute(lambda w: w.respondent_user.user_id)
    fineos_managed_requirement_id = factory.Sequence(lambda n: n)
    follow_up_date = factory.LazyAttribute(lambda w: w.claim.created_at + timedelta(days=10))
    managed_requirement_status_id = (
        employee_models.ManagedRequirementStatus.OPEN.managed_requirement_status_id
    )
    managed_requirement_category_id = (
        employee_models.ManagedRequirementCategory.EMPLOYER_CONFIRMATION.managed_requirement_category_id
    )
    managed_requirement_type_id = (
        employee_models.ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id
    )


class PaymentFactory(BaseFactory):
    class Meta:
        model = employee_models.Payment

    payment_id = Generators.UuidObj

    amount = Generators.Money
    # Using dates set in Jan 2021 similar to magic dates in other factories, such as
    # IntermittentLeavePeriodFactory and ContinuousLeavePeriodFactory.
    # TODO: We should see if we can convert all dates made by factories to be
    #       more random.
    period_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 1), date_end=date(2021, 1, 15)
    )
    period_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 16), date_end=date(2021, 1, 28)
    )
    payment_date = factory.LazyAttribute(lambda a: a.period_end_date - timedelta(days=1))
    # Magic number: the C value is the same for all payments, but it doesn't actually
    # matter what number it is, so picking a static number is fine.
    fineos_pei_c_value = "9000"
    # The I value is unique for all payments and should be a string, not an int.
    fineos_pei_i_value = factory.Sequence(lambda n: "%d" % n)

    fineos_leave_request_id = factory.Faker("random_int")

    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda a: a.claim.claim_id)

    fineos_employee_first_name = factory.Faker("first_name")
    fineos_employee_last_name = factory.Faker("last_name")


class PaymentDetailsFactory(BaseFactory):
    class Meta:
        model = employee_models.PaymentDetails

    payment_details_id = Generators.UuidObj

    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda a: a.payment.payment_id)

    period_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 1), date_end=date(2021, 1, 15)
    )
    period_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 16), date_end=date(2021, 1, 28)
    )

    amount = Generators.Money


class PaymentReferenceFileFactory(BaseFactory):
    class Meta:
        model = employee_models.PaymentReferenceFile

    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda a: a.payment.payment_id)

    reference_file = factory.SubFactory(ReferenceFileFactory)
    reference_file_id = factory.LazyAttribute(lambda a: a.reference_file.reference_file_id)

    ctr_document_identifier = factory.SubFactory(CtrDocumentIdentifierFactory)
    ctr_document_identifier_id = factory.LazyAttribute(
        lambda a: a.ctr_document_identifier.ctr_document_identifier_id
    )


class PhoneFactory(BaseFactory):
    """A working Cell phone number"""

    class Meta:
        model = application_models.Phone

    phone_number = "+12404879945"
    phone_type_id = application_models.PhoneType.CELL.phone_type_id


class LeaveReasonFactory(BaseFactory):
    class Meta:
        model = application_models.LkLeaveReason

    leave_reason_id = None
    leave_reason_description = None


class ApplicationFactory(BaseFactory):
    class Meta:
        model = application_models.Application

    application_id = Generators.UuidObj

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
    hours_worked_per_week = None
    is_withholding_tax = None

    # Leave Periods
    has_continuous_leave_periods = False
    has_intermittent_leave_periods = False
    has_reduced_schedule_leave_periods = False

    # Other leaves
    has_concurrent_leave = False
    has_employer_benefits = False
    has_other_incomes = False
    has_previous_leaves_other_reason = False
    has_previous_leaves_same_reason = False

    # Relationships
    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda a: a.user.user_id)

    employer_fein = Generators.Fein

    tax_identifier = factory.SubFactory(TaxIdentifierFactory)
    tax_identifier_id = factory.LazyAttribute(lambda t: t.tax_identifier.tax_identifier_id)

    phone = factory.SubFactory(PhoneFactory)

    # Lookups
    gender_id = None
    occupation_id = None
    employment_status_id = None
    relationship_to_caregiver_id = None
    relationship_qualifier_id = None
    employer_notification_method_id = None
    leave_reason_id = (
        application_models.LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
    )
    leave_reason_qualifier_id = None
    split_from_application_id = None

    created_at = Generators.TransactionDateTime
    updated_at = factory.LazyAttribute(lambda a: a.created_at + timedelta(days=1))


class AddressFactory(BaseFactory):
    class Meta:
        model = employee_models.Address

    address_type_id = 1
    address_line_one = factory.Faker("street_address")
    city = factory.Faker("city")
    zip_code = factory.Faker("postcode")
    geo_state_id = geo_models.GeoState.MA.geo_state_id


class CtrAddressPairFactory(BaseFactory):
    class Meta:
        model = employee_models.CtrAddressPair

    fineos_address = factory.SubFactory(AddressFactory)
    fineos_address_id = factory.LazyAttribute(lambda c: c.fineos_address.address_id)


class ExperianAddressPairFactory(BaseFactory):
    class Meta:
        model = employee_models.ExperianAddressPair

    fineos_address = factory.SubFactory(AddressFactory)
    fineos_address_id = factory.LazyAttribute(lambda c: c.fineos_address.address_id)


class PaymentPreferenceFactory(BaseFactory):
    class Meta:
        model = application_models.ApplicationPaymentPreference

    payment_pref_id = Generators.UuidObj
    payment_method_id = employee_models.PaymentMethod.ACH.payment_method_id
    account_number = "123456789"
    routing_number = "011401533"
    bank_account_type_id = employee_models.BankAccountType.CHECKING.bank_account_type_id


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
    thursday_off_minutes = 90
    friday_off_minutes = 90
    saturday_off_minutes = 90
    sunday_off_minutes = 90
    monday_off_minutes = 90
    tuesday_off_minutes = 90
    wednesday_off_minutes = 90


class EmployerBenefitFactory(BaseFactory):
    class Meta:
        model = application_models.EmployerBenefit

    # application_id must be passed into the create() call
    benefit_type_id = (
        application_models.EmployerBenefitType.SHORT_TERM_DISABILITY.employer_benefit_type_id
    )
    benefit_amount_dollars = factory.Faker("random_int")
    benefit_amount_frequency_id = application_models.AmountFrequency.PER_MONTH.amount_frequency_id
    benefit_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 1), date_end=date(2021, 3, 15)
    )
    benefit_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 16), date_end=date(2021, 3, 28)
    )
    is_full_salary_continuous = True


class OtherIncomeFactory(BaseFactory):
    class Meta:
        model = application_models.OtherIncome

    # application_id must be passed into the create() call
    income_type_id = application_models.OtherIncomeType.SSDI.other_income_type_id
    income_amount_dollars = factory.Faker("random_int")
    income_amount_frequency_id = application_models.AmountFrequency.PER_MONTH.amount_frequency_id
    income_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 1), date_end=date(2021, 3, 15)
    )
    income_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 16), date_end=date(2021, 3, 28)
    )


class ConcurrentLeaveFactory(BaseFactory):
    class Meta:
        model = application_models.ConcurrentLeave

    # application_id must be passed into the create() call
    is_for_current_employer = factory.Faker("boolean")
    leave_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 1), date_end=date(2021, 3, 15)
    )
    leave_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 16), date_end=date(2021, 3, 28)
    )


class PreviousLeaveFactory(BaseFactory):
    class Meta:
        model = application_models.PreviousLeave

    # application_id must be passed into the create() call
    leave_reason_id = (
        application_models.PreviousLeaveQualifyingReason.PREGNANCY_MATERNITY.previous_leave_qualifying_reason_id
    )
    is_for_current_employer = factory.Faker("boolean")
    leave_start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 1), date_end=date(2021, 3, 15)
    )
    leave_end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 3, 16), date_end=date(2021, 3, 28)
    )

    worked_per_week_minutes = random.randint(600, 2400)
    leave_minutes = random.randint(600, 2400)


class PreviousLeaveOtherReasonFactory(PreviousLeaveFactory):
    class Meta:
        model = application_models.PreviousLeaveOtherReason


class PreviousLeaveSameReasonFactory(PreviousLeaveFactory):
    class Meta:
        model = application_models.PreviousLeaveSameReason


class BenefitsMetricsFactory(BaseFactory):
    class Meta:
        model = application_models.BenefitsMetrics

    effective_date = datetime(2019, 10, 1)
    average_weekly_wage = Decimal("1331.66")
    maximum_weekly_benefit_amount = Decimal("1000.00")


class UnemploymentMetricFactory(BaseFactory):
    class Meta:
        model = application_models.UnemploymentMetric

    effective_date = datetime(2019, 10, 1)
    unemployment_minimum_earnings = Decimal("5000")


class DocumentFactory(BaseFactory):
    class Meta:
        model = application_models.Document

    document_id = Generators.UuidObj

    # TODO: This should point to a User object but that relationship does not exist in the base model.
    #
    # user = factory.SubFactory(UserFactory)
    # user_id = factory.LazyAttribute(lambda a: a.user.user_id)
    user_id = Generators.UuidObj

    # TODO: This should point to an Application object but that relationship does not exist in the base model.
    #
    # application = factory.SubFactory(ApplicationFactory)
    # application_id = factory.LazyAttribute(lambda a: a.application.application_id)
    application_id = Generators.UuidObj

    created_at = Generators.UtcNow
    updated_at = Generators.UtcNow

    # Initialize these type_ids to some random value.
    document_type_id = random.randint(
        1, application_models.DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_id
    )

    # These values have no special meaning, just bounds so we get some variation.
    size_bytes = random.randint(1989, 24_072_020)

    is_stored_in_s3 = False
    name = ""
    description = ""


class WorkPatternFixedFactory(BaseFactory):
    """A single week work pattern for someone working a fixed (consistent) schedule"""

    class Meta:
        model = application_models.WorkPattern

    work_pattern_id = Generators.UuidObj

    work_pattern_type_id = application_models.WorkPatternType.FIXED.work_pattern_type_id
    work_pattern_days = factory.LazyAttribute(
        lambda w: [
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.SUNDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.MONDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.TUESDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.WEDNESDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.THURSDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.FRIDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id,
                day_of_week_id=application_models.DayOfWeek.SATURDAY.day_of_week_id,
                minutes=8 * 60 + 15,
            ),
        ]
    )


class WorkPatternVariableFactory(WorkPatternFixedFactory):
    work_pattern_type_id = application_models.WorkPatternType.VARIABLE.work_pattern_type_id


class WorkPatternRotatingFactory(WorkPatternFixedFactory):
    work_pattern_type_id = application_models.WorkPatternType.ROTATING.work_pattern_type_id
    work_pattern_days = factory.LazyAttribute(
        lambda w: [
            application_models.WorkPatternDay(
                work_pattern_id=w.work_pattern_id, day_of_week_id=i % 7 + 1, minutes=8 * 60
            )
            for i in range(28)
        ]
    )


class DuaReductionPaymentFactory(BaseFactory):
    class Meta:
        model = employee_models.DuaReductionPayment

    fineos_customer_number = factory.Faker("numerify", text="####")
    employer_fein = Generators.Fein
    payment_date = factory.Faker("date_object")
    request_week_begin_date = factory.Faker("date_object")
    gross_payment_amount_cents = random.randint(100, 100000)
    payment_amount_cents = random.randint(100, 100000)
    fraud_indicator = None
    benefit_year_begin_date = factory.Faker("date_object")
    benefit_year_end_date = factory.Faker("date_object")


class DiaReductionPaymentFactory(BaseFactory):
    class Meta:
        model = employee_models.DiaReductionPayment

    fineos_customer_number = factory.Faker("numerify", text="####")
    board_no = factory.Faker("uuid4")
    event_id = factory.Faker("uuid4")
    event_description = "PC"
    eve_created_date = factory.Faker("date_object")
    event_occurrence_date = factory.Faker("date_object")
    award_id = factory.Faker("uuid4")
    award_code = "34"
    award_amount = 1600.00
    award_date = factory.Faker("date_object")
    start_date = factory.Faker("date_object")
    end_date = factory.Faker("date_object")
    weekly_amount = 400.00
    award_created_date = factory.Faker("date_object")
    termination_date = factory.Faker("date_object")


class CaringLeaveMetadataFactory(BaseFactory):
    class Meta:
        model = application_models.CaringLeaveMetadata

    family_member_first_name = factory.Faker("first_name")
    family_member_middle_name = factory.Faker("first_name")
    family_member_last_name = factory.Faker("last_name")
    family_member_date_of_birth = factory.Faker("date_object")


class ImportLogFactory(BaseFactory):
    class Meta:
        model = employee_models.ImportLog


class MmarsPaymentDataFactory(BaseFactory):
    class Meta:
        model = payment_models.MmarsPaymentData

    mmars_payment_data_id = Generators.UuidObj

    budget_fiscal_year = 2021
    fiscal_year = 2021
    fiscal_period = random.randint(1, 12)
    pymt_doc_code = "GAX"
    pymt_doc_department_code = "EOL"
    pymt_doc_unit = "8770"
    pymt_doc_identifier = "GAXMDFMLAAAAJUFG3FJO"
    pymt_doc_version_no = "1"
    pymt_doc_vendor_line_no = "1"
    pymt_doc_comm_line_no = "0"
    pymt_doc_actg_line_no = "1"
    pymt_actg_line_amount = 100.00
    pymt_discount_line_amount = 0
    pymt_penalty_line_amount = 0
    pymt_interest_line_amount = 0
    pymt_backup_withholding_line_amount = 0
    pymt_intercept_amount = 0
    pymt_retainage_line_amount = 0
    pymt_freight_amount = 0
    pymt_default_intercept_fee_amount = 0
    pymt_supplementary_intercept_fee_amount = 0
    pymt_service_from_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 1), date_end=date(2021, 1, 15)
    )
    pymt_service_to_date = factory.LazyAttribute(
        lambda a: a.pymt_service_from_date + timedelta(days=7) if a.pymt_service_from_date else None
    )
    encumbrance_doc_code = "GAE"
    encumbrance_doc_dept = "EOL"
    encumbrance_doc_identifier = "PFMLFAMLFY2170030632"
    encumbrance_vendor_line_no = "1"
    encumbrance_accounting_line_no = "1"
    disb_doc_code = "AD"
    disb_doc_department_code = "CTR"
    disb_doc_identifier = "DISB0301210000263380"
    disb_doc_version_no = "1"
    disb_vendor_line_no = "1"
    disb_commodity_line_no = "0"
    disb_actg_line_no = "1"
    disb_actg_line_amount = 100.00
    disb_check_amount = 100.00
    disb_discount_line_amount = 0
    disb_penalty_line_amount = 0
    disb_interest_line_amount = 0
    disb_backup_withholding_line_amount = 0
    disb_intercept_amount = 0
    disb_retainage_line_amount = 0
    disb_freight_amount = 0
    disb_default_intercept_fee_amount = 0
    disb_supplementary_intercept_fee_amount = 0
    disb_doc_phase_code = "3"
    disb_doc_function_code = "1"
    actg_line_descr = "REQ 18939"
    check_descr = "Check Description - Factory"
    warrant_no = "M11"
    warrant_select_date = factory.LazyAttribute(
        lambda a: a.pymt_service_to_date + timedelta(days=1) if a.pymt_service_to_date else None
    )
    check_eft_issue_date = factory.LazyAttribute(
        lambda a: a.warrant_select_date + timedelta(days=2) if a.warrant_select_date else None
    )
    bank_account_code = "0"
    check_eft_no = "1234456"
    cleared_date = factory.LazyAttribute(
        lambda a: a.warrant_select_date + timedelta(days=10) if a.warrant_select_date else None
    )
    appropriation = "70030632"
    appropriation_name = "Family and Medical Leave Benefit Payments"
    object_class = "RR"
    object_class_name = "BENEFIT PROGRAMS"
    object = "R40"
    object_name = "Paid Family Medical Leave"
    income_type = "6"
    income_type_name = "Taxable Grants"
    form_type_indicator = "G"
    form_typ_ind_descr = "1099-G"
    disbursement_frequency = "1"
    disbursement_frequency_name = "Daily"
    payment_lag = "1"
    fund = "631"
    fund_name = "Family and Employment Secuirty Trust Fund"
    fund_category = "5"
    fund_category_name = "Trust and Agency"
    major_program = "DF0632"
    major_program_name = "DFML Benefit Payment"
    program = "DFML2021B"
    program_name = "DEPARTMENT OF FAMILY AND MEDICAL LEAVE COLLECTIONS 2021"
    phase = "K165"
    phase_name = "DEPARTMENT OF FAMILY AND MEDICAL LEAVE BENEFITS 2021"
    activity = "7246"
    activity_name = "Paid Medical Leave"
    vendor_customer_code = "VC0001201168"
    legal_name = "JOHN Q. CLAIMANT"
    address_id = "AD010"
    address_type = "PA"
    address_line_1 = "1 MAIN ST."
    city = "DARTMOUTH"
    state = "MA"
    zip_code = "02747-2722"
    country = "USA"
    vendor_invoice_no = "NTN-241347-ABS-01_14166"
    vendor_invoice_date = warrant_select_date
    scheduled_payment_date = warrant_select_date
    doc_function_code = "1"
    doc_function_code_name = "New"
    doc_phase_code = "3"
    doc_phase_name = "Final"
    government_branch = "10"
    government_branch_name = "EXECUTIVE BRANCH"
    cabinet = "93"
    cabinet_name = "EXECUTIVE OFFICE of LABOR and WORKFORCE DEVELOPMENT"
    department = "EOL"
    department_name = "Executive Office of Labor and Workforce Development"
    division = "1000"
    division_name = "EXECUTIVE OFFICE OF LABOR AND WORKFORCE DEVELOPMENT"
    group_name = "DEPARTMENT OF FAMILY AND MEDICAL LEAVE"
    section_name = "DEPARTMENT OF FAMILY AND MEDICAL LEAVE"
    district = "8700"
    district_name = "DEPARTMENT OF FAMILY AND MEDICAL LEAVE"
    bureau = "8710"
    bureau_name = "DFML ADMINISTRATION"
    unit = "8770"
    unit_name = "PFML Benefit Payments"
    doc_record_date = warrant_select_date
    acceptance_date = warrant_select_date
    doc_created_by = "EOL Interface"
    doc_created_on = warrant_select_date
    doc_last_modified_by = "System Admin"
    doc_last_modified_on = warrant_select_date


class Pfml1099BatchFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099Batch

    pfml_1099_batch_id = Generators.UuidObj

    tax_year = 2021
    batch_run_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 1, 1), date_end=date(2021, 1, 15)
    )
    correction_ind = False
    batch_status = "Created"


class Pfml1099Factory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099

    pfml_1099_id = Generators.UuidObj

    pfml_1099_batch_id = Generators.UuidObj

    tax_year = 2021
    employee_id = Generators.UuidObj
    tax_identifier_id = Generators.UuidObj
    c = "9999"
    i = "9999"
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    address_line_1 = factory.Faker("street_address")
    address_line_2 = ""
    city = factory.Faker("city")
    state = factory.Faker("state_abbr")
    zip = factory.Faker("postcode")
    gross_payments = Generators.Money
    state_tax_withholdings = Generators.Money
    federal_tax_withholdings = Generators.Money
    overpayment_repayments = 0.00
    correction_ind = False
    s3_location = "local_s3/Batch-1/Sub-Batch-1/test.pdf"
    fineos_status = "New"


class Pfml1099MMARSPaymentFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099MMARSPayment

    pfml_1099_mmars_payment_id = Generators.UuidObj

    # Pfml1099Batch
    batch = factory.SubFactory(Pfml1099BatchFactory)
    pfml_1099_batch_id = factory.LazyAttribute(lambda a: a.batch.pfml_1099_batch_id)

    # MmarsPaymentData
    mmars_payment = factory.SubFactory(MmarsPaymentDataFactory)
    mmars_payment_id = factory.LazyAttribute(lambda a: a.mmars_payment.mmars_payment_data_id)
    payment_amount = factory.LazyAttribute(lambda a: a.mmars_payment.pymt_actg_line_amount)
    payment_date = factory.LazyAttribute(lambda a: a.mmars_payment.warrant_select_date)

    # Employee
    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)


class Pfml1099PaymentFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099Payment

    pfml_1099_payment_id = Generators.UuidObj

    # Pfml1099Batch
    batch = factory.SubFactory(Pfml1099BatchFactory)
    pfml_1099_batch_id = factory.LazyAttribute(lambda a: a.batch.pfml_1099_batch_id)

    # Payment
    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda a: a.payment.payment_id)
    payment_amount = factory.LazyAttribute(lambda a: a.payment.amount)
    payment_date = factory.LazyAttribute(lambda a: a.payment.payment_date)

    # Claim
    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda a: a.claim.claim_id)

    # Employee
    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)


class Pfml1099RefundFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099Refund

    pfml_1099_refund_id = Generators.UuidObj

    # Pfml1099Batch
    batch = factory.SubFactory(Pfml1099BatchFactory)
    pfml_1099_batch_id = factory.LazyAttribute(lambda a: a.batch.pfml_1099_batch_id)

    # Payment
    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda a: a.payment.payment_id)
    # Refund amount is a negative value
    refund_amount = factory.LazyAttribute(lambda a: a.payment.amount)
    refund_date = factory.LazyAttribute(lambda a: a.payment.payment_date)

    # Employee
    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)


class Pfml1099FederalWithholdingFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099Withholding

    pfml_1099_refund_id = Generators.UuidObj

    # Pfml1099Batch
    batch = factory.SubFactory(Pfml1099BatchFactory)
    pfml_1099_batch_id = factory.LazyAttribute(lambda a: a.batch.pfml_1099_batch_id)

    # Payment
    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda a: a.payment.payment_id)
    withholding_amount = factory.LazyAttribute(lambda a: a.payment.amount)
    withholding_date = factory.LazyAttribute(lambda a: a.payment.payment_date)

    # Claim
    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda a: a.claim.claim_id)

    # Employee
    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)

    # Withholding Type
    withholding_type = payment_models.WithholdingType.FEDERAL
    withholding_type_id = withholding_type.withholding_type_id


class Pfml1099StateWithholdingFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099Withholding

    pfml_1099_refund_id = Generators.UuidObj

    # Pfml1099Batch
    batch = factory.SubFactory(Pfml1099BatchFactory)
    pfml_1099_batch_id = factory.LazyAttribute(lambda a: a.batch.pfml_1099_batch_id)

    # Payment
    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda a: a.payment.payment_id)
    withholding_amount = factory.LazyAttribute(lambda a: a.payment.amount)
    withholding_date = factory.LazyAttribute(lambda a: a.payment.payment_date)

    # Claim
    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda a: a.claim.claim_id)

    # Employee
    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda e: e.employee.employee_id)

    # Withholding Type
    withholding_type = payment_models.WithholdingType.STATE
    withholding_type_id = withholding_type.withholding_type_id
    organization_unit_id = Generators.UuidObj

    fineos_id = None
    name = factory.Faker("company")
    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda c: c.employer.employer_id)


class DuaEmployeeDemographicsFactory(BaseFactory):
    class Meta:
        model = employee_models.DuaEmployeeDemographics

    dua_employee_demographics_id = Generators.UuidObj

    fineos_customer_number = factory.Faker("numerify", text="####")
    date_of_birth = factory.Faker("date_object")
    gender_code = random.choices(["F", "M", "U", None])
    occupation_code = random.randint(1, 6000)
    occupation_description = None
    employer_fein = Generators.Fein
    employer_reporting_unit_number = random.randint(1, 100000)


class DuaReportingUnitFactory(BaseFactory):
    class Meta:
        model = employee_models.DuaReportingUnit

    dua_reporting_unit_id = Generators.UuidObj
    dua_id = factory.Sequence(lambda n: n)
    dba = None

    organization_unit = factory.SubFactory(OrganizationUnitFactory)
    organization_unit_id = factory.LazyAttribute(lambda d: d.organization_unit.organization_unit_id)


class EmployeeOccupationFactory(BaseFactory):
    class Meta:
        model = employee_models.EmployeeOccupation

    employee_occupation_id = Generators.UuidObj

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda d: d.employee.employee_id)

    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda d: d.employer.employer_id)


class UserLeaveAdministratorFactory(BaseFactory):
    class Meta:
        model = employee_models.UserLeaveAdministrator

    user = factory.SubFactory(UserFactory, roles=[employee_models.Role.EMPLOYER])
    user_id = factory.LazyAttribute(lambda u: u.user.user_id)
    employer = factory.SubFactory(EmployerFactory)
    employer_id = factory.LazyAttribute(lambda u: u.employer.employer_id)
    fineos_web_id = factory.Faker("numerify", text="pfml_leave_admin_#####")
    verification = None


class LinkSplitPaymentFactory(BaseFactory):
    class Meta:
        model = payment_models.LinkSplitPayment

    payment = factory.SubFactory(PaymentFactory)
    payment_id = factory.LazyAttribute(lambda c: c.payment.payment_id)

    related_payment = factory.SubFactory(PaymentFactory)
    related_payment_id = factory.LazyAttribute(lambda c: c.related_payment.payment_id)


class BenefitYearFactory(BaseFactory):
    class Meta:
        model = employee_models.BenefitYear

    employee = factory.SubFactory(EmployeeFactory)
    employee_id = factory.LazyAttribute(lambda w: w.employee.employee_id)

    start_date = date(2021, 1, 3)
    end_date = date(2022, 1, 1)

    base_period_start_date = None
    base_period_end_date = None
    total_wages = 0


class Pfml1099RequestFactory(BaseFactory):
    class Meta:
        model = payment_models.Pfml1099Request

    pfml_1099_request_id = Generators.UuidObj
    employee_id = Generators.UuidObj
    correction_ind = factory.Faker("boolean")
    pfml_1099_batch_id = Generators.UuidObj


class ChangeRequestFactory(BaseFactory):
    class Meta:
        model = employee_models.ChangeRequest

    change_request_id = Generators.UuidObj
    change_request_type_id = 1
    claim = factory.SubFactory(ClaimFactory)
    claim_id = factory.LazyAttribute(lambda w: w.claim.claim_id)
    start_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 2, 1), date_end=date(2021, 2, 15)
    )
    end_date = factory.Faker(
        "date_between_dates", date_start=date(2021, 2, 16), date_end=date(2021, 2, 28)
    )
    submitted_time = None

from datetime import date, timedelta

import pytest

from massgov.pfml import db
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import BenefitYear, Employee
from massgov.pfml.db.models.factories import BenefitYearFactory, EmployeeFactory
from massgov.pfml.db.models.payments import PaymentAuditReportDetails
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.postprocessing.fineos_total_leave_duration_processor import (
    FineosTotalLeaveDurationProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)
from tests.delegated_payments.postprocessing import (
    _create_absence_data,
    _create_absence_periods_data,
)


@pytest.fixture
def payment_post_processing_step(
    initialize_factories_session,
    test_db_session,
):
    return PaymentPostProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


@pytest.fixture
def fineos_total_leave_duration_processor(payment_post_processing_step):
    return FineosTotalLeaveDurationProcessor(payment_post_processing_step)


@pytest.fixture
def use_employee(initialize_factories_session):
    return EmployeeFactory.create()


@pytest.fixture
def by(initialize_factories_session, use_employee):
    def create(start_date: date, end_date: date):
        return BenefitYearFactory.create(
            employee=use_employee, start_date=start_date, end_date=end_date
        )

    return create


# Benefit years to be referenced throughout.
@pytest.fixture
def by_0(by):
    return by(date(2020, 1, 5), date(2021, 1, 2))


@pytest.fixture
def by_1(by):
    return by(date(2021, 1, 3), date(2022, 1, 1))


@pytest.fixture
def by_2(by):
    return by(date(2022, 1, 2), date(2022, 12, 31))


@pytest.fixture
def by_3(by):
    return by(date(2023, 1, 1), date(2023, 12, 30))


@pytest.mark.parametrize(
    "absence_status", [AbsenceStatus.APPROVED, AbsenceStatus.COMPLETED, AbsenceStatus.IN_REVIEW]
)
def test_processor_leave_less_than_26_weeks(
    fineos_total_leave_duration_processor: FineosTotalLeaveDurationProcessor,
    test_db_session: db.Session,
    initialize_factories_session,
    absence_status: AbsenceStatus,
    by_1: BenefitYear,
):

    leave_duration = timedelta(weeks=26, days=-1).days
    employer = _create_absence_periods_data(
        by_1, leave_duration, 2, fineos_absence_status=absence_status
    )[0]
    payment_factory = DelegatedPaymentFactory(
        test_db_session, employee=by_1.employee, employer=employer
    )
    payment = payment_factory.get_or_create_payment()

    fineos_total_leave_duration_processor.process(payment)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert audit_report is None


@pytest.mark.parametrize(
    "absence_status", [AbsenceStatus.APPROVED, AbsenceStatus.COMPLETED, AbsenceStatus.IN_REVIEW]
)
def test_processor_leave_greater_than_26_weeks(
    fineos_total_leave_duration_processor: FineosTotalLeaveDurationProcessor,
    test_db_session: db.Session,
    initialize_factories_session,
    absence_status: AbsenceStatus,
    by_1: BenefitYear,
    use_employee: Employee,
):
    """
    Leave duration for a single employer exceeds the
    the maximum 182 days (26 weeks).
    """

    leave_start_date = date(2021, 1, 5)
    leave_duration = timedelta(weeks=26, days=1).days
    (employer, _, leave_duration_total) = _create_absence_data(
        use_employee, [(leave_start_date, leave_duration)]
    )
    assert leave_duration == 183
    assert leave_duration_total == leave_duration

    payment_factory = DelegatedPaymentFactory(
        test_db_session, employee=by_1.employee, employer=employer
    )
    payment = payment_factory.get_or_create_payment()

    fineos_total_leave_duration_processor.process(payment)

    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    message = audit_report.details["message"]

    assert message == "\n".join(
        [
            f"Benefit Year Start: {by_1.start_date}, Benefit Year End: {by_1.end_date}",
            f"- Employer ID: {employer.fineos_employer_id}, Leave Duration: {leave_duration_total}",
        ]
    )


def test_processor_leave_greater_than_26_weeks__multiple_employers_within_benefit_year(
    fineos_total_leave_duration_processor: FineosTotalLeaveDurationProcessor,
    test_db_session: db.Session,
    initialize_factories_session,
):
    """
    Leave duration for multiple employers exceed the
    the maximum 182 days (26 weeks) for a single benefit year.
    All absence periods within a single benefit year.
    """

    benefit_year_start_date = date(2021, 1, 3)
    benefit_year_end_date = date(2022, 1, 1)
    start_date_A = date(2021, 1, 5)
    start_date_B = start_date_A + timedelta(days=60)
    start_date_C = start_date_B + timedelta(days=60)

    employee = EmployeeFactory.create()
    by = BenefitYearFactory.create(
        employee=employee, start_date=benefit_year_start_date, end_date=benefit_year_end_date
    )

    # Employer I
    # exceeds maximum with 3 absence periods
    case_1 = _create_absence_data(
        employee, [(start_date_A, 61), (start_date_B, 62), (start_date_C, 63)]
    )

    # Employer II
    # exceeds maximum with 2 absence periods
    case_2 = _create_absence_data(employee, [(start_date_A, 96), (start_date_B, 97)])

    # Employer III
    # exceeds maximum with 1 absence period
    case_3 = _create_absence_data(employee, [(start_date_A, 194)])

    # Employer IV
    # does not exceeds maximum
    _create_absence_data(employee, [(start_date_A, 56)])
    # Employer V
    # does not exceeds maximum
    _create_absence_data(employee, [(start_date_A, 23)])

    payment_factory = DelegatedPaymentFactory(test_db_session, employee=employee)
    payment = payment_factory.get_or_create_payment()

    fineos_total_leave_duration_processor.process(payment)
    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    message = audit_report.details["message"]

    # The message is sorted on benefit year then employer id
    cases = sorted([case_1, case_2, case_3], key=lambda x: x[0].employer_id)

    assert case_1[2] == 61 + 62 + 63 == 186
    assert case_2[2] == 96 + 97 == 193
    assert case_3[2] == 194

    expected_message = "\n".join(
        [
            f"Benefit Year Start: {by.start_date}, Benefit Year End: {by.end_date}",
            f"- Employer ID: {cases[0][0].fineos_employer_id}, Leave Duration: {cases[0][2]}",
            f"- Employer ID: {cases[1][0].fineos_employer_id}, Leave Duration: {cases[1][2]}",
            f"- Employer ID: {cases[2][0].fineos_employer_id}, Leave Duration: {cases[2][2]}",
        ]
    )

    assert message == expected_message


def test_processor_leave_greater_than_26_weeks__multi_employers_multi_benefit_years(
    fineos_total_leave_duration_processor: FineosTotalLeaveDurationProcessor,
    test_db_session: db.Session,
    initialize_factories_session,
    use_employee: Employee,
    by_0: BenefitYear,
    by_1: BenefitYear,
    by_2: BenefitYear,
    by_3: BenefitYear,
):
    """
    Leave duration for multiple emlpoyers exceeds the
    the maximum 182 days (26 weeks) across multiple benefit years.
    Absence periods across multiple benefit years.
    """

    # Benefit Year I
    # exceeds maximum for multiple employers
    case_0_1 = _create_absence_periods_data(by_0, 183)
    case_0_2 = _create_absence_periods_data(by_0, 184, 3)
    _create_absence_periods_data(by_0, 182, 1)

    # Benefit Year II
    # exceeds maximum for multiple employers
    case_1_1 = _create_absence_periods_data(by_1, 185)
    case_1_2 = _create_absence_periods_data(by_1, 186, 4)
    case_1_3 = _create_absence_periods_data(by_1, 187, 5)
    _create_absence_periods_data(by_1, 182, 4)

    # Benefit Year III
    # exceeds maximum for single employer
    case_2_1 = _create_absence_periods_data(by_2, 188, 2)

    _create_absence_periods_data(by_2, 91)
    _create_absence_periods_data(by_2, 91)

    # Benefit Year IV
    # does not exceed maximum for any employer
    _create_absence_periods_data(by_3, 60)
    _create_absence_periods_data(by_3, 60, 2)
    _create_absence_periods_data(by_3, 60, 3)

    payment_factory = DelegatedPaymentFactory(test_db_session, employee=use_employee)
    payment = payment_factory.get_or_create_payment()

    fineos_total_leave_duration_processor.process(payment)
    audit_report = (
        test_db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    message = audit_report.details["message"]

    # The message is sorted on benefit year then employer id so its
    # a bit cumbersome to validate.
    cases_by_0 = sorted([case_0_1, case_0_2], key=lambda x: x[0].employer_id)
    cases_by_1 = sorted([case_1_1, case_1_2, case_1_3], key=lambda x: x[0].employer_id)
    cases_by_2 = [case_2_1]

    assert 183 == case_0_1[2]
    assert 184 == case_0_2[2]
    assert 185 == case_1_1[2]
    assert 186 == case_1_2[2]
    assert 187 == case_1_3[2]
    assert 188 == case_2_1[2]

    expected_message = "\n".join(
        [
            f"Benefit Year Start: {by_0.start_date}, Benefit Year End: {by_0.end_date}",
            f"- Employer ID: {cases_by_0[0][0].fineos_employer_id}, Leave Duration: {cases_by_0[0][2]}",
            f"- Employer ID: {cases_by_0[1][0].fineos_employer_id}, Leave Duration: {cases_by_0[1][2]}",
            f"Benefit Year Start: {by_1.start_date}, Benefit Year End: {by_1.end_date}",
            f"- Employer ID: {cases_by_1[0][0].fineos_employer_id}, Leave Duration: {cases_by_1[0][2]}",
            f"- Employer ID: {cases_by_1[1][0].fineos_employer_id}, Leave Duration: {cases_by_1[1][2]}",
            f"- Employer ID: {cases_by_1[2][0].fineos_employer_id}, Leave Duration: {cases_by_1[2][2]}",
            f"Benefit Year Start: {by_2.start_date}, Benefit Year End: {by_2.end_date}",
            f"- Employer ID: {cases_by_2[0][0].fineos_employer_id}, Leave Duration: {cases_by_2[0][2]}",
        ]
    )
    assert message == expected_message

import datetime
import time

from massgov.pfml.api.eligibility import benefit_year
from massgov.pfml.api.eligibility.task import backfill_benefit_years
from massgov.pfml.db.models import employees, factories
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.util.batch import log
from tests.delegated_payments.test_delegated_payments_e2e import assert_metrics


def test_get_claimants_to_backfill(test_db_session, initialize_factories_session):
    # existing employee without any claims (should not be included)
    factories.EmployeeWithFineosNumberFactory.create()

    # existing employee with claim and corresponding benefit year (should not be included)
    employee_one: employees.Employee = factories.EmployeeFactory.create()
    employee_one_claim: employees.Claim = factories.ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=employee_one,
        absence_period_start_date=datetime.date(2021, 2, 15),
    )
    benefit_year.get_benefit_year_by_employee_id(
        test_db_session, employee_one.employee_id, employee_one_claim.absence_period_start_date
    )

    # claimant w/o a corresopnding benefit year (should be included)
    employee_two: employees.Employee = factories.EmployeeWithFineosNumberFactory.create()
    factories.ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=employee_two,
        absence_period_start_date=datetime.date(2021, 2, 15),
    )

    # claimant with multiple claims w/o a benefit year (should be included)
    employee_three: employees.Employee = factories.EmployeeWithFineosNumberFactory.create()
    factories.ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
        employee=employee_three,
        absence_period_start_date=datetime.date(2021, 2, 15),
    )
    factories.ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=employee_three,
        absence_period_start_date=datetime.date(2021, 5, 15),
    )
    factories.ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=employee_three,
        absence_period_start_date=datetime.date(2021, 7, 15),
    )

    claimants_to_backfill = backfill_benefit_years.get_claimants_to_backfill(test_db_session)
    assert claimants_to_backfill == [employee_two, employee_three]


def test_backfill_benefit_year_successfully(
    test_db_session, initialize_factories_session, test_db_other_session
):
    employee: employees.Employee = factories.EmployeeWithFineosNumberFactory.create()
    factories.ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=employee,
        absence_period_start_date=datetime.date(2021, 2, 15),
    )
    claimants = [employee]

    benefit_years = (
        test_db_session.query(employees.BenefitYear)
        .filter(employees.BenefitYear.employee_id == employee.employee_id)
        .all()
    )
    assert len(benefit_years) == 0

    expected_metrics = {
        backfill_benefit_years.Metrics.CLAIMANTS_TO_BACKFILL: 1,
        backfill_benefit_years.Metrics.CLAIMANTS_BENEFIT_YEARS_CREATED: 1,
        backfill_benefit_years.Metrics.TOTAL_BENEFIT_YEARS_CREATED: 1,
        backfill_benefit_years.Metrics.STATUS: "Backfill completed succesfully",
    }

    with log.LogEntry(test_db_other_session, "BackfillBenefitYears") as log_entry:
        backfill_benefit_years.backfill_benefit_years(test_db_session, claimants, log_entry)
        # sleeping here to ensure we commit all of the metrics to the DB
        time.sleep(5)
        log_entry._commit_metrics()
        assert_metrics(test_db_other_session, "BackfillBenefitYears", expected_metrics)

    benefit_years = (
        test_db_session.query(employees.BenefitYear)
        .filter(employees.BenefitYear.employee_id == employee.employee_id)
        .all()
    )
    assert len(benefit_years) == 1

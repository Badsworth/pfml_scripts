import pytest

from massgov.pfml.db.models.employees import Claim, Employee, Employer, Payment
from massgov.pfml.payments.mock.payments_test_scenario_generator import (
    ScenarioDataConfig,
    ScenarioName,
    ScenarioNameWithCount,
    generate_scenario_dataset,
)


@pytest.mark.integration
def test_generator(test_db_session, initialize_factories_session):
    # configure
    scenario_config = ScenarioDataConfig(
        scenario_config=[
            ScenarioNameWithCount(ScenarioName.SCENARIO_A, 1),
            ScenarioNameWithCount(ScenarioName.SCENARIO_B, 2),
        ]
    )

    # run the generator
    generate_scenario_dataset(scenario_config)

    # get counts
    employees = test_db_session.query(Employee).all()
    employers = test_db_session.query(Employer).all()
    claims = test_db_session.query(Claim).all()
    payments = test_db_session.query(Payment).all()

    # Employees and Employers should match count in ScenarioNameWithCount
    assert len(employees) == 3
    assert len(employers) == 3

    # Claims should match EmployeePaymentScenarioDescriptor.absence_claims_count
    assert len(claims) == 4

    # Payments are generated if EmployeePaymentScenarioDescriptor.has_payment_extract is true
    assert len(payments) == 4

import pytest

from massgov.pfml.api.generate_wagesandcontributions import generate
from massgov.pfml.db.models.employees import (
    Employee,
    Employer,
    TaxIdentifier,
    WagesAndContributions,
)
from massgov.pfml.types import Fein, TaxId


@pytest.mark.integration
def test_full_generate_wagesandcontributions(test_db_session):
    employer_fein = Fein("929292929")
    employee_ssn = TaxId("123456789")

    assert test_db_session.query(Employer).count() == 0
    assert test_db_session.query(Employee).count() == 0
    assert test_db_session.query(TaxIdentifier).count() == 0
    assert test_db_session.query(WagesAndContributions).count() == 0

    generate(employer_fein, employee_ssn, test_db_session)

    assert test_db_session.query(Employer).count() == 1
    assert test_db_session.query(Employee).count() == 1
    assert test_db_session.query(TaxIdentifier).count() == 1
    assert test_db_session.query(WagesAndContributions).count() == 1

    employer = test_db_session.query(Employer).first()
    employee = test_db_session.query(Employee).first()
    tax_identifier = test_db_session.query(TaxIdentifier).first()
    wages = test_db_session.query(WagesAndContributions).first()

    assert employer.employer_fein == employer_fein
    assert employer.fineos_employer_id == 1
    assert employee.tax_identifier_id == tax_identifier.tax_identifier_id
    assert tax_identifier.tax_identifier == employee_ssn
    assert wages.employer_id == employer.employer_id
    assert wages.employee_id == employee.employee_id

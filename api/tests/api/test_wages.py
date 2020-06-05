import json
import uuid

from massgov.pfml.api.wages import WagesAndContributionsResponse
from massgov.pfml.db.models.employees import WagesAndContributions
from massgov.pfml.db.models.factories import EmployeeFactory, WagesAndContributionsFactory


def build_json_response(wages: WagesAndContributions) -> WagesAndContributionsResponse:
    """Build a JSON-serialized response object directly from a WagesAndContributions object."""
    return json.loads(WagesAndContributionsResponse.from_orm(wages).json())


def test_get_no_wages(client):
    """Verify that no wages are returned when employee has no wages."""
    WagesAndContributionsFactory.create()
    response = client.get("/v1/wages", query_string={"employee_id": uuid.uuid4()})

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_single_wage_item(client):
    """Verify that single wage is returned when employee has a wage."""
    wages = WagesAndContributionsFactory.create()
    WagesAndContributionsFactory.create()

    response = client.get("/v1/wages", query_string={"employee_id": wages.employee_id})
    assert response.status_code == 200
    assert response.get_json() == [build_json_response(wages)]


def test_get_multiple_wage_items(client):
    """Verify that many wages for an employee are returned."""
    all_wages = WagesAndContributionsFactory.create_batch(
        size=50, employee=EmployeeFactory.create()
    )

    response = client.get("/v1/wages", query_string={"employee_id": all_wages[0].employee_id})

    assert response.status_code == 200
    assert response.get_json() == list(map(build_json_response, all_wages))


def test_get_no_wages_with_wage_period(client):
    """Verify that no wages are returned if employee did not earn in a period."""
    wages = WagesAndContributionsFactory.create()
    missing_filing_period = WagesAndContributionsFactory.filing_period.generate()

    response = client.get(
        "/v1/wages",
        query_string={"employee_id": wages.employee_id, "filing_period": missing_filing_period},
    )

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_single_wage_with_wage_period(client):
    """Verify that single wage is returned if employee has a single wage."""
    wages = WagesAndContributionsFactory.create()
    WagesAndContributionsFactory.create(filing_period=wages.filing_period)

    response = client.get(
        "/v1/wages",
        query_string={"employee_id": wages.employee_id, "filing_period": wages.filing_period},
    )

    assert response.status_code == 200
    assert response.get_json() == [build_json_response(wages)]


def test_get_multiple_wages_with_wage_period(client):
    """Verify that multiple wages are returned for an employee in a filing period."""

    # Create multiple wages with the same employee and filing period,
    # but generate different employers.
    all_wages = WagesAndContributionsFactory.create_batch(
        size=3,
        employee=EmployeeFactory.create(),
        filing_period=WagesAndContributionsFactory.filing_period.generate(),
    )

    response = client.get(
        "/v1/wages",
        query_string={
            "employee_id": all_wages[0].employee_id,
            "filing_period": all_wages[0].filing_period,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == list(map(build_json_response, all_wages))

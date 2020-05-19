from dataclasses import dataclass
from typing import Optional

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import Employee


def employees_get(employee_id):
    with app.db_session() as db_session:
        employee = db_session.query(Employee).get(employee_id)

    if employee is None:
        raise NotFound()

    return employee_response(employee)


def employees_patch(employee_id):
    """ this endpoint will allow an employee's personal information to be updated """
    body = connexion.request.json
    with app.db_session() as db_session:
        db_session.query(Employee).filter(Employee.employee_id == employee_id).update(body)
        updated_employee = db_session.query(Employee).get(employee_id)
    return employee_response(updated_employee)


def employees_search():
    body = connexion.request.json
    with app.db_session() as db_session:
        employee = (
            db_session.query(Employee)
            .filter_by(
                first_name=body["first_name"],
                last_name=body["last_name"],
                tax_identifier=body["tax_identifier"].replace("-", ""),
            )
            .first()
        )
    if employee is None:
        raise NotFound()

    return employee_response(employee)


@dataclass
class EmployeeResponse:
    employee_id: Optional[str]
    tax_identifier: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    other_name: Optional[str]
    email_address: Optional[str]
    phone_number: Optional[str]


class EmployeeUpdateRequest:
    first_name: str
    middle_name: str
    last_name: str


def serialize_tax_identifier(tax_identifier: Optional[str]) -> Optional[str]:
    if not tax_identifier:
        return None

    return "{}-{}-{}".format(tax_identifier[:3], tax_identifier[3:5], tax_identifier[5:])


def employee_response(employee: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        employee_id=employee.employee_id,
        tax_identifier=serialize_tax_identifier(employee.tax_identifier),
        first_name=employee.first_name,
        middle_name=employee.middle_name,
        last_name=employee.last_name,
        other_name=employee.other_name,
        email_address=employee.email_address,
        phone_number=employee.phone_number,
    )

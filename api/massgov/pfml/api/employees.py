from typing import Optional

import connexion
from pydantic import UUID4
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.db.models.employees import Employee, TaxIdentifier, HRD
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.sqlalchemy import get_or_404


class EmployeeUpdateRequest(PydanticBaseModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    email_address: Optional[str]


class EmployeeSearchRequest(PydanticBaseModel):
    first_name: str
    middle_name: Optional[str]
    last_name: str
    tax_identifier_last4: str


class EmployeeResponse(PydanticBaseModel):
    employee_id: UUID4
    tax_identifier_last4: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    other_name: Optional[str]
    email_address: Optional[str]
    phone_number: Optional[str]

    @classmethod
    def from_orm(cls, employee: Employee) -> "EmployeeResponse":
        employee_response = super().from_orm(employee)

        if employee.tax_identifier:
            employee_response.tax_identifier_last4 = employee.tax_identifier.tax_identifier_last4

        return employee_response


class HRDEmployeeSearchRequest(PydanticBaseModel):
    tax_identifier: Optional[str]
    employee_id: Optional[str]


class HRDEmployeeResponse(PydanticBaseModel):
    employee_id: UUID4
    tax_identifier: str
    full_name: Optional[str]
    department_id: str
    department_name: Optional[str]


def employees_get(employee_id):
    with app.db_session() as db_session:
        employee = get_or_404(db_session, Employee, employee_id)

    ensure(READ, employee)

    return response_util.success_response(
        message="Successfully retrieved employee", data=EmployeeResponse.from_orm(employee).dict(),
    ).to_api_response()


def employees_patch(employee_id):
    """This endpoint updates an Employee record"""
    request = EmployeeUpdateRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        updated_employee = get_or_404(db_session, Employee, employee_id)
        ensure(EDIT, updated_employee)
        for key in request.__fields_set__:
            value = getattr(request, key)
            setattr(updated_employee, key, value)

    return response_util.success_response(
        message="Successfully updated employee",
        data=EmployeeResponse.from_orm(updated_employee).dict(),
    ).to_api_response()


def employees_search():
    request = EmployeeSearchRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        employee_query = (
            db_session.query(Employee)
            .join(Employee.tax_identifier)
            .filter(
                TaxIdentifier.tax_identifier_last4 == request.tax_identifier_last4,  # type: ignore
                Employee.first_name == request.first_name,
                Employee.last_name == request.last_name,
            )
        )

        if request.middle_name is not None:
            employee_query.filter(Employee.middle_name == request.middle_name)

        employee = employee_query.first()

    if employee is None:
        raise NotFound()

    ensure(READ, employee)

    return response_util.success_response(
        message="Successfully found employee", data=EmployeeResponse.from_orm(employee).dict(),
    ).to_api_response()


def employees_departments_search():
    request = HRDEmployeeSearchRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        if request.employee_id:
            departments_query = (
                db_session.query(HRD)
                .filter(
                    HRD.employee_id == request.employee_id
                )
            )
        elif request.tax_identifier:
            departments_query = (
                db_session.query(HRD)
                .filter(
                    HRD.tax_identifier == request.tax_identifier
                )
            )
        
        departments = departments_query.all()

    if departments is None or len(departments) == 0:
        raise NotFound()

    ensure(READ, departments)

    departmentsResponse = [HRDEmployeeResponse.from_orm(department).dict() for department in departments]
    return response_util.success_response(
        message="Successfully found employee departments", data=departmentsResponse,
    ).to_api_response()

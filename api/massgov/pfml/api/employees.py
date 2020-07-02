from typing import Optional

import connexion
from pydantic import UUID4
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
from massgov.pfml.db.models.employees import Employee
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import TaxIdFormattedStr, TaxIdUnformattedStr
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
    tax_identifier: TaxIdUnformattedStr


class EmployeeResponse(PydanticBaseModel):
    employee_id: UUID4
    tax_identifier: TaxIdFormattedStr
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    other_name: Optional[str]
    email_address: Optional[str]
    phone_number: Optional[str]


def employees_get(employee_id):
    with app.db_session() as db_session:
        employee = get_or_404(db_session, Employee, employee_id)

    return EmployeeResponse.from_orm(employee).dict()


def employees_patch(employee_id):
    """This endpoint updates an Employee record"""
    request = EmployeeUpdateRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        updated_employee = get_or_404(db_session, Employee, employee_id)

        for key in request.__fields_set__:
            value = getattr(request, key)
            setattr(updated_employee, key, value)

    return EmployeeResponse.from_orm(updated_employee).dict()


def employees_search():
    request = EmployeeSearchRequest.parse_obj(connexion.request.json)
    with app.db_session() as db_session:
        employee = db_session.query(Employee).filter_by(**request.dict(exclude_none=True)).first()
    if employee is None:
        raise NotFound()

    return EmployeeResponse.from_orm(employee).dict()

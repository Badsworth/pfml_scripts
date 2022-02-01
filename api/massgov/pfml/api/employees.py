import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.api.models.employees.requests import EmployeeSearchRequest, EmployeeUpdateRequest
from massgov.pfml.api.models.employees.responses import EmployeeForPfmlCrmResponse, EmployeeResponse
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.db.models.employees import Employee, Role, TaxIdentifier
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.users import has_role_in

logger = massgov.pfml.util.logging.get_logger(__name__)


def employees_get(employee_id):
    with app.db_session() as db_session:
        employee = get_or_404(db_session, Employee, employee_id)
        ensure(READ, employee)

        user = app.current_user()
        response_type = (
            EmployeeForPfmlCrmResponse if has_role_in(user, [Role.PFML_CRM]) else EmployeeResponse
        )

    return response_util.success_response(
        message="Successfully retrieved employee", data=response_type.from_orm(employee).dict(),
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
            return response_util.error_response(
                status_code=NotFound,
                message="Could not find Employee with the given details",
                errors=[
                    ValidationErrorDetail(
                        message="Could not find Employee with the given details",
                        type=IssueType.object_not_found,
                    )
                ],
                data={},
            ).to_api_response()

        ensure(READ, employee)

        user = app.current_user()

        response_type = (
            EmployeeForPfmlCrmResponse if has_role_in(user, [Role.PFML_CRM]) else EmployeeResponse
        )

    return response_util.success_response(
        message="Successfully found employee", data=response_type.from_orm(employee).dict(),
    ).to_api_response()

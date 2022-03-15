from typing import Type, Union

import connexion
import flask
from sqlalchemy import asc, desc, or_
from sqlalchemy_utils import escape_like
from werkzeug.exceptions import Forbidden

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import READ, ensure
from massgov.pfml.api.models.common import OrderDirection, search_request_log_info
from massgov.pfml.api.models.employees.requests import EmployeeSearchRequest
from massgov.pfml.api.models.employees.responses import EmployeeForPfmlCrmResponse, EmployeeResponse
from massgov.pfml.api.util.paginate.paginator import (
    PaginationAPIContext,
    make_paging_meta_data_from_paginator,
    page_for_api_context,
)
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
        message="Successfully retrieved employee", data=response_type.from_orm(employee).dict()
    ).to_api_response()


def employees_search() -> flask.Response:
    current_user = app.current_user()
    is_pfml_crm_user = has_role_in(current_user, [Role.PFML_CRM])

    if not is_pfml_crm_user:
        raise Forbidden

    request = EmployeeSearchRequest.parse_obj(connexion.request.json)
    terms = request.terms

    with PaginationAPIContext(Employee, request=request) as pagination_context:
        with app.db_session() as db_session:
            query = db_session.query(Employee).join(TaxIdentifier)

            if terms.fineos_customer_number is not None:
                query = query.filter(
                    Employee.fineos_customer_number == terms.fineos_customer_number
                )

            if terms.tax_identifier is not None:
                query = query.filter(TaxIdentifier.tax_identifier == terms.tax_identifier)

            if terms.email_address is not None:
                query = query.filter(Employee.email_address.ilike(escape_like(terms.email_address)))

            if terms.first_name is not None and terms.last_name is not None:
                # currently request validation is blocking any non-alphanumeric
                # values, but still possible something we don't want sneaks in
                # or the validation changes in the future, so escape the input
                # for now
                escaped_first_name = escape_like(terms.first_name)
                escaped_last_name = escape_like(terms.last_name)

                query = query.filter(
                    or_(
                        Employee.first_name.ilike(f"%{escaped_first_name}%"),
                        Employee.fineos_employee_first_name.ilike(f"%{escaped_first_name}%"),
                    ),
                    or_(
                        Employee.last_name.ilike(f"%{escaped_last_name}%"),
                        Employee.fineos_employee_last_name.ilike(f"%{escaped_last_name}%"),
                    ),
                )

            if terms.phone_number is not None:
                query = query.filter(
                    or_(
                        Employee.phone_number == terms.phone_number,
                        Employee.cell_phone_number == terms.phone_number,
                    )
                )

            is_asc = pagination_context.order_direction == OrderDirection.asc.value
            sort_fn = asc if is_asc else desc
            query = query.order_by(sort_fn(pagination_context.order_key))

            page = page_for_api_context(pagination_context, query)

            search_request_log_attributes = search_request_log_info(request)
            page_data_log_attributes = make_paging_meta_data_from_paginator(
                pagination_context, page
            ).to_dict()

    logger.info(
        "Employees_search success",
        extra={**page_data_log_attributes, **search_request_log_attributes},
    )

    response_model: Union[Type[EmployeeForPfmlCrmResponse], Type[EmployeeResponse]] = (
        EmployeeForPfmlCrmResponse if is_pfml_crm_user else EmployeeResponse
    )

    return response_util.paginated_success_response(
        message="Successfully retrieved Employees",
        model=response_model,
        page=page,
        context=pagination_context,
        status_code=200,
    ).to_api_response()

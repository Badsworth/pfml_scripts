from typing import Optional, cast

from pydantic import UUID4

from massgov.pfml.db.models.employees import Employee
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployeeBasicResponse(PydanticBaseModel):
    employee_id: UUID4
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    other_name: Optional[str]

    @classmethod
    def from_orm(cls, employee: Employee) -> "EmployeeBasicResponse":
        employee_response = super().from_orm(employee)

        employee_response.first_name = employee.fineos_employee_first_name or employee.first_name
        employee_response.middle_name = employee.fineos_employee_middle_name or employee.middle_name
        employee_response.last_name = employee.fineos_employee_last_name or employee.last_name

        return employee_response


class EmployeeResponse(EmployeeBasicResponse):
    tax_identifier_last4: Optional[str]
    email_address: Optional[str]
    phone_number: Optional[str]

    @classmethod
    def from_orm(cls, employee: Employee) -> "EmployeeResponse":
        employee_response = cast(EmployeeResponse, super().from_orm(employee))

        if employee.tax_identifier:
            employee_response.tax_identifier_last4 = employee.tax_identifier.tax_identifier_last4

        return employee_response

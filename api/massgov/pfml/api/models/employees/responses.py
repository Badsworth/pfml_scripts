from typing import Optional

from pydantic import UUID4

from massgov.pfml.db.models.employees import Employee, Employer
from massgov.pfml.util.pydantic import PydanticBaseModel


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
    def from_orm(
        cls, employee: Employee, employer: Optional[Employer] = None
    ) -> "EmployeeResponse":
        employee_response = super().from_orm(employee)

        if employee.tax_identifier:
            employee_response.tax_identifier_last4 = employee.tax_identifier.tax_identifier_last4

        return employee_response

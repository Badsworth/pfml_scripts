from datetime import date
from typing import List, Optional, cast

from pydantic import UUID4

from massgov.pfml.api.models.applications.common import MaskedAddress
from massgov.pfml.api.models.common import PhoneResponse, PhoneType
from massgov.pfml.db.models.employees import Employee
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import MaskedDateStr, MassIdStr, TaxIdFormattedStr


class EmployeeBasicResponse(PydanticBaseModel):
    employee_id: UUID4
    fineos_customer_number: Optional[str]
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
    tax_identifier: Optional[TaxIdFormattedStr]
    fineos_customer_number: Optional[str]
    email_address: Optional[str]
    phone_numbers: Optional[List[PhoneResponse]]
    mass_id_number: Optional[MassIdStr]
    date_of_birth: Optional[MaskedDateStr]
    addresses: Optional[List[MaskedAddress]]
    created_at: Optional[date]

    @classmethod
    def from_orm(cls, employee: Employee) -> "EmployeeResponse":
        employee_response = cast(EmployeeResponse, super().from_orm(employee))

        employee_response.phone_numbers = employee_response_phone_numbers(employee)

        return employee_response


class EmployeeForPfmlCrmResponse(EmployeeBasicResponse):
    tax_identifier_last4: Optional[str]
    tax_identifier: Optional[TaxIdFormattedStr]
    fineos_customer_number: Optional[str]
    email_address: Optional[str]
    phone_numbers: Optional[List[PhoneResponse]]
    mass_id_number: Optional[MassIdStr]
    date_of_birth: Optional[MaskedDateStr]
    addresses: Optional[List[MaskedAddress]]
    created_at: Optional[date]

    @classmethod
    def from_orm(cls, employee: Employee) -> "EmployeeForPfmlCrmResponse":
        employee_response = cast(EmployeeForPfmlCrmResponse, super().from_orm(employee))

        employee_response.phone_numbers = list()
        if employee.phone_number:
            phone_response = PhoneResponse.from_orm(employee.phone_number)
            phone_response.phone_type = PhoneType.Phone
            employee_response.phone_numbers.append(phone_response)

        if employee.cell_phone_number:
            phone_response = PhoneResponse.from_orm(employee.cell_phone_number)
            phone_response.phone_type = PhoneType.Phone
            employee_response.phone_numbers.append(phone_response)

        return employee_response


def employee_response_phone_numbers(employee: Employee) -> List[PhoneResponse]:
    phone_numbers = list()
    if employee.phone_number:
        phone_response = PhoneResponse.from_orm(employee.phone_number)
        phone_response.phone_type = PhoneType.Phone
        phone_numbers.append(phone_response)

    if employee.cell_phone_number:
        phone_response = PhoneResponse.from_orm(employee.cell_phone_number)
        phone_response.phone_type = PhoneType.Cell
        phone_numbers.append(phone_response)

    return phone_numbers

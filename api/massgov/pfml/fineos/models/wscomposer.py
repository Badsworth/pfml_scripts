#
# Models for Web Services Composer.
#

import datetime
from typing import Optional

import pydantic


class EmployeeRegistration(pydantic.BaseModel):
    user_id: str
    customer_number: Optional[int]
    employer_id: str
    date_of_birth: datetime.date
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    national_insurance_no: str

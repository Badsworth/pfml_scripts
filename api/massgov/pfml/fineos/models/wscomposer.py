#
# Models for Web Services Composer.
#

import datetime

import pydantic


class EmployeeRegistration(pydantic.BaseModel):
    user_id: str
    customer_number: int
    employer_id: int
    date_of_birth: datetime.date
    email: str
    first_name: str
    last_name: str

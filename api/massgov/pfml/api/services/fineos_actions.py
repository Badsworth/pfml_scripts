###
# This file houses all FINEOS actions currently defined. We may have
# to split the code into multiple files down the road. As of this
# writing we have the following actions:
#
# 1 - Register user with FINEOS using employee SSN and employer FEIN
# 2 - Submit an application
#
# The FINEOS API calls are defined in the FINEOSClient class. Here we
# stitch together the various API calls we have to do to complete the
# two actions described above.
#
###
import datetime
import uuid
from typing import Optional

from werkzeug.exceptions import BadRequest, NotFound

import massgov.pfml.fineos.factory as fineos_factory
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


def register_employee(employee_ssn: int, employer_fein: int) -> Optional[str]:
    fineos_client = fineos_factory.create_client()

    # Find FINEOS employer id using employer FEIN
    try:
        employer_id = fineos_client.find_employer(employer_fein)
    except NotFound:
        return None

    # Generate external id
    employee_external_id = "pfml_api_{}".format(str(uuid.uuid4()))

    employee_registration = massgov.pfml.fineos.models.EmployeeRegistration(
        user_id=employee_external_id,
        customer_number=None,
        date_of_birth=datetime.date(1753, 1, 1),
        email=None,
        employer_id=employer_id,
        first_name=None,
        last_name=None,
        national_insurance_no=employee_ssn,
    )
    try:
        fineos_client.register_api_user(employee_registration)
    except BadRequest:
        return None

    # If successful save ExternalIdentifier in the database

    return employee_external_id

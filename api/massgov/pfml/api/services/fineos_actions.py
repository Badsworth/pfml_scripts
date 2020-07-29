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

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.applications import Application, FINEOSWebIdExt

logger = logging.get_logger(__name__)


def register_employee(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    employee_ssn: str,
    employer_fein: str,
    db_session: massgov.pfml.db.Session,
) -> Optional[str]:
    # If a FINEOS Id exists for SSN/FEIN return it.
    fineos_web_id_ext = (
        db_session.query(FINEOSWebIdExt)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier == str(employee_ssn),
            FINEOSWebIdExt.employer_fein == str(employer_fein),
        )
        .one_or_none()
    )

    if fineos_web_id_ext is not None:
        return fineos_web_id_ext.fineos_web_id

    # Find FINEOS employer id using employer FEIN
    employer_id = fineos.find_employer(employer_fein)
    logger.info("fein %s: found employer_id %s", employer_fein, employer_id)

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

    fineos.register_api_user(employee_registration)

    logger.info("registered as %s", employee_external_id)

    # If successful save ExternalIdentifier in the database
    fineos_web_id_ext = FINEOSWebIdExt()
    fineos_web_id_ext.employee_tax_identifier = employee_ssn
    fineos_web_id_ext.employer_fein = employer_fein
    fineos_web_id_ext.fineos_web_id = employee_external_id
    db_session.add(fineos_web_id_ext)

    return employee_external_id


def send_to_fineos(application: Application, db_session: massgov.pfml.db.Session) -> bool:
    """Send a completed application to FINEOS for processing."""

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    customer = build_customer_model(application)
    absence_case = build_absence_case(application)

    # Create the FINEOS client.
    fineos = massgov.pfml.fineos.create_client()

    try:
        fineos_user_id = register_employee(
            fineos, application.tax_identifier.tax_identifier, application.employer_fein, db_session
        )

        if fineos_user_id is None:
            logger.warning("register_employee did not find a match")
            return False

        fineos.update_customer_details(fineos_user_id, customer)
        new_case = fineos.start_absence(fineos_user_id, absence_case)
        fineos.complete_intake(fineos_user_id, str(new_case.notificationCaseId))

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error")
        return False

    return True


def build_customer_model(application):
    """Convert an application to a FINEOS API Customer model."""
    customer = massgov.pfml.fineos.models.customer_api.Customer(
        firstName=application.first_name,
        secondName=application.middle_name,
        lastName=application.last_name,
        dateOfBirth=application.date_of_birth,
        # We have to send back the SSN as FINEOS wipes it from the Customer otherwise.
        idNumber=application.tax_identifier.tax_identifier,
    )
    return customer


def build_absence_case(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.AbsenceCase:
    """Convert an Application to a FINEOS API AbsenceCase model."""
    leave_periods = []
    for leave_period in application.continuous_leave_periods:
        leave_periods.append(
            massgov.pfml.fineos.models.customer_api.TimeOffLeavePeriod(
                startDate=leave_period.start_date,
                endDate=leave_period.end_date,
                lastDayWorked=leave_period.start_date,
                expectedReturnToWorkDate=leave_period.end_date,
                startDateFullDay=True,
                endDateFullDay=True,
                status="Known",
            )
        )
    # Temporary workaround while API appends leave periods on each edit. TODO: remove when fixed.
    leave_periods = leave_periods[-1:]
    absence_case = massgov.pfml.fineos.models.customer_api.AbsenceCase(
        additionalComments="PFML API " + str(application.application_id),
        intakeSource="Self-Service",
        notifiedBy="Employee",
        reason="Serious Health Condition - Employee",
        reasonQualifier1="Not Work Related",
        reasonQualifier2="Sickness",
        timeOffLeavePeriods=leave_periods,
        employerNotified=application.employer_notified,
        employerNotificationDate=application.employer_notification_date,
    )
    return absence_case

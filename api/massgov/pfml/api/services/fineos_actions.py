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
import math
import mimetypes
import uuid
from typing import List, Optional

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.applications.responses import DocumentResponse
from massgov.pfml.db.models.applications import Application, FINEOSWebIdExt

logger = logging.get_logger(__name__)

# TODO: remove this workaround after Portal starts sending SSN in prod
# https://lwd.atlassian.net/browse/API-497
TEST_TAX_IDENTIFIER = "900990000"


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
    """Send an application to FINEOS for processing."""

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    customer = build_customer_model(application)
    absence_case = build_absence_case(application)

    # Create the FINEOS client.
    fineos = massgov.pfml.fineos.create_client()

    try:
        tax_identifier = TEST_TAX_IDENTIFIER
        if application.tax_identifier is not None:
            tax_identifier = application.tax_identifier.tax_identifier

        fineos_user_id = register_employee(
            fineos, tax_identifier, application.employer_fein, db_session
        )

        if fineos_user_id is None:
            logger.warning("register_employee did not find a match")
            return False

        fineos.update_customer_details(fineos_user_id, customer)
        new_case = fineos.start_absence(fineos_user_id, absence_case)

        application.fineos_absence_id = new_case.absenceId
        application.fineos_notification_case_id = new_case.notificationCaseId
        db_session.commit()

        upsert_week_based_work_pattern(fineos, fineos_user_id, application)

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error")
        return False

    return True


def complete_intake(application: Application, db_session: massgov.pfml.db.Session) -> bool:
    """Send an application to FINEOS for completion."""

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    if application.fineos_notification_case_id is None:
        raise ValueError("application.fineos_notification_case_id is None")

    fineos = massgov.pfml.fineos.create_client()

    try:
        tax_identifier = TEST_TAX_IDENTIFIER
        if application.tax_identifier is not None:
            tax_identifier = application.tax_identifier.tax_identifier

        fineos_user_id = register_employee(
            fineos, tax_identifier, application.employer_fein, db_session
        )

        if fineos_user_id is None:
            logger.warning("register_employee did not find a match")
            return False

        db_session.commit()
        fineos.complete_intake(fineos_user_id, str(application.fineos_notification_case_id))

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error")
        return False

    return True


def build_customer_model(application):
    """Convert an application to a FINEOS API Customer model."""
    tax_identifier = TEST_TAX_IDENTIFIER
    if application.tax_identifier is not None:
        tax_identifier = application.tax_identifier.tax_identifier
    customer = massgov.pfml.fineos.models.customer_api.Customer(
        firstName=application.first_name,
        secondName=application.middle_name,
        lastName=application.last_name,
        dateOfBirth=application.date_of_birth,
        # We have to send back the SSN as FINEOS wipes it from the Customer otherwise.
        idNumber=tax_identifier,
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


def upsert_week_based_work_pattern(fineos_client, user_id, application):
    """Add or update work pattern on an in progress absence case"""

    week_based_work_pattern = build_week_based_work_pattern(application)
    absence_id = application.fineos_absence_id
    occupation = fineos_client.get_absence_occupations(user_id, absence_id)[0]
    occupation_id = occupation.occupationId

    if occupation_id is None:
        raise ValueError

    try:
        fineos_client.add_week_based_work_pattern(user_id, occupation_id, week_based_work_pattern)
    except massgov.pfml.fineos.exception.FINEOSClientBadResponse as error:
        # FINEOS returns a 403 forbidden when attempting to an add a work pattern
        # for an occupation when one already exists
        if error.response_status == 403:
            fineos_client.update_week_based_work_pattern(
                user_id, occupation_id, week_based_work_pattern
            )
        else:
            raise error


def build_week_based_work_pattern(application):
    """Split hours_worked_per_week across 7 week days"""

    hours_worked_per_week = getattr(application, "hours_worked_per_week", 40)
    week_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    hours_per_day = math.floor(hours_worked_per_week / 7)
    remainder = hours_worked_per_week % 7
    minutes_remainder = round(60 * (remainder % 1))
    work_pattern_days = []

    for i, week_day in enumerate(week_days):
        hours = hours_per_day + 1 if remainder >= 1 else hours_per_day
        minutes = minutes_remainder if i == 0 else 0

        work_pattern_days.append(
            massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                dayOfWeek=week_day, weekNumber=1, hours=hours, minutes=minutes
            )
        )

        remainder -= 1

    return massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern(
        workPatternType="Fixed",
        workWeekStarts=week_days[0],
        patternStartDate=None,
        patternStatus=None,
        workPatternDays=work_pattern_days,
    )


def upload_document(
    application: Application,
    document_type: str,
    file_content: bytes,
    file_name: str,
    content_type: str,
    description: str,
    db_session: massgov.pfml.db.Session,
) -> massgov.pfml.fineos.models.customer_api.Document:
    try:
        fineos = massgov.pfml.fineos.create_client()

        tax_identifier = TEST_TAX_IDENTIFIER
        if application.tax_identifier is not None:
            tax_identifier = application.tax_identifier.tax_identifier

        employer_fein = ""
        if application.employer_fein is None:
            raise ValueError("Missing employer fein")
        employer_fein = application.employer_fein

        fineos_user_id = register_employee(fineos, tax_identifier, employer_fein, db_session)

        if fineos_user_id is None:
            logger.error("register_employee did not find a match")
            raise ValueError("register_employee did not find a match")

        absence_id = ""
        if application.fineos_absence_id is None:
            raise ValueError("Missing absence id")
        absence_id = application.fineos_absence_id

        fineos_document = fineos.upload_document(
            fineos_user_id,
            absence_id,
            document_type,
            file_content,
            file_name,
            content_type,
            description,
        )
        return fineos_document
    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS Client Exception")
        raise ValueError("FINEOS Client Exception")


def fineos_document_response_to_document_response(
    fineos_document_response: massgov.pfml.fineos.models.customer_api.Document,
    application: Application,
) -> DocumentResponse:
    user_id = application.user_id
    application_id = application.application_id
    created_at = None
    if fineos_document_response.receivedDate:
        created_at = datetime.datetime.combine(
            fineos_document_response.receivedDate, datetime.time.min
        )
    content_type, encoding = mimetypes.guess_type(fineos_document_response.originalFilename or "")

    document_response = DocumentResponse(
        user_id=user_id,
        application_id=application_id,
        created_at=created_at,
        document_type=fineos_document_response.name,
        content_type=content_type,
        fineos_document_id=fineos_document_response.documentId,
        name=fineos_document_response.originalFilename,
        description=fineos_document_response.description,
    )
    return document_response


def get_documents(
    application: Application, db_session: massgov.pfml.db.Session
) -> List[DocumentResponse]:
    try:
        fineos = massgov.pfml.fineos.create_client()

        tax_identifier = TEST_TAX_IDENTIFIER
        if application.tax_identifier is not None:
            tax_identifier = application.tax_identifier.tax_identifier

        employer_fein = ""
        if application.employer_fein is None:
            raise ValueError("Missing employer fein")
        employer_fein = application.employer_fein

        fineos_user_id = register_employee(fineos, tax_identifier, employer_fein, db_session)

        if fineos_user_id is None:
            logger.error("register_employee did not find a match")
            raise ValueError("register_employee did not find a match")

        absence_id = ""
        if application.fineos_absence_id is None:
            raise ValueError("Missing absence id")
        absence_id = application.fineos_absence_id

        fineos_documents = fineos.get_documents(fineos_user_id, absence_id)
        document_responses = list(
            map(
                lambda fd: fineos_document_response_to_document_response(fd, application),
                fineos_documents,
            )
        )
        return document_responses
    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS Client Exception")
        raise ValueError("FINEOS Client Exception")

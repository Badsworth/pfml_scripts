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
import mimetypes
import uuid
from typing import List, Optional, Set

import phonenumbers

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.applications.responses import DocumentResponse
from massgov.pfml.api.util.response import Issue, IssueType
from massgov.pfml.db.models.applications import (
    Application,
    Document,
    DocumentType,
    FINEOSWebIdExt,
    LeaveReason,
    LeaveReasonQualifier,
    RelationshipQualifier,
    RelationshipToCaregiver,
)
from massgov.pfml.db.models.employees import Address, Country, Employer, PaymentMethod
from massgov.pfml.util.datetime import convert_minutes_to_hours_minutes

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

    try:
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
    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error while attempting to register employee/fineos api user.")
        return None

    # If successful save ExternalIdentifier in the database
    fineos_web_id_ext = FINEOSWebIdExt()
    fineos_web_id_ext.employee_tax_identifier = employee_ssn
    fineos_web_id_ext.employer_fein = employer_fein
    fineos_web_id_ext.fineos_web_id = employee_external_id
    db_session.add(fineos_web_id_ext)

    return employee_external_id


def send_to_fineos(application: Application, db_session: massgov.pfml.db.Session) -> List[Issue]:
    """Send an application to FINEOS for processing."""

    issues = []

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    customer = build_customer_model(application)
    absence_case = build_absence_case(application)
    contact_details = build_contact_details(application)

    # Create the FINEOS client.
    fineos = massgov.pfml.fineos.create_client()

    try:
        tax_identifier = application.tax_identifier.tax_identifier

        fineos_user_id = register_employee(
            fineos, tax_identifier, application.employer_fein, db_session
        )

        if fineos_user_id is None:
            logger.warning("register_employee did not find a match")
            return [
                Issue(
                    IssueType.fineos_case_creation_issues, "register_employee did not find a match"
                )
            ]

        fineos.update_customer_details(fineos_user_id, customer)
        new_case = fineos.start_absence(fineos_user_id, absence_case)

        application.fineos_absence_id = new_case.absenceId
        application.fineos_notification_case_id = new_case.notificationCaseId

        updated_contact_details = fineos.update_customer_contact_details(
            fineos_user_id, contact_details
        )
        phone_numbers = updated_contact_details.phoneNumbers
        if phone_numbers is not None and len(phone_numbers) > 0:
            application.phone.fineos_phone_id = phone_numbers[0].id

        db_session.commit()

        if application.leave_reason_qualifier_id in [
            LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id,
            LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
            LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
        ]:
            reflexive_question = build_bonding_date_reflexive_question(application)
            fineos.update_reflexive_questions(
                fineos_user_id, application.fineos_absence_id, reflexive_question
            )

        occupation = get_occupation(fineos, fineos_user_id, application)
        upsert_week_based_work_pattern(fineos, fineos_user_id, application, occupation.occupationId)
        update_occupation_details(fineos, application, occupation.occupationId)

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error")
        issues.append(
            Issue(
                IssueType.fineos_case_error,
                "Unexpected error encountered when submitting to the Claims Processing System",
            )
        )

    return issues


def complete_intake(application: Application, db_session: massgov.pfml.db.Session) -> List[Issue]:
    """Send an application to FINEOS for completion."""

    issues = []

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    if application.fineos_notification_case_id is None:
        raise ValueError("application.fineos_notification_case_id is None")

    fineos = massgov.pfml.fineos.create_client()

    try:
        tax_identifier = application.tax_identifier.tax_identifier

        fineos_user_id = register_employee(
            fineos, tax_identifier, application.employer_fein, db_session
        )

        if not fineos_user_id:
            logger.warning("register_employee did not find a match")
            return [
                Issue(
                    IssueType.fineos_case_creation_issues, "register_employee did not find a match"
                )
            ]

        fineos_user_id = str(fineos_user_id)
        db_session.commit()
        fineos.complete_intake(fineos_user_id, str(application.fineos_notification_case_id))

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error")
        issues.append(
            Issue(
                IssueType.fineos_case_error,
                "Unexpected error encountered when submitting to the Claims Processing System",
            )
        )

    return issues


DOCUMENT_TYPES_ASSOCIATED_WITH_EVIDENCE = (
    DocumentType.IDENTIFICATION_PROOF.document_type_id,
    DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_id,
)


def mark_documents_as_received(
    application: Application, db_session: massgov.pfml.db.Session
) -> bool:
    """Mark documents attached to an application as received in FINEOS."""

    if application.fineos_absence_id is None:
        raise ValueError("application.fineos_absence_id is None")

    try:
        fineos = massgov.pfml.fineos.create_client()
        fineos_user_id = get_or_register_employee_fineos_user_id(fineos, application, db_session)

        documents = (
            db_session.query(Document)
            .filter(Document.application_id == application.application_id)
            .filter(Document.document_type_id.in_(DOCUMENT_TYPES_ASSOCIATED_WITH_EVIDENCE))
        )
        for document in documents:
            if document.fineos_id is None:
                logger.error(
                    "Document does not have a fineos_id",
                    extra={"document_id": document.document_id},
                )
                return False

            fineos.mark_document_as_received(
                fineos_user_id, str(application.fineos_absence_id), str(document.fineos_id)
            )
    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS API error")
        return False

    return True


def mark_single_document_as_received(
    application: Application, document: Document, db_session: massgov.pfml.db.Session
) -> None:
    if document.document_type_id not in DOCUMENT_TYPES_ASSOCIATED_WITH_EVIDENCE:
        return None

    if application.fineos_absence_id is None:
        raise ValueError("application.fineos_absence_id is None")

    if document.fineos_id is None:
        raise ValueError("document.fineos_id is None")

    try:
        fineos = massgov.pfml.fineos.create_client()
        fineos_user_id = get_or_register_employee_fineos_user_id(fineos, application, db_session)
        fineos.mark_document_as_received(
            fineos_user_id, str(application.fineos_absence_id), str(document.fineos_id)
        )
    except Exception:
        logger.exception("FINEOS API error")
        raise ValueError("FINEOS API error")


def build_customer_model(application):
    """Convert an application to a FINEOS API Customer model."""
    tax_identifier = application.tax_identifier.tax_identifier
    mass_id = massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
        name="MassachusettsID", stringValue=application.mass_id or ""
    )
    confirmed = massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
        name="Confirmed", booleanValue=True
    )
    customer = massgov.pfml.fineos.models.customer_api.Customer(
        firstName=application.first_name,
        secondName=application.middle_name,
        lastName=application.last_name,
        dateOfBirth=application.date_of_birth,
        # We have to send back the SSN as FINEOS wipes it from the Customer otherwise.
        idNumber=tax_identifier,
        classExtensionInformation=[mass_id, confirmed,],
    )

    # API-394: Residential address is added using updateCustomerDetails endpoint,
    # but mailing address (if different from residential address) is added using
    # the addPaymentPreference or updatePaymentPreference endpoints
    if application.residential_address is not None:
        customer.customerAddress = build_customer_address(application.residential_address)
    return customer


def build_contact_details(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.ContactDetails:
    """Convert an application's email and phone number to FINEOS API ContactDetails model."""

    contact_details = massgov.pfml.fineos.models.customer_api.ContactDetails(
        emailAddresses=[
            massgov.pfml.fineos.models.customer_api.EmailAddress(
                emailAddress=application.user.email_address
            )
        ]
    )

    phone_number = phonenumbers.parse(application.phone.phone_number)

    phone_number_type = application.phone.phone_type_instance.phone_type_description
    int_code = phone_number.country_code
    telephone_no = phone_number.national_number
    area_code = None

    # For US numbers, set the area code separately
    if int_code == 1:
        area_code = str(telephone_no)[:3]
        telephone_no = str(telephone_no)[-7:]

    contact_details.phoneNumbers = [
        massgov.pfml.fineos.models.customer_api.PhoneNumber(
            areaCode=area_code,
            id=application.phone.fineos_phone_id,
            intCode=int_code,
            telephoneNo=telephone_no,
            phoneNumberType=phone_number_type,
        )
    ]

    return contact_details


def build_customer_address(
    application_address: Address,
) -> massgov.pfml.fineos.models.customer_api.CustomerAddress:
    """ Convert an application's address into a FINEOS API CustomerAddress model."""
    # Note: In the FINEOS model:
    # - addressLine1 = Address Line 1
    # - addressLine2 = Address Line 2
    # - addressLine3 = Unknown. Do not use
    # - addressLine4 = City
    # - addressLine5 = Unknown. Do not use
    # - addressLine6 = State
    address = massgov.pfml.fineos.models.customer_api.Address(
        addressLine1=application_address.address_line_one,
        addressLine2=application_address.address_line_two,
        addressLine4=application_address.city,
        addressLine6=application_address.geo_state.geo_state_description,
        postCode=application_address.zip_code,
        country=Country.USA.country_description,
    )
    customer_address = massgov.pfml.fineos.models.customer_api.CustomerAddress(address=address)
    return customer_address


def determine_absence_period_status(application: Application) -> str:
    absence_period_status = ""
    known = massgov.pfml.fineos.models.customer_api.AbsencePeriodStatus.KNOWN.value
    estimated = massgov.pfml.fineos.models.customer_api.AbsencePeriodStatus.ESTIMATED.value

    pregnancy_maternity_reason_id = LeaveReason.PREGNANCY_MATERNITY.leave_reason_id
    serious_health_condition_reason_id = (
        LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
    )

    if application.leave_reason.leave_reason_id in [
        pregnancy_maternity_reason_id,
        serious_health_condition_reason_id,
    ]:

        return known

    elif application.leave_reason.leave_reason_id == LeaveReason.CHILD_BONDING.leave_reason_id:
        if application.has_future_child_date:
            absence_period_status = estimated
        else:
            absence_period_status = known

    return absence_period_status


def build_absence_case(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.AbsenceCase:
    """Convert an Application to a FINEOS API AbsenceCase model."""
    continuous_leave_periods = []

    for leave_period in application.continuous_leave_periods:
        # determine the status of the absence period
        absence_period_status = determine_absence_period_status(application)

        continuous_leave_periods.append(
            massgov.pfml.fineos.models.customer_api.TimeOffLeavePeriod(
                startDate=leave_period.start_date,
                endDate=leave_period.end_date,
                lastDayWorked=leave_period.start_date,
                expectedReturnToWorkDate=leave_period.end_date,
                startDateFullDay=True,
                endDateFullDay=True,
                status=absence_period_status,
            )
        )

    reduced_schedule_leave_periods = []
    for reduced_leave_period in application.reduced_schedule_leave_periods:
        [
            monday_hours_minutes,
            tuesday_hours_minutes,
            wednesday_hours_minutes,
            thursday_hours_minutes,
            friday_hours_minutes,
            saturday_hours_minutes,
            sunday_hours_minutes,
        ] = map(
            convert_minutes_to_hours_minutes,
            [
                reduced_leave_period.monday_off_minutes,
                reduced_leave_period.tuesday_off_minutes,
                reduced_leave_period.wednesday_off_minutes,
                reduced_leave_period.thursday_off_minutes,
                reduced_leave_period.friday_off_minutes,
                reduced_leave_period.saturday_off_minutes,
                reduced_leave_period.sunday_off_minutes,
            ],
        )

        # determine the status of the absence period
        absence_period_status = determine_absence_period_status(application)

        reduced_schedule_leave_periods.append(
            massgov.pfml.fineos.models.customer_api.ReducedScheduleLeavePeriod(
                startDate=reduced_leave_period.start_date,
                endDate=reduced_leave_period.end_date,
                status=absence_period_status,
                mondayOffHours=monday_hours_minutes.hours,
                mondayOffMinutes=monday_hours_minutes.minutes,
                tuesdayOffHours=tuesday_hours_minutes.hours,
                tuesdayOffMinutes=tuesday_hours_minutes.minutes,
                wednesdayOffHours=wednesday_hours_minutes.hours,
                wednesdayOffMinutes=wednesday_hours_minutes.minutes,
                thursdayOffHours=thursday_hours_minutes.hours,
                thursdayOffMinutes=thursday_hours_minutes.minutes,
                fridayOffHours=friday_hours_minutes.hours,
                fridayOffMinutes=friday_hours_minutes.minutes,
                saturdayOffHours=saturday_hours_minutes.hours,
                saturdayOffMinutes=saturday_hours_minutes.minutes,
                sundayOffHours=sunday_hours_minutes.hours,
                sundayOffMinutes=sunday_hours_minutes.minutes,
            )
        )

    intermittent_leave_periods = []
    for int_leave_period in application.intermittent_leave_periods:
        intermittent_leave_periods.append(
            massgov.pfml.fineos.models.customer_api.EpisodicLeavePeriod(
                startDate=int_leave_period.start_date,
                endDate=int_leave_period.end_date,
                frequency=int_leave_period.frequency,
                frequencyInterval=int_leave_period.frequency_interval,
                frequencyIntervalBasis=int_leave_period.frequency_interval_basis,
                duration=int_leave_period.duration,
                durationBasis=int_leave_period.duration_basis,
            )
        )

    # Leave Reason and Leave Reason Qualifier mapping.
    # Relationship and Relationship Qualifier mapping.
    reason = reason_qualifier_1 = reason_qualifier_2 = None
    primary_relationship = primary_rel_qualifier_1 = primary_rel_qualifier_2 = None

    if application.leave_reason_id == LeaveReason.PREGNANCY_MATERNITY.leave_reason_id or (
        application.leave_reason_id == LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
        and application.pregnant_or_recent_birth
    ):
        reason = LeaveReason.PREGNANCY_MATERNITY.leave_reason_description
        reason_qualifier_1 = (
            LeaveReasonQualifier.POSTNATAL_DISABILITY.leave_reason_qualifier_description
        )

    elif (
        application.leave_reason_id == LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
    ):
        reason = LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description
        reason_qualifier_1 = (
            LeaveReasonQualifier.NOT_WORK_RELATED.leave_reason_qualifier_description
        )
        reason_qualifier_2 = LeaveReasonQualifier.SICKNESS.leave_reason_qualifier_description

    elif application.leave_reason_id == LeaveReason.CHILD_BONDING.leave_reason_id:
        reason = application.leave_reason.leave_reason_description
        reason_qualifier = application.leave_reason_qualifier
        reason_qualifier_1 = application.leave_reason_qualifier.leave_reason_qualifier_description
        primary_relationship = RelationshipToCaregiver.CHILD.relationship_to_caregiver_description

        if (
            reason_qualifier.leave_reason_qualifier_id
            == LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id
        ):
            primary_rel_qualifier_1 = (
                RelationshipQualifier.ADOPTED.relationship_qualifier_description
            )
        elif (
            reason_qualifier.leave_reason_qualifier_id
            == LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id
        ):
            primary_rel_qualifier_1 = (
                RelationshipQualifier.FOSTER.relationship_qualifier_description
            )
        else:
            primary_rel_qualifier_1 = (
                RelationshipQualifier.BIOLOGICAL.relationship_qualifier_description
            )

    else:
        raise ValueError("Invalid application.leave_reason")

    absence_case = massgov.pfml.fineos.models.customer_api.AbsenceCase(
        additionalComments="PFML API " + str(application.application_id),
        intakeSource="Self-Service",
        notifiedBy="Employee",
        reason=reason,
        reasonQualifier1=reason_qualifier_1,
        reasonQualifier2=reason_qualifier_2,
        timeOffLeavePeriods=continuous_leave_periods if continuous_leave_periods else None,
        reducedScheduleLeavePeriods=reduced_schedule_leave_periods
        if reduced_schedule_leave_periods
        else None,
        episodicLeavePeriods=intermittent_leave_periods if intermittent_leave_periods else None,
        employerNotified=application.employer_notified,
        employerNotificationDate=application.employer_notification_date,
        primaryRelationship=primary_relationship,
        primaryRelQualifier1=primary_rel_qualifier_1,
        primaryRelQualifier2=primary_rel_qualifier_2,
    )
    return absence_case


def get_or_register_employee_fineos_user_id(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    application: Application,
    db_session: massgov.pfml.db.Session,
) -> str:
    tax_identifier = application.tax_identifier.tax_identifier

    employer_fein = ""
    if application.employer_fein is None:
        raise ValueError("Missing employer fein")
    employer_fein = application.employer_fein

    fineos_user_id = register_employee(fineos, tax_identifier, employer_fein, db_session)

    if fineos_user_id is None:
        logger.error("register_employee did not find a match")
        raise ValueError("register_employee did not find a match")

    return fineos_user_id


def get_fineos_absence_id_from_application(application: Application) -> str:
    if application.fineos_absence_id is None:
        raise ValueError("Missing absence id")

    return application.fineos_absence_id


def build_bonding_date_reflexive_question(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.AdditionalInformation:
    if (
        application.leave_reason_qualifier_id
        == LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id
    ):
        field_name = "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions.dateOfBirth"
        date_value = application.child_birth_date
    else:
        field_name = "PlacementQuestionGroup.placementQuestions.adoptionDate"
        date_value = application.child_placement_date

    reflexive_details = massgov.pfml.fineos.models.customer_api.Attribute(
        fieldName=field_name, dateValue=date_value,
    )
    reflexive_question = massgov.pfml.fineos.models.customer_api.AdditionalInformation(
        reflexiveQuestionLevel="reason", reflexiveQuestionDetails=[reflexive_details],
    )
    return reflexive_question


def get_occupation(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient, user_id: str, application: Application
) -> massgov.pfml.fineos.models.customer_api.ReadCustomerOccupation:
    return fineos_client.get_case_occupations(
        user_id, str(application.fineos_notification_case_id)
    )[0]


def upsert_week_based_work_pattern(fineos_client, user_id, application, occupation_id):
    """Add or update work pattern on an in progress absence case"""
    if occupation_id is None:
        raise ValueError

    try:
        week_based_work_pattern = build_week_based_work_pattern(application)
        fineos_client.add_week_based_work_pattern(user_id, occupation_id, week_based_work_pattern)
    except massgov.pfml.fineos.exception.FINEOSClientBadResponse as error:
        # FINEOS returns 403 when attempting to add a work pattern for an occupation when one already exists.
        if error.response_status == 403:
            fineos_client.update_week_based_work_pattern(
                user_id, occupation_id, week_based_work_pattern
            )
        else:
            raise error


def update_occupation_details(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient,
    application: Application,
    occupation_id: Optional[int],
) -> None:
    if occupation_id is None:
        raise ValueError("occupation_id is None")

    employment_status_label = None
    if application.employment_status:
        employment_status_label = application.employment_status.fineos_label

    fineos_client.update_occupation(
        occupation_id, employment_status_label, application.hours_worked_per_week,
    )


def build_week_based_work_pattern(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern:
    """Construct FINEOS customer api work pattern models from application"""
    fineos_work_pattern_days = []

    for day in application.work_pattern.work_pattern_days:
        (hours, minutes) = convert_minutes_to_hours_minutes(day.minutes or 0)

        fineos_work_pattern_days.append(
            massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                dayOfWeek=day.day_of_week.day_of_week_description,
                weekNumber=1,
                hours=hours,
                minutes=minutes,
            )
        )

    return massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern(
        # FINEOS does not support Variable work patterns.
        # We capture variable work patterns as average hours worked per week,
        # split the hours evenly across 7 work pattern days, and send the days to
        # FINEOS as a Fixed pattern
        # TODO (CP-1377): Record variable work pattern somewhere in FINEOS
        workPatternType="Fixed",
        workWeekStarts="Sunday",
        patternStartDate=None,
        patternStatus=None,
        workPatternDays=fineos_work_pattern_days,
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

        fineos_user_id = get_or_register_employee_fineos_user_id(fineos, application, db_session)
        absence_id = get_fineos_absence_id_from_application(application)

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
        created_at = fineos_document_response.receivedDate
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

        fineos_user_id = get_or_register_employee_fineos_user_id(fineos, application, db_session)
        absence_id = get_fineos_absence_id_from_application(application)

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


def build_payment_preference(
    application: Application,
    payment_address: Optional[massgov.pfml.fineos.models.customer_api.CustomerAddress],
) -> massgov.pfml.fineos.models.customer_api.NewPaymentPreference:
    payment_preference = application.payment_preference
    override_postal_addr = True if payment_address else None
    if payment_preference.payment_method_id == PaymentMethod.ACH.payment_method_id:
        account_details = massgov.pfml.fineos.models.customer_api.AccountDetails(
            accountName=f"{application.first_name} {application.last_name}",
            accountNo=payment_preference.account_number,
            routingNumber=payment_preference.routing_number,
            accountType=payment_preference.bank_account_type.bank_account_type_description,
        )
        fineos_payment_preference = massgov.pfml.fineos.models.customer_api.NewPaymentPreference(
            paymentMethod=PaymentMethod.ACH.payment_method_description,
            isDefault=True,
            customerAddress=payment_address,
            accountDetails=account_details,
            overridePostalAddress=override_postal_addr,
        )
    elif payment_preference.payment_method_id == PaymentMethod.CHECK.payment_method_id:
        fineos_payment_preference = massgov.pfml.fineos.models.customer_api.NewPaymentPreference(
            paymentMethod=PaymentMethod.CHECK.payment_method_description,
            isDefault=True,
            customerAddress=payment_address,
            chequeDetails=massgov.pfml.fineos.models.customer_api.ChequeDetails(),
            overridePostalAddress=override_postal_addr,
        )
    else:
        raise ValueError("Invalid application.payment_preference.payment_method")
    return fineos_payment_preference


def submit_payment_preference(
    application: Application, db_session: massgov.pfml.db.Session
) -> massgov.pfml.fineos.models.customer_api.PaymentPreferenceResponse:
    try:
        fineos = massgov.pfml.fineos.create_client()
        fineos_user_id = get_or_register_employee_fineos_user_id(fineos, application, db_session)
        if application.has_mailing_address and application.mailing_address:
            fineos_payment_addr: Optional[
                massgov.pfml.fineos.models.customer_api.CustomerAddress
            ] = build_customer_address(application.mailing_address)
        else:
            fineos_payment_addr = None
        fineos_payment_preference = build_payment_preference(application, fineos_payment_addr)
        return fineos.add_payment_preference(fineos_user_id, fineos_payment_preference)

    except massgov.pfml.fineos.FINEOSClientError:
        raise ValueError("FINEOS Client Exception")


def download_document(
    application: Application, fineos_document_id: str, db_session: massgov.pfml.db.Session
) -> massgov.pfml.fineos.models.customer_api.Base64EncodedFileData:
    try:
        fineos = massgov.pfml.fineos.create_client()

        fineos_user_id = get_or_register_employee_fineos_user_id(fineos, application, db_session)
        absence_id = get_fineos_absence_id_from_application(application)

        return fineos.download_document(fineos_user_id, absence_id, fineos_document_id)

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS Client Exception")
        raise ValueError("FINEOS Client Exception")


def create_or_update_employer(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient, employer: Employer,
) -> int:
    # Determine if operation is create or update by seeing if the API Employer
    # record has a fineos_employer_id already.
    is_create = employer.fineos_employer_id is None

    employer_request_body = massgov.pfml.fineos.models.CreateOrUpdateEmployer(
        # `fineos_customer_nbr` is used as the Organization's CustomerNo
        # attribute for the request, which FINOES uses to determine if this is a
        # create or update on their end.
        fineos_customer_nbr=str(employer.employer_id),
        employer_fein=employer.employer_fein,
        employer_legal_name=employer.employer_name,
        employer_dba=employer.employer_dba,
    )

    fineos_customer_nbr, fineos_employer_id = fineos.create_or_update_employer(
        employer_request_body
    )

    logger.debug(
        f"{'Created' if is_create else 'Updated'} employer in FINEOS",
        extra={
            "is_create": is_create,
            "internal_employer_id": employer.employer_id,
            "fineos_customer_nbr": fineos_customer_nbr,
            "fineos_employer_id": fineos_employer_id,
        },
    )

    employer.fineos_employer_id = fineos_employer_id

    return fineos_employer_id


def create_service_agreement_for_employer(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient, employer: Employer
) -> str:
    if not employer.fineos_employer_id:
        raise ValueError(
            "An Employer must have a fineos_employer_id in order to create a service agreement."
        )

    family_exemption = bool(employer.family_exemption)
    medical_exemption = bool(employer.medical_exemption)
    leave_plans = resolve_leave_plans(family_exemption, medical_exemption)

    fineos_service_agreement_id = fineos.create_service_agreement_for_employer(
        employer.fineos_employer_id, ", ".join(leave_plans)
    )

    return fineos_service_agreement_id


def resolve_leave_plans(family_exemption: bool, medical_exemption: bool) -> Set[str]:
    # Logic to set leave plan list
    if family_exemption:
        if medical_exemption:
            leave_plans: set = set("")
        else:
            leave_plans = {"MA PFML - Employee"}
    else:
        if medical_exemption:
            leave_plans = {"MA PFML - Family", "MA PFML - Military Care"}
        else:
            leave_plans = {
                "MA PFML - Employee",
                "MA PFML - Family",
                "MA PFML - Military Care",
            }

    return leave_plans

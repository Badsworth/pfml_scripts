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
from enum import Enum
from itertools import chain
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import phonenumbers

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.applications.common import LeaveReason as LeaveReasonApi
from massgov.pfml.api.models.applications.common import OtherIncome
from massgov.pfml.api.models.applications.responses import DocumentResponse
from massgov.pfml.api.models.claims.responses import AbsencePeriodStatusResponse
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave
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
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    Country,
    Employee,
    Employer,
    PaymentMethod,
    TaxIdentifier,
    User,
)
from massgov.pfml.fineos.exception import FINEOSClientError, FINEOSForbidden, FINEOSNotFound
from massgov.pfml.fineos.models import CreateOrUpdateServiceAgreement
from massgov.pfml.fineos.models.customer_api import (
    AbsenceDetails,
    Base64EncodedFileData,
    ReflexiveQuestionType,
)
from massgov.pfml.fineos.transforms.to_fineos.base import EFormBody
from massgov.pfml.fineos.transforms.to_fineos.eforms.employee import (
    OtherIncomesEFormBuilder,
    PreviousLeavesEFormBuilder,
)
from massgov.pfml.util.datetime import convert_minutes_to_hours_minutes
from massgov.pfml.util.logging.applications import get_application_log_attributes

logger = logging.get_logger(__name__)


RELATIONSHIP_REFLEXIVE_FIELD_MAPPING = {
    RelationshipToCaregiver.CHILD.relationship_to_caregiver_description: "AgeCapacityFamilyMemberQuestionGroup.familyMemberDetailsQuestions",
    RelationshipToCaregiver.GRANDCHILD.relationship_to_caregiver_description: "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions",
    RelationshipToCaregiver.GRANDPARENT.relationship_to_caregiver_description: "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions",
    RelationshipToCaregiver.INLAW.relationship_to_caregiver_description: "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions",
    RelationshipToCaregiver.PARENT.relationship_to_caregiver_description: "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions",
    RelationshipToCaregiver.SPOUSE.relationship_to_caregiver_description: "FamilyMemberDetailsQuestionGroup.familyMemberDetailsQuestions",
    RelationshipToCaregiver.SIBLING.relationship_to_caregiver_description: "FamilyMemberSiblingDetailsQuestionGroup.familyMemberDetailsQuestions",
}


class LeaveNotificationReason(str, Enum):
    PREGNANCY_BIRTH_OR_RELATED_MEDICAL_TREATMENT = "Pregnancy, birth or related medical treatment"
    BONDING_WITH_A_NEW_CHILD = "Bonding with a new child (adoption/ foster care/ newborn)"
    CARING_FOR_A_FAMILY_MEMBER = "Caring for a family member"
    ACCIDENT_OR_TREATMENT_REQUIRED = "Accident or treatment required for an injury"
    SICKNESS_TREATMENT_REQUIRED_FOR_MEDICAL_CONDITION = (
        "Sickness, treatment required for a medical condition or any other medical procedure"
    )
    OUT_OF_WORK_FOR_ANOTHER_REASON = "Out of work for another reason"


def register_employee(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    employee_ssn: str,
    employer_fein: str,
    db_session: massgov.pfml.db.Session,
) -> str:
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
        # This should never happen and we should have a db constraint,
        # but keep mypy happy for now.
        #
        # We don't have a non-sensitive identifier for fineos_web_id_ext so just log
        # that something's wrong and have someone take a look at it.
        if fineos_web_id_ext.fineos_web_id is None:
            raise ValueError("fineos_web_id_ext is missing a fineos_web_id")

        return fineos_web_id_ext.fineos_web_id

    # Find FINEOS employer id using employer FEIN
    employer_id = fineos.find_employer(employer_fein)
    logger.info("found employer_id %s", employer_id)

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


def send_to_fineos(
    application: Application, db_session: massgov.pfml.db.Session, current_user: Optional[User]
) -> None:
    """Send an application to FINEOS for processing."""

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    customer = build_customer_model(application, current_user)
    absence_case = build_absence_case(application)
    contact_details = build_contact_details(application)
    tax_identifier = application.tax_identifier.tax_identifier

    # Create the FINEOS client.
    fineos = massgov.pfml.fineos.create_client()

    fineos_web_id = register_employee(fineos, tax_identifier, application.employer_fein, db_session)

    fineos.update_customer_details(fineos_web_id, customer)

    occupation = get_customer_occupation(fineos, fineos_web_id, customer.idNumber)
    if occupation is None:
        logger.error(
            "Did not find customer occupation.", extra={"fineos_web_id": fineos_web_id,},
        )

        raise ValueError("customer occupation is None")

    upsert_week_based_work_pattern(fineos, fineos_web_id, application, occupation.occupationId)
    update_occupation_details(fineos, application, str(occupation.occupationId))

    new_case = fineos.start_absence(fineos_web_id, absence_case)

    employee = (
        db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == tax_identifier)
        .one_or_none()
    )
    employer = (
        db_session.query(Employer)
        .filter(Employer.employer_fein == application.employer_fein)
        .one_or_none()
    )

    # Create a claim here since it's the earliest place we can
    # begin surfacing the claim information to leave admins,
    # and most importantly the Claim is how the Application
    # references the fineos_absence_id, which is shown to
    # the Claimant once they have an absence case created
    new_claim = Claim(
        fineos_absence_id=new_case.absenceId,
        fineos_notification_id=new_case.notificationCaseId,
        absence_period_start_date=new_case.startDate,
        absence_period_end_date=new_case.endDate,
    )
    if employee:
        new_claim.employee = employee
    else:
        logger.warning(
            "Did not find Employee to associate to Claim.",
            extra={
                "absence_case_id": new_case.absenceId,
                "application.absence_case_id": new_case.absenceId,
                "application.application_id": application.application_id,
            },
        )
    if employer:
        new_claim.employer = employer
    else:
        logger.warning(
            "Did not find Employer to associate to Claim.",
            extra={
                "absence_case_id": new_case.absenceId,
                "application.absence_case_id": new_case.absenceId,
                "application.application_id": application.application_id,
            },
        )

    if application.leave_reason_id:
        new_claim.claim_type_id = application.leave_reason.absence_to_claim_type

    application.claim = new_claim

    updated_contact_details = fineos.update_customer_contact_details(fineos_web_id, contact_details)
    phone_numbers = updated_contact_details.phoneNumbers
    if phone_numbers is not None and len(phone_numbers) > 0:
        application.phone.fineos_phone_id = phone_numbers[0].id

    # Reflexive questions for bonding and caring leave
    # "The reflexive questions allows to update additional information of an absence case leave request."
    # Source - https://documentation.fineos.com/support/documentation/customer-swagger-21.1.html#operation/createReflexiveQuestions
    if application.leave_reason_qualifier_id in [
        LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id,
        LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
        LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
    ]:
        reflexive_question = build_bonding_date_reflexive_question(application)
        fineos.update_reflexive_questions(
            fineos_web_id, application.claim.fineos_absence_id, reflexive_question
        )

    if application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id:
        reflexive_question = build_caring_leave_reflexive_question(application)
        fineos.update_reflexive_questions(
            fineos_web_id, application.claim.fineos_absence_id, reflexive_question
        )

    db_session.add(application)
    db_session.add(new_claim)
    db_session.commit()


def complete_intake(application: Application, db_session: massgov.pfml.db.Session) -> None:
    """Send an application to FINEOS for completion."""

    if application.employer_fein is None:
        raise ValueError("application.employer_fein is None")

    if application.claim.fineos_notification_id is None:
        raise ValueError("application.claim.fineos_notification_id is None")

    fineos = massgov.pfml.fineos.create_client()

    tax_identifier = application.tax_identifier.tax_identifier

    fineos_web_id = register_employee(fineos, tax_identifier, application.employer_fein, db_session)

    fineos_web_id = str(fineos_web_id)
    db_session.commit()
    fineos.complete_intake(fineos_web_id, str(application.claim.fineos_notification_id))


DOCUMENT_TYPES_ASSOCIATED_WITH_EVIDENCE = (
    DocumentType.IDENTIFICATION_PROOF.document_type_id,
    DocumentType.STATE_MANAGED_PAID_LEAVE_CONFIRMATION.document_type_id,
    DocumentType.OWN_SERIOUS_HEALTH_CONDITION_FORM.document_type_id,
    DocumentType.PREGNANCY_MATERNITY_FORM.document_type_id,
    DocumentType.CHILD_BONDING_EVIDENCE_FORM.document_type_id,
    DocumentType.CARE_FOR_A_FAMILY_MEMBER_FORM.document_type_id,
    DocumentType.MILITARY_EXIGENCY_FORM.document_type_id,
)


def document_log_attrs(doc: Document) -> Dict[str, Any]:
    return {
        "document_id": doc.document_id,
        "document.document_type": doc.document_type_instance.document_type_description,
    }


def mark_documents_as_received(
    application: Application, db_session: massgov.pfml.db.Session
) -> None:
    """Mark documents attached to an application as received in FINEOS."""

    if application.claim.fineos_absence_id is None:
        raise ValueError("application.claim.fineos_absence_id is None")

    fineos = massgov.pfml.fineos.create_client()
    fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)

    documents = (
        db_session.query(Document)
        .filter(Document.application_id == application.application_id)
        .filter(Document.document_type_id.in_(DOCUMENT_TYPES_ASSOCIATED_WITH_EVIDENCE))
    )

    exception_count = 0
    for document in documents:
        if document.fineos_id is None:
            logger.warning(
                "Document does not have a fineos_id", extra={**document_log_attrs(document)},
            )
            raise ValueError("Document does not have a fineos_id")

        try:
            fineos.mark_document_as_received(
                fineos_web_id, str(application.claim.fineos_absence_id), str(document.fineos_id)
            )
        except FINEOSClientError as ex:
            exception_count += 1
            logger.warning(
                "Unable to mark document as received",
                extra={**document_log_attrs(document)},
                exc_info=ex,
            )
    if exception_count > 0:
        raise RuntimeError


def mark_single_document_as_received(
    application: Application, document: Document, db_session: massgov.pfml.db.Session
) -> None:
    if document.document_type_id not in DOCUMENT_TYPES_ASSOCIATED_WITH_EVIDENCE:
        return None

    if application.claim.fineos_absence_id is None:
        raise ValueError("application.claim.fineos_absence_id is None")

    if document.fineos_id is None:
        raise ValueError("document.fineos_id is None")

    fineos = massgov.pfml.fineos.create_client()
    try:
        fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)
        fineos.mark_document_as_received(
            fineos_web_id, str(application.claim.fineos_absence_id), str(document.fineos_id)
        )
    except FINEOSClientError as ex:
        logger.warning(
            "Unable to mark document as received",
            extra={**document_log_attrs(document)},
            exc_info=ex,
        )
        raise


def build_customer_model(application, current_user):
    """Convert an application to a FINEOS API Customer model."""
    tax_identifier = application.tax_identifier.tax_identifier
    mass_id = massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
        name="MassachusettsID", stringValue=application.mass_id or ""
    )
    confirmed = massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
        name="Confirmed", booleanValue=True
    )
    class_ext_info = [
        mass_id,
        confirmed,
    ]
    if current_user is not None:
        consented_to_data_sharing = massgov.pfml.fineos.models.customer_api.ExtensionAttribute(
            name="ConsenttoShareData", booleanValue=current_user.consented_to_data_sharing
        )
        class_ext_info.append(consented_to_data_sharing)

    customer = massgov.pfml.fineos.models.customer_api.Customer(
        firstName=application.first_name,
        secondName=application.middle_name,
        lastName=application.last_name,
        dateOfBirth=application.date_of_birth,
        # We have to send back the SSN as FINEOS wipes it from the Customer otherwise.
        idNumber=tax_identifier,
        classExtensionInformation=class_ext_info,
    )

    # API-394: Residential address is added using updateCustomerDetails endpoint,
    # but mailing address (if different from residential address) is added using
    # the addPaymentPreference or updatePaymentPreference endpoints
    if application.residential_address is not None:
        customer.customerAddress = build_customer_address(application.residential_address)
    if application.gender is not None:
        customer.gender = application.gender.fineos_gender_description

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
    """Convert an application's address into a FINEOS API CustomerAddress model."""
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

    if application.leave_reason.leave_reason_id in [
        LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id,
        LeaveReason.PREGNANCY_MATERNITY.leave_reason_id,
        LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id,
    ]:

        return known

    elif application.leave_reason.leave_reason_id == LeaveReason.CHILD_BONDING.leave_reason_id:
        if application.has_future_child_date:
            absence_period_status = estimated
        else:
            absence_period_status = known

    return absence_period_status


def build_leave_periods(
    application: Application,
) -> Tuple[
    List[massgov.pfml.fineos.models.customer_api.ReducedScheduleLeavePeriod],
    List[massgov.pfml.fineos.models.customer_api.EpisodicLeavePeriod],
]:
    reduced_schedule_leave_periods = []
    for reduced_leave_period in application.reduced_schedule_leave_periods:
        if not reduced_leave_period.start_date or not reduced_leave_period.end_date:
            raise ValueError("Leave periods must have a start and end date.")

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
        if not int_leave_period.start_date or not int_leave_period.end_date:
            raise ValueError("Leave periods must have a start and end date.")
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

    return reduced_schedule_leave_periods, intermittent_leave_periods


def application_reason_to_claim_reason(
    application: Application,
) -> Tuple[
    str,
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    LeaveNotificationReason,
]:
    """ Calculate a claim reason, reason qualifiers, relationship qualifiers, and notification reason
    from an application's reason and related fields. For example, an application may have have a medical
    leave reason and also have pregnant_or_recent_birth set to true which would get saved to FINEOS as a
    claim with reason set to pregnancy.
    """
    # Leave Reason and Leave Reason Qualifier mapping.
    # Relationship and Relationship Qualifier mapping.
    reason = reason_qualifier_1 = reason_qualifier_2 = None
    primary_relationship = primary_rel_qualifier_1 = primary_rel_qualifier_2 = None
    notification_reason = None

    if application.leave_reason_id == LeaveReason.PREGNANCY_MATERNITY.leave_reason_id:
        reason = LeaveReason.PREGNANCY_MATERNITY.leave_reason_description
        reason_qualifier_1 = (
            LeaveReasonQualifier.POSTNATAL_DISABILITY.leave_reason_qualifier_description
        )
        notification_reason = LeaveNotificationReason.PREGNANCY_BIRTH_OR_RELATED_MEDICAL_TREATMENT

    elif (
        application.leave_reason_id == LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id
    ):
        reason = LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_description
        reason_qualifier_1 = (
            LeaveReasonQualifier.NOT_WORK_RELATED.leave_reason_qualifier_description
        )
        reason_qualifier_2 = LeaveReasonQualifier.SICKNESS.leave_reason_qualifier_description
        notification_reason = LeaveNotificationReason.ACCIDENT_OR_TREATMENT_REQUIRED

    elif application.leave_reason_id == LeaveReason.CHILD_BONDING.leave_reason_id:
        reason = application.leave_reason.leave_reason_description
        reason_qualifier = application.leave_reason_qualifier
        reason_qualifier_1 = application.leave_reason_qualifier.leave_reason_qualifier_description
        notification_reason = LeaveNotificationReason.BONDING_WITH_A_NEW_CHILD
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

    elif application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id:
        reason = application.leave_reason.leave_reason_description
        reason_qualifier_1 = (
            LeaveReasonQualifier.SERIOUS_HEALTH_CONDITION.leave_reason_qualifier_description
        )
        notification_reason = LeaveNotificationReason.CARING_FOR_A_FAMILY_MEMBER
        primary_relationship = (
            application.caring_leave_metadata.relationship_to_caregiver.relationship_to_caregiver_description
        )

        # Map relationship to qualifiers
        # All relationships use BIOLOGICAL as qualifier_1 and have no qualifier_2 qualifier except:
        # INLAW - uses PARENT_IN_LAW as qualifier_1 and has no qualifier_2
        # SPOUSE - uses LEGALLY_MARRIED as qualifier_1 and UNDISCLOSED as qualifier_2 (this is the only relationship with a qualifier_2)
        if (
            application.caring_leave_metadata.relationship_to_caregiver_id
            == RelationshipToCaregiver.INLAW.relationship_to_caregiver_id
        ):
            primary_rel_qualifier_1 = (
                RelationshipQualifier.PARENT_IN_LAW.relationship_qualifier_description
            )

        elif (
            application.caring_leave_metadata.relationship_to_caregiver_id
            == RelationshipToCaregiver.SPOUSE.relationship_to_caregiver_id
        ):
            primary_rel_qualifier_1 = (
                RelationshipQualifier.LEGALLY_MARRIED.relationship_qualifier_description
            )
            primary_rel_qualifier_2 = (
                RelationshipQualifier.UNDISCLOSED.relationship_qualifier_description
            )

        else:
            primary_rel_qualifier_1 = (
                RelationshipQualifier.BIOLOGICAL.relationship_qualifier_description
            )

    else:
        raise ValueError("Invalid application.leave_reason")

    assert reason

    return (
        reason,
        reason_qualifier_1,
        reason_qualifier_2,
        primary_relationship,
        primary_rel_qualifier_1,
        primary_rel_qualifier_2,
        notification_reason,
    )


def build_absence_case(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.AbsenceCase:
    """Convert an Application to a FINEOS API AbsenceCase model."""
    continuous_leave_periods = []

    for leave_period in application.continuous_leave_periods:
        if not leave_period.start_date or not leave_period.end_date:
            raise ValueError("Leave periods must have a start and end date.")

        # determine the status of the absence period
        absence_period_status = determine_absence_period_status(application)

        continuous_leave_periods.append(
            massgov.pfml.fineos.models.customer_api.TimeOffLeavePeriod(
                startDate=leave_period.start_date,
                endDate=leave_period.end_date,
                startDateFullDay=True,
                endDateFullDay=True,
                status=absence_period_status,
            )
        )

    reduced_schedule_leave_periods, intermittent_leave_periods = build_leave_periods(application)

    # Leave Reason and Leave Reason Qualifier mapping.
    # Relationship and Relationship Qualifier mapping.
    (
        reason,
        reason_qualifier_1,
        reason_qualifier_2,
        primary_relationship,
        primary_rel_qualifier_1,
        primary_rel_qualifier_2,
        notification_reason,
    ) = application_reason_to_claim_reason(application)

    absence_case = massgov.pfml.fineos.models.customer_api.AbsenceCase(
        additionalComments="PFML API " + str(application.application_id),
        intakeSource="Self-Service",
        notifiedBy="Employee",
        reason=reason,
        reasonQualifier1=reason_qualifier_1,
        reasonQualifier2=reason_qualifier_2,
        notificationReason=notification_reason,
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


def get_or_register_employee_fineos_web_id(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    application: Application,
    db_session: massgov.pfml.db.Session,
) -> str:
    tax_identifier = application.tax_identifier.tax_identifier

    employer_fein = ""
    if application.employer_fein is None:
        raise ValueError("Missing employer fein")
    employer_fein = application.employer_fein

    return register_employee(fineos, tax_identifier, employer_fein, db_session)


def get_fineos_absence_id_from_application(application: Application) -> str:
    if application.claim is None:
        raise ValueError("Missing claim")

    if application.claim.fineos_absence_id is None:
        raise ValueError("Missing absence id")

    return application.claim.fineos_absence_id


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


def build_caring_leave_reflexive_question(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.AdditionalInformation:
    reflexive_question_field_name = RELATIONSHIP_REFLEXIVE_FIELD_MAPPING[
        application.caring_leave_metadata.relationship_to_caregiver.relationship_to_caregiver_description
    ]

    caring_leave_metadata = application.caring_leave_metadata

    reflexive_question_details: List[ReflexiveQuestionType] = []
    # first name
    first_name_details = massgov.pfml.fineos.models.customer_api.Attribute(
        fieldName=f"{reflexive_question_field_name}.firstName",
        stringValue=caring_leave_metadata.family_member_first_name,
    )
    reflexive_question_details.append(first_name_details)

    # middle name
    if caring_leave_metadata.family_member_middle_name:
        middle_name_details = massgov.pfml.fineos.models.customer_api.Attribute(
            fieldName=f"{reflexive_question_field_name}.middleInital",  # FINEOS API calls this field middleInital (with incorrect spelling), though it will accept a middle name
            stringValue=caring_leave_metadata.family_member_middle_name,
        )
        reflexive_question_details.append(middle_name_details)

    # last name
    last_name_name_details = massgov.pfml.fineos.models.customer_api.Attribute(
        fieldName=f"{reflexive_question_field_name}.lastName",
        stringValue=caring_leave_metadata.family_member_last_name,
    )
    reflexive_question_details.append(last_name_name_details)

    # family member date of birth
    if caring_leave_metadata.family_member_date_of_birth:
        date_of_birth_details = massgov.pfml.fineos.models.customer_api.Attribute(
            fieldName=f"{reflexive_question_field_name}.dateOfBirth",
            dateValue=caring_leave_metadata.family_member_date_of_birth,
        )
        reflexive_question_details.append(date_of_birth_details)

    reflexive_question = massgov.pfml.fineos.models.customer_api.AdditionalInformation(
        reflexiveQuestionLevel="primary relationship",
        reflexiveQuestionDetails=reflexive_question_details,
    )

    return reflexive_question


def get_customer_occupation(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient, fineos_web_id: str, customer_id: str
) -> Optional[massgov.pfml.fineos.models.customer_api.ReadCustomerOccupation]:
    logger.info("getting occupation for customer %s", customer_id)
    try:
        # fineos_web_id is associated with a specific employee and employer, so this will only return the occupations for the employee from the associated employer
        occupations = fineos_client.get_customer_occupations_customer_api(
            fineos_web_id, customer_id
        )
        return occupations[0]
    except Exception as error:
        logger.warning(
            "get_customer_occuption failure",
            extra={"customer_id": customer_id, "status": getattr(error, "response_status", None),},
            exc_info=True,
        )
        raise error


def get_occupation(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient, user_id: str, application: Application
) -> massgov.pfml.fineos.models.customer_api.ReadCustomerOccupation:
    logger.info("getting occupation for absence_case %s", application.claim.fineos_absence_id)
    try:
        return fineos_client.get_case_occupations(
            user_id, str(application.claim.fineos_notification_id)
        )[0]
    except Exception as error:
        logger.warning(
            "get_occuption failure",
            extra={
                "absence_case_id": application.claim.fineos_absence_id,
                "application.absence_case_id": application.claim.fineos_absence_id,
                "application.application_id": application.application_id,
                "status": getattr(error, "response_status", None),
            },
            exc_info=True,
        )
        raise error


def upsert_week_based_work_pattern(fineos_client, user_id, application, occupation_id):
    """Add or update work pattern on an in progress absence case"""
    if occupation_id is None:
        raise ValueError("occupation_id is None")

    week_based_work_pattern = build_week_based_work_pattern(application)
    log_attributes = {
        "application.application_id": application.application_id,
        "occupation_id": occupation_id,
    }

    if application.claim is not None:
        log_attributes["application.absence_case_id"] = application.claim.fineos_absence_id
        logger.info(
            "upserting work_pattern for absence case %s",
            application.claim.fineos_absence_id,
            extra=log_attributes,
        )
    else:
        logger.info(
            "upserting work_pattern for empty claim", extra=log_attributes,
        )

    try:
        add_week_based_work_pattern(
            fineos_client, user_id, occupation_id, week_based_work_pattern, log_attributes
        )

        logger.info(
            "added work_pattern successfully for customer occupation %s",
            occupation_id,
            extra=log_attributes,
        )

    except massgov.pfml.fineos.exception.FINEOSClientBadResponse as error:
        # FINEOS returns 403 when attempting to add a work pattern for an occupation when one already exists.
        if error.response_status == 403:
            update_week_based_work_pattern(
                fineos_client, user_id, occupation_id, week_based_work_pattern, log_attributes
            )
            if application.claim is not None:
                logger.info(
                    "updated work_pattern successfully for absence case %s",
                    application.claim.fineos_absence_id,
                    extra=log_attributes,
                )
            else:
                logger.info(
                    "updated work_pattern successfully", extra=log_attributes,
                )

        else:
            raise error


def add_week_based_work_pattern(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient,
    user_id: str,
    occupation_id: str,
    week_based_work_pattern: massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern,
    log_attributes: Optional[Dict] = None,
) -> None:
    try:
        fineos_client.add_week_based_work_pattern(user_id, occupation_id, week_based_work_pattern)
    except Exception as error:
        extra = {} if log_attributes is None else log_attributes
        extra.update({"status": getattr(error, "response_status", None)})
        logger.warning("add_week_based_work_pattern failure", extra=extra, exc_info=True)
        raise error


def update_week_based_work_pattern(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient,
    user_id: str,
    occupation_id: str,
    week_based_work_pattern: massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern,
    log_attributes: Optional[Dict] = None,
) -> None:
    try:
        fineos_client.update_week_based_work_pattern(
            user_id, occupation_id, week_based_work_pattern
        )
    except Exception as error:
        extra = {} if log_attributes is None else log_attributes
        extra.update({"status": getattr(error, "response_status", None)})
        logger.warning("update_week_based_work_pattern failure", extra=extra, exc_info=True)
        raise error


def update_occupation_details(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient,
    application: Application,
    occupation_id: Optional[str],
) -> None:
    if occupation_id is None:
        raise ValueError("occupation_id is None")

    employment_status_label = None
    if application.employment_status:
        employment_status_label = application.employment_status.fineos_label

    fineos_client.update_occupation(
        int(occupation_id), employment_status_label, application.hours_worked_per_week,
    )


def build_week_based_work_pattern(
    application: Application,
) -> massgov.pfml.fineos.models.customer_api.WeekBasedWorkPattern:
    """Construct FINEOS customer api work pattern models from application"""
    fineos_work_pattern_days = []

    for day in application.work_pattern.work_pattern_days:
        if not day.day_of_week or not day.day_of_week.day_of_week_description:
            raise ValueError("Work pattern days must include the day of the week.")

        (hours, minutes) = convert_minutes_to_hours_minutes(day.minutes or 0)

        fineos_work_pattern_days.append(
            massgov.pfml.fineos.models.customer_api.WorkPatternDay(
                dayOfWeek=day.day_of_week.day_of_week_description,
                weekNumber=1,
                hours=hours or 0,
                minutes=minutes or 0,
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
    fineos = massgov.pfml.fineos.create_client()

    fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)
    absence_id = get_fineos_absence_id_from_application(application)

    fineos_document = fineos.upload_document(
        fineos_web_id,
        absence_id,
        document_type,
        file_content,
        file_name,
        content_type,
        description,
    )
    return fineos_document


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
        fineos_document_id=str(fineos_document_response.documentId),
        name=fineos_document_response.originalFilename or "",
        description=fineos_document_response.description or "",
    )
    return document_response


def get_documents(
    application: Application, db_session: massgov.pfml.db.Session
) -> List[DocumentResponse]:
    fineos = massgov.pfml.fineos.create_client()

    fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)
    absence_id = get_fineos_absence_id_from_application(application)

    fineos_documents = fineos.get_documents(fineos_web_id, absence_id)
    appeal_01_documents = fineos.get_documents(fineos_web_id, absence_id + "-AP-01")
    appeal_02_documents = fineos.get_documents(fineos_web_id, absence_id + "-AP-02")

    logger.info(
        "retrieved appeal documents",
        extra={
            "num_appeal_01_documents": len(appeal_01_documents),
            "num_appeal_02_documents": len(appeal_02_documents),
        },
    )

    fineos_documents += appeal_01_documents + appeal_02_documents

    document_responses = list(
        map(
            lambda fd: fineos_document_response_to_document_response(fd, application),
            fineos_documents,
        )
    )
    return document_responses


def build_payment_preference(
    application: Application,
    payment_address: Optional[massgov.pfml.fineos.models.customer_api.CustomerAddress],
) -> massgov.pfml.fineos.models.customer_api.NewPaymentPreference:
    payment_preference = application.payment_preference
    override_postal_addr = True if payment_address else None
    if payment_preference.payment_method_id == PaymentMethod.ACH.payment_method_id:
        if not payment_preference.account_number or not payment_preference.routing_number:
            raise ValueError(
                "ACH payment preference must include an account number and routing number."
            )

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
    fineos = massgov.pfml.fineos.create_client()
    fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)

    if application.has_mailing_address and application.mailing_address:
        fineos_payment_addr: Optional[
            massgov.pfml.fineos.models.customer_api.CustomerAddress
        ] = build_customer_address(application.mailing_address)
    else:
        fineos_payment_addr = None

    fineos_payment_preference = build_payment_preference(application, fineos_payment_addr)
    return fineos.add_payment_preference(fineos_web_id, fineos_payment_preference)


def download_document(
    application: Application,
    fineos_document_id: str,
    db_session: massgov.pfml.db.Session,
    document_type: Union[str, None],
) -> Base64EncodedFileData:
    fineos = massgov.pfml.fineos.create_client()

    fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)
    absence_id = get_fineos_absence_id_from_application(application)
    if not document_type or document_type != "Appeal Acknowledgment":
        try:
            return fineos.download_document(fineos_web_id, absence_id, fineos_document_id)
        except FINEOSForbidden:
            logger.info("Document not found in Absence Case - trying next case")
            pass
    try:
        return fineos.download_document(fineos_web_id, absence_id + "-AP-01", fineos_document_id)
    except FINEOSForbidden:
        logger.info("Document not found in '-AP-01' case - trying next case")
        pass
    return fineos.download_document(fineos_web_id, absence_id + "-AP-02", fineos_document_id)


def create_or_update_employer(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient, employer: Employer
) -> int:
    # Determine if operation is create or update by seeing if the API Employer
    # record has a fineos_employer_id already.
    is_create = employer.fineos_employer_id is None

    existing_fineos_record = None
    if not is_create:
        try:
            read_employer_response = fineos.read_employer(employer.employer_fein)
            existing_fineos_record = read_employer_response.OCOrganisation[0]
        except FINEOSNotFound:
            logger.warning(
                "Did not find employer in FINEOS as expected. Continuing with update as create.",
                extra={
                    "internal_employer_id": employer.employer_id,
                    "fineos_employer_id": employer.fineos_employer_id,
                },
            )
            is_create = True
            pass

    if not employer.employer_name:
        raise ValueError(
            "An Employer must have a employer_name in order to create or update an employer."
        )

    employer_request_body = massgov.pfml.fineos.models.CreateOrUpdateEmployer(
        # `fineos_customer_nbr` is used as the Organization's CustomerNo
        # attribute for the request, which FINEOS uses to determine if this is a
        # create or update on their end.
        fineos_customer_nbr=str(employer.employer_id),
        employer_fein=employer.employer_fein,
        employer_legal_name=employer.employer_name,
        employer_dba=employer.employer_dba,
    )

    fineos_customer_nbr, fineos_employer_id = fineos.create_or_update_employer(
        employer_request_body, existing_fineos_record
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
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    employer: Employer,
    is_create: bool,
    prev_family_exemption: Optional[bool] = None,
    prev_medical_exemption: Optional[bool] = None,
    prev_exemption_cease_date: Optional[datetime.date] = None,
) -> Optional[str]:
    if not employer.fineos_employer_id:
        raise ValueError(
            "An Employer must have a fineos_employer_id in order to create a service agreement."
        )

    service_agreement_inputs = resolve_service_agreement_inputs(
        is_create,
        employer,
        prev_family_exemption,
        prev_medical_exemption,
        prev_exemption_cease_date,
    )

    if service_agreement_inputs is not None:
        return fineos.create_service_agreement_for_employer(
            employer.fineos_employer_id, service_agreement_inputs
        )

    return None


def resolve_service_agreement_inputs(
    is_create: bool,
    employer: Employer,
    prev_family_exemption: Optional[bool] = None,
    prev_medical_exemption: Optional[bool] = None,
    prev_exemption_cease_date: Optional[datetime.date] = None,
) -> Optional[CreateOrUpdateServiceAgreement]:
    if not is_create and (prev_family_exemption is None or prev_medical_exemption is None):
        logger.info(
            "Previous exemption values were not provided when updating a service agreement.",
            extra={
                "internal_employer_id": employer.employer_id,
                "fineos_employer_id": employer.fineos_employer_id,
            },
        )
        return None

    family_exemption = bool(employer.family_exemption)
    medical_exemption = bool(employer.medical_exemption)
    prev_family_exemption = bool(prev_family_exemption)
    prev_medical_exemption = bool(prev_medical_exemption)

    was_exempt = prev_family_exemption and prev_medical_exemption
    was_not_exempt = not prev_family_exemption and not prev_medical_exemption
    was_partially_exempt = (not prev_family_exemption and prev_medical_exemption) or (
        prev_family_exemption and not prev_medical_exemption
    )
    is_exempt = family_exemption and medical_exemption
    is_not_exempt = not family_exemption and not medical_exemption
    is_partially_exempt = (not family_exemption and medical_exemption) or (
        family_exemption and not medical_exemption
    )

    # If it's an update there should be previous exemption values.
    leave_plans = resolve_leave_plans(family_exemption, medical_exemption)
    absence_management_flag = False if len(leave_plans) == 0 else True
    if is_create:
        return CreateOrUpdateServiceAgreement(
            absence_management_flag=absence_management_flag,
            leave_plans=", ".join(leave_plans),
            unlink_leave_plans=True,
        )
    elif was_exempt and (is_not_exempt or is_partially_exempt):
        # Set the start date to the previous exemption cease_date.
        return CreateOrUpdateServiceAgreement(
            absence_management_flag=absence_management_flag,
            leave_plans=", ".join(leave_plans),
            start_date=prev_exemption_cease_date,
            unlink_leave_plans=True,
        )
    elif (was_not_exempt or was_partially_exempt) and is_exempt:
        if employer.exemption_commence_date is None:
            raise ValueError(
                "An Employer's exemption_commence_date is required when the Employer is becoming exempt."
            )
        # Set end date to a day before the exemption_commence_date.
        leave_plans = resolve_leave_plans(prev_family_exemption, prev_medical_exemption)
        absence_management_flag = False if len(leave_plans) == 0 else True
        unlink_leave_plans = False
        return CreateOrUpdateServiceAgreement(
            absence_management_flag=absence_management_flag,
            leave_plans=", ".join(leave_plans),
            end_date=employer.exemption_commence_date - datetime.timedelta(1),
            unlink_leave_plans=unlink_leave_plans,
        )
    return None


def resolve_leave_plans(family_exemption: bool, medical_exemption: bool) -> Set[str]:
    if family_exemption:
        if medical_exemption:
            return set()
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


def format_other_leaves_data(application: Application) -> Optional[EFormBody]:
    # Convert from DB models to API models because the API enum models are easier to serialize to strings
    previous_leave_other_reason_items = map(
        lambda other_leave: PreviousLeave.from_orm(other_leave),
        application.previous_leaves_other_reason,
    )
    previous_leave_same_reason_items = list(
        map(
            lambda same_leave: PreviousLeave.from_orm(same_leave),
            application.previous_leaves_same_reason,
        )
    )

    leave_reason = LeaveReasonApi.to_previous_leave_qualifying_reason(
        LeaveReasonApi.validate_type(application.leave_reason.leave_reason_description)
    )
    for leave in previous_leave_same_reason_items:
        leave.leave_reason = leave_reason

    previous_leave_items = chain(
        previous_leave_other_reason_items, previous_leave_same_reason_items
    )
    concurrent_leave_item = None
    if application.concurrent_leave:
        concurrent_leave_item = ConcurrentLeave.from_orm(application.concurrent_leave)

    return PreviousLeavesEFormBuilder.build(previous_leave_items, concurrent_leave_item)


def create_eform(
    application: Application, db_session: massgov.pfml.db.Session, eform: EFormBody
) -> None:
    fineos = massgov.pfml.fineos.create_client()
    fineos_web_id = get_or_register_employee_fineos_web_id(fineos, application, db_session)
    fineos_absence_id = get_fineos_absence_id_from_application(application)
    fineos.customer_create_eform(fineos_web_id, fineos_absence_id, eform)


def create_other_leaves_and_other_incomes_eforms(
    application: Application, db_session: massgov.pfml.db.Session
) -> None:
    log_attributes = get_application_log_attributes(application)

    # Send Other Leaves to FINEOS - this eForm contains previous leaves for the same reason, some other reason, and concurrent leaves.
    if (
        application.previous_leaves_other_reason
        or application.previous_leaves_same_reason
        or application.concurrent_leave
    ):
        eform = format_other_leaves_data(application)
        if eform:
            create_eform(application, db_session, eform)
            logger.info("Created Other Leaves eform", extra=log_attributes)
        else:
            raise ValueError("expected an Other Leaves eform but got None")
    # Send employer benefits and other incomes to fineos
    if application.employer_benefits or application.other_incomes:
        # Convert from DB models to API models because the API enum models are easier to serialize to strings
        other_incomes = map(lambda income: OtherIncome.from_orm(income), application.other_incomes)
        employer_benefits = map(
            lambda benefit: EmployerBenefit.from_orm(benefit), application.employer_benefits,
        )

        eform = OtherIncomesEFormBuilder.build(employer_benefits, other_incomes,)
        create_eform(application, db_session, eform)
        logger.info("Created Other Incomes eform", extra=log_attributes)


def get_absence_periods(
    employee_tax_id: str, employer_fein: str, absence_id: str, db_session: massgov.pfml.db.Session,
) -> List[AbsencePeriodStatusResponse]:
    fineos = massgov.pfml.fineos.create_client()

    try:
        # Get FINEOS web admin id
        web_id = register_employee(fineos, employee_tax_id, employer_fein, db_session)

        # Get absence periods
        response: AbsenceDetails = fineos.get_absence(web_id, absence_id)
    except FINEOSClientError as ex:
        logger.warn("Unable to get absence periods", exc_info=ex, extra={"absence_id": absence_id})
        raise

    # Map FINEOS response to PFML response
    absence_periods = []
    if response and response.absencePeriods:
        for absence_period in response.absencePeriods:
            absence_period_status = AbsencePeriodStatusResponse()
            absence_period_status.absence_period_start_date = absence_period.startDate
            absence_period_status.absence_period_end_date = absence_period.endDate
            absence_period_status.period_type = absence_period.absenceType
            absence_period_status.reason = absence_period.reason
            absence_period_status.reason_qualifier_one = absence_period.reasonQualifier1
            absence_period_status.reason_qualifier_two = absence_period.reasonQualifier2
            absence_period_status.request_decision = absence_period.requestStatus
            absence_period_status.fineos_leave_period_id = absence_period.id

            absence_periods.append(absence_period_status)

    return absence_periods

from dataclasses import dataclass
from typing import Dict
from uuid import UUID

import massgov.pfml.util.datetime as datetime_util
from massgov.pfml import db, fineos
from massgov.pfml.api.services.fineos_actions import (
    build_absence_case,
    build_bonding_date_reflexive_question,
    build_caring_leave_reflexive_question,
    build_contact_details,
    build_customer_model,
    get_customer_occupation,
    register_employee,
    update_occupation_details,
    upsert_week_based_work_pattern,
)
from massgov.pfml.db.models.applications import Application, LeaveReason, LeaveReasonQualifier
from massgov.pfml.db.models.employees import Claim, Employee, Employer, TaxIdentifier, User
from massgov.pfml.fineos import models
from massgov.pfml.fineos.client import AbstractFINEOSClient
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


@dataclass(eq=True, frozen=True)
class SsnFeinPair:
    employee_ssn: str
    employer_fein: str


def _get_employers(
    employer_feins: list[str], fineos: AbstractFINEOSClient
) -> Dict[str, models.OCOrganisation]:
    employers: Dict[str, models.OCOrganisation] = {}
    for fein in employer_feins:
        if fein in employers.keys():
            continue
        fineos_employer = fineos.read_employer(fein)
        employers[fein] = fineos_employer
    return employers


def _build_customers(
    applications: Dict[SsnFeinPair, list[Application]], user: User
) -> Dict[SsnFeinPair, models.customer_api.Customer]:
    customers: Dict[SsnFeinPair, models.customer_api.Customer] = {}
    for ssn_fein_pair, application in applications.items():
        if ssn_fein_pair in customers.keys():
            continue
        customers[ssn_fein_pair] = build_customer_model(
            application[0], user
        )  # TODO: is this right? Is it possible for the same employee ssn/employer fein pair to need multiple customers
        # Main use of application appears to grab applicant details as well mass id?
    return customers


def _build_absence_cases(
    applications: list[Application],
) -> Dict[UUID, models.customer_api.AbsenceCase]:
    absence_cases: Dict[UUID, models.customer_api.AbsenceCase] = {}
    for application in applications:
        absence_cases[application.application_id] = build_absence_case(application)

    return absence_cases


def _map_applications_to_employee_ssn_employer_fein_pairs(
    applications: list[Application],
) -> Dict[SsnFeinPair, list[Application]]:
    pairs: Dict[SsnFeinPair, list[Application]] = {}
    for application in applications:
        if application.employer_fein is None:
            raise ValueError("application.employer_fein is None")
        pair = SsnFeinPair(application.tax_identifier.tax_identifier, application.employer_fein)
        if pair in pairs.keys():
            pairs[pair].append(application)
        else:
            pairs[pair] = [application]
    return pairs


def _build_contact_details(
    applications: list[Application],
) -> Dict[str, models.customer_api.ContactDetails]:
    contact_details: Dict[str, models.customer_api.ContactDetails] = {}
    for application in applications:
        assert application.user.email_address
        if application.user.email_address in contact_details.keys():
            continue
        contact_details[application.user.email_address] = build_contact_details(application)
    return contact_details


def submit_applications(
    db_session: db.Session, applications: list[Application], user: User
) -> None:
    applications_with_claims = [application for application in applications if application.claim]
    applications_without_claims = [
        application for application in applications if not application.claim
    ]

    application_with_claims_by_ssn_fein = _map_applications_to_employee_ssn_employer_fein_pairs(
        applications_with_claims
    )
    application_without_claims_by_ssn_fein = _map_applications_to_employee_ssn_employer_fein_pairs(
        applications_without_claims
    )
    # Create the FINEOS client.
    fineos_client = fineos.create_client()
    customers = _build_customers(application_without_claims_by_ssn_fein, user)
    absence_cases = _build_absence_cases(applications_without_claims)
    contact_details = _build_contact_details(applications_without_claims)
    # read_employer
    all_fineos_employers = _get_employers(
        [application.employer_fein for application in applications if application.employer_fein],
        fineos_client,
    )

    fineos_web_ids: Dict[SsnFeinPair, str] = {}
    for ssn_fein_pair in application_with_claims_by_ssn_fein.keys():
        fineos_employer_id = all_fineos_employers[ssn_fein_pair.employer_fein].get_customer_number()
        # register_api_user
        fineos_web_id = register_employee(
            fineos_client,
            ssn_fein_pair.employee_ssn,
            ssn_fein_pair.employer_fein,
            db_session,
            fineos_employer_id,
        )
        fineos_web_ids[ssn_fein_pair] = fineos_web_id

    for ssn_fein_pair in application_without_claims_by_ssn_fein.keys():
        fineos_employer_id = all_fineos_employers[ssn_fein_pair.employer_fein].get_customer_number()
        # register_api_user
        fineos_web_id = register_employee(
            fineos_client,
            ssn_fein_pair.employee_ssn,
            ssn_fein_pair.employer_fein,
            db_session,
            fineos_employer_id,
        )
        fineos_web_ids[ssn_fein_pair] = fineos_web_id

    for ssn_fein_pair, fineos_web_id in fineos_web_ids.items():
        if ssn_fein_pair not in customers.keys():
            continue
        build_customer = customers[ssn_fein_pair]
        assert build_customer.idNumber
        fineos_employer = all_fineos_employers[ssn_fein_pair.employer_fein]
        fineos_client.update_customer_details(fineos_web_id, build_customer)
        occupation = get_customer_occupation(fineos_client, fineos_web_id, build_customer.idNumber)
        if occupation is None:
            logger.error(
                "Did not find customer occupation.", extra={"fineos_web_id": fineos_web_id}
            )
            raise ValueError("customer occupation is None")
        occupation = get_customer_occupation(fineos_client, fineos_web_id, build_customer.idNumber)
        if occupation is None:
            logger.error(
                "Did not find customer occupation.", extra={"fineos_web_id": fineos_web_id}
            )
            raise ValueError("customer occupation is None")
        applications_for_pair = application_without_claims_by_ssn_fein[ssn_fein_pair]
        for application in applications_for_pair:
            upsert_week_based_work_pattern(
                fineos_client,
                fineos_web_id,
                application,
                occupation.occupationId,
                occupation.workPatternBasis,
            )
            # Only pick a worksite if an organization unit was picked
            worksite_id = None
            if application.organization_unit_id:
                worksite_id = fineos_employer.get_worksite_id()
            update_occupation_details(
                fineos_client, application, occupation.occupationId, worksite_id
            )

    for _, applications in application_with_claims_by_ssn_fein.items():
        for application in applications:
            fineos_client.complete_intake(
                fineos_web_id, str(application.claim.fineos_notification_id)
            )
            application.submitted_time = datetime_util.utcnow()

    for ssn_fein_pair, applications in application_without_claims_by_ssn_fein.items():
        for application in applications:
            absence_case = absence_cases[application.application_id]
            fineos_web_id = fineos_web_ids[ssn_fein_pair]
            ## TODO parallelize this FINEOS call
            new_case = fineos_client.start_absence(fineos_web_id, absence_case)
            employee = (
                db_session.query(Employee)
                .join(TaxIdentifier)
                .filter(TaxIdentifier.tax_identifier == ssn_fein_pair.employee_ssn)
                .one_or_none()
            )
            employer = (
                db_session.query(Employer)
                .filter(Employer.employer_fein == ssn_fein_pair.employer_fein)
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

            if application.organization_unit_id:
                new_claim.organization_unit_id = application.organization_unit_id

            application.claim = new_claim
            assert application.user.email_address
            contact_detail = contact_details[application.user.email_address]
            updated_contact_details = fineos_client.update_customer_contact_details(
                fineos_web_id, contact_detail
            )
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
                fineos_client.update_reflexive_questions(
                    fineos_web_id, application.claim.fineos_absence_id, reflexive_question
                )

            if application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id:
                reflexive_question = build_caring_leave_reflexive_question(application)
                fineos_client.update_reflexive_questions(
                    fineos_web_id, application.claim.fineos_absence_id, reflexive_question
                )

            db_session.commit()
            ## TODO parallelize this FINEOS call
            fineos_client.complete_intake(
                fineos_web_id, str(application.claim.fineos_notification_id)
            )
            application.submitted_time = datetime_util.utcnow()

from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from dataclasses import dataclass
from typing import Dict, Tuple
from uuid import UUID

import massgov.pfml.util.datetime as datetime_util
from massgov.pfml import db, fineos
from massgov.pfml.api.services.fineos_actions import (
    build_absence_case,
    build_bonding_date_reflexive_question,
    build_caring_leave_reflexive_question,
    build_contact_details,
    build_customer_model,
    create_other_leaves_and_other_incomes_eforms,
    get_customer_occupation,
    register_employee,
    update_occupation_details,
    upsert_week_based_work_pattern,
)
from massgov.pfml.db.models.applications import (
    Application,
    FINEOSWebIdExt,
    LeaveReason,
    LeaveReasonQualifier,
)
from massgov.pfml.db.models.employees import Claim, Employee, Employer, TaxIdentifier, User
from massgov.pfml.fineos import models
from massgov.pfml.fineos.models.customer_api.overrides import (
    AbsenceCaseSummary,
    AdditionalInformation,
    ContactDetails,
)
from massgov.pfml.fineos.models.customer_api.spec import AbsenceCase, Customer
from massgov.pfml.fineos.models.wscomposer import OCOrganisation
from massgov.pfml.util import logging

logger = logging.get_logger(__name__)


@dataclass(eq=True, frozen=True)
class SsnFeinPair:
    employee_ssn: str
    employer_fein: str


def _thread_safe_read_employer(fein: str) -> Dict[str, models.OCOrganisation]:
    fineos_client = fineos.create_client()
    fineos_employer = fineos_client.read_employer(fein)
    return {fein: fineos_employer}


def _get_fineos_employers(
    employer_feins: list[str], executor: ThreadPoolExecutor
) -> Dict[str, models.OCOrganisation]:
    employers: Dict[str, models.OCOrganisation] = {}
    employer_futures = list(
        map(lambda fein: executor.submit(_thread_safe_read_employer, fein), employer_feins)
    )
    for future in as_completed(employer_futures):
        employers = employers | future.result()
    return employers


def _build_fineos_customers(
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


# Questions
# Is it accurate that only one customer needs to be created per ssn/fein pair?
# Is it accurate that contact details only need to be updated once per ssn/fein pair?
# Is this fineos API sequence accurate?  Paren indicate calls can occur concurrently
# register_api_user ->
# update_customer_details ->
# (get_customer_occupations_customer_api -> get_customer_occupation -> (update_week_based_work_pattern, update_occupation), update_customer_contact_details) ->
# start_absence ->
# update_reflexive_questions ->
# complete_intake

# TODO:
# Refactor to fetch employers and employees earlier
# Refactor fetching fineos_web_ids to avoid register_employee
# Refactor to make cleaner handling applications that have claims already


def _update_occupation(
    fineos_web_id: str,
    fineos_customer: Customer,
    fineos_employer: models.OCOrganisation,
    applications: list[Application],
) -> None:
    fineos_client = fineos.create_client()
    assert fineos_customer.idNumber
    occupation = get_customer_occupation(fineos_client, fineos_web_id, fineos_customer.idNumber)
    if occupation is None:
        logger.error("Did not find customer occupation.", extra={"fineos_web_id": fineos_web_id})
        raise ValueError("customer occupation is None")
    for application in applications:
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
        update_occupation_details(fineos_client, application, occupation.occupationId, worksite_id)


def _get_fineos_web_ids(
    db_session: db.Session, ssn_fein_pairs: list[SsnFeinPair]
) -> Dict[SsnFeinPair, str]:
    feins = [pair.employer_fein for pair in ssn_fein_pairs]
    ssns = [pair.employee_ssn for pair in ssn_fein_pairs]
    web_ids = (
        db_session.query(FINEOSWebIdExt)
        .filter(
            FINEOSWebIdExt.employee_tax_identifier.in_(ssns),
            FINEOSWebIdExt.employer_fein.in_(feins),
        )
        .all()
    )
    ssn_fein_pair_to_web_id = {}
    for pair in ssn_fein_pairs:
        for web_id in web_ids:
            if (
                pair.employee_ssn == web_id.employee_tax_identifier
                and pair.employer_fein == web_id.employer_fein
            ):
                assert web_id.fineos_web_id
                ssn_fein_pair_to_web_id[pair] = web_id.fineos_web_id
                break

    return ssn_fein_pair_to_web_id


def _update_customer_details(fineos_web_id: str, fineos_customer: Customer) -> None:
    fineos_client = fineos.create_client()
    fineos_client.update_customer_details(fineos_web_id, fineos_customer)


def _start_absence(
    ssn_fein_pair: SsnFeinPair, fineos_web_id: str, absence_case: AbsenceCase, application_id: str
) -> Tuple[SsnFeinPair, str, AbsenceCaseSummary]:
    fineos_client = fineos.create_client()
    new_case = fineos_client.start_absence(fineos_web_id, absence_case)
    return (ssn_fein_pair, application_id, new_case)


def _update_customer_contact_details(
    ssn_fein_pair: SsnFeinPair,
    fineos_web_id: str,
    contact_detail: ContactDetails,
    application_id: str,
) -> Tuple[SsnFeinPair, str, ContactDetails]:
    fineos_client = fineos.create_client()
    updated_contact_details = fineos_client.update_customer_contact_details(
        fineos_web_id, contact_detail
    )
    return (ssn_fein_pair, application_id, updated_contact_details)


def _update_reflexive_questions(
    ssn_fein_pair: SsnFeinPair,
    fineos_web_id: str,
    fineos_absence_id: str,
    reflexive_question: AdditionalInformation,
    application_id: str,
) -> None:
    fineos_client = fineos.create_client()
    fineos_client.update_reflexive_questions(fineos_web_id, fineos_absence_id, reflexive_question)


def _complete_intake(
    ssn_fein_pair: SsnFeinPair, fineos_web_id: str, fineos_notification_id: str, application_id: str
) -> Tuple[SsnFeinPair, str]:
    fineos_client = fineos.create_client()
    fineos_client.complete_intake(fineos_web_id, fineos_notification_id)
    return (ssn_fein_pair, application_id)


def submit(
    db_session: db.Session,
    applications: list[Application],
    user: User,
    executor: ThreadPoolExecutor,
) -> None:
    # Applications with a claim already only need to have the complete intake call executed
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

    # Collect all the data required for the calls
    all_fineos_employers: Dict[str, OCOrganisation] = _get_fineos_employers(
        [application.employer_fein for application in applications if application.employer_fein],
        executor,
    )

    fineos_web_ids: Dict[SsnFeinPair, str] = _get_fineos_web_ids(
        db_session, list(application_with_claims_by_ssn_fein.keys())
    )

    # Build all the fineos models
    # These are all dictionaries mapping the SsnFeinPair to the fineos model
    customers = _build_fineos_customers(application_without_claims_by_ssn_fein, user)
    absence_cases = _build_absence_cases(applications_without_claims)
    contact_details = _build_contact_details(applications_without_claims)

    for ssn_fein_pair in (
        application_with_claims_by_ssn_fein.keys() | application_without_claims_by_ssn_fein.keys()
    ):
        if ssn_fein_pair in fineos_web_ids.keys():
            # If there is already a web id, do not attempt to register the employee/employer again
            continue
        fineos_employer_id = all_fineos_employers[ssn_fein_pair.employer_fein].get_customer_number()
        # TODO this method needs to be refactored in order to be parallelized as it modifies the DB
        # in addition to making fineos calls
        # register_api_user
        fineos_web_id = register_employee(
            fineos_client,
            ssn_fein_pair.employee_ssn,
            ssn_fein_pair.employer_fein,
            db_session,
            fineos_employer_id,
        )
        fineos_web_ids[ssn_fein_pair] = fineos_web_id

    update_customer_details_futures = []
    for ssn_fein_pair, fineos_web_id in fineos_web_ids.items():
        if ssn_fein_pair not in customers.keys():
            continue
        fineos_customer = customers[ssn_fein_pair]
        assert fineos_customer.idNumber
        fineos_employer = all_fineos_employers[ssn_fein_pair.employer_fein]

        update_customer_details_futures.append(
            executor.submit(_update_customer_details, fineos_web_id, fineos_customer)
        )
    wait(update_customer_details_futures)

    update_occupation_futures = []
    for ssn_fein_pair, fineos_web_id in fineos_web_ids.items():
        if ssn_fein_pair not in customers.keys():
            continue
        fineos_customer = customers[ssn_fein_pair]
        applications_for_pair = application_without_claims_by_ssn_fein[ssn_fein_pair]
        assert fineos_customer.idNumber
        fineos_employer = all_fineos_employers[ssn_fein_pair.employer_fein]

        update_occupation_futures.append(
            executor.submit(
                _update_occupation,
                fineos_web_id,
                fineos_customer,
                fineos_employer,
                applications_for_pair,
            )
        )

    wait(update_occupation_futures)

    for _, applications in application_with_claims_by_ssn_fein.items():
        for application in applications:
            fineos_client.complete_intake(
                fineos_web_id, str(application.claim.fineos_notification_id)
            )
            application.submitted_time = datetime_util.utcnow()

    create_absence_futures = []
    for ssn_fein_pair, applications in application_without_claims_by_ssn_fein.items():
        for application in applications:
            absence_case = absence_cases[application.application_id]
            fineos_web_id = fineos_web_ids[ssn_fein_pair]
            create_absence_futures.append(
                executor.submit(
                    _start_absence,
                    ssn_fein_pair,
                    fineos_web_id,
                    absence_case,
                    application.application_id,
                )
            )

    for start_absence_future in as_completed(create_absence_futures):
        (ssn_fein_pair, application_id, new_case) = start_absence_future.result()
        applications = application_without_claims_by_ssn_fein[ssn_fein_pair]
        application = next(
            application
            for application in applications
            if application.application_id == application_id
        )
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

    updated_customer_contact_details_futures = []
    for ssn_fein_pair, applications in application_without_claims_by_ssn_fein.items():
        fineos_web_id = fineos_web_ids[ssn_fein_pair]
        for application in applications:
            assert application.user.email_address
            contact_detail = contact_details[application.user.email_address]
            updated_customer_contact_details_futures.append(
                executor.submit(
                    _update_customer_contact_details,
                    ssn_fein_pair,
                    fineos_web_id,
                    contact_detail,
                    application.application_id,
                )
            )

    for update_customer_contact_details_future in as_completed(
        updated_customer_contact_details_futures
    ):
        (
            ssn_fein_pair,
            application_id,
            updated_contact_details,
        ) = update_customer_contact_details_future.result()
        applications = application_without_claims_by_ssn_fein[ssn_fein_pair]
        application = next(
            application
            for application in applications
            if application.application_id == application_id
        )
        phone_numbers = updated_contact_details.phoneNumbers
        if phone_numbers is not None and len(phone_numbers) > 0:
            application.phone.fineos_phone_id = phone_numbers[0].id

    update_reflexive_questions_futures = []
    for ssn_fein_pair, applications in application_without_claims_by_ssn_fein.items():
        fineos_web_id = fineos_web_ids[ssn_fein_pair]
        for application in applications:
            # Reflexive questions for bonding and caring leave
            # "The reflexive questions allows to update additional information of an absence case leave request."
            # Source - https://documentation.fineos.com/support/documentation/customer-swagger-21.1.html#operation/createReflexiveQuestions
            if application.leave_reason_qualifier_id in [
                LeaveReasonQualifier.NEWBORN.leave_reason_qualifier_id,
                LeaveReasonQualifier.ADOPTION.leave_reason_qualifier_id,
                LeaveReasonQualifier.FOSTER_CARE.leave_reason_qualifier_id,
            ]:
                reflexive_question = build_bonding_date_reflexive_question(application)
                update_reflexive_questions_futures.append(
                    executor.submit(
                        _update_reflexive_questions,
                        ssn_fein_pair,
                        fineos_web_id,
                        application.claim.fineos_absence_id,
                        reflexive_question,
                        application.application_id,
                    )
                )

            if application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id:
                reflexive_question = build_caring_leave_reflexive_question(application)
                update_reflexive_questions_futures.append(
                    executor.submit(
                        _update_reflexive_questions,
                        ssn_fein_pair,
                        fineos_web_id,
                        application.claim.fineos_absence_id,
                        reflexive_question,
                        application.application_id,
                    )
                )
    complete_intake_futures = []
    for ssn_fein_pair, applications in application_without_claims_by_ssn_fein.items():
        fineos_web_id = fineos_web_ids[ssn_fein_pair]
        for application in applications:
            complete_intake_futures.append(
                executor.submit(
                    _complete_intake,
                    ssn_fein_pair,
                    fineos_web_id,
                    str(application.claim.fineos_notification_id),
                    application.application_id,
                )
            )
    for _complete_intake_future in as_completed(complete_intake_futures):
        applications = application_without_claims_by_ssn_fein[ssn_fein_pair]
        application = next(
            application
            for application in applications
            if application.application_id == application_id
        )
        application.submitted_time = datetime_util.utcnow()
        # Send previous leaves, employer benefits, and other incomes as eforms to FINEOS
        create_other_leaves_and_other_incomes_eforms(application, db_session)

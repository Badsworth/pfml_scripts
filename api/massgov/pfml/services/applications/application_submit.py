from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
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


@dataclass
class ApplicationsContainer:
    """
    This is a container class to hold the list of applications
    that the same claimant/employer pair is submitting.  It also contains
    relevant FINEOS data models
    """

    ssn_fein_pair: SsnFeinPair
    applications: list[Application]
    fineos_employer: models.OCOrganisation
    fineos_web_id: Optional[str] = None
    customer: Optional[models.customer_api.Customer] = None
    customer_contact_details: Optional[models.customer_api.ContactDetails] = None
    absence_cases: Dict[UUID, models.customer_api.AbsenceCase] = field(default_factory=dict)

    def get_application(self, application_id: UUID) -> Application:
        return next(
            application
            for application in self.applications
            if application.application_id == application_id
        )

    def get_absence_case_for_application(
        self, application_id: UUID
    ) -> models.customer_api.AbsenceCase:
        return self.absence_cases[application_id]

    def does_claim_exist_for_any_application(self):
        return True in [application.claim is not None for application in self.applications]


def _get_container_by_ssn_fein_pair(
    containers: list[ApplicationsContainer], ssn_fein_pair: SsnFeinPair
) -> ApplicationsContainer:
    return next(container for container in containers if container.ssn_fein_pair == ssn_fein_pair)


def _get_fineos_web_ids(
    db_session: db.Session, ssn_fein_pairs: set[SsnFeinPair]
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


def _build_fineos_customers(
    applications_containers: list[ApplicationsContainer], user: User
) -> None:
    for container in applications_containers:
        # The update_customer_details will get invoked once per SsnFeinPair (via fineos_web_id)
        # so use the first application to build the customer
        # see https://github.com/EOLWD/pfml/blob/d2d1674c168f9d8e9c07cb221778b21f0eb714d1/api/massgov/pfml/fineos/fineos_client.py#L488
        application = container.applications[0]
        container.customer = build_customer_model(application, user)


def _build_absence_cases(
    containers: list[ApplicationsContainer],
) -> None:
    for container in containers:
        for application in container.applications:
            container.absence_cases[application.application_id] = build_absence_case(application)


def _build_contact_details(
    containers: list[ApplicationsContainer],
) -> None:
    for container in containers:
        # update_customer_contact_details will only get exectued once per SsnFeinPar
        # so we just take the email associated with the first application being
        # submitted by the same claimant for the same employer
        # see: https://github.com/EOLWD/pfml/blob/d2d1674c168f9d8e9c07cb221778b21f0eb714d1/api/massgov/pfml/fineos/fineos_client.py#L506
        application = container.applications[0]
        assert application.user.email_address
        if container.customer_contact_details:
            continue
        container.customer_contact_details = build_contact_details(application)


def _build_applications_containers(
    applications: list[Application],
    user: User,
    fineos_web_ids: Dict[SsnFeinPair, str],
    all_fineos_employers: Dict[str, OCOrganisation],
) -> list["ApplicationsContainer"]:
    containers: list[ApplicationsContainer] = []
    pairs: Dict[SsnFeinPair, list[Application]] = {}
    for application in applications:
        if application.employer_fein is None:
            raise ValueError("application.employer_fein is None")
        pair = SsnFeinPair(application.tax_identifier.tax_identifier, application.employer_fein)
        if pair in pairs.keys():
            pairs[pair].append(application)
        else:
            pairs[pair] = [application]
    for (ssn_fein_pair, applications) in pairs.items():
        assert application.employer_fein
        containers.append(
            ApplicationsContainer(
                ssn_fein_pair,
                applications,
                all_fineos_employers[ssn_fein_pair.employer_fein],
                fineos_web_ids[ssn_fein_pair] if ssn_fein_pair in fineos_web_ids else None,
            )
        )
    _build_fineos_customers(containers, user)
    _build_absence_cases(containers)
    _build_contact_details(containers)
    return containers


def _thread_safe_read_employer(fein: str) -> Dict[str, models.OCOrganisation]:
    fineos_client = fineos.create_client()
    fineos_employer = fineos_client.read_employer(fein)
    return {fein: fineos_employer}


def _get_fineos_employers(
    employer_feins: set[str], executor: ThreadPoolExecutor
) -> Dict[str, models.OCOrganisation]:
    employers: Dict[str, models.OCOrganisation] = {}
    employer_futures = list(
        map(lambda fein: executor.submit(_thread_safe_read_employer, fein), employer_feins)
    )
    for future in as_completed(employer_futures):
        employers = employers | future.result()
    return employers


def _thread_safe_update_occupation(
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


def _thread_safe_update_customer_details(fineos_web_id: str, fineos_customer: Customer) -> None:
    fineos_client = fineos.create_client()
    fineos_client.update_customer_details(fineos_web_id, fineos_customer)


def _thread_safe_start_absence(
    ssn_fein_pair: SsnFeinPair, fineos_web_id: str, absence_case: AbsenceCase, application_id: UUID
) -> Tuple[SsnFeinPair, UUID, AbsenceCaseSummary]:
    fineos_client = fineos.create_client()
    new_case = fineos_client.start_absence(fineos_web_id, absence_case)
    return (ssn_fein_pair, application_id, new_case)


def _thread_safe_update_customer_contact_details(
    ssn_fein_pair: SsnFeinPair,
    fineos_web_id: str,
    contact_detail: ContactDetails,
) -> Tuple[SsnFeinPair, ContactDetails]:
    fineos_client = fineos.create_client()
    updated_contact_details = fineos_client.update_customer_contact_details(
        fineos_web_id, contact_detail
    )
    return (ssn_fein_pair, updated_contact_details)


def _thread_safe_update_reflexive_questions(
    fineos_web_id: str,
    fineos_absence_id: str,
    reflexive_question: AdditionalInformation,
) -> None:
    fineos_client = fineos.create_client()
    fineos_client.update_reflexive_questions(fineos_web_id, fineos_absence_id, reflexive_question)


def _thread_safe_complete_intake(
    ssn_fein_pair: SsnFeinPair,
    fineos_web_id: str,
    fineos_notification_id: str,
    application_id: UUID,
) -> Tuple[SsnFeinPair, UUID]:
    fineos_client = fineos.create_client()
    fineos_client.complete_intake(fineos_web_id, fineos_notification_id)
    return (ssn_fein_pair, application_id)


def submit(
    db_session: db.Session,
    applications: list[Application],
    user: User,
    executor: ThreadPoolExecutor,
) -> None:
    """
    This methods accepts a list of applications and submits them all to FINEOS.  It will make the minimum number of
    calls required based on the data conditions of the passed applications and make the calls to the FINEOS API
    concurrently when possible.

    Flow of API calls (per application); each line break represents calls that have to occur sequentially:
    register_api_user ->
    (update_customer_details, get_customer_occupations_customer_api -> get_customer_occupation -> (update_week_based_work_pattern, update_occupation), update_customer_contact_details) ->
    start_absence ->
    update_reflexive_questions ->
    complete_intake

    """
    # Collect created fineos web ids and read all the employers that the applications reference
    fineos_web_ids: Dict[SsnFeinPair, str] = _get_fineos_web_ids(
        db_session,
        {
            SsnFeinPair(application.tax_identifier.tax_identifier, application.employer_fein)
            for application in applications
            if application.employer_fein
        },
    )
    all_fineos_employers: Dict[str, OCOrganisation] = _get_fineos_employers(
        {application.employer_fein for application in applications if application.employer_fein},
        executor,
    )

    # Build the applications containers
    applications_containers = _build_applications_containers(
        applications, user, fineos_web_ids, all_fineos_employers
    )

    # Create the FINEOS client for the `register_employee`
    # Other thread safe FINEOS calls will create their own client
    # See the todo below
    fineos_client = fineos.create_client()
    for container in applications_containers:
        if container.ssn_fein_pair in fineos_web_ids.keys():
            # If there is already a web id, do not attempt to register the employee/employer again
            container.fineos_web_id = fineos_web_ids[container.ssn_fein_pair]
            continue
        fineos_employer_id = container.fineos_employer.get_customer_number()
        # TODO this method needs to be refactored to extract the fineos api calls
        # from the synchronous code.
        fineos_web_id = register_employee(
            fineos_client,
            container.ssn_fein_pair.employee_ssn,
            container.ssn_fein_pair.employer_fein,
            db_session,
            fineos_employer_id,
        )
        container.fineos_web_id = fineos_web_id

    update_customer_details_futures = []
    for container in applications_containers:
        # If any claim has been associated with an application
        # all the User-centric FINEOS calls (just requiring fineos_web_id)
        # have already been made
        if not container.does_claim_exist_for_any_application():
            assert container.customer
            update_customer_details_futures.append(
                executor.submit(
                    _thread_safe_update_customer_details,
                    container.fineos_web_id,
                    container.customer,
                )
            )

    update_occupation_futures = []
    for container in applications_containers:
        # If any claim has been associated with an application
        # all the User-centric FINEOS calls (just requiring fineos_web_id)
        # have already been made
        if not container.does_claim_exist_for_any_application():
            assert container.customer
            fineos_employer = all_fineos_employers[container.ssn_fein_pair.employer_fein]

            update_occupation_futures.append(
                executor.submit(
                    _thread_safe_update_occupation,
                    container.fineos_web_id,
                    container.customer,
                    fineos_employer,
                    container.applications,
                )
            )

    updated_customer_contact_details_futures = []
    for container in applications_containers:
        # If any claim has been associated with an application
        # all the User-centric FINEOS calls (just requiring fineos_web_id)
        # have already been made
        if not container.does_claim_exist_for_any_application():
            updated_customer_contact_details_futures.append(
                executor.submit(
                    _thread_safe_update_customer_contact_details,
                    container.ssn_fein_pair,
                    container.fineos_web_id,
                    container.customer_contact_details,
                )
            )
    for update_customer_details in as_completed(update_customer_details_futures):
        # Don't care about the result, but if an exception occurred
        # that should bubble up
        update_customer_details.result()

    for update_occupation_future in as_completed(update_occupation_futures):
        # Don't care about the result, but if an exception occurred
        # that should bubble up
        update_occupation_future.result()

    for update_customer_contact_details_future in as_completed(
        updated_customer_contact_details_futures
    ):
        (
            ssn_fein_pair,
            updated_contact_details,
        ) = update_customer_contact_details_future.result()
        container = _get_container_by_ssn_fein_pair(applications_containers, ssn_fein_pair)
        phone_numbers = updated_contact_details.phoneNumbers
        if phone_numbers is not None and len(phone_numbers) > 0:
            for application in container.applications:
                application.phone.fineos_phone_id = phone_numbers[0].id

    create_absence_futures = []
    for container in applications_containers:
        for application in container.applications:
            absence_case = container.get_absence_case_for_application(application.application_id)
            # Do not create the claim if it already exists
            if not application.claim:
                create_absence_futures.append(
                    executor.submit(
                        _thread_safe_start_absence,
                        container.ssn_fein_pair,
                        container.fineos_web_id,
                        absence_case,
                        application.application_id,
                    )
                )

    update_reflexive_questions_futures = []
    for start_absence_future in as_completed(create_absence_futures):
        (ssn_fein_pair, application_id, new_case) = start_absence_future.result()
        container = _get_container_by_ssn_fein_pair(applications_containers, ssn_fein_pair)
        application = container.get_application(application_id)
        employee = (
            db_session.query(Employee)
            .join(TaxIdentifier)
            .filter(TaxIdentifier.tax_identifier == container.ssn_fein_pair.employee_ssn)
            .one_or_none()
        )
        employer = (
            db_session.query(Employer)
            .filter(Employer.employer_fein == container.ssn_fein_pair.employer_fein)
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
                    _thread_safe_update_reflexive_questions,
                    container.fineos_web_id,
                    application.claim.fineos_absence_id,
                    reflexive_question,
                )
            )

        if application.leave_reason_id == LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id:
            reflexive_question = build_caring_leave_reflexive_question(application)
            update_reflexive_questions_futures.append(
                executor.submit(
                    _thread_safe_update_reflexive_questions,
                    container.fineos_web_id,
                    application.claim.fineos_absence_id,
                    reflexive_question,
                )
            )

    for update_reflexive_questions_future in as_completed(update_reflexive_questions_futures):
        # Don't care about the result, but if an exception occurred
        # that should bubble up
        update_reflexive_questions_future.result()

    complete_intake_futures = []
    for container in applications_containers:
        for application in container.applications:
            complete_intake_futures.append(
                executor.submit(
                    _thread_safe_complete_intake,
                    container.ssn_fein_pair,
                    container.fineos_web_id,
                    str(application.claim.fineos_notification_id),
                    application.application_id,
                )
            )
    for complete_intake_future in as_completed(complete_intake_futures):
        (ssn_fein_pair, application_id) = complete_intake_future.result()
        container = _get_container_by_ssn_fein_pair(applications_containers, ssn_fein_pair)
        application = container.get_application(application_id)
        application.submitted_time = datetime_util.utcnow()
        # Send previous leaves, employer benefits, and other incomes as eforms to FINEOS
        # TODO this should be refactored so that FIENOS call can be made concurrentlys
        create_other_leaves_and_other_incomes_eforms(application, db_session)

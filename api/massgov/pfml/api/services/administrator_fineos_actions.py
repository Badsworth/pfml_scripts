import mimetypes
import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.claims.common import (
    Address,
    EmployerBenefit,
    IntermittentLeavePeriod,
    LeaveDetails,
    PreviousLeave,
    StandardLeavePeriod,
)
from massgov.pfml.api.models.claims.responses import ClaimReviewResponse, DocumentResponse
from massgov.pfml.db.models.employees import Employer, User, UserLeaveAdministrator
from massgov.pfml.fineos.models.leave_admin_creation import CreateOrUpdateLeaveAdmin
from massgov.pfml.fineos.transforms.from_fineos.eforms import (
    TransformOtherIncomeEform,
    TransformOtherLeaveEform,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import EFormBody
from massgov.pfml.util.converters.json_to_obj import set_empty_dates_to_none

LEAVE_ADMIN_INFO_REQUEST_TYPE = "Employer Confirmation of Leave Data"

# Downloadable leave admin doc types: https://lwd.atlassian.net/wiki/spaces/DD/pages/691208493/Document+Categorization
# Lower case to prevent casing discrepancies
DOWNLOADABLE_DOC_TYPES = [
    "state managed paid leave confirmation",
    "approval notice",
    "request for more information",
    "denial notice",
    "employer response additional documentation",
    "care for a family member form",
]

logger = logging.get_logger(__name__)


EFORM_TYPES = {
    "OTHER_INCOME": "Other Income",
    "OTHER_INCOME_V2": "Other Income v2",
    "OTHER_LEAVES": "Other Leaves",
    "OTHER_LEAVES_V2": "Other Leaves v2",
}


class RegisterFINEOSDuplicateRecord(Exception):
    pass


def get_leave_details(absence_periods: Dict) -> LeaveDetails:
    """ Extracts absence data based on a PeriodDecisions dict and returns a LeaveDetails """
    leave_details = {}
    leave_details["reason"] = absence_periods["decisions"][0]["period"]["leaveRequest"][
        "reasonName"
    ]
    reduced_start_date: Optional[datetime] = None
    reduced_end_date: Optional[datetime] = None
    continuous_start_date: Optional[datetime] = None
    continuous_end_date: Optional[datetime] = None
    intermittent_start_date: Optional[datetime] = None
    intermittent_end_date: Optional[datetime] = None

    for decision in absence_periods["decisions"]:
        start_date = decision["period"]["startDate"]
        end_date = decision["period"]["endDate"]
        if decision["period"]["type"] == "Time off period":
            if continuous_start_date is None or start_date < continuous_start_date:
                continuous_start_date = start_date

            if continuous_end_date is None or end_date > continuous_end_date:
                continuous_end_date = end_date

        elif decision["period"]["type"] == "Reduced Schedule":
            if reduced_start_date is None or start_date < reduced_start_date:
                reduced_start_date = start_date

            if reduced_end_date is None or end_date > reduced_end_date:
                reduced_end_date = end_date

        elif decision["period"]["type"] == "Episodic":
            # FINEOS has yet to implement data for Episodic (intermittent) leaves
            # TODO when this info is available https://lwd.atlassian.net/browse/EMPLOYER-448
            # Send a static fake start and end date for recognition from the front end
            intermittent_start_date = datetime(2021, 1, 1, 0, 0)
            intermittent_end_date = datetime(2021, 2, 1, 0, 0)

    if continuous_start_date is not None and continuous_end_date is not None:
        leave_details["continuous_leave_periods"] = [
            StandardLeavePeriod(start_date=continuous_start_date, end_date=continuous_end_date)
        ]

    if reduced_start_date is not None and reduced_end_date is not None:
        leave_details["reduced_schedule_leave_periods"] = [
            StandardLeavePeriod(start_date=reduced_start_date, end_date=reduced_end_date)
        ]

    if intermittent_start_date is not None and intermittent_end_date is not None:
        leave_details["intermittent_leave_periods"] = [
            IntermittentLeavePeriod(
                start_date=intermittent_start_date, end_date=intermittent_end_date
            )
        ]

    return LeaveDetails.parse_obj(leave_details)


def fineos_document_response_to_document_response(
    fineos_document_response: massgov.pfml.fineos.models.group_client_api.GroupClientDocument,
) -> DocumentResponse:
    content_type, encoding = mimetypes.guess_type(fineos_document_response.originalFilename or "")

    document_response = DocumentResponse(
        created_at=fineos_document_response.dateCreated,
        document_type=fineos_document_response.name,
        content_type=content_type,
        fineos_document_id=fineos_document_response.documentId,
        name=fineos_document_response.originalFilename,
        description=fineos_document_response.description,
    )
    return document_response


def get_documents_as_leave_admin(fineos_user_id: str, absence_id: str) -> List[DocumentResponse]:
    """
    Given an absence ID, gets the documents associated with the claim
    """
    fineos = massgov.pfml.fineos.create_client()
    fineos_documents = fineos.group_client_get_documents(fineos_user_id, absence_id)
    # FINEOS response uses the "name" field for what we call "document_type"
    downloadable_documents = filter(
        lambda fd: fd.name.lower() in DOWNLOADABLE_DOC_TYPES, fineos_documents
    )
    document_responses = list(
        map(lambda fd: fineos_document_response_to_document_response(fd), downloadable_documents,)
    )
    return document_responses


def download_document_as_leave_admin(
    fineos_user_id: str, absence_id: str, fineos_document_id: str
) -> massgov.pfml.fineos.models.group_client_api.Base64EncodedFileData:
    fineos = massgov.pfml.fineos.create_client()

    return fineos.download_document_as_leave_admin(fineos_user_id, absence_id, fineos_document_id)


def get_claim_as_leave_admin(
    fineos_user_id: str,
    absence_id: str,
    employer: Employer,
    fineos_client: Optional[massgov.pfml.fineos.AbstractFINEOSClient] = None,
) -> Optional[ClaimReviewResponse]:
    """
    Given an absence ID, gets a full claim for the claim review page by calling multiple endpoints from FINEOS
    """
    if not fineos_client:
        fineos_client = massgov.pfml.fineos.create_client()

    absence_periods = fineos_client.get_absence_period_decisions(fineos_user_id, absence_id).dict()
    set_empty_dates_to_none(absence_periods, ["startDate", "endDate"])

    if not absence_periods.get("decisions", []):
        logger.error(
            "Did not receive leave period decisions for absence periods",
            extra={
                "fineos_user_id": fineos_user_id,
                "absence_id": absence_id,
                "employer_id": employer.employer_id,
            },
        )
        return None

    customer_id = absence_periods["decisions"][0]["employee"]["id"]
    status = absence_periods["decisions"][0]["period"]["status"] or "Unknown"
    customer_info = fineos_client.get_customer_info(fineos_user_id, customer_id).dict()
    customer_occupations = fineos_client.get_customer_occupations(
        fineos_user_id, customer_id
    ).dict()
    hours_worked_per_week = customer_occupations["elements"][0]["hrsWorkedPerWeek"]
    eform_summaries = fineos_client.get_eform_summary(fineos_user_id, absence_id)
    managed_reqs = fineos_client.get_managed_requirements(fineos_user_id, absence_id)
    other_leaves: List[PreviousLeave] = []
    other_incomes: List[EmployerBenefit] = []
    is_reviewable = False
    follow_up_date = None
    contains_version_one_eforms = False
    contains_version_two_eforms = False
    outstanding_requirement_status = None

    for req in managed_reqs:
        if req.type == LEAVE_ADMIN_INFO_REQUEST_TYPE:
            follow_up_date = req.followUpDate
            outstanding_requirement_status = req.status
            break

    for eform_summary_obj in eform_summaries:
        eform_summary = eform_summary_obj.dict()
        if eform_summary["eformType"] == EFORM_TYPES["OTHER_INCOME"]:
            contains_version_one_eforms = True
            eform = fineos_client.get_eform(fineos_user_id, absence_id, eform_summary["eformId"])
            other_incomes.extend(
                other_income
                for other_income in TransformOtherIncomeEform.from_fineos(eform)
                if other_income.program_type == "Employer"
            )
        elif eform_summary["eformType"] == EFORM_TYPES["OTHER_LEAVES"]:
            contains_version_one_eforms = True
            eform = fineos_client.get_eform(fineos_user_id, absence_id, eform_summary["eformId"])
            other_leaves = other_leaves + TransformOtherLeaveEform.from_fineos(eform)
        elif eform_summary["eformType"] == EFORM_TYPES["OTHER_INCOME_V2"]:
            contains_version_two_eforms = True
        elif eform_summary["eformType"] == EFORM_TYPES["OTHER_LEAVES_V2"]:
            contains_version_two_eforms = True

    if customer_info["address"] is not None:
        claimant_address = Address(
            line_1=customer_info["address"]["addressLine1"],
            line_2=customer_info["address"]["addressLine2"],
            city=customer_info["address"]["addressLine4"],
            state=customer_info["address"]["addressLine6"],
            zip=customer_info["address"]["postCode"],
        )
    else:
        claimant_address = Address()

    if follow_up_date is not None and outstanding_requirement_status == "Open":
        is_reviewable = date.today() < follow_up_date

    leave_details = get_leave_details(absence_periods)

    logger.info("Count of info request employer benefits:", extra={"count": len(other_incomes)})

    return ClaimReviewResponse(
        date_of_birth=customer_info["dateOfBirth"],
        employer_benefits=other_incomes,
        employer_fein=employer.employer_fein,
        employer_dba=employer.employer_dba,
        employer_id=employer.employer_id,
        fineos_absence_id=absence_id,
        first_name=customer_info["firstName"],
        hours_worked_per_week=hours_worked_per_week,
        last_name=customer_info["lastName"],
        leave_details=leave_details,
        middle_name=customer_info["secondName"],
        previous_leaves=other_leaves,
        residential_address=claimant_address,
        tax_identifier=customer_info["idNumber"] if customer_info["idNumber"] is not None else "",
        status=status,
        follow_up_date=follow_up_date,
        is_reviewable=is_reviewable,
        contains_version_one_eforms=contains_version_one_eforms,
        contains_version_two_eforms=contains_version_two_eforms,
    )


def register_leave_admin_with_fineos(
    admin_full_name: str,
    admin_email: str,
    admin_area_code: Optional[str],
    admin_phone_number: Optional[str],
    employer: Employer,
    user: User,
    db_session: massgov.pfml.db.Session,
    fineos_client: Optional[massgov.pfml.fineos.AbstractFINEOSClient],
    force_register: Optional[bool] = False,
) -> UserLeaveAdministrator:
    """
    Given information about a Leave administrator, create a FINEOS user for that leave admin
    and associate that user to the leave admin within the PFML DB
    """
    leave_admin_record = (
        db_session.query(UserLeaveAdministrator)
        .filter(
            UserLeaveAdministrator.user_id == user.user_id,
            UserLeaveAdministrator.employer_id == employer.employer_id,
        )
        .one_or_none()
    )

    if leave_admin_record and leave_admin_record.fineos_web_id is not None:
        if not force_register:
            logger.info(
                "User previously registered in FINEOS and force_register off",
                extra={"email": admin_email, "fineos_web_id": leave_admin_record.fineos_web_id},
            )
            return leave_admin_record

    fineos = fineos_client if fineos_client else massgov.pfml.fineos.create_client()
    fineos_web_id = f"pfml_leave_admin_{str(uuid.uuid4())}"
    logger.info(
        "Calling FINEOS to Create Leave Admin",
        extra={"email": admin_email, "fineos_web_id": fineos_web_id},
    )
    leave_admin_create_payload = CreateOrUpdateLeaveAdmin(
        fineos_web_id=fineos_web_id,
        fineos_employer_id=str(employer.fineos_employer_id),
        admin_full_name=admin_full_name,
        admin_area_code=admin_area_code,
        admin_phone_number=admin_phone_number,
        admin_email=admin_email,
    )
    fineos.create_or_update_leave_admin(leave_admin_create_payload)

    if leave_admin_record:
        leave_admin_record.fineos_web_id = fineos_web_id
    else:
        leave_admin_record = UserLeaveAdministrator(
            user=user, employer=employer, fineos_web_id=fineos_web_id
        )
    db_session.add(leave_admin_record)
    db_session.commit()
    return leave_admin_record


def create_eform(user_id: str, absence_id: str, eform: EFormBody) -> None:
    fineos = massgov.pfml.fineos.create_client()
    fineos.create_eform(user_id, absence_id, eform)


def awaiting_leave_info(user_id: str, absence_id: str) -> bool:
    fineos = massgov.pfml.fineos.create_client()

    # FINEOS throws an error if we attempt to update outstanding information that is not needed.
    # Determine if employer confirmation is outstanding and mark it as received if it is.
    outstanding_information = fineos.get_outstanding_information(user_id, absence_id)

    for information in outstanding_information:
        if (
            not information.infoReceived
            and information.informationType == LEAVE_ADMIN_INFO_REQUEST_TYPE
        ):
            return True

    return False


def complete_claim_review(user_id: str, absence_id: str) -> None:
    fineos = massgov.pfml.fineos.create_client()

    # By time this function is called, we should
    # have already checked that there is outstanding information.
    received_information = massgov.pfml.fineos.models.group_client_api.OutstandingInformationData(
        informationType=LEAVE_ADMIN_INFO_REQUEST_TYPE
    )
    fineos.update_outstanding_information_as_received(user_id, absence_id, received_information)

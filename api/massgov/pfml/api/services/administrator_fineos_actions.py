import mimetypes
import uuid
from typing import Dict, List, Optional

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.api.models.claims.common import (
    Address,
    EmployerBenefit,
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
from massgov.pfml.fineos.transforms.to_fineos.eforms import EFormBody

LEAVE_ADMIN_INFO_REQUEST_TYPE = "Employer Confirmation of Leave Data"

logger = logging.get_logger(__name__)


def get_leave_details(absence_periods: Dict) -> LeaveDetails:
    # TODO Currently only parsing absence periods for a single leave,
    # but will need to support mixed schedule: https://lwd.atlassian.net/browse/EMPLOYER-449
    """ Extracts absence data based on a PeriodDecisions dict and returns a LeaveDetails """
    leave_details = {}
    leave_details["reason"] = absence_periods["decisions"][0]["period"]["leaveRequest"][
        "reasonName"
    ]

    if absence_periods["decisions"][0]["period"]["type"] == "Time off period":
        leave_details["continuous_leave_periods"] = [
            StandardLeavePeriod(
                start_date=absence_periods["startDate"], end_date=absence_periods["endDate"]
            )
        ]
    # FINEOS has yet to implement data for Episodic (intermittent) leaves
    # TODO when this info is available https://lwd.atlassian.net/browse/EMPLOYER-448
    #
    # elif(absence_periods["decisions"][0]["period"]["type"] == "Episodic"):
    #     leave_details["intermittent_leave_periods"] = IntermittentLeavePeriod(
    #         start_date=absence_periods["startDate"],
    #         end_date=absence_periods["endDate"]
    #     )
    elif absence_periods["decisions"][0]["period"]["type"] == "Reduced Schedule":
        leave_details["reduced_schedule_leave_periods"] = [
            StandardLeavePeriod(
                start_date=absence_periods["startDate"], end_date=absence_periods["endDate"]
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
    try:
        fineos = massgov.pfml.fineos.create_client()
        fineos_documents = fineos.group_client_get_documents(fineos_user_id, absence_id)
        document_responses = list(
            map(lambda fd: fineos_document_response_to_document_response(fd), fineos_documents,)
        )
        return document_responses
    except massgov.pfml.fineos.FINEOSClientError as error:
        logger.exception("FINEOS Client Exception", extra={"error": error})
        raise ValueError("FINEOS Client Exception")


def download_document_as_leave_admin(
    fineos_user_id: str, absence_id: str, fineos_document_id: str
) -> massgov.pfml.fineos.models.group_client_api.Base64EncodedFileData:
    try:
        fineos = massgov.pfml.fineos.create_client()

        return fineos.download_document_as_leave_admin(
            fineos_user_id, absence_id, fineos_document_id
        )

    except massgov.pfml.fineos.FINEOSClientError:
        logger.exception("FINEOS Client Exception")
        raise ValueError("FINEOS Client Exception")


def get_claim_as_leave_admin(
    fineos_user_id: str, absence_id: str, employer_fein: str
) -> ClaimReviewResponse:
    """
    Given an absence ID, gets a full claim for the claim review page by calling multiple endpoints from FINEOS
    """
    try:
        fineos = massgov.pfml.fineos.create_client()
        absence_periods = fineos.get_absence_period_decisions(fineos_user_id, absence_id).dict()
        customer_id = absence_periods["decisions"][0]["employee"]["id"]
        customer_info = fineos.get_customer_info(fineos_user_id, customer_id).dict()
        customer_occupations = fineos.get_customer_occupations(fineos_user_id, customer_id).dict()
        hours_worked_per_week = customer_occupations["elements"][0]["hrsWorkedPerWeek"]
        eform_summaries = fineos.get_eform_summary(fineos_user_id, absence_id)
        managed_reqs = fineos.get_managed_requirements(fineos_user_id, absence_id)
        other_leaves: List[PreviousLeave] = []
        other_incomes: List[EmployerBenefit] = []
        follow_up_date = None

        for req in managed_reqs:
            if req.type == LEAVE_ADMIN_INFO_REQUEST_TYPE:
                follow_up_date = req.followUpDate
                break

        for eform_summary_obj in eform_summaries:
            eform_summary = eform_summary_obj.dict()
            if eform_summary["eformType"] == "Other Income":
                eform = fineos.get_eform(fineos_user_id, absence_id, eform_summary["eformId"])
                other_incomes = other_incomes + TransformOtherIncomeEform.from_fineos(eform)
            elif eform_summary["eformType"] == "Other Leaves":
                eform = fineos.get_eform(fineos_user_id, absence_id, eform_summary["eformId"])
                other_leaves = other_leaves + TransformOtherLeaveEform.from_fineos(eform)

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

        leave_details = get_leave_details(absence_periods)

        return ClaimReviewResponse(
            date_of_birth=customer_info["dateOfBirth"],
            employer_benefits=other_incomes,
            employer_fein=employer_fein,
            fineos_absence_id=absence_id,
            first_name=customer_info["firstName"],
            hours_worked_per_week=hours_worked_per_week,
            last_name=customer_info["lastName"],
            leave_details=leave_details,
            middle_name=customer_info["secondName"],
            previous_leaves=other_leaves,
            residential_address=claimant_address,
            tax_identifier=customer_info["idNumber"]
            if customer_info["idNumber"] is not None
            else "",
            follow_up_date=follow_up_date,
        )
    except massgov.pfml.fineos.FINEOSClientError as error:
        logger.exception("FINEOS Client Exception", extra={"error": error})
        raise ValueError("FINEOS Client Exception")


def register_leave_admin_with_fineos(
    admin_full_name: str,
    admin_email: str,
    admin_area_code: Optional[str],
    admin_phone_number: Optional[str],
    employer: Employer,
    user: User,
    db_session: massgov.pfml.db.Session,
    fineos_client: Optional[massgov.pfml.fineos.AbstractFINEOSClient],
) -> UserLeaveAdministrator:
    """
    Given information about a Leave administrator, create a FINEOS user for that leave admin
    and associate that user to the leave admin within the PFML DB
    """
    try:
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

    except massgov.pfml.fineos.FINEOSClientError as error:
        logger.exception("FINEOS Client Exception", extra={"error": error})
        raise ValueError("FINEOS Client Exception")

    try:
        leave_admin_record = (
            db_session.query(UserLeaveAdministrator)
            .filter(
                UserLeaveAdministrator.user_id == user.user_id,
                UserLeaveAdministrator.employer_id == employer.employer_id,
            )
            .one_or_none()
        )
        if leave_admin_record:
            leave_admin_record.fineos_web_id = fineos_web_id
        else:
            leave_admin_record = UserLeaveAdministrator(
                user=user, employer=employer, fineos_web_id=fineos_web_id
            )
        db_session.add(leave_admin_record)

        return leave_admin_record
    except Exception as db_error:
        logger.exception("Error adding leave admin to DB", extra={"error": db_error})
        raise ValueError("Error adding leave admin to DB")


def create_eform(user_id: str, absence_id: str, eform: EFormBody) -> None:
    fineos = massgov.pfml.fineos.create_client()
    fineos.create_eform(user_id, absence_id, eform)


def complete_claim_review(user_id: str, absence_id: str) -> None:
    fineos = massgov.pfml.fineos.create_client()

    # FINEOS throws an error if we attempt to update outstanding information that is not needed.
    # Determine if employer confirmation is outstanding and mark it as received if it is.
    outstanding_information = fineos.get_outstanding_information(user_id, absence_id)

    for information in outstanding_information:
        if (
            not information.infoReceived
            and information.informationType == LEAVE_ADMIN_INFO_REQUEST_TYPE
        ):
            received_information = massgov.pfml.fineos.models.group_client_api.OutstandingInformationData(
                informationType=LEAVE_ADMIN_INFO_REQUEST_TYPE
            )
            fineos.update_outstanding_information_as_received(
                user_id, absence_id, received_information
            )
            break

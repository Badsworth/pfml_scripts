import mimetypes
from typing import Dict, List

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
from massgov.pfml.fineos.transforms.from_fineos.eforms import (
    TransformOtherIncomeEform,
    TransformOtherLeaveEform,
)

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
        eform_summaries = fineos.get_eform_summary(fineos_user_id, absence_id)
        other_leaves: List[PreviousLeave] = []
        other_incomes: List[EmployerBenefit] = []

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
            last_name=customer_info["lastName"],
            leave_details=leave_details,
            middle_name=customer_info["secondName"],
            previous_leaves=other_leaves,
            residential_address=claimant_address,
            tax_identifier=customer_info["idNumber"][-4:]
            if customer_info["idNumber"] is not None
            else "",
        )
    except massgov.pfml.fineos.FINEOSClientError as error:
        logger.exception("FINEOS Client Exception", extra={"error": error})
        raise ValueError("FINEOS Client Exception")

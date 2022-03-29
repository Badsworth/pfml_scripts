import mimetypes
import uuid
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pydantic
from pydantic.types import UUID4

import massgov.pfml.db
import massgov.pfml.fineos.models
import massgov.pfml.util.logging as logging
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.exceptions import ClaimWithdrawn, ObjectNotFound
from massgov.pfml.api.models.claims.common import (
    Address,
    IntermittentLeavePeriod,
    LeaveDetails,
    PreviousLeave,
    StandardLeavePeriod,
)
from massgov.pfml.api.models.claims.responses import ClaimReviewResponse, DocumentResponse
from massgov.pfml.api.models.common import (
    ComputedStartDates,
    ConcurrentLeave,
    EmployerBenefit,
    get_computed_start_dates,
)
from massgov.pfml.api.services.claims import maybe_update_employee_relationship
from massgov.pfml.api.services.fineos_actions import get_absence_periods
from massgov.pfml.api.validation.exceptions import ContainsV1AndV2Eforms
from massgov.pfml.db.models.employees import Employer, User, UserLeaveAdministrator
from massgov.pfml.db.queries.absence_periods import (
    convert_fineos_absence_period_to_claim_response_absence_period,
)
from massgov.pfml.fineos.common import DOWNLOADABLE_DOC_TYPES, SUB_CASE_DOC_TYPES
from massgov.pfml.fineos.models.customer_api.spec import AbsencePeriod as FineosAbsencePeriod
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    GroupClientDocument,
    ManagedRequirementDetails,
)
from massgov.pfml.fineos.models.leave_admin_creation import CreateOrUpdateLeaveAdmin
from massgov.pfml.fineos.transforms.from_fineos.eforms import (
    TransformConcurrentLeaveFromOtherLeaveEform,
    TransformEmployerBenefitsFromOtherIncomeEform,
    TransformOtherIncomeEform,
    TransformPreviousLeaveFromOtherLeaveEform,
)
from massgov.pfml.fineos.transforms.to_fineos.eforms.employer import EFormBody
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINFormattedStr, MaskedTaxIdFormattedStr

LEAVE_ADMIN_INFO_REQUEST_TYPE = "Employer Confirmation of Leave Data"

logger = logging.get_logger(__name__)


class EformTypes(str, Enum):
    OTHER_INCOME = "Other Income"
    OTHER_INCOME_V2 = "Other Income - current version"
    OTHER_LEAVES = "Other Leaves - current version"

    @classmethod
    def values(cls):
        return cls.__members__.values()


class RegisterFINEOSDuplicateRecord(Exception):
    pass


class EformDataForReview(PydanticBaseModel):
    """Data from Eforms that should be reviewed by leave admins"""

    previous_leaves: List[PreviousLeave]
    concurrent_leave: Optional[ConcurrentLeave]
    employer_benefits: List[EmployerBenefit]
    uses_second_eform_version: bool


class CustomerInfoForReview(PydanticBaseModel):
    """Data parsed from FINEOS customer info for leave admin review and claim status page"""

    date_of_birth: Optional[date] = pydantic.Field(..., alias="dateOfBirth")
    first_name: Optional[str] = pydantic.Field(..., alias="firstName")
    last_name: Optional[str] = pydantic.Field(..., alias="lastName")
    middle_name: Optional[str] = pydantic.Field(..., alias="secondName")
    tax_identifier: Optional[MaskedTaxIdFormattedStr] = pydantic.Field(..., alias="idNumber")


class EmployerInfoForReview(PydanticBaseModel):
    """Data parsed from PFML DB employer for leave admin review and claim status page"""

    employer_fein: FEINFormattedStr
    employer_dba: Optional[str]
    employer_id: UUID4


def _get_leave_details(absence_periods: Dict[str, Dict]) -> LeaveDetails:
    """Extracts absence data based on a PeriodDecisions dict and returns a LeaveDetails"""
    leave_details = {}
    leave_details["reason"] = absence_periods["decisions"][0]["period"]["leaveRequest"][
        "reasonName"
    ]
    reduced_start_date: Optional[date] = None
    reduced_end_date: Optional[date] = None
    continuous_start_date: Optional[date] = None
    continuous_end_date: Optional[date] = None
    intermittent_start_date: Optional[date] = None
    intermittent_end_date: Optional[date] = None

    for decision in absence_periods["decisions"]:
        start_date = decision["period"]["startDate"]
        end_date = decision["period"]["endDate"]

        # Note: Fineos gives us a wider range of period types than what's
        # accounted for below. We'll be removing leave_details in the future
        # though (PORTAL-1118), so this is being left as is.
        # More context: https://lwd.atlassian.net/browse/PORTAL-1296
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
            if intermittent_start_date is None or start_date < intermittent_start_date:
                intermittent_start_date = start_date

            if intermittent_end_date is None or end_date > intermittent_end_date:
                intermittent_end_date = end_date

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


def _get_computed_start_dates(absence_periods: Dict[str, Dict]) -> ComputedStartDates:
    """Extracts absence data based on a PeriodDecisions dict and returns ComputedStartDates"""
    if len(absence_periods["decisions"]) == 0 or not absence_periods["decisions"][0]["period"]:
        return ComputedStartDates(other_reason=None, same_reason=None)

    # This assumes a multiple leave claim won't have a mix of caring leave and some other leave reason
    leave_reason = absence_periods["decisions"][0]["period"]["leaveRequest"]["reasonName"]

    leave_period_start_dates = [
        decision["period"]["startDate"]
        for decision in absence_periods["decisions"]
        if decision["period"]["startDate"]
    ]
    earliest_start_date = min(leave_period_start_dates, default=None)

    return get_computed_start_dates(earliest_start_date, leave_reason)


def fineos_document_response_to_document_response(
    fineos_document_response: massgov.pfml.fineos.models.group_client_api.GroupClientDocument,
) -> DocumentResponse:
    content_type, encoding = mimetypes.guess_type(fineos_document_response.originalFilename or "")

    document_response = DocumentResponse(
        created_at=fineos_document_response.dateCreated,
        document_type=fineos_document_response.name,
        content_type=content_type,
        fineos_document_id=str(fineos_document_response.documentId),
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
        map(
            lambda fd: fineos_document_response_to_document_response(fd),
            # Certain document types are Word documents when first created, then converted to PDF documents
            # Only PDF documents should be returned to the portal
            filter(lambda fd: fd.fileExtension not in [".doc", ".docx"], downloadable_documents),
        )
    )

    return document_responses


def download_document_as_leave_admin(
    fineos_user_id: str,
    absence_id: str,
    fineos_document_id: str,
    log_attributes: Optional[Dict] = None,
) -> Base64EncodedFileData:
    if log_attributes is None:
        log_attributes = {}
    log_attributes.update(
        {
            "fineos_user_id": fineos_user_id,
            "absence_id": absence_id,
            "absence_case_id": absence_id,
            "fineos_document_id": fineos_document_id,
        }
    )

    document = _get_document(fineos_user_id, absence_id, fineos_document_id)

    if document is None:
        logger.warning("Unable to find FINEOS document for user", extra=log_attributes)
        raise ObjectNotFound(description="Unable to find FINEOS document for user")

    doc_type = document.name.lower()
    log_attributes["document.document_type"] = doc_type
    if not document.is_downloadable_by_leave_admin():
        logger.warning(
            f"Leave Admin is not authorized to download documents of type {doc_type}",
            extra=log_attributes,
        )
        raise NotAuthorizedForAccess(
            description=f"User is not authorized to access documents of type: {doc_type}",
            error_type="unauthorized_document_type",
            data={"document.document_type": doc_type},
        )
    fineos = massgov.pfml.fineos.create_client()
    # Some document types cannot be fetched from the absence case, but only from the sub case, in which case we need the corresponding case id
    if doc_type in SUB_CASE_DOC_TYPES:
        case_id = find_sub_case_id(fineos, fineos_user_id, absence_id, fineos_document_id)
    else:
        case_id = absence_id

    return fineos.download_document_as_leave_admin(fineos_user_id, case_id, fineos_document_id)


def find_sub_case_id(
    fineos: massgov.pfml.fineos.AbstractFINEOSClient,
    fineos_user_id: str,
    absence_id: str,
    fineos_document_id: str,
) -> str:
    fineos_documents = fineos.group_client_get_documents(fineos_user_id, absence_id)
    for doc in fineos_documents:
        if fineos_document_id == str(doc.documentId):
            case_id = doc.caseId
            break
    if not case_id:
        logger.warning(
            "Document with that fineos_document_id could not be found",
            extra={
                "absence_id": absence_id,
                "absence_case_id": absence_id,
                "fineos_document_id": fineos_document_id,
            },
        )
        raise Exception("Document with that fineos_document_id could not be found")
    return case_id


def _get_document(
    fineos_user_id: str, absence_id: str, fineos_document_id: str
) -> Optional[GroupClientDocument]:
    fineos = massgov.pfml.fineos.create_client()

    documents = fineos.group_client_get_documents(fineos_user_id, absence_id)
    return next((doc for doc in documents if str(doc.documentId) == fineos_document_id), None)


def _parse_eform_data(
    fineos_client: massgov.pfml.fineos.AbstractFINEOSClient,
    fineos_user_id: str,
    absence_id: str,
    log_attributes: Dict,
) -> EformDataForReview:
    """Retrieve Eforms data from FINEOS and parse them for leave admin review"""

    previous_leaves: List[PreviousLeave] = []
    concurrent_leave: Optional[ConcurrentLeave] = None
    employer_benefits: List[EmployerBenefit] = []
    contains_version_one_eforms = False
    contains_version_two_eforms = False

    eform_summaries = fineos_client.get_eform_summary(fineos_user_id, absence_id)

    for eform_summary in eform_summaries:
        if eform_summary.eformType not in EformTypes.values():
            continue

        eform = fineos_client.get_eform(fineos_user_id, absence_id, eform_summary.eformId)

        if eform_summary.eformType == EformTypes.OTHER_INCOME:
            logger.info("Claim contains an other income eform", extra=log_attributes)
            contains_version_one_eforms = True

            employer_benefits.extend(
                other_income
                for other_income in TransformOtherIncomeEform.from_fineos(eform)
                if other_income.program_type == "Employer"
            )

        elif eform_summary.eformType == EformTypes.OTHER_INCOME_V2:
            logger.info("Claim contains an other income V2 eform", extra=log_attributes)
            contains_version_two_eforms = True

            employer_benefits.extend(
                TransformEmployerBenefitsFromOtherIncomeEform.from_fineos(eform)
            )

        elif eform_summary.eformType == EformTypes.OTHER_LEAVES:
            logger.info("Claim contains an other leaves eform", extra=log_attributes)
            contains_version_two_eforms = True

            previous_leaves.extend(
                previous_leave
                for previous_leave in TransformPreviousLeaveFromOtherLeaveEform.from_fineos(eform)
                if previous_leave.is_for_current_employer
            )

            concurrent_leave = TransformConcurrentLeaveFromOtherLeaveEform.from_fineos(eform)
            if concurrent_leave and not concurrent_leave.is_for_current_employer:
                concurrent_leave = None

    if contains_version_one_eforms and contains_version_two_eforms:
        logger.error("Contains version one and version two eforms", extra=log_attributes)
        raise ContainsV1AndV2Eforms()

    # Default to version two eforms unless this is a legacy case containing version one eforms
    uses_second_eform_version = not contains_version_one_eforms
    logger.info(
        "Count of info request employer benefits:",
        extra={**log_attributes, "count": len(employer_benefits)},
    )

    return EformDataForReview(
        concurrent_leave=concurrent_leave,
        previous_leaves=previous_leaves,
        employer_benefits=employer_benefits,
        uses_second_eform_version=uses_second_eform_version,
    )


def get_claim_as_leave_admin(
    fineos_user_id: str,
    absence_id: str,
    employer: Employer,
    db_session: massgov.pfml.db.Session,
    fineos_client: Optional[massgov.pfml.fineos.AbstractFINEOSClient] = None,
) -> Tuple[ClaimReviewResponse, List[ManagedRequirementDetails], List[FineosAbsencePeriod]]:
    """
    Gets all absence case details from Fineos for a Leave Admin to review.
    """

    log_attributes = {
        "fineos_user_id": fineos_user_id,
        "absence_id": absence_id,
        "absence_case_id": absence_id,
        "employer_id": employer.employer_id,
    }

    if not fineos_client:
        fineos_client = massgov.pfml.fineos.create_client()

    # Retrieve absence periods and eventually sync them back to the database.
    # In order to mitigate security concerns and continue to ensure this leave admin
    # should have access to the absence case, we first perform a Group Client
    # call before making a Fineos Customer API call. The Customer API is used because
    # the Fineos Group Client didn't include an endpoint for retrieving absence periods.
    # See: https://lwd.atlassian.net/l/c/KYnUpPEq
    absence_period_decisions = fineos_client.get_absence_period_decisions(
        fineos_user_id, absence_id
    )
    if not absence_period_decisions.decisions:
        logger.error(
            "Did not receive leave period decisions for absence periods", extra=log_attributes
        )
        raise ClaimWithdrawn()

    # We retrieve the Employee from Fineos, rather than through the Claim in our DB,
    # since it's not guranteed that the Employee will be set yet for cases created
    # through the contact center.
    fineos_employee = absence_period_decisions.decisions[0].employee
    if fineos_employee is None or fineos_employee.id is None:
        raise ValueError("Absence period is missing an associated employee or ID")

    customer_info = fineos_client.get_customer_info(fineos_user_id, fineos_employee.id)
    tax_identifier = customer_info.idNumber

    if tax_identifier is None:
        raise ValueError("Employee tax identifier was empty")

    maybe_update_employee_relationship(absence_id, tax_identifier)
    absence_periods = get_absence_periods(
        absence_id,
        tax_identifier,
        employer.employer_fein,
        db_session,
        str(employer.fineos_employer_id),
    )

    # TODO (PORTAL-1118):
    #   The status gets overwritten in the review endpoint by DB claim status in order to match the status shown to claimants.
    #   Once the status page is surfacing absence periods, we can remove this.
    first_period = absence_period_decisions.decisions[0].period
    status = (first_period.status if first_period else None) or "Unknown"

    # TODO (PORTAL-1118):
    #   This field is deprecated. Once the review page is surfacing absence periods, we can remove this.
    leave_details = _get_leave_details(absence_period_decisions.dict())

    # Calculate the claimant's hours_worked_per_week.
    customer_occupations = fineos_client.get_customer_occupations(
        fineos_user_id, fineos_employee.id
    )
    if customer_occupations.elements is None:
        raise ValueError("No customer occupations were returned")
    hours_worked_per_week = customer_occupations.elements[0].hrsWorkedPerWeek

    # Determine if the claim needs a review from the leave admin.
    managed_reqs = fineos_client.get_managed_requirements(fineos_user_id, absence_id)

    # Pull existing eforms data, like "Employer benefits", for the claim
    eform_data = _parse_eform_data(fineos_client, fineos_user_id, absence_id, log_attributes)

    # Parse claimant and employer details
    if customer_info.address is None:
        claimant_address = Address()
    else:
        claimant_address = Address(
            line_1=customer_info.address.addressLine1,
            line_2=customer_info.address.addressLine2,
            city=customer_info.address.addressLine4,
            state=customer_info.address.addressLine6,
            zip=customer_info.address.postCode,
        )

    customer_info_for_review = CustomerInfoForReview.parse_obj(customer_info)
    employer_info_for_review = EmployerInfoForReview.from_orm(employer)

    # Get computed start dates based on absence_periods
    computed_start_dates = _get_computed_start_dates(absence_period_decisions.dict())

    return (
        ClaimReviewResponse(
            **customer_info_for_review.dict(),
            **employer_info_for_review.dict(),
            **eform_data.dict(),
            fineos_absence_id=absence_id,
            hours_worked_per_week=hours_worked_per_week,
            residential_address=claimant_address,
            leave_details=leave_details,
            status=status,
            absence_periods=[
                convert_fineos_absence_period_to_claim_response_absence_period(
                    absence_period, log_attributes
                )
                for absence_period in absence_periods
            ],
            computed_start_dates=computed_start_dates,
        ),
        managed_reqs,
        absence_periods,
    )


def generate_fineos_web_id() -> str:
    return f"pfml_leave_admin_{str(uuid.uuid4())}"


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
    fineos_web_id = generate_fineos_web_id()
    logger.info(
        "Calling FINEOS to Create Leave Admin",
        extra={"email": admin_email, "fineos_web_id": fineos_web_id},
    )
    if not employer.fineos_employer_id:
        raise ValueError("Employer must have a Fineos employer ID to register a leave admin.")
    leave_admin_create_payload = CreateOrUpdateLeaveAdmin(
        fineos_web_id=fineos_web_id,
        fineos_employer_id=employer.fineos_employer_id,
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

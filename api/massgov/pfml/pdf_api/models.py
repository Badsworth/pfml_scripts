from typing import Any, Optional

from massgov.pfml.db.models.payments import Pfml1099
from massgov.pfml.util.pydantic import PydanticBaseModel

from . import common


class MergePDFRequest(PydanticBaseModel):
    type: Optional[str]
    batchId: str
    numOfRecords: Optional[int]

    def __init__(self, **args: Any):
        _type = args.get("type", None)
        self.type = _type if _type in common.DOC_TYPES else None
        self.batchId = str(args.get("batch_id"))
        self.numOfRecords = int(args.get("numOfRecords", None)) or None


class GeneratePDFRequest(PydanticBaseModel):
    id: str
    batchId: Optional[str]
    type: str


class PDF1099(GeneratePDFRequest):
    year: Optional[int]
    corrected: Optional[bool]
    paymentAmount: Optional[str]
    socialNumber: str
    sub_batch: str
    federalTaxesWithheld: Optional[str]
    stateTaxesWithheld: Optional[str]
    repayments: Optional[str]
    name: Optional[str]
    address: Optional[str]
    address2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zipCode: Optional[str]
    accountNumber: Optional[str]

    def __init__(self, record: Pfml1099, **args: Any):
        self.id = str(record.pfml_1099_id)
        self.batchId = str(record.pfml_1099_batch_id)
        self.type = common.PDF_1099
        self.year = record.tax_year
        self.corrected = record.correction_ind
        self.paymentAmount = str(record.gross_payments)
        self.socialNumber = args.get("socialNumber", None)
        self.federalTaxesWithheld = str(record.federal_tax_withholdings)
        self.stateTaxesWithheld = str(record.state_tax_withholdings)
        self.repayments = str(record.overpayment_repayments)
        sub_batch = args.get("sub_batch", None)
        self.name = f"{sub_batch}/{record.first_name} {record.last_name}"
        self.address = record.address_line_1
        self.address2 = record.address_line_2
        self.city = record.city
        self.state = record.state
        self.zipCode = record.zip
        self.accountNumber = record.account_number


class PDFClaimantInfo(GeneratePDFRequest):
    applicationId: str
    submissionTime: str
    name: str
    address: str
    dateOfBirth: str
    gender: str
    email: str
    phone: str
    idNumber: str
    hoursWorkedPerWeek: str
    ssn: str
    fein: str
    employerName: str
    dateOfHire: str
    stillWorksForEmployer: str
    requestedLeaveReason: str
    requestedLeaveStartDate: str

    # TODO: "record" argument type
    def __init__(self, record: Pfml1099, **args: Any):
        self.type = common.PDF_CLAIMANT_INFO

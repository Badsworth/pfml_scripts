from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, cast

from massgov.pfml.util.pydantic import PydanticBaseModel

from . import common


class MergePDFRequest(PydanticBaseModel):
    type: Optional[str]
    batchId: str
    numOfRecords: Optional[int]

    def __init__(self, **args: Dict[str, Any]):
        self.type = args.type if args.type in common.DOC_TYPES else None
        self.batchId = args.batch_id
        self.numOfRecords = args.numOfRecords or None


class GeneratePDFRequest(PydanticBaseModel):
    id: str
    batchId: Optional[str]
    type: str


class PDF1099(GeneratePDFRequest):
    year: str
    corrected: str
    paymentAmount: str
    socialNumber: str
    federalTaxesWithheld: str
    stateTaxesWithheld: str
    repayments: str
    name: str
    address: str
    address2: str
    city: str
    state: str
    zipCode: str
    accountNumber: str

    def __init__(self, record: Pfml1099, **args: Dict[str, Any]):
        self.id = str(record.pfml_1099_id)
        self.batchId = str(record.pfml_1099_batch_id)
        self.type = common.PDF_1099
        self.year = record.tax_year
        self.corrected = record.correction_ind
        self.paymentAmount = str(record.gross_payments)
        self.socialNumber = args.ssn
        self.federalTaxesWithheld = str(record.federal_tax_withholdings)
        self.stateTaxesWithheld = str(record.state_tax_withholdings)
        self.repayments = str(record.overpayment_repayments)
        self.name = f"{args.sub_batch}/{record.first_name} {record.last_name}"
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
    def __init__(self, record: Pfml1099, **args: Dict[str, Any]):
        self.type = common.PDF_CLAIMANT_INFO

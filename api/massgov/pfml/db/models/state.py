from sqlalchemy import Column, ForeignKey, Integer, Text

from ..lookup import LookupTable
from .base import Base


class LkFlow(Base):
    __tablename__ = "lk_flow"
    flow_id = Column(Integer, primary_key=True, autoincrement=True)
    flow_description = Column(Text, nullable=False)

    def __init__(self, flow_id, flow_description):
        self.flow_id = flow_id
        self.flow_description = flow_description


class LkState(Base):
    __tablename__ = "lk_state"
    state_id = Column(Integer, primary_key=True, autoincrement=True)
    state_description = Column(Text, nullable=False)
    flow_id = Column(Integer, ForeignKey("lk_flow.flow_id"))

    def __init__(self, state_id, state_description, flow_id):
        self.state_id = state_id
        self.state_description = state_description
        self.flow_id = flow_id


class Flow(LookupTable):
    model = LkFlow
    column_names = ("flow_id", "flow_description")

    PAYMENT = LkFlow(1, "Payment")
    DUA_CLAIMANT_LIST = LkFlow(2, "DUA claimant list")
    DIA_CLAIMANT_LIST = LkFlow(3, "DIA claimant list")
    DUA_PAYMENT_LIST = LkFlow(4, "DUA payment list")
    DIA_PAYMENT_LIST = LkFlow(5, "DIA payment list")
    DFML_AGENCY_REDUCTION_REPORT = LkFlow(6, "DFML agency reduction report")
    VENDOR_CHECK = LkFlow(7, "Vendor check")
    VENDOR_EFT = LkFlow(8, "Vendor EFT")
    UNUSED = LkFlow(9, "Unused flow")
    PEI_WRITEBACK_FILES = LkFlow(10, "PEI Writeback files")
    DFML_DUA_REDUCTION_REPORT = LkFlow(11, "DUA agency reduction report")
    DFML_DIA_REDUCTION_REPORT = LkFlow(12, "DIA agency reduction report")

    # ==============================
    # Delegated Payments Flows
    # ==============================
    DELEGATED_CLAIMANT = LkFlow(20, "Claimant")
    DELEGATED_PAYMENT = LkFlow(21, "Payment")
    DELEGATED_EFT = LkFlow(22, "EFT")
    DELEGATED_CLAIM_VALIDATION = LkFlow(23, "Claim Validation")
    DELEGATED_PEI_WRITEBACK = LkFlow(24, "Payment PEI Writeback")

    LEGACY_MMARS_PAYMENTS = LkFlow(25, "Legacy MMARS Payment")


class State(LookupTable):
    model = LkState
    column_names = ("state_id", "state_description", "flow_id")

    VERIFY_VENDOR_STATUS = LkState(1, "Verify vendor status", Flow.UNUSED.flow_id)  # Not used
    DIA_CLAIMANT_LIST_CREATED = LkState(
        2, "Create claimant list for DIA", Flow.DIA_CLAIMANT_LIST.flow_id
    )
    DIA_CLAIMANT_LIST_SUBMITTED = LkState(
        3, "Submit claimant list to DIA", Flow.DIA_CLAIMANT_LIST.flow_id
    )
    PAYMENTS_RETRIEVED = LkState(4, "Payments retrieved", Flow.UNUSED.flow_id)  # Not used
    PAYMENTS_STORED_IN_DB = LkState(5, "Payments stored in db", Flow.UNUSED.flow_id)  # Not used
    DUA_REPORT_FOR_DFML_CREATED = LkState(
        6, "Create DUA report for DFML", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
    )
    # not used, see DUA_REDUCTIONS_REPORT_SENT
    DUA_REPORT_FOR_DFML_SUBMITTED = LkState(
        7, "Submit DUA report for DFML", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
    )

    # Payments State Machine LucidChart: https://app.lucidchart.com/lucidchart/invitations/accept/8ae0d129-b21e-4678-8f98-0b0feafb9ace
    # States for Payment flow
    PAYMENT_PROCESS_INITIATED = LkState(8, "Payment process initiated", Flow.PAYMENT.flow_id)
    ADD_TO_PAYMENT_EXPORT_ERROR_REPORT = LkState(
        9, "Add to payment export error report", Flow.PAYMENT.flow_id
    )
    PAYMENT_EXPORT_ERROR_REPORT_SENT = LkState(
        10, "Payment export error report sent", Flow.PAYMENT.flow_id
    )
    MARK_AS_EXTRACTED_IN_FINEOS = LkState(11, "Mark as extracted in FINEOS", Flow.PAYMENT.flow_id)
    CONFIRM_VENDOR_STATUS_IN_MMARS = LkState(
        12, "Confirm vendor status in MMARS", Flow.PAYMENT.flow_id
    )
    PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED = LkState(
        13, "Payment: allowable time in state exceeded", Flow.PAYMENT.flow_id
    )
    ADD_TO_GAX = LkState(14, "Add to GAX", Flow.PAYMENT.flow_id)
    GAX_SENT = LkState(15, "GAX sent", Flow.PAYMENT.flow_id)
    ADD_TO_GAX_ERROR_REPORT = LkState(16, "Add to GAX error report", Flow.PAYMENT.flow_id)
    GAX_ERROR_REPORT_SENT = LkState(17, "GAX error report sent", Flow.PAYMENT.flow_id)
    CONFIRM_PAYMENT = LkState(18, "Confirm payment", Flow.PAYMENT.flow_id)
    SEND_PAYMENT_DETAILS_TO_FINEOS = LkState(
        19, "Send payment details to FINEOS", Flow.PAYMENT.flow_id
    )
    PAYMENT_COMPLETE = LkState(20, "Payment complete", Flow.PAYMENT.flow_id)

    # States for Vendor Check flow
    VENDOR_CHECK_INITIATED_BY_VENDOR_EXPORT = LkState(
        21, "Vendor check initiated by vendor export", Flow.VENDOR_CHECK.flow_id
    )
    ADD_TO_VENDOR_EXPORT_ERROR_REPORT = LkState(
        22, "Add to vendor export error report", Flow.VENDOR_CHECK.flow_id
    )
    VENDOR_EXPORT_ERROR_REPORT_SENT = LkState(
        23, "Vendor export error report sent", Flow.VENDOR_CHECK.flow_id
    )
    VENDOR_CHECK_INITIATED_BY_PAYMENT_EXPORT = LkState(
        24, "Vendor check initiated by payment export", Flow.VENDOR_CHECK.flow_id
    )
    IDENTIFY_MMARS_STATUS = LkState(25, "Identify MMARS status", Flow.VENDOR_CHECK.flow_id)
    ADD_TO_VCM_REPORT = LkState(26, "Add to VCM report", Flow.VENDOR_CHECK.flow_id)
    VCM_REPORT_SENT = LkState(27, "VCM report sent", Flow.VENDOR_CHECK.flow_id)
    VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED = LkState(
        28, "Vendor: allowable time in state exceeded", Flow.VENDOR_CHECK.flow_id
    )
    ADD_TO_VCC = LkState(29, "Add to VCC", Flow.VENDOR_CHECK.flow_id)
    VCC_SENT = LkState(30, "VCC sent", Flow.VENDOR_CHECK.flow_id)
    ADD_TO_VCC_ERROR_REPORT = LkState(31, "Add to VCC error report", Flow.VENDOR_CHECK.flow_id)
    VCC_ERROR_REPORT_SENT = LkState(32, "VCC error report sent", Flow.VENDOR_CHECK.flow_id)
    MMARS_STATUS_CONFIRMED = LkState(33, "MMARS status confirmed", Flow.VENDOR_CHECK.flow_id)

    # States for Vendor EFT flow
    EFT_DETECTED_IN_VENDOR_EXPORT = LkState(
        34, "EFT detected in vendor export", Flow.VENDOR_EFT.flow_id
    )
    EFT_DETECTED_IN_PAYMENT_EXPORT = LkState(
        35, "EFT detected in payment export", Flow.VENDOR_EFT.flow_id
    )
    EFT_REQUEST_RECEIVED = LkState(36, "EFT request received", Flow.VENDOR_EFT.flow_id)
    EFT_PENDING = LkState(37, "EFT pending", Flow.VENDOR_EFT.flow_id)
    ADD_TO_EFT_ERROR_REPORT = LkState(38, "Add to EFT error report", Flow.VENDOR_EFT.flow_id)
    EFT_ERROR_REPORT_SENT = LkState(39, "EFT error report sent", Flow.VENDOR_EFT.flow_id)
    EFT_ALLOWABLE_TIME_IN_STATE_EXCEEDED = LkState(
        40, "EFT: allowable time in state exceeded", Flow.VENDOR_EFT.flow_id
    )
    EFT_ELIGIBLE = LkState(41, "EFT eligible", Flow.VENDOR_EFT.flow_id)

    # State for sending the PEI writeback file to FINEOS.
    # https://app.lucidchart.com/lucidchart/3ad90c37-4cbb-467e-bfcf-bc98504c98f2/edit
    SEND_PEI_WRITEBACK = LkState(42, "Send PEI writeback", Flow.PEI_WRITEBACK_FILES.flow_id)
    PEI_WRITEBACK_SENT = LkState(
        43, "PEI writeback sent to FINEOS", Flow.PEI_WRITEBACK_FILES.flow_id
    )

    # DUA payment list retrieval.
    DUA_PAYMENT_LIST_SAVED_TO_S3 = LkState(
        44, "DUA payment list saved to S3", Flow.DUA_PAYMENT_LIST.flow_id
    )
    DUA_PAYMENT_LIST_SAVED_TO_DB = LkState(
        45, "New DUA payments stored in database", Flow.DUA_PAYMENT_LIST.flow_id
    )

    # DUA claimant list operations.
    DUA_CLAIMANT_LIST_CREATED = LkState(
        46, "Created claimant list for DUA", Flow.DUA_CLAIMANT_LIST.flow_id
    )
    DUA_CLAIMANT_LIST_SUBMITTED = LkState(
        47, "Submitted claimant list to DIA", Flow.DUA_CLAIMANT_LIST.flow_id
    )

    # DIA payment list retrieval.
    DIA_PAYMENT_LIST_SAVED_TO_S3 = LkState(
        48, "DIA payment list saved to S3", Flow.DIA_PAYMENT_LIST.flow_id
    )
    DIA_PAYMENT_LIST_SAVED_TO_DB = LkState(
        49, "New DIA payments stored in database", Flow.DIA_PAYMENT_LIST.flow_id
    )

    # State for sending new reductions payments to DFML
    DIA_REDUCTIONS_REPORT_SENT = LkState(
        50,
        "New DIA reductions payments report sent to DFML",
        Flow.DFML_DIA_REDUCTION_REPORT.flow_id,
    )
    DUA_REDUCTIONS_REPORT_SENT = LkState(
        51,
        "New DUA reductions payments report sent to DFML",
        Flow.DFML_DUA_REDUCTION_REPORT.flow_id,
    )

    DIA_REPORT_FOR_DFML_CREATED = LkState(
        162, "Create DIA report for DFML", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
    )

    # ==============================
    # Delegated Payments States
    # https://lucid.app/lucidchart/edf54a33-1a3f-432d-82b7-157cf02667a4/edit?useCachedRole=false&shared=true&page=NnnYFBRiym9J#
    # ==============================

    # == Claimant States

    DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS = LkState(
        100, "Claimant extracted from FINEOS", Flow.DELEGATED_CLAIMANT.flow_id
    )
    DELEGATED_CLAIMANT_ADD_TO_CLAIMANT_EXTRACT_ERROR_REPORT = LkState(
        101, "Add to Claimant Extract Error Report", Flow.DELEGATED_CLAIMANT.flow_id
    )
    DEPRECATED_DELEGATED_CLAIMANT_EXTRACT_ERROR_REPORT_SENT = LkState(
        102,
        "DEPRECATED STATE - Claimant Extract Error Report sent",
        Flow.DELEGATED_CLAIMANT.flow_id,
    )

    # == EFT States

    DELEGATED_EFT_SEND_PRENOTE = LkState(110, "Send EFT Prenote", Flow.DELEGATED_EFT.flow_id)
    DELEGATED_EFT_PRENOTE_SENT = LkState(111, "EFT Prenote Sent", Flow.DELEGATED_EFT.flow_id)
    DEPRECATED_DELEGATED_EFT_ALLOWABLE_TIME_IN_PRENOTE_STATE_EXCEEDED = LkState(
        112,
        "DEPRECATED STATE - EFT alllowable time in Prenote state exceeded",
        Flow.DELEGATED_EFT.flow_id,
    )
    DEPRECATED_DELEGATED_EFT_ELIGIBLE = LkState(
        113, "DEPRECATED STATE - EFT eligible", Flow.DELEGATED_EFT.flow_id
    )
    DEPRECATED_DELEGATED_EFT_ADD_TO_ERROR_REPORT = LkState(
        114, "DEPRECATED STATE - Add to EFT Error Report", Flow.DELEGATED_EFT.flow_id
    )
    DEPRECATED_DELEGATED_EFT_ERROR_REPORT_SENT = LkState(
        115, "DEPRECATED STATE - EFT Error Report sent", Flow.DELEGATED_EFT.flow_id
    )

    # == Payment States

    # FINEOS Extract stage
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT = LkState(
        120, "Add to Payment Error Report", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ERROR_REPORT_SENT = LkState(
        121, "DEPRECATED STATE - Payment Error Report sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT = LkState(
        122, "Processed - $0 payment", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        123, "DEPRECATED STATE - Add $0 payment to FINEOS Writeback", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        124, "DEPRECATED STATE - $0 payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT = LkState(
        125, "Processed - overpayment", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK = LkState(
        126,
        "DEPRECATED STATE - Add overpayment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPREACTED_DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        127, "DEPRECATED STATE - Overpayment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING = LkState(
        128, "Staged for Payment Audit Report sampling", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT = LkState(
        129, "Add to Payment Audit Report", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT = LkState(
        130, "Payment Audit Report sent", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED = LkState(
        131,
        "Waiting for Payment Audit Report response - not sampled",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # Payment Rejects processing stage
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT = LkState(
        132, "Add to Payment Reject Report", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        134,
        "DEPRECATED STATE - Add accepted payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_ACCEPTED_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        135,
        "DEPRECATED STATE - Accepted payment FINEOS Writeback sent",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    DELEGATED_PAYMENT_VALIDATED = LkState(157, "Payment Validated", Flow.DELEGATED_PAYMENT.flow_id)

    DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK = LkState(
        136, "Add to PUB Transaction - Check", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT = LkState(
        137, "PUB Transaction sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT = LkState(
        138, "Add to PUB Transaction - EFT", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT = LkState(
        139, "PUB Transaction sent - EFT", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT = LkState(
        158, "FINEOS Writeback sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT = LkState(
        159, "FINEOS Writeback sent - EFT", Flow.DELEGATED_PAYMENT.flow_id
    )

    # PUB Status Return stage
    DEPRECATED_DELEGATED_PAYMENT_ADD_TO_PUB_ERROR_REPORT = LkState(
        140, "DEPRECATED STATE - Add to PUB Error Report", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_PUB_ERROR_REPORT_SENT = LkState(
        141, "DEPRECATED STATE - PUB Error Report sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_ADD_TO_PUB_PAYMENT_FINEOS_WRITEBACK = LkState(
        142,
        "DEPRECATED STATE - Add to PUB payment FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_PUB_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        143, "DEPRECATED STATE - PUB payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_COMPLETE = LkState(144, "Payment complete", Flow.DELEGATED_PAYMENT.flow_id)

    # Delegated payment states for cancellations (similar to 122-127)
    DELEGATED_PAYMENT_PROCESSED_CANCELLATION = LkState(
        145, "Processed - Cancellation", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        146,
        "DEPRECATED STATE - Add cancellation payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        147,
        "DEPRECATED STATE - cancellation payment FINEOS Writeback sent",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # Report states for employer reimbursement payment states
    DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT = LkState(
        148, "Processed - Employer Reimbursement", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_EMPLOYER_REIMBURSEMENT_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        149,
        "DEPRECATED STATE - Add employer reimbursement payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        150,
        "DEPRECATED STATE - Employer reimbursement payment FINEOS Writeback sent",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # PEI WRITE BACK ERROR TO FINEOS
    # These states are not retryable because this is erroring after we've sent a payment to PUB
    # If there was an error, it will require a manual effort to fix.
    DEPRECATED_ADD_TO_ERRORED_PEI_WRITEBACK = LkState(
        151, "DEPRECATED STATE - Add to Errored PEI writeback", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPREACTED_ERRORED_PEI_WRITEBACK_SENT = LkState(
        152,
        "DEPRECATED STATE - Errored PEI write back sent to FINEOS",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # Delegated payments address validation states.
    DEPRECATED_CLAIMANT_READY_FOR_ADDRESS_VALIDATION = LkState(
        153,
        "DEPRECATED STATE - Claimant ready for address validation",
        Flow.DELEGATED_CLAIMANT.flow_id,
    )
    DEPRECATED_CLAIMANT_FAILED_ADDRESS_VALIDATION = LkState(
        154,
        "DEPRECATED STATE - Claimant failed address validation",
        Flow.DELEGATED_CLAIMANT.flow_id,
    )
    PAYMENT_READY_FOR_ADDRESS_VALIDATION = LkState(
        155, "Payment ready for address validation", Flow.DELEGATED_PAYMENT.flow_id
    )
    PAYMENT_FAILED_ADDRESS_VALIDATION = LkState(
        156, "Payment failed address validation", Flow.DELEGATED_PAYMENT.flow_id
    )

    # 2nd writeback to FINEOS for successful checks
    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_ADD_CHECK = LkState(
        160, "DEPRECATED STATE - Add to FINEOS Writeback #2 - Check", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_SENT_CHECK = LkState(
        161, "DEPRECATED STATE - FINEOS Writeback #2 sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_POST_PROCESSING_CHECK = LkState(
        163, "Delegated payment post processing check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS = LkState(
        164, "Claim extracted from FINEOS", Flow.DELEGATED_CLAIM_VALIDATION.flow_id
    )
    DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT = LkState(
        165, "Add to Claim Extract Error Report", Flow.DELEGATED_CLAIM_VALIDATION.flow_id
    )

    ### Generic states used to send payment transaction statuses back to FINEOS
    ###  without preventing us from receiving them again in subsequent extracts
    DELEGATED_ADD_TO_FINEOS_WRITEBACK = LkState(
        170, "Add to FINEOS writeback", Flow.DELEGATED_PEI_WRITEBACK.flow_id
    )
    DELEGATED_FINEOS_WRITEBACK_SENT = LkState(
        171, "FINEOS writeback sent", Flow.DELEGATED_PEI_WRITEBACK.flow_id
    )

    # Deprecated writeback states
    DEPRECATED_ADD_AUDIT_REJECT_TO_FINEOS_WRITEBACK = LkState(
        172,
        "DEPRECATED STATE - Add audit reject to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_AUDIT_REJECT_FINEOS_WRITEBACK_SENT = LkState(
        173,
        "DEPRECATED STATE - Audit reject FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_ADD_AUTOMATED_VALIDATION_ERROR_TO_FINEOS_WRITEBACK = LkState(
        174,
        "DEPRECATED STATE - Add automated validation error to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_AUTOMATED_VALIDATION_ERROR_FINEOS_WRITEBACK_SENT = LkState(
        175,
        "DEPRECATED STATE - Automated validation error FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_ADD_PENDING_PRENOTE_TO_FINEOS_WRITEBACK = LkState(
        176,
        "DEPRECATED STATE - Add pending prenote to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_PENDING_PRENOTE_FINEOS_WRITEBACK_SENT = LkState(
        177,
        "DEPRECATED STATE - Pending prenote FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_ADD_PRENOTE_REJECTED_ERROR_TO_FINEOS_WRITEBACK = LkState(
        178,
        "DEPRECATED STATE - Add prenote rejected error to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_PRENOTE_REJECTED_ERROR_FINEOS_WRITEBACK_SENT = LkState(
        179,
        "DEPRECATED STATE - Prenote rejected error FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )

    # Restartable error states. Payments in these states will be accepted
    # on subsequent runs of processing (assuming no other issues).
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE = LkState(
        180, "Add to Payment Error Report - RESTARTABLE", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE = LkState(
        181, "Add to Payment Reject Report - RESTARTABLE", Flow.DELEGATED_PAYMENT.flow_id
    )

    # Payment was rejected as part of a PUB ACH or Check return file processing
    # Replaces deprecated DEPRECATED_ADD_TO_ERRORED_PEI_WRITEBACK and DEPREACTED_ERRORED_PEI_WRITEBACK_SENT states as part of transition to generic writeback flow
    DELEGATED_PAYMENT_ERROR_FROM_BANK = LkState(
        182, "Payment Errored from Bank", Flow.DELEGATED_PAYMENT.flow_id
    )

    # This state signifies that a payment was successfully sent, but the
    # bank told us it had issues that may prevent payment in the future
    DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION = LkState(
        183, "Payment Complete with change notification", Flow.DELEGATED_PAYMENT.flow_id
    )

    DIA_REDUCTIONS_REPORT_ERROR = LkState(
        184,
        "Error sending DIA reductions payments report to DFML",
        Flow.DFML_DIA_REDUCTION_REPORT.flow_id,
    )

    DUA_REDUCTIONS_REPORT_ERROR = LkState(
        185,
        "Error sending DUA reductions payments report to DFML",
        Flow.DFML_DUA_REDUCTION_REPORT.flow_id,
    )

    DIA_PAYMENT_LIST_ERROR_SAVE_TO_DB = LkState(
        186, "Error saving new DIA payments in database", Flow.DIA_PAYMENT_LIST.flow_id
    )

    DUA_PAYMENT_LIST_ERROR_SAVE_TO_DB = LkState(
        187, "Error saving new DUA payments in database", Flow.DUA_PAYMENT_LIST.flow_id
    )

    DIA_CONSOLIDATED_REPORT_CREATED = LkState(
        188, "Create consolidated report for DFML", Flow.DFML_DIA_REDUCTION_REPORT.flow_id
    )
    DIA_CONSOLIDATED_REPORT_SENT = LkState(
        189, "Send consolidated DIA report for DFML", Flow.DFML_DIA_REDUCTION_REPORT.flow_id
    )

    DIA_CONSOLIDATED_REPORT_ERROR = LkState(
        190, "Consolidated DIA report for DFML error", Flow.DFML_DIA_REDUCTION_REPORT.flow_id
    )

    # Tax Withholding States
    STATE_WITHHOLDING_READY_FOR_PROCESSING = LkState(
        191, "State Withholding ready for processing", Flow.DELEGATED_PAYMENT.flow_id
    )

    STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT = LkState(
        192, "State Withholding awaiting Audit Report", Flow.DELEGATED_PAYMENT.flow_id
    )

    STATE_WITHHOLDING_ERROR = LkState(
        193, "State Withholding Rejected", Flow.DELEGATED_PAYMENT.flow_id
    )

    STATE_WITHHOLDING_SEND_FUNDS = LkState(
        194, "State Withholding send funds to DOR", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_READY_FOR_PROCESSING = LkState(
        195, "Federal Withholding ready for processing", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT = LkState(
        196, "Federal Withholding awaiting Audit Report", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_ERROR = LkState(
        197, "Federal Withholding Rejected", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_SEND_FUNDS = LkState(
        198, "Federal Withholding send funds to IRS", Flow.DELEGATED_PAYMENT.flow_id
    )

    PAYMENT_READY_FOR_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION = LkState(
        199,
        "Payment ready for max weekly benefit amount validation",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    PAYMENT_FAILED_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION = LkState(
        200, "Payment failed max weekly benefit amount validation", Flow.DELEGATED_PAYMENT.flow_id
    )

    STATE_WITHHOLDING_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE = LkState(
        201,
        "Add State Withholding to Payment Reject Report - RESTARTABLE",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    FEDERAL_WITHHOLDING_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE = LkState(
        202,
        "Add Federal Withholding to Payment Reject Report - RESTARTABLE",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    STATE_WITHHOLDING_RELATED_PENDING_AUDIT = LkState(
        203, "State Withholding Related Pending Audit", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_RELATED_PENDING_AUDIT = LkState(
        204, "Federal Withholding Related Pending Audit", Flow.DELEGATED_PAYMENT.flow_id
    )

    STATE_WITHHOLDING_ERROR_RESTARTABLE = LkState(
        205, "State Withholding Error Restartable", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_ERROR_RESTARTABLE = LkState(
        206, "Federal Withholding Error Restartable", Flow.DELEGATED_PAYMENT.flow_id
    )

    STATE_WITHHOLDING_FUNDS_SENT = LkState(
        207, "State Withholding Funds Sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    FEDERAL_WITHHOLDING_FUNDS_SENT = LkState(
        208, "Federal Withholding Funds Sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    LEGACY_MMARS_PAYMENT_PAID = LkState(
        210, "Legacy MMARS Payment Paid", Flow.LEGACY_MMARS_PAYMENTS.flow_id
    )

    EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING = LkState(
        211, "Employer Reimbursement Ready For Processing", Flow.DELEGATED_PAYMENT.flow_id
    )

    EMPLOYER_REIMBURSEMENT_RELATED_PENDING_AUDIT = LkState(
        212, "Employer Reimbursement Related Pending Audit", Flow.DELEGATED_PAYMENT.flow_id
    )

    EMPLOYER_REIMBURSEMENT_ERROR = LkState(
        214, "Employer Reimbursement Error", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_CASCADED_ERROR_RESTARTABLE = LkState(
        215, "Delegated Payment Cascaded Error Restartable", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_CASCADED_ERROR = LkState(
        216, "Delegated Payment Cascaded Error", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_RESTARTABLE = LkState(
        217, "Processed - Employer Reimbursement Restartable", Flow.DELEGATED_PAYMENT.flow_id
    )


def sync_lookup_tables(db_session):
    # Order of operations matters here:
    # Flow must be synced before State.
    Flow.sync_to_database(db_session)
    State.sync_to_database(db_session)

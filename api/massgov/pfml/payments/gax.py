import decimal
import random
import string
import xml.dom.minidom as minidom
from datetime import datetime
from typing import Dict, List, Optional, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    ClaimType,
    CtrDocumentIdentifier,
    LkPaymentMethod,
    Payment,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import Constants, email_inf_data
from massgov.pfml.util.aws.ses import EmailRecipient

logger = massgov.pfml.util.logging.get_logger(__name__)

TWOPLACES = decimal.Decimal(10) ** -2
STATE_LOG_PICKUP_STATE = State.ADD_TO_GAX

# Mappings of attributes to their static values
# These generic ones are reused by each element type
generic_attributes = {
    "DOC_CAT": "ABS",
    "DOC_TYP": "ABS",
    "DOC_CD": "GAX",
    "DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": Constants.COMPTROLLER_UNIT_CODE,
    "DOC_VERS_NO": "1",
}

ams_doc_attributes = {"DOC_IMPORT_MODE": "OE"}

# Note: DFML should never explicitly set the SCHED_PYMT_DT attribute
# CTR wants DFML to let this be calculated by MMARS
# MMARS calculates this as either VEND_INV_DT or SVC_TO_DT, whichever is later
abs_doc_vend_attributes = {
    "DOC_VEND_LN_NO": "1",
    "VEND_DISB_CAT": "350",
    "VEND_SNGL_CHK_FL": "TRUE",
}

abs_doc_actg_attributes = {
    "DOC_VEND_LN_NO": "1",
    "DOC_ACTG_LN_NO": "1",
    "EVNT_TYP_ID": "AP01",
    "VEND_INV_LN_NO": "1",
    "RFED_DOC_CD": "GAE",
    "RFED_DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "RFED_VEND_LN_NO": "1",
    "RFED_ACTG_LN_NO": "1",
    "RF_TYP": "1",
}


def get_fiscal_year(date_value: datetime) -> int:
    # Fiscal year matches calendar year for the first six months
    # of the year and is incremented by one from July onward.
    if date_value.month > 6:
        return date_value.year + 1
    return date_value.year


def get_fiscal_month(date_value: datetime) -> int:
    # Fiscal month/period is ahead by six months (January = 7, July = 1)
    # If it's the last six months, subtract 6
    if date_value.month > 6:
        return date_value.month - 6
    # Otherwise it's the first six months of the year, add six
    return date_value.month + 6


def get_activity_code(leave_type: int) -> str:
    if (
        leave_type == ClaimType.FAMILY_LEAVE.claim_type_id
        or leave_type == ClaimType.MILITARY_LEAVE.claim_type_id
    ):
        return "7246"
    if leave_type == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "7247"

    raise Exception(f"Leave type {leave_type} not found")


def get_rfed_doc_id(leave_type: int) -> str:
    # Note: the RFED_DOC_ID changes at the beginning of each fiscal year
    if (
        leave_type == ClaimType.FAMILY_LEAVE.claim_type_id
        or leave_type == ClaimType.MILITARY_LEAVE.claim_type_id
    ):
        return "PFMLFAMLFY2170030632"
    if leave_type == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "PFMLMEDIFY2170030632"

    raise Exception(f"Leave type {leave_type} not found")


def get_disbursement_format(payment_method: Optional[LkPaymentMethod]) -> Optional[str]:
    if payment_method is None:
        raise Exception("Payment method cannot be None")

    # ACH is coded as "EFT" in MMARS
    # If the payment method is ACH, then CTR wants us to allow MMARS to fill in this value.
    # MMARS sets the disbursement method to whatever is set in the AD010 address.
    if payment_method.payment_method_id == PaymentMethod.ACH.payment_method_id:
        return None
    # Check is coded as "REGW" in MMARS
    # We explicitly specify if we want the payment method to be check.
    if payment_method.payment_method_id == PaymentMethod.CHECK.payment_method_id:
        return "REGW"

    raise Exception(f"Payment method {payment_method} not found")


def get_doc_id() -> str:
    # All values we send to MMARS should be in uppercase, but the DOC_ID must be in uppercase
    # Otherwise, MMARS will enter a weird error state, so we also explicitly set to upper here
    return "INTFDFML" + "".join(random.choices(string.ascii_letters + string.digits, k=12)).upper()


def get_date_format(date_value: datetime) -> str:
    return date_value.strftime("%Y-%m-%d")


def get_payment_amount(amount: decimal.Decimal) -> str:
    if amount > 0:
        return "{:0.2f}".format(amount)
    else:
        raise ValueError(f"Payment amount needs to be greater than 0: '{amount}'")


def build_individual_gax_document(
    xml_document: minidom.Document, payment: Payment, now: datetime
) -> minidom.Element:
    try:
        claim = payment.claim
        employee = claim.employee
    except Exception as e:
        raise Exception(f"Required payment model not present {str(e)}")

    payment_date_str = payments_util.validate_db_input(
        key="payment_date",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,
        func=get_date_format,
    )
    fiscal_year = get_fiscal_year(cast(datetime, payment.payment_date))
    doc_period = get_fiscal_month(cast(datetime, payment.payment_date))
    vendor_customer_code = payments_util.validate_db_input(
        key="ctr_vendor_customer_code",
        db_object=employee,
        required=True,
        max_length=20,
        truncate=False,
    )
    monetary_amount = payments_util.validate_db_input(
        key="amount",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,  # the 10 is not a limitation that comes from MMARS
        func=get_payment_amount,
    )
    absence_case_id = payments_util.validate_db_input(
        key="fineos_absence_id", db_object=claim, required=True, max_length=19, truncate=False
    )
    # I value has a max of 10 so when it gets combines with absence_case_id (and _)
    # it is a maximum of 30 characters.
    i_value = payments_util.validate_db_input(
        key="fineos_pei_i_value", db_object=payment, required=True, max_length=10, truncate=False
    )
    # Log a warning if absence case IDs or I values are getting close to the max length
    if len(cast(str, absence_case_id)) > 17 or len(cast(str, i_value)) > 8:
        # If you're coming to this because you saw this warning, here's some more info:
        # We combine absence_case_id and i_value into a vendor_invoice_number below.
        # This value has a max length of 30 as designated by the program. If we're
        # getting close to this value, we'll need to address this maximum.
        # See discussion on https://github.com/EOLWD/pfml/pull/2837
        logger.warning(
            "Absence case ID or FINEOS PEI I value are approaching their max length",
            extra={
                "absence_case_id": absence_case_id,
                "fineos_pei_i_value": i_value,
                "payment_id": payment.payment_id,
            },
        )

    today = now.date()
    start = cast(datetime, payment.period_start_date)
    end = cast(datetime, payment.period_end_date)

    if end > today or start > end:
        raise Exception(
            f"Payment period start ({start}) and end ({end}) dates are invalid. Both need to be before now ({today})."
        )

    start_date_str = payments_util.validate_db_input(
        key="period_start_date",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,
        func=get_date_format,
    )
    end_date_str = payments_util.validate_db_input(
        key="period_end_date",
        db_object=payment,
        required=True,
        truncate=False,
        max_length=10,
        func=get_date_format,
    )

    doc_id = get_doc_id()
    activity_code = get_activity_code(claim.claim_type.claim_type_id)
    rfed_doc_id = get_rfed_doc_id(claim.claim_type.claim_type_id)
    disbursement_format = get_disbursement_format(employee.payment_method)

    vendor_invoice_number = f"{absence_case_id}_{i_value}"
    check_description = f"PFML PAYMENT {absence_case_id}"[:250]

    # Create the root of the document
    ams_document_attributes = {"DOC_ID": doc_id}
    ams_document_attributes.update(ams_doc_attributes.copy())
    ams_document_attributes.update(generic_attributes.copy())
    root = xml_document.createElement("AMS_DOCUMENT")
    payments_util.add_attributes(root, ams_document_attributes)

    # Add the ABS_DOC_HDR
    abs_doc_hdr = xml_document.createElement("ABS_DOC_HDR")
    payments_util.add_attributes(abs_doc_hdr, {"AMSDataObject": "Y"})
    root.appendChild(abs_doc_hdr)

    # Add the individual ABS_DOC_HDR values
    abs_doc_hdr_elements = {
        "DOC_ID": doc_id,
        "DOC_BFY": fiscal_year,
        "DOC_FY_DC": fiscal_year,
        "DOC_PER_DC": doc_period,
    }
    abs_doc_hdr_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_hdr, xml_document, abs_doc_hdr_elements)

    # Add the ABS_DOC_VEND
    abs_doc_vend = xml_document.createElement("ABS_DOC_VEND")
    payments_util.add_attributes(abs_doc_vend, {"AMSDataObject": "Y"})
    root.appendChild(abs_doc_vend)
    # Add the individual ABS_DOC_VEND values
    abs_doc_vend_elements = {
        "AD_ID": payments_util.Constants.COMPTROLLER_AD_ID,
        "DOC_ID": doc_id,
        "VEND_CUST_CD": vendor_customer_code,
        "DFLT_DISB_FRMT": disbursement_format,
    }
    abs_doc_vend_elements.update(abs_doc_vend_attributes.copy())
    abs_doc_vend_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_vend, xml_document, abs_doc_vend_elements)

    # Add the ABS_DOC_ACTG
    abs_doc_actg = xml_document.createElement("ABS_DOC_ACTG")
    payments_util.add_attributes(abs_doc_actg, {"AMSDataObject": "Y"})
    root.appendChild(abs_doc_actg)

    # Add the individual ABS_DOC_ACTG values.
    # Note: Both the CHK_DSCR and the VEND_INV_NO are printed on a check if the payment method is Check.
    abs_doc_actg_elements = {
        "DOC_ID": doc_id,
        "LN_AM": monetary_amount,
        "BFY": fiscal_year,
        "FY_DC": fiscal_year,
        "PER_DC": doc_period,
        "VEND_INV_NO": vendor_invoice_number,
        "VEND_INV_DT": payment_date_str,
        "CHK_DSCR": check_description,
        "RFED_DOC_ID": rfed_doc_id,
        "ACTV_CD": activity_code,
        "SVC_FRM_DT": start_date_str,
        "SVC_TO_DT": end_date_str,
    }
    abs_doc_actg_elements.update(abs_doc_actg_attributes.copy())
    abs_doc_actg_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(abs_doc_actg, xml_document, abs_doc_actg_elements)

    return root


def build_gax_dat(
    payments: List[Payment], now: datetime, ref_file: ReferenceFile, db_session: db.Session
) -> Tuple[minidom.Document, List[Payment]]:
    # xml_document represents the overall XML object
    xml_document = minidom.Document()
    added_payments = []

    # Document root contains all of the GAX documents
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    # Add the index so we can populate the non-nullable ctr_document_identifier.document_counter
    # field with something useful.
    for i, payment in enumerate(payments):
        try:
            ctr_doc_id = CtrDocumentIdentifier(
                ctr_document_identifier=get_doc_id(), document_date=now.date(), document_counter=i,
            )
            db_session.add(ctr_doc_id)

            # gax_document refers to individual documents which contain payment data
            gax_document = build_individual_gax_document(xml_document, payment, now)
            document_root.appendChild(gax_document)

            # Add records to the database for the document.
            payment_ref_file = PaymentReferenceFile(
                payment=payment, reference_file=ref_file, ctr_document_identifier=ctr_doc_id,
            )
            db_session.add(payment_ref_file)

            # Record in StateLog that we've added this payment to the GAX.
            state_log_util.create_finished_state_log(
                associated_model=payment,
                start_state=STATE_LOG_PICKUP_STATE,
                end_state=State.GAX_SENT,
                outcome=state_log_util.build_outcome("Added Payment to GAX"),
                db_session=db_session,
            )

            added_payments.append(payment)
        except Exception:
            logger.exception(
                "Failed to add Payment to GAX.", extra={"payment_id": payment.payment_id},
            )

    if len(added_payments) == 0:
        logger.error(
            "No Payment records added to GAX. Raising Exception",
            extra={
                "reference_file": ref_file.reference_file_id,
                "errored_payment_record_count": len(payments),
            },
        )
        raise Exception("No Payment records added to GAX")

    return (xml_document, added_payments)


def build_gax_inf(payments: List[Payment], now: datetime, batch_id: str) -> Dict[str, str]:
    total_dollar_amount = decimal.Decimal(sum(payment.amount for payment in payments))

    return {
        "NewMmarsBatchID": batch_id,
        "NewMmarsBatchDeptCode": Constants.COMPTROLLER_DEPT_CODE,
        "NewMmarsUnitCode": Constants.COMPTROLLER_UNIT_CODE,
        "NewMmarsImportDate": now.strftime("%Y-%m-%d"),
        "NewMmarsTransCode": "GAX",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": str(len(payments)),
        "NewMmarsTransDollarAmount": str(total_dollar_amount.quantize(TWOPLACES)),
    }


def get_eligible_payments(db_session: db.Session) -> List[Payment]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=STATE_LOG_PICKUP_STATE,
        db_session=db_session,
    )

    return [state_log.payment for state_log in state_logs]


def build_gax_files(db_session: db.Session, ctr_outbound_path: str) -> Tuple[str, str]:
    try:
        now = payments_util.get_now()

        ctr_batch_id, ref_file, filename = payments_util.create_batch_id_and_reference_file(
            now, ReferenceFileType.GAX, db_session, ctr_outbound_path
        )

        payments = get_eligible_payments(db_session)

        if len(payments) == 0:
            logger.info("Did not find any payments to add to GAX. Not creating GAX files.")
            return (
                payments_util.Constants.MMARS_FILE_SKIPPED,
                payments_util.Constants.MMARS_FILE_SKIPPED,
            )

        dat_xml_document, added_payments = build_gax_dat(payments, now, ref_file, db_session)
        inf_dict = build_gax_inf(added_payments, now, ctr_batch_id.ctr_batch_identifier)
        ctr_batch_id.inf_data = inf_dict

        dat_filepath, inf_filepath = payments_util.create_mmars_files_in_s3(
            ref_file.file_location, str(filename), dat_xml_document, inf_dict,
        )

        send_bievnt_email(ref_file, db_session)

        db_session.commit()

        return (dat_filepath, inf_filepath)
    except Exception as e:
        logger.exception("Unable to create GAX", extra={"ctr_outbound_path": ctr_outbound_path})
        db_session.rollback()
        raise e


def build_gax_files_for_s3(db_session: db.Session) -> Tuple[str, str]:
    return build_gax_files(db_session, payments_config.get_s3_config().pfml_ctr_outbound_path)


def send_bievnt_email(ref_file: ReferenceFile, db_session: db.Session) -> None:
    subject = f"DFML GAX BIEVNT info for Batch ID {ref_file.ctr_batch_identifier_id} on {payments_util.get_now():%m/%d/%Y}"

    try:
        email_config = payments_config.get_email_config()
        gax_bienvt_email = email_config.ctr_gax_bievnt_email_address
        project_manager_email = email_config.dfml_project_manager_email_address
        email_recipient = EmailRecipient(
            to_addresses=[gax_bienvt_email], cc_addresses=[project_manager_email]
        )

        email_inf_data(ref_file, db_session, email_recipient, subject)
    except RuntimeError:
        logger.exception("Error sending GAX BIEVNT email")

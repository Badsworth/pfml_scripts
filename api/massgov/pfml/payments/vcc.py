import uuid
import xml.dom.minidom as minidom
from datetime import datetime
from typing import Dict, List, Optional, Tuple, cast

from sqlalchemy import func

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    CtrDocumentIdentifier,
    Employee,
    EmployeeReferenceFile,
    LkGeoState,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import Constants, email_fineos_vendor_customer_numbers
from massgov.pfml.util.aws.ses import EmailRecipient

logger = massgov.pfml.util.logging.get_logger(__name__)

generic_attributes = {
    "DOC_CAT": "VCUST",
    "DOC_TYP": "VCC",
    "DOC_CD": "VCC",
    "DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": Constants.COMPTROLLER_UNIT_CODE,
    "DOC_VERS_NO": "1",
}

ams_doc_attributes = {"DOC_IMPORT_MODE": "OE"}

vcc_doc_vcust_attributes = {"DOC_VCUST_LN_NO": "1", "ORG_TYP": "1", "ORG_CLS": "1", "TIN_TYP": "2"}

vcc_doc_ad_attributes = {
    "DOC_VCUST_LN_NO": "1",
    "DFLT_AD_TYP": "TRUE",
    "CNTAC_NO": "PC001",
    "PRIN_CNTAC": "NONE PROVIDED",
    "CNTAC_PH_NO": "NONE PROVIDED",
    "AD_ID": "AD010",
}

# We add two of these sections with the only difference being static values
vcc_doc_ad_attributes_pa = {"AD_TYP": "PA", "DOC_AD_LN_NO": "1"}

vcc_doc_ad_attributes_pr = {"AD_TYP": "PR", "DOC_AD_LN_NO": "2"}

vcc_doc_1099_attributes = {"DOC_VCUST_LN_NO": "1", "DOC_1099_LN_NO": "1", "RPT_1099_FL": "TRUE"}

vcc_doc_bus_attributes = {"DOC_VCUST_LN_NO": "1", "CERT_NO": "DFMLCERTIFIED"}

# If EFT data is present, we'll add a second vcc_doc_bus section with different static attributes
vcc_doc_bus_attributes_w9 = {"DOC_BUS_LN_NO": "1", "BUS_TYP": "W9"}

vcc_doc_bus_attributes_eft = {"DOC_BUS_LN_NO": "2", "BUS_TYP": "EFT"}

vcc_doc_cert_attributes = {
    "DOC_VCUST_LN_NO": "1",
    "DOC_CERT_LN_NO": "1",
    "VEND_ACT_STA": "2",
    "VEND_APRV_STA": "3",
}

MAX_VCC_DOCUMENTS_PER_DAY = 9999
DOC_ID_TEMPLATE = "INTFDFML{}{}"  # INTFDFML121920200012 <- 13th document for December 19, 2020.
BATCH_ID_TEMPLATE = Constants.COMPTROLLER_DEPT_CODE + "{}VCC{}"  # eg. EOL0101VCC24
STATE_LOG_PICKUP_STATE = State.ADD_TO_VCC


def get_doc_id(now: datetime, count: int) -> str:
    return DOC_ID_TEMPLATE.format(now.strftime("%d%m%Y"), f"{count:04}")


def get_state_str(geo_state: LkGeoState) -> Optional[str]:
    return geo_state.geo_state_description


def combine_address_lines(address_line_one: Optional[str], address_line_two: Optional[str]) -> str:
    if address_line_one is None:
        raise Exception("combine_address_lines: address_line_one cannot be None")
    combined_address = address_line_one
    if address_line_two:
        combined_address += f" {address_line_two}"
    return combined_address


def build_individual_vcc_document(
    document: minidom.Document, employee: Employee, now: datetime, doc_id: str
) -> minidom.Element:

    first_name = payments_util.validate_db_input(
        key="first_name", db_object=employee, required=True, max_length=14, truncate=True
    )
    last_name = payments_util.validate_db_input(
        key="last_name", db_object=employee, required=True, max_length=30, truncate=True
    )

    if employee.tax_identifier is None:
        raise Exception("Value for tax_identifier is required to generate document.")

    payee_ssn = payments_util.validate_db_input(
        key="tax_identifier",
        db_object=employee.tax_identifier,
        required=True,
        max_length=9,
        truncate=False,
    )
    payee_aba_num = payments_util.validate_db_input(
        key="routing_nbr", db_object=employee.eft, required=False, max_length=9, truncate=False
    )
    payee_acct_type = payments_util.validate_db_input(
        key="bank_account_type_id",  # Conveniently, the lookup IDs we already use are the right values for the VCC
        db_object=employee.eft,
        required=False,
        max_length=1,
        truncate=False,
    )
    payee_acct_num = payments_util.validate_db_input(
        key="account_nbr", db_object=employee.eft, required=False, max_length=40, truncate=False
    )

    if employee.ctr_address_pair is None:
        raise Exception("Employee must have a ctr_address_pair")

    payment_address_line_1 = payments_util.validate_db_input(
        key="address_line_one",
        db_object=employee.ctr_address_pair.fineos_address,
        required=True,
        max_length=75,
        truncate=True,
    )
    payment_address_line_2 = payments_util.validate_db_input(
        key="address_line_two",
        db_object=employee.ctr_address_pair.fineos_address,
        required=False,
        max_length=75,
        truncate=True,
    )
    city = payments_util.validate_db_input(
        key="city",
        db_object=employee.ctr_address_pair.fineos_address,
        required=True,
        max_length=60,
        truncate=True,
    )
    city = cast(
        str, city
    )  # We've validated it's present, cast it to remove the Optional for linting
    state = payments_util.validate_db_input(
        key="geo_state",
        db_object=employee.ctr_address_pair.fineos_address,
        required=True,
        max_length=2,
        truncate=False,
        func=get_state_str,
    )
    zip_code = payments_util.validate_db_input(
        key="zip_code",
        db_object=employee.ctr_address_pair.fineos_address,
        required=True,
        max_length=10,
        truncate=False,
    )
    payment_method = employee.payment_method

    has_eft = payee_aba_num and payee_acct_type and payee_acct_num

    # If the payment method is ACH, all related params must be present
    if payment_method.payment_method_id == PaymentMethod.ACH.payment_method_id and not (
        payee_aba_num or payee_acct_type or payee_acct_num
    ):
        raise Exception("ACH parameters missing when payment method is ACH")

    # Create the root of the document
    ams_document_attributes = {"DOC_ID": doc_id}
    ams_document_attributes.update(ams_doc_attributes.copy())
    ams_document_attributes.update(generic_attributes.copy())
    root = document.createElement("AMS_DOCUMENT")
    payments_util.add_attributes(root, ams_document_attributes)

    # Add the VCC_DOC_HDR
    vcc_doc_hdr = document.createElement("VCC_DOC_HDR")
    payments_util.add_attributes(vcc_doc_hdr, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_hdr)

    # Add the individual VCC_DOC_HDR values
    vcc_doc_hdr_elements = {
        "DOC_ID": doc_id,
    }
    vcc_doc_hdr_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_hdr, document, vcc_doc_hdr_elements)

    # Add the VCC_DOC_VCUST
    vcc_doc_vcust = document.createElement("VCC_DOC_VCUST")
    payments_util.add_attributes(vcc_doc_vcust, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_vcust)

    # Add the individual VCC_DOC_VCUST values
    vcc_doc_vcust_elements = {
        "DOC_ID": doc_id,
        "FRST_NM": first_name,
        "LAST_NM": last_name,
        "TIN": payee_ssn,
    }
    vcc_doc_vcust_elements.update(vcc_doc_vcust_attributes.copy())
    vcc_doc_vcust_elements.update(generic_attributes.copy())

    # Only add these attributes if there is EFT information
    if has_eft:
        vcc_doc_vcust_elements.update(
            {
                "ABA_NO": payee_aba_num,
                "ACCT_TYP": payee_acct_type,
                "ACCT_NO_VIEW": payee_acct_num,
                "EFT_STA": "1",
            }
        )

    payments_util.add_cdata_elements(vcc_doc_vcust, document, vcc_doc_vcust_elements)

    # Add the PA VCC_DOC_AD
    vcc_doc_ad_pa = document.createElement("VCC_DOC_AD")
    payments_util.add_attributes(vcc_doc_ad_pa, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_ad_pa)

    # MMARS needs the two address lines combined into a single line. The 75 character limit remains.
    # (https://lwd.atlassian.net/browse/API-1312)
    combined_address = combine_address_lines(payment_address_line_1, payment_address_line_2)[:75]

    # Add the PA individual VCC_DOC_AD values
    vcc_doc_ad_pa_elements = {
        "DOC_ID": doc_id,
        "STR_1_NM": combined_address,
        "CITY_NM": city,
        "ST": state,
        "ZIP": zip_code,
    }
    vcc_doc_ad_pa_elements.update(vcc_doc_ad_attributes.copy())
    vcc_doc_ad_pa_elements.update(vcc_doc_ad_attributes_pa.copy())
    vcc_doc_ad_pa_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_ad_pa, document, vcc_doc_ad_pa_elements)

    # Add the PR VCC_DOC_AD
    vcc_doc_ad_pr = document.createElement("VCC_DOC_AD")
    payments_util.add_attributes(vcc_doc_ad_pr, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_ad_pr)

    # Add the PR individual VCC_DOC_AD values
    vcc_doc_ad_pr_elements = {
        "DOC_ID": doc_id,
        "STR_1_NM": combined_address,
        "CITY_NM": city,
        "ST": state,
        "ZIP": zip_code,
    }
    vcc_doc_ad_pr_elements.update(vcc_doc_ad_attributes.copy())
    vcc_doc_ad_pr_elements.update(vcc_doc_ad_attributes_pr.copy())
    vcc_doc_ad_pr_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_ad_pr, document, vcc_doc_ad_pr_elements)

    # Add the VCC_DOC_1099
    vcc_doc_1099 = document.createElement("VCC_DOC_1099")
    payments_util.add_attributes(vcc_doc_1099, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_1099)

    # Add the individual VCC_DOC_1099 values
    vcc_doc_1099_elements = {
        "DOC_ID": doc_id,
        "TIN_AD": combined_address[:40],  # TIN_AD has max length 40 chars. CTR says ok to truncate
        "TIN_CITY_NM": city[:30],  # This has a max length of 30 despite it being 60 elsewhere
        "TIN_ST": state,
        "TIN_ZIP": zip_code,
    }
    vcc_doc_1099_elements.update(generic_attributes.copy())
    vcc_doc_1099_elements.update(vcc_doc_1099_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_1099, document, vcc_doc_1099_elements)

    # Add the W9 VCC_DOC_BUS
    vcc_doc_bus_w9 = document.createElement("VCC_DOC_BUS")
    payments_util.add_attributes(vcc_doc_bus_w9, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_bus_w9)

    # Add the W9 individual VCC_DOC_BUS values
    vcc_doc_bus_w9_elements = {"DOC_ID": doc_id, "CERT_STRT_DT": now.strftime("%Y-%m-%d")}
    vcc_doc_bus_w9_elements.update(vcc_doc_bus_attributes.copy())
    vcc_doc_bus_w9_elements.update(vcc_doc_bus_attributes_w9.copy())
    vcc_doc_bus_w9_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_bus_w9, document, vcc_doc_bus_w9_elements)

    # An EFT vcc_doc_bus section is needed if there is EFT information
    if has_eft:
        # Add the EFT VCC_DOC_BUS
        vcc_doc_bus_eft = document.createElement("VCC_DOC_BUS")
        payments_util.add_attributes(vcc_doc_bus_eft, {"AMSDataObject": "Y"})
        root.appendChild(vcc_doc_bus_eft)

        # Add the EFT individual VCC_DOC_BUS values
        vcc_doc_bus_eft_elements = {"DOC_ID": doc_id, "CERT_STRT_DT": now.strftime("%Y-%m-%d")}
        vcc_doc_bus_eft_elements.update(vcc_doc_bus_attributes.copy())
        vcc_doc_bus_eft_elements.update(vcc_doc_bus_attributes_eft.copy())
        vcc_doc_bus_eft_elements.update(generic_attributes.copy())
        payments_util.add_cdata_elements(vcc_doc_bus_eft, document, vcc_doc_bus_eft_elements)

    # Add the VCC_DOC_CERT
    vcc_doc_cert = document.createElement("VCC_DOC_CERT")
    payments_util.add_attributes(vcc_doc_cert, {"AMSDataObject": "Y"})
    root.appendChild(vcc_doc_cert)

    # Add the individual VCC_DOC_CERT values
    vcc_doc_cert_elements = {
        "DOC_ID": doc_id,
    }
    vcc_doc_cert_elements.update(vcc_doc_cert_attributes.copy())
    vcc_doc_cert_elements.update(generic_attributes.copy())
    payments_util.add_cdata_elements(vcc_doc_cert, document, vcc_doc_cert_elements)

    logger.debug(
        "Added to VCC: employee with fineos_customer_number %s",
        employee.fineos_customer_number,
        extra={"fineos_customer_number": employee.fineos_customer_number},
    )

    return root


def get_vcc_doc_counter_offset_for_today(now: datetime, db_session: db.Session) -> int:
    max_doc_counter_today = (
        db_session.query(func.max(CtrDocumentIdentifier.document_counter))
        .join(CtrDocumentIdentifier.employee_reference_files)
        .join(EmployeeReferenceFile.reference_file)
        .filter(
            CtrDocumentIdentifier.document_date == now.date(),
            ReferenceFile.reference_file_type_id == ReferenceFileType.VCC.reference_file_type_id,
        )
        .scalar()
    )

    if max_doc_counter_today:
        return max_doc_counter_today + 1

    return 0


def build_vcc_dat(
    employees: List[Employee], now: datetime, ref_file: ReferenceFile, db_session: db.Session,
) -> Tuple[minidom.Document, List[Employee]]:
    logger.info("Building VCC .DAT files for %i employee records", len(employees))

    # xml_document represents the overall XML object
    xml_document = minidom.Document()
    added_employees = []

    # Document root contains all of the VCC documents
    document_root = xml_document.createElement("AMS_DOC_XML_IMPORT_FILE")
    payments_util.add_attributes(document_root, {"VERSION": "1.0"})
    xml_document.appendChild(document_root)

    doc_count_offset = get_vcc_doc_counter_offset_for_today(now, db_session)
    for count, employee in enumerate(employees):
        try:
            logger.debug(
                "Process: employee with fineos_customer_number %s",
                employee.fineos_customer_number,
                extra={"fineos_customer_number": employee.fineos_customer_number},
            )

            # If an employee has already been added to a VCC, don't add them
            # again. The only legitimate case where an employee can be added
            # to multiple VCCs is if the BIEVNT was not created in time and
            # we need to recreate the VCC.
            if state_log_util.has_been_in_end_state(employee, db_session, State.VCC_SENT):
                logger.warning(
                    "Employee with customer number %s has already been added to a VCC.",
                    employee.fineos_customer_number,
                    extra={"fineos_customer_number": employee.fineos_customer_number},
                )
                continue

            doc_count = count + doc_count_offset
            if doc_count > MAX_VCC_DOCUMENTS_PER_DAY:
                logger.error(
                    "Reached limit of %d VCC documents per day. Started current batch from offset %d. Made it through %d VCC documents in current batch before reaching daily limit",
                    MAX_VCC_DOCUMENTS_PER_DAY,
                    doc_count_offset,
                    count - 1,
                )
                break

            doc_id = get_doc_id(now, doc_count)
            ctr_doc_id = CtrDocumentIdentifier(
                ctr_document_identifier_id=uuid.uuid4(),
                ctr_document_identifier=doc_id,
                document_date=now.date(),
                document_counter=doc_count,
            )

            db_session.add(ctr_doc_id)

            # vcc_document refers to individual documents which contain employee/payment data
            vcc_document = build_individual_vcc_document(xml_document, employee, now, doc_id)
            document_root.appendChild(vcc_document)

            # Add records to the database for the document.
            emp_ref_file = EmployeeReferenceFile(
                employee=employee, reference_file=ref_file, ctr_document_identifier=ctr_doc_id,
            )

            db_session.add(emp_ref_file)

            logger.debug(
                "Added VCC document XML for employee: %s",
                employee.employee_id,
                extra={
                    "ref_file": ref_file.file_location,
                    "ctr_doc_id": ctr_doc_id.ctr_document_identifier,
                },
            )

            # Record in StateLog that we've added this employee to the VCC.
            state_log_util.create_finished_state_log(
                associated_model=employee,
                end_state=State.VCC_SENT,
                outcome=state_log_util.build_outcome("Added vendor to VCC"),
                db_session=db_session,
            )

            # If the employee has EFT info, move them forward in the VENDOR_EFT flow
            if employee.eft and employee.payment_method_id == PaymentMethod.ACH.payment_method_id:
                state_log_util.create_finished_state_log(
                    associated_model=employee,
                    end_state=State.EFT_PENDING,
                    outcome=state_log_util.build_outcome(
                        "Added vendor to VCC, EFT data is included"
                    ),
                    db_session=db_session,
                )

            added_employees.append(employee)
        except Exception:
            logger.exception(
                "Failed to add Employee to VCC.", extra={"employee_id": employee.employee_id},
            )

    if len(added_employees) == 0:
        logger.error(
            "No Employee records added to VCC. Raising Exception",
            extra={
                "reference_file": ref_file.reference_file_id,
                "errored_employee_record_count": len(employees),
            },
        )
        raise Exception("No Employee records added to VCC")

    logger.info("Successfully built VCC .DAT files for %i employee records", len(employees))

    return (xml_document, added_employees)


def build_vcc_inf(employees: List[Employee], now: datetime, batch_id: str) -> Dict[str, str]:
    logger.info("Building VCC .INF file for %i employee records", len(employees))

    return {
        "NewMmarsBatchID": batch_id,
        "NewMmarsBatchDeptCode": Constants.COMPTROLLER_DEPT_CODE,
        "NewMmarsUnitCode": Constants.COMPTROLLER_UNIT_CODE,
        "NewMmarsImportDate": now.strftime("%Y-%m-%d"),
        "NewMmarsTransCode": "VCC",
        "NewMmarsTableName": "",
        "NewMmarsTransCount": str(len(employees)),
        "NewMmarsTransDollarAmount": "",
    }


def get_eligible_employees(db_session: db.Session) -> List[Employee]:
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.EMPLOYEE,
        end_state=STATE_LOG_PICKUP_STATE,
        db_session=db_session,
    )

    return [state_log.employee for state_log in state_logs]


def build_vcc_files(db_session: db.Session, ctr_outbound_path: str) -> Tuple[str, str]:
    logger.info("Creating VCC files")

    try:
        now = payments_util.get_now()

        ctr_batch_id, ref_file, filename = payments_util.create_batch_id_and_reference_file(
            now, ReferenceFileType.VCC, db_session, ctr_outbound_path
        )

        logger.info(
            "Created VCC reference file and ctr batch id - reference file: %s, ctr batch id: %s ",
            ref_file.file_location,
            ctr_batch_id.ctr_batch_identifier,
        )

        employees = get_eligible_employees(db_session)

        if len(employees) == 0:
            logger.info(
                "Gracefully exiting: Did not find any employees to add to VCC. Not creating VCC files."
            )
            return (
                payments_util.Constants.MMARS_FILE_SKIPPED,
                payments_util.Constants.MMARS_FILE_SKIPPED,
            )

        dat_xml_document, added_employees = build_vcc_dat(employees, now, ref_file, db_session)
        inf_dict = build_vcc_inf(added_employees, now, ctr_batch_id.ctr_batch_identifier)
        ctr_batch_id.inf_data = inf_dict

        dat_filepath, inf_filepath = payments_util.create_mmars_files_in_s3(
            ref_file.file_location, str(filename), dat_xml_document, inf_dict
        )

        send_bievnt_email(ref_file, db_session)

        db_session.commit()

        logger.info("Successfully created VCC files in: %s", ref_file.file_location)

        return (dat_filepath, inf_filepath)
    except Exception as e:
        logger.exception("Unable to create VCC")
        db_session.rollback()
        raise e


def build_vcc_files_for_s3(db_session: db.Session) -> Tuple[str, str]:
    logger.info("VCC: Begin")
    dat_filepath, inf_filepath = build_vcc_files(
        db_session, payments_config.get_s3_config().pfml_ctr_outbound_path
    )
    logger.info("VCC: Done")
    return (dat_filepath, inf_filepath)


def send_bievnt_email(ref_file: ReferenceFile, db_session: db.Session) -> None:
    subject = f"DFML VCC BIEVNT info for Batch ID {ref_file.ctr_batch_identifier_id} on {payments_util.get_now():%m/%d/%Y}"

    try:
        email_config = payments_config.get_email_config()
        vcc_bienvt_email = email_config.ctr_vcc_bievnt_email_address
        project_manager_email = email_config.dfml_project_manager_email_address
        email_recipient = EmailRecipient(
            to_addresses=[vcc_bienvt_email], cc_addresses=[project_manager_email]
        )

        email_fineos_vendor_customer_numbers(ref_file, db_session, email_recipient, subject)
    except RuntimeError:
        logger.exception("Error sending VCC BIEVNT email")

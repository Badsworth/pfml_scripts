import uuid
from typing import List, Optional, Tuple
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.payments.payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    CtrDocumentIdentifier,
    Employee,
    EmployeeReferenceFile,
    Flow,
    GeoState,
    ReferenceFile,
    ReferenceFileType,
)

logger = logging.get_logger(__name__)

# Constant values used to validate OVR
OUTBOUND_VENDOR_CUSTOMER_RETURN_CONSTANTS = {
    "DOC_CAT": "VCUST",
    "DOC_TYP": "VCC",
    "DOC_CD": "VCC",
    "DOC_DEPT_CD": payments_util.Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": payments_util.Constants.COMPTROLLER_UNIT_CODE,
    "ORG_TYP": "1",
    "TIN_TYP": "2",
}

REQUIRED_ADDRESS_FIELDS = ["ST", "STR_1_NM", "CITY_NM", "ZIP"]


class VcDocVcustData:
    DOC_CAT: Optional[str]
    DOC_TYP: Optional[str]
    DOC_CD: Optional[str]
    DOC_DEPT_CD: Optional[str]
    DOC_UNIT_CD: Optional[str]
    ORG_TYP: Optional[str]
    TIN: Optional[str]
    TIN_TYP: Optional[str]
    VEND_CUST_CD: Optional[str]
    ORG_VEND_VCUST_CD: Optional[str]

    def __init__(self, vc_doc_vcust: Element):
        self.DOC_CAT = payments_util.get_xml_subelement(vc_doc_vcust, "DOC_CAT")
        self.DOC_TYP = payments_util.get_xml_subelement(vc_doc_vcust, "DOC_TYP")
        self.DOC_CD = payments_util.get_xml_subelement(vc_doc_vcust, "DOC_CD")
        self.DOC_DEPT_CD = payments_util.get_xml_subelement(vc_doc_vcust, "DOC_DEPT_CD")
        self.DOC_UNIT_CD = payments_util.get_xml_subelement(vc_doc_vcust, "DOC_UNIT_CD")
        self.ORG_TYP = payments_util.get_xml_subelement(vc_doc_vcust, "ORG_TYP")
        self.TIN = payments_util.get_xml_subelement(vc_doc_vcust, "TIN")
        self.TIN_TYP = payments_util.get_xml_subelement(vc_doc_vcust, "TIN_TYP")
        self.VEND_CUST_CD = payments_util.get_xml_subelement(vc_doc_vcust, "VEND_CUST_CD")
        self.ORG_VEND_VCUST_CD = payments_util.get_xml_subelement(vc_doc_vcust, "ORG_VEND_CUST_CD")


class VcDocAdData:
    AD_TYP: Optional[str]
    AD_ID: Optional[str]
    STR_1_NM: Optional[str]
    STR_2_NM: Optional[str]
    CITY_NM: Optional[str]
    ST: Optional[str]
    ZIP: Optional[str]

    def __init__(self, vc_doc_ad: Element):
        self.AD_TYP = payments_util.get_xml_subelement(vc_doc_ad, "AD_TYP")
        self.AD_ID = payments_util.get_xml_subelement(vc_doc_ad, "AD_ID")
        self.STR_1_NM = payments_util.get_xml_subelement(vc_doc_ad, "STR_1_NM")
        self.STR_2_NM = payments_util.get_xml_subelement(vc_doc_ad, "STR_2_NM")
        self.CITY_NM = payments_util.get_xml_subelement(vc_doc_ad, "CITY_NM")
        self.ST = payments_util.get_xml_subelement(vc_doc_ad, "ST")
        self.ZIP = payments_util.get_xml_subelement(vc_doc_ad, "ZIP")


class Dependencies:
    ams_document_id: Optional[str]
    ctr_document_identifier: Optional[CtrDocumentIdentifier]
    employee: Optional[Employee]
    vc_doc_vcust: Optional[Element]
    vcc: Optional[EmployeeReferenceFile]

    def __init__(self):
        self.ams_document_id = None
        self.ctr_document_identifier = None
        self.employee = None
        self.vc_doc_vcust = None
        self.vcc = None


def get_pfml_payment_addresses(ams_document: Element) -> List[Element]:
    addresses = ams_document.findall("VC_DOC_AD")
    pfml_payment_addresses = []
    for address in addresses:
        AD_ID = address.find("AD_ID")
        AD_TYP = address.find("AD_TYP")
        if AD_ID is None or AD_TYP is None:
            continue
        if (
            AD_ID.text == payments_util.Constants.COMPTROLLER_AD_ID
            and AD_TYP.text == payments_util.Constants.COMPTROLLER_AD_TYPE
        ):
            pfml_payment_addresses.append(address)

    return pfml_payment_addresses


def validate_pfml_address(
    vc_doc_ad: Element, validation_container: payments_util.ValidationContainer
) -> Optional[VcDocAdData]:
    vc_doc_ad_data = VcDocAdData(vc_doc_ad)

    # Only update the address if the required fields are provided
    address_issues = False

    for field in REQUIRED_ADDRESS_FIELDS:
        value = getattr(vc_doc_ad_data, field)
        if not value:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_FIELD, field
            )
            address_issues = True

    if address_issues:
        return None
    else:
        return vc_doc_ad_data


def validate_ams_document(
    ams_document: Element,
    ams_document_id: str,
    vc_doc_vcust: Element,
    employee: Employee,
    validation_container: payments_util.ValidationContainer,
) -> Tuple[payments_util.ValidationContainer, Optional[VcDocAdData]]:
    # validate DOC_ID
    if not ams_document_id.startswith("INTFDFML"):
        validation_container.add_validation_issue(
            payments_util.ValidationReason.INVALID_VALUE, "DOC_ID"
        )

    # validate VC_DOC_VCUST constant values
    vc_doc_vcust_data = VcDocVcustData(vc_doc_vcust)
    for k, v in OUTBOUND_VENDOR_CUSTOMER_RETURN_CONSTANTS.items():
        field_value = getattr(vc_doc_vcust_data, k)
        if not field_value:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.MISSING_FIELD, k
            )
        elif field_value != v:
            validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, k
            )

    # validate originating VCC document data
    tin_value = vc_doc_vcust_data.TIN

    if tin_value:
        if employee.tax_identifier:
            if tin_value.replace("_", "") != employee.tax_identifier.tax_identifier:
                validation_container.add_validation_issue(
                    payments_util.ValidationReason.INVALID_VALUE, "TIN"
                )
    else:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_FIELD, "TIN"
        )

    # additional validations

    # Check that there's a valid address (AD_ID == AD010 and AD_TYP == "PA")
    vc_doc_ads = get_pfml_payment_addresses(ams_document)
    validated_address_data = None
    if len(vc_doc_ads) > 1:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MULTIPLE_VALUES_FOUND, "VC_DOC_AD"
        )
    elif len(vc_doc_ads) == 0:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.VALUE_NOT_FOUND, "VC_DOC_AD"
        )
    else:
        validated_address_data = validate_pfml_address(vc_doc_ads[0], validation_container)

    # Check that VEND_CUST_CD and ORG_VEND_CUST_CD are not null
    if not vc_doc_vcust_data.VEND_CUST_CD:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.NON_NULLABLE, "VEND_CUST_CD"
        )

    if not vc_doc_vcust_data.ORG_VEND_VCUST_CD:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.NON_NULLABLE, "ORG_VEND_CUST_CD"
        )

    return validation_container, validated_address_data


def update_employee_data(
    validated_address_data: VcDocAdData,
    ams_document_id: str,
    vc_doc_vcust: Element,
    employee: Employee,
    db_session: db.Session,
) -> None:
    if employee.ctr_address_pair is None:
        raise Exception("Employee must have a ctr_address_pair")

    # update address fields on the CTR half of the CtrAddressPair
    if not employee.ctr_address_pair.ctr_address:
        logger.info(
            "Creating CTR address for Employee ID %s",
            employee.employee_id,
            extra={
                "employee_id": employee.employee_id,
                "fineos_customer_number": employee.fineos_customer_number,
            },
        )
        ctr_address = Address(
            address_id=uuid.uuid4(), address_type_id=AddressType.MAILING.address_type_id
        )
        employee.ctr_address_pair.ctr_address = ctr_address
        db_session.add(employee)

    logger.info(
        "Setting CTR address for Employee ID %s",
        employee.employee_id,
        extra={
            "employee_id": employee.employee_id,
            "fineos_customer_number": employee.fineos_customer_number,
            "address_id": ctr_address.address_id,
        },
    )

    ctr_address = employee.ctr_address_pair.ctr_address
    geo_state_id = GeoState.get_id(validated_address_data.ST)
    ctr_address.geo_state_id = geo_state_id
    ctr_address.address_line_one = validated_address_data.STR_1_NM
    ctr_address.city = validated_address_data.CITY_NM
    ctr_address.zip_code = validated_address_data.ZIP

    if validated_address_data.STR_2_NM not in ["null", None]:
        ctr_address.address_line_two = validated_address_data.STR_2_NM
    db_session.add(ctr_address)


def get_employee(ams_document_id: str, db_session: db.Session,) -> Optional[Employee]:
    employee = None
    try:
        employee = (
            db_session.query(Employee)
            .join(Employee.reference_files)
            .join(EmployeeReferenceFile.ctr_document_identifier)
            .filter(CtrDocumentIdentifier.ctr_document_identifier == ams_document_id)
            .one_or_none()
        )

    except MultipleResultsFound:
        # This should never happen, but if it does, it means that the same
        # DOC_ID was reused for multiple employees. Our db is in a bad place.
        # Resolution: Identify which employees have this DOC_ID and try to
        #             find out why.
        logger.exception(
            "Multiple employees found for specified CTR Document Identifier %s",
            ams_document_id,
            extra={"ctr_document_identifier": ams_document_id},
        )
        raise

    # This should never happen, but if it does: it means that no employee
    # record was found associated with this DOC_ID. Our db may be in a bad
    # place.
    # Resolution: Identify what record (if any) is associated with this DOC_ID
    if not employee:
        logger.error(
            "Employee not found for AMS_DOCUMENT with DOC_ID %s",
            ams_document_id,
            extra={"ctr_document_identifier": ams_document_id},
        )

    return employee


def vcc_check(ams_document_id: str, db_session: db.Session) -> Optional[EmployeeReferenceFile]:
    try:
        vcc_employee_reference_file = (
            db_session.query(EmployeeReferenceFile)
            .join(EmployeeReferenceFile.ctr_document_identifier)
            .join(EmployeeReferenceFile.reference_file)
            .filter(
                CtrDocumentIdentifier.ctr_document_identifier == ams_document_id,
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.VCC.reference_file_type_id,
            )
        ).first()

    except SQLAlchemyError:
        # Unknown other SQLAlchemy errors
        logger.exception(
            "SQLAlchemyError while querying for VCC with DOC_ID %s",
            ams_document_id,
            extra={"ctr_document_identifier": ams_document_id},
        )
        return None

    # This should never happen, but if it does:
    # 1. CTR has sent us a DOC_ID we never sent them OR
    # 2. Our db lost a DOC_ID that we previously sent to CTR in a VCC
    # Resolution: Grep all the VCCs in the PFML agency transfer bucket for
    #             this DOC_ID to see whether this is a bug in our code or an
    #             error in MMARS
    if not vcc_employee_reference_file:
        logger.error(
            "Failed to find VCC file for specified CTR Document Identifier %s",
            ams_document_id,
            extra={"ctr_document_identifier": ams_document_id},
        )
    return vcc_employee_reference_file


def get_ctr_document_identifier(
    ams_document_id: str, db_session: db.Session
) -> Optional[CtrDocumentIdentifier]:
    ctr_document_identifier = None

    try:
        ctr_document_identifier = (
            db_session.query(CtrDocumentIdentifier)
            .filter(CtrDocumentIdentifier.ctr_document_identifier == ams_document_id)
            .one_or_none()
        )
    except MultipleResultsFound:
        # This should never happen, but if it does, it means that something
        # went wrong with our db. The ctr_document_identifier column should
        # be unique.
        logger.exception(
            "Multiple CtrDocumentIdentifiers found for specified CTR Document Identifier %s",
            ams_document_id,
            extra={"ams_document_id": ams_document_id},
        )
        raise
    except SQLAlchemyError as e:
        # Unknown other SQLAlchemy errors
        logger.exception(
            "SQLAlchemyError %s while querying for DOC_ID %s",
            type(e),
            ams_document_id,
            extra={"ctr_document_identifier": ams_document_id},
        )
        raise

    # This should never happen, but if it does:
    # 1. CTR has sent us a DOC_ID we never sent them OR
    # 2. Our db lost a DOC_ID that we previously sent to CTR in a VCC
    # Resolution: Grep all the VCCs in the PFML agency transfer bucket for
    #             this DOC_ID to see whether this is a bug in our code or an
    #             error in MMARS
    if not ctr_document_identifier:
        logger.error(
            "DOC_ID %s not found in db",
            ams_document_id,
            extra={"ctr_document_identifier": ams_document_id},
        )
        raise ValueError("DOC_ID {ams_document_id} not found in PFML DB")

    return ctr_document_identifier


def check_dependencies(
    ams_document: Element, db_session: db.Session, reference_file: ReferenceFile,
) -> Dependencies:

    checked_dependencies = Dependencies()

    ams_document_id = ams_document.get("DOC_ID")

    if ams_document_id is None or ams_document_id == "null":
        # This is a malformed Outbound Vendor Customer Return.
        # We should notify CTR
        logger.exception(
            "AMS_DOCUMENT is missing DOC_ID value in file %s",
            reference_file.file_location,
            extra={"file_location": reference_file.file_location},
        )
        return checked_dependencies
    else:
        checked_dependencies.ams_document_id = ams_document_id

    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")
    if not vc_doc_vcust:
        # This is a malformed Outbound Vendor Customer Return.
        # We should notify CTR
        logger.exception(
            "Missing VC_DOC_VCUST in AMS_DOCUMENT with DOC_ID %s in file %s",
            ams_document_id,
            reference_file.file_location,
            extra={
                "file_location": reference_file.file_location,
                "ams_document_id": ams_document_id,
            },
        )
        return checked_dependencies
    else:
        checked_dependencies.vc_doc_vcust = vc_doc_vcust

    ctr_document_identifier = None
    try:
        ctr_document_identifier = get_ctr_document_identifier(ams_document_id, db_session)
    except Exception:
        logger.exception("An error occurred while attempting to fetch the ctr_document_identifier")

    if not ctr_document_identifier:
        return checked_dependencies
    else:
        checked_dependencies.ctr_document_identifier = ctr_document_identifier

    employee = None
    try:
        employee = get_employee(ams_document_id, db_session)
    except Exception:
        logger.exception("An error occurred while attempting to fetch the employee")

    if not employee:
        return checked_dependencies
    else:
        checked_dependencies.employee = employee

    # Check for a valid VCC
    checked_dependencies.vcc = vcc_check(ams_document_id, db_session)

    return checked_dependencies


def process_ams_document(
    ams_document: Element, db_session: db.Session, reference_file: ReferenceFile
) -> Tuple[Optional[payments_util.ValidationContainer], Optional[state_log_util.StateLog]]:

    logger.debug("Processing AMS document for reference file: %s", reference_file.file_location)

    # verify all dependencies exist
    dependencies = check_dependencies(ams_document, db_session, reference_file)

    if (
        dependencies.ams_document_id is None
        or dependencies.ctr_document_identifier is None
        or dependencies.employee is None
        or dependencies.vc_doc_vcust is None
        or dependencies.vcc is None
    ):
        return None, None

    employee_reference_file = EmployeeReferenceFile(
        employee_id=dependencies.employee.employee_id,
        reference_file_id=reference_file.reference_file_id,
        ctr_document_identifier=dependencies.ctr_document_identifier,
    )
    db_session.add(employee_reference_file)

    validation_container = payments_util.ValidationContainer(dependencies.ams_document_id)

    validation_container, validated_address_data = validate_ams_document(
        ams_document,
        dependencies.ams_document_id,
        dependencies.vc_doc_vcust,
        dependencies.employee,
        validation_container,
    )

    if not dependencies.employee.ctr_address_pair:
        validation_container.add_validation_issue(
            payments_util.ValidationReason.MISSING_IN_DB, "employee.ctr_address_pair"
        )

    current_state = state_log_util.get_latest_state_log_in_flow(
        dependencies.employee, Flow.VENDOR_CHECK, db_session
    )

    if current_state is None or current_state.end_state is None:
        logger.error("An unexpected error occurred with the state_log")
        raise Exception("Missing state_log or state_log missing end_state")

    if validation_container.has_validation_issues():
        state_log = state_log_util.create_finished_state_log(
            end_state=current_state.end_state,
            associated_model=dependencies.employee,
            outcome=state_log_util.build_outcome(
                "Processed Outbound Vendor Return: Validation issues found", validation_container
            ),
            db_session=db_session,
        )

    elif validated_address_data:
        update_employee_data(
            validated_address_data,
            dependencies.ams_document_id,
            dependencies.vc_doc_vcust,
            dependencies.employee,
            db_session=db_session,
        )

        state_log = state_log_util.create_finished_state_log(
            end_state=current_state.end_state,
            associated_model=dependencies.employee,
            outcome=state_log_util.build_outcome(
                "Processed Outbound Vendor Return: No validation issues found", validation_container
            ),
            db_session=db_session,
        )

    return validation_container, state_log


def process_outbound_vendor_customer_return(
    db_session: db.Session, ref_file: ReferenceFile
) -> None:
    logger.info("Processing outbound vendor customer return file: %s", ref_file.file_location)

    # Read the ReferenceFile to string
    # Raise an error if the ReferenceFile is not readable
    try:
        xml_string = payments_util.read_reference_file(
            ref_file, ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN
        )
    except Exception:
        # There was an issue attempting to read the reference file
        logger.exception(
            "Unable to process ReferenceFile", extra={"file_location": ref_file.file_location}
        )
        raise

    # Parse file as XML Document
    # Using .fromstring because file_util.read_file returns the file as a string, not a File object
    # If there is an error, move the file to the error folder
    try:
        root = ET.fromstring(xml_string)
    except Exception:
        # XML parsing issue
        logger.exception("Unable to parse XML", extra={"file_location": ref_file.file_location})
        payments_util.move_reference_file(
            db_session,
            ref_file,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            payments_util.Constants.S3_INBOUND_ERROR_DIR,
        )
        raise

    # Process each AMS_DOCUMENT in the XML Document
    # Move the file to the processed folder
    try:
        for i, ams_document in enumerate(root):
            logger.info(
                "Proccessing record %i of %i total records in outbound vendor customer return file",
                i,
                len(root),
            )
            process_ams_document(ams_document, db_session, ref_file)

        # Note: this function also calls db_session.commit(), so no need to
        # explicitly call it again.
        payments_util.move_reference_file(
            db_session,
            ref_file,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
            payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
    except Exception:
        # Rollback the db
        db_session.rollback()
        # Something bad enough happened that we halted processing
        logger.exception(
            "Unable to process ReferenceFile", extra={"file_location": ref_file.file_location}
        )
        raise

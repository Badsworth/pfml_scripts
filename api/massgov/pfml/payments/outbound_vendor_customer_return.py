from typing import List, Optional, Tuple
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    CtrDocumentIdentifier,
    Employee,
    EmployeeReferenceFile,
    GeoState,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.payments.payments_util import (
    Constants,
    ValidationContainer,
    ValidationReason,
    get_xml_attribute,
)
from massgov.pfml.util.files import read_file, rename_file

logger = logging.get_logger(__name__)

# Constant values used to validate OVR
OUTBOUND_VENDOR_CUSTOMER_RETURN_CONSTANTS = {
    "DOC_CAT": "VCUST",
    "DOC_TYP": "VCC",
    "DOC_CD": "VCC",
    "DOC_DEPT_CD": Constants.COMPTROLLER_DEPT_CODE,
    "DOC_UNIT_CD": Constants.COMPTROLLER_UNIT_CODE,
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
        self.DOC_CAT = get_xml_attribute(vc_doc_vcust, "DOC_CAT")
        self.DOC_TYP = get_xml_attribute(vc_doc_vcust, "DOC_TYP")
        self.DOC_CD = get_xml_attribute(vc_doc_vcust, "DOC_CD")
        self.DOC_DEPT_CD = get_xml_attribute(vc_doc_vcust, "DOC_DEPT_CD")
        self.DOC_UNIT_CD = get_xml_attribute(vc_doc_vcust, "DOC_UNIT_CD")
        self.ORG_TYP = get_xml_attribute(vc_doc_vcust, "ORG_TYP")
        self.TIN = get_xml_attribute(vc_doc_vcust, "TIN")
        self.TIN_TYP = get_xml_attribute(vc_doc_vcust, "TIN_TYP")
        self.VEND_CUST_CD = get_xml_attribute(vc_doc_vcust, "VEND_CUST_CD")
        self.ORG_VEND_VCUST_CD = get_xml_attribute(vc_doc_vcust, "ORG_VEND_CUST_CD")


class VcDocAdData:
    AD_TYP: Optional[str]
    AD_ID: Optional[str]
    STR_1_NM: Optional[str]
    STR_2_NM: Optional[str]
    CITY_NM: Optional[str]
    ST: Optional[str]
    ZIP: Optional[str]

    def __init__(self, vc_doc_ad: Element):
        self.AD_TYP = get_xml_attribute(vc_doc_ad, "AD_TYP")
        self.AD_ID = get_xml_attribute(vc_doc_ad, "AD_ID")
        self.STR_1_NM = get_xml_attribute(vc_doc_ad, "STR_1_NM")
        self.STR_2_NM = get_xml_attribute(vc_doc_ad, "STR_2_NM")
        self.CITY_NM = get_xml_attribute(vc_doc_ad, "CITY_NM")
        self.ST = get_xml_attribute(vc_doc_ad, "ST")
        self.ZIP = get_xml_attribute(vc_doc_ad, "ZIP")


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
            AD_ID.text == Constants.COMPTROLLER_AD_ID
            and AD_TYP.text == Constants.COMPTROLLER_AD_TYPE
        ):
            pfml_payment_addresses.append(address)

    return pfml_payment_addresses


def validate_pfml_address(
    vc_doc_ad: Element, validation_container: ValidationContainer
) -> Optional[VcDocAdData]:
    vc_doc_ad_data = VcDocAdData(vc_doc_ad)

    # Only update the address if the required fields are provided
    address_issues = False

    for field in REQUIRED_ADDRESS_FIELDS:
        value = getattr(vc_doc_ad_data, field)
        if not value:
            validation_container.add_validation_issue(ValidationReason.MISSING_FIELD, field)
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
    validation_container: ValidationContainer,
) -> Tuple[ValidationContainer, Optional[VcDocAdData]]:
    # validate DOC_ID
    if not ams_document_id.startswith("INTFDFML"):
        validation_container.add_validation_issue(ValidationReason.INVALID_VALUE, "DOC_ID")

    # validate VC_DOC_VCUST constant values
    vc_doc_vcust_data = VcDocVcustData(vc_doc_vcust)
    for k, v in OUTBOUND_VENDOR_CUSTOMER_RETURN_CONSTANTS.items():
        field_value = getattr(vc_doc_vcust_data, k)
        if not field_value:
            validation_container.add_validation_issue(ValidationReason.MISSING_FIELD, k)
        elif field_value != v:
            validation_container.add_validation_issue(ValidationReason.INVALID_VALUE, k)

    # validate originating VCC document data
    tin_value = vc_doc_vcust_data.TIN

    if tin_value:
        if employee.tax_identifier:
            if tin_value != employee.tax_identifier.tax_identifier:
                validation_container.add_validation_issue(ValidationReason.INVALID_VALUE, "TIN")
    else:
        validation_container.add_validation_issue(ValidationReason.MISSING_FIELD, "TIN")

    # additional validations

    # Check that there's a valid address (AD_ID == AD010 and AD_TYP == "PA")
    vc_doc_ads = get_pfml_payment_addresses(ams_document)
    validated_address_data = None
    if len(vc_doc_ads) > 1:
        validation_container.add_validation_issue(
            ValidationReason.MULTIPLE_VALUES_FOUND, "VC_DOC_AD"
        )
    elif len(vc_doc_ads) == 0:
        validation_container.add_validation_issue(ValidationReason.VALUE_NOT_FOUND, "VC_DOC_AD")
    else:
        validated_address_data = validate_pfml_address(vc_doc_ads[0], validation_container)

    # Check that VEND_CUST_CD and ORG_VEND_CUST_CD are not null
    if not vc_doc_vcust_data.VEND_CUST_CD:
        validation_container.add_validation_issue(ValidationReason.NON_NULLABLE, "VEND_CUST_CD")

    if not vc_doc_vcust_data.ORG_VEND_VCUST_CD:
        validation_container.add_validation_issue(ValidationReason.NON_NULLABLE, "ORG_VEND_CUST_CD")

    return validation_container, validated_address_data


def handle_xml_syntax_error(
    reference_file: ReferenceFile, outer_exception: Exception, db_session: db.Session
) -> None:
    file_location = reference_file.file_location

    # move file to S3 bucket 'ctr/inbound/error'
    error_filepath = file_location.replace("/received", "/error")
    try:
        rename_file(reference_file.file_location, error_filepath)
    except Exception as inner_exception:
        logger.exception(
            f"File at location '{file_location}' could not be parsed into valid XML, and an error occurred when attempting to move to '{error_filepath}'",
            extra={"error": inner_exception},
        )
        return

    # save new location
    try:
        # update the ReferenceFile's file_location in the db
        reference_file.file_location = error_filepath
        db_session.add(reference_file)
        db_session.commit()
    except Exception as inner_exception:
        logger.exception(
            f"File at location '{file_location}' could not be parsed into valid XML, and has been moved to '{error_filepath}', but an error occurred when saving the new location",
            extra={"error": inner_exception},
        )
        db_session.rollback()
        return

    logger.exception(
        f"File at location '{file_location}' could not be parsed into valid XML, and has been moved to '{error_filepath}'",
        extra={"error": outer_exception},
    )


def update_employee_data(
    validated_address_data: VcDocAdData,
    ams_document_id: str,
    vc_doc_vcust: Element,
    employee: Employee,
    db_session: db.Session,
) -> None:
    # update address fields on the CTR half of the CtrAddressPair
    if not employee.ctr_address_pair.ctr_address:
        ctr_address = Address(address_type_id=AddressType.MAILING.address_type_id)
        employee.ctr_address_pair.ctr_address = ctr_address
        db_session.add(employee)

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
        logger.exception(
            f"Multiple employees found for specified CTR Document Identifier {ams_document_id}"
        )

    if not employee:
        logger.error(f"Employee not found for AMS_DOCUMENT with DOC_ID {ams_document_id}")

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
        logger.exception(
            f"Could not find matching VCC for AMS_DOCUMENT with DOC_ID {ams_document_id}"
        )
        return None

    if not vcc_employee_reference_file:
        logger.error(
            f"Failed to find VCC file for specified CTR Document Identifier {ams_document_id}"
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
        logger.exception(
            f"Multiple CtrDocumentIdentifiers found for specified CTR Document Identifier {ams_document_id}"
        )
        return ctr_document_identifier

    if not ctr_document_identifier:
        logger.error(
            f"CTR_DOCUMENT_IDENTIFIER not found for AMS_DOCUMENT with DOC_ID {ams_document_id}"
        )

    return ctr_document_identifier


def check_dependencies(
    ams_document: Element, db_session: db.Session, reference_file: ReferenceFile,
) -> Dependencies:

    checked_dependencies = Dependencies()

    ams_document_id = ams_document.get("DOC_ID")

    if ams_document_id is None or ams_document_id == "null":
        logger.error(f"AMS_DOCUMENT is missing DOC_ID value in file {reference_file.file_location}")
        return checked_dependencies
    else:
        checked_dependencies.ams_document_id = ams_document_id

    vc_doc_vcust = ams_document.find("VC_DOC_VCUST")
    if not vc_doc_vcust:
        logger.error(f"Missing VC_DOC_VCUST in AMS_DOCUMENT with DOC_ID {ams_document_id}")
        return checked_dependencies
    else:
        checked_dependencies.vc_doc_vcust = vc_doc_vcust

    ctr_document_identifier = get_ctr_document_identifier(ams_document_id, db_session)
    if not ctr_document_identifier:
        return checked_dependencies
    else:
        checked_dependencies.ctr_document_identifier = ctr_document_identifier

    employee = get_employee(ams_document_id, db_session)
    if not employee:
        return checked_dependencies
    else:
        checked_dependencies.employee = employee

    # Check for a valid VCC
    checked_dependencies.vcc = vcc_check(ams_document_id, db_session)

    return checked_dependencies


def process_ams_document(
    ams_document: Element, db_session: db.Session, reference_file: ReferenceFile
) -> Tuple[Optional[ValidationContainer], Optional[state_log_util.StateLog]]:

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

    state_log = state_log_util.create_state_log(
        start_state=State.VCC_SENT,
        associated_model=dependencies.employee,
        db_session=db_session,
        commit=False,
    )

    employee_reference_file = EmployeeReferenceFile(
        employee_id=dependencies.employee.employee_id,
        reference_file_id=reference_file.reference_file_id,
        ctr_document_identifier=dependencies.ctr_document_identifier,
    )
    db_session.add(employee_reference_file)

    validation_container = ValidationContainer(dependencies.ams_document_id)

    validation_container, validated_address_data = validate_ams_document(
        ams_document,
        dependencies.ams_document_id,
        dependencies.vc_doc_vcust,
        dependencies.employee,
        validation_container,
    )

    if not dependencies.employee.ctr_address_pair:
        validation_container.add_validation_issue(
            ValidationReason.MISSING_IN_DB, "employee.ctr_address_pair"
        )

    if validation_container.has_validation_issues():
        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.VCC_SENT,
            outcome=state_log_util.build_outcome("Validation issues found", validation_container),
            db_session=db_session,
            commit=False,
        )
    elif validated_address_data:
        update_employee_data(
            validated_address_data,
            dependencies.ams_document_id,
            dependencies.vc_doc_vcust,
            dependencies.employee,
            db_session=db_session,
        )

        state_log_util.finish_state_log(
            state_log=state_log,
            end_state=State.VCC_SENT,
            outcome=state_log_util.build_outcome(
                "No validation issues found", validation_container
            ),
            db_session=db_session,
            commit=False,
        )

    return validation_container, state_log


def move_processed_file(reference_file: ReferenceFile) -> None:
    file_location = reference_file.file_location
    # Move the file within the agency transfer S3 bucket to ctr/inbound/processed
    # TODO: Switch to using get_s3_config?
    success_filepath = file_location.replace("/received", "/processed")

    rename_file(reference_file.file_location, success_filepath)

    # Update the file_location in the db
    reference_file.file_location = success_filepath


def validate_and_fetch_file(reference_file: ReferenceFile) -> Optional[ReferenceFile]:
    file_location = reference_file.file_location
    outbound_vendor_customer_return_file = None
    if (
        reference_file.reference_file_type_id
        != ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_id
    ):
        logger.error(
            f"Skipping processing file at location '{file_location}' because it is not of type \
                '{ReferenceFileType.OUTBOUND_VENDOR_CUSTOMER_RETURN.reference_file_type_description}'"
        )
        return outbound_vendor_customer_return_file

    # Retrieve file from S3 bucket
    try:
        outbound_vendor_customer_return_file = read_file(file_location)
    except Exception as e:
        logger.error(f"Error retrieving file from S3 at: {file_location}", extra={"error": e})

    return outbound_vendor_customer_return_file


def process_outbound_vendor_customer_return(
    reference_file: ReferenceFile, db_session: db.Session
) -> None:
    outbound_vendor_customer_return_file = validate_and_fetch_file(reference_file)

    if not outbound_vendor_customer_return_file:
        return

    xml_document = None
    # Parse file as XML Document
    # Using .fromstring because .read_file returns the file as a string, not a File object
    try:
        xml_document = ET.fromstring(outbound_vendor_customer_return_file)
    except Exception as exception:
        handle_xml_syntax_error(reference_file, exception, db_session)
        return

    # Process each AMS_DOCUMENT in the XML Document
    try:
        for ams_document in xml_document:
            process_ams_document(ams_document, db_session, reference_file)

        try:
            move_processed_file(reference_file)
        except Exception as e:
            db_session.rollback()
            logger.exception(
                f"Outbound Vendor Customer Return ReferenceFile at {reference_file.file_location} processed, but could not move the file to the processed folder in S3",
                extra={"error": e},
            )
            return

        db_session.commit()
    except Exception as exception:
        db_session.rollback()
        logger.exception(
            f"Unexpected exception processing outbound vendor customer return at {reference_file.file_location}",
            extra={"error": exception},
        )

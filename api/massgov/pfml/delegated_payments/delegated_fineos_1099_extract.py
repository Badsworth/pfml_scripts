import enum
import uuid
from typing import Any, Callable, Dict, Optional, cast

import defusedxml.ElementTree as ET

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import Employee, ReferenceFile, ReferenceFileType
from massgov.pfml.db.models.payments import FineosExtractVbi1099DataSom, Pfml1099Request
from massgov.pfml.delegated_payments.step import Step

logger = logging.get_logger(__name__)


REQUEST_TYPE_ONE = "512512001"
REQUEST_TYPE_TWO = "512512002"
REQUEST_TYPE_THREE = "512512003"


class Data1099:
    """
    A class for containing any and all 1099 extract data. Handles validation
    and pulling values out of the extract and into pfmlrequest table.
    """

    validation_container: payments_util.ValidationContainer

    data_1099_record: FineosExtractVbi1099DataSom

    count_incrementer: Optional[Callable[[str], None]]

    vbi_1099_data_som_id: str
    first_names: Optional[str] = None
    last_name: Optional[str] = None
    customer_no: Optional[str] = None
    packed_data: Optional[str] = None
    document_type: Optional[str] = None
    c_value: Optional[str] = None
    request_type: str
    packed_xml: ET
    employee_id: uuid.UUID

    def __init__(
        self,
        vbi_1099_data_som_id: str,
        employee_id: uuid.UUID,
        data_1099_record: FineosExtractVbi1099DataSom,
        packed_xml: ET,
        count_incrementer: Optional[Callable[[str], None]] = None,
    ):
        self.validation_container = payments_util.ValidationContainer(vbi_1099_data_som_id)
        self.count_incrementer = count_incrementer
        self.vbi_1099_data_som_id = vbi_1099_data_som_id
        self.data_1099_record = data_1099_record
        self.employee_id = employee_id
        self.packed_data = payments_util.validate_db_input(
            "packeddata", data_1099_record, self.validation_container, True
        )
        self.packed_xml = packed_xml
        if self.packed_data:
            self.request_type = self.parse_packed_data_info()
            self.packed_data_validator()

        self.first_names = payments_util.validate_db_input(
            "firstnames", data_1099_record, self.validation_container, False
        )
        self.last_name = payments_util.validate_db_input(
            "lastname", data_1099_record, self.validation_container, False
        )
        self.customer_no = payments_util.validate_db_input(
            "customerno", data_1099_record, self.validation_container, False
        )
        self.document_type = payments_util.validate_db_input(
            "documenttype", data_1099_record, self.validation_container, False
        )
        self.c_value = payments_util.validate_db_input(
            "c", data_1099_record, self.validation_container, False
        )
        if self.validation_container.has_validation_issues():
            logger.error("Packed Data validation issues for customer %s", self.customer_no)
            logger.error(self.validation_container.validation_issues)

    def increment(self, metric: str) -> None:
        if self.count_incrementer:
            self.count_incrementer(metric)

    def packed_data_validator(self) -> None:
        valid_values = ["512512001", "512512002", "512512003"]
        value_str = self.request_type
        logger.info("The request type is %s", value_str)
        if value_str is None or value_str not in valid_values:
            self.validation_container.add_validation_issue(
                payments_util.ValidationReason.INVALID_VALUE, "packeddata"
            )

    def parse_packed_data_info(self) -> str:
        logger.info("Processing xml packed data object")
        data_pack = self.packed_xml

        if data_pack is not None:

            try:
                for elem in data_pack.iter("EnumObject"):
                    if elem.findtext("value") is not None:
                        request_reason = elem.findtext("value")
                        logger.info(elem.findtext("value"))
                        if self.count_incrementer:
                            if request_reason == REQUEST_TYPE_ONE:
                                self.count_incrementer(Data1099ExtractStep.Metrics.REPRINT_REQUESTS)
                            elif request_reason == REQUEST_TYPE_TWO:
                                self.count_incrementer(
                                    Data1099ExtractStep.Metrics.CORRECTION_ADDRESS_CHANGE
                                )

                            elif request_reason == REQUEST_TYPE_THREE:
                                self.count_incrementer(
                                    Data1099ExtractStep.Metrics.CORRECTION_PAYMENT
                                )

                            else:

                                self.count_incrementer(Data1099ExtractStep.Metrics.INVALID_REQUESTS)
                    logger.info("Found reason type", extra={"reason_type": request_reason})
            except Exception:
                logger.error("Unable to get reason for 1099 request")
        return request_reason

    def get_1099_data_message_str(self) -> str:
        return f"[C={self.c_value},customer_no={self.customer_no},vbi_som_id={self.vbi_1099_data_som_id}]"

    def get_traceable_details(self) -> Dict[str, Optional[Any]]:

        return {
            "c_value": self.c_value,
            "packed_data": self.packed_data,
            "vbi_1099_data_som_id": self.vbi_1099_data_som_id,
            "fineos_customer_no": self.customer_no,
            "request_type": self.request_type,
            "document_type": self.document_type,
        }


class Data1099ExtractStep(Step):
    class Metrics(str, enum.Enum):

        PROCESSED_REQUESTS = "processed_requests"
        SKIPPED_REQUESTS_ERRORED = "skipped_errored_requests"
        NEW_REQUESTS = "new_requests"
        DUPLICATE_REQUESTS = "duplicate_requets"
        REPRINT_REQUESTS = "reprint_requests"
        CORRECTION_ADDRESS_CHANGE = "address_change_requests"
        CORRECTION_PAYMENT = "payment_correction_requests"
        INVALID_REQUESTS = "invalid_requests"
        VBI_1099_DATA_SOM_RECORD_COUNT = "vbi_1099_data_som_record_count"

    def run_step(self) -> None:
        logger.info("Processing 1099 extract data")
        self.process_1099_records()
        logger.info("Successfully processed 1099 requests data")

    def process_1099_records(self) -> None:

        reference_file = (
            self.db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.FINEOS_1099_DATA_EXTRACT.reference_file_type_id
            )
            .order_by(ReferenceFile.created_at.desc())
            .first()
        )
        if not reference_file:
            raise Exception(
                "This would only happen the first time you run in an env and have no extracts, make sure FINEOS has created extracts"
            )
        if reference_file.processed_import_log_id:
            logger.warning(
                "Already processed the most recent extracts for %s in import run %s",
                reference_file.file_location,
                reference_file.processed_import_log_id,
            )
            return
        records = (
            self.db_session.query(FineosExtractVbi1099DataSom)
            .filter(
                FineosExtractVbi1099DataSom.reference_file_id == reference_file.reference_file_id
            )
            .order_by(FineosExtractVbi1099DataSom.customerno)
            .all()
        )
        record_iter = iter(records)
        # For each record, check if there is a employee id for customer number,
        # process the xml data.
        # Do validation and then check existing requests for each employee id
        # and sort of
        for record in record_iter:
            self.increment(self.Metrics.VBI_1099_DATA_SOM_RECORD_COUNT)
            customerno = record.customerno
            employee_record = (
                self.db_session.query(Employee)
                .filter(Employee.fineos_customer_number == customerno)
                .first()
            )
            if not employee_record:
                logger.warning(
                    "There is no employee record for the customer number, %s", customerno
                )
                self.increment(self.Metrics.SKIPPED_REQUESTS_ERRORED)
                continue
            else:
                logger.info("Found a employee record for customer number %s", customerno)
                vbi_1099_data_som_id = cast(str, record.vbi_1099_data_som_id)
                if record.packeddata is not None:
                    packed_data_str = cast(ET, record.packeddata)
                else:
                    packed_data_str = ""
                vbi_1099_data = Data1099(
                    vbi_1099_data_som_id,
                    employee_record.employee_id,
                    record,
                    packed_data_str,
                    count_incrementer=self.increment,
                )
                if vbi_1099_data.validation_container.has_validation_issues():
                    self.increment(self.Metrics.SKIPPED_REQUESTS_ERRORED)
                    logger.info(
                        "There are validation issues",
                        extra={"validation_reason": vbi_1099_data.validation_container.get_reasons},
                    )

                else:
                    self.process_1099_data_record(vbi_1099_data, reference_file)
                    logger.info(
                        "After consuming extracts and performing initial validation, payment %s added to state [%s]",
                        vbi_1099_data.get_1099_data_message_str(),
                        "Successfully processed 1099 extract records",
                        extra=vbi_1099_data.get_traceable_details(),
                    )

    def process_1099_data_record(
        self, vbi_1099_data: Data1099, reference_file: ReferenceFile
    ) -> None:

        if not vbi_1099_data.validation_container.has_validation_issues():
            # Check if there is an existing record in db for the employee id
            # if so, get the record, if there is still a open request, overwrite
            # if no record exists, createthe new record
            logger.info("Checking to see if this request is duplicate ")
            existing_requests = (
                self.db_session.query(Pfml1099Request)
                .filter(Pfml1099Request.employee_id == vbi_1099_data.employee_id)
                .all()
            )
            correction_ind = self.map_request_type(vbi_1099_data.request_type)

            if len(existing_requests) > 0:
                existing_requests_list = iter(existing_requests)
                for existing_record in existing_requests_list:
                    if existing_record.pfml_1099_batch_id:
                        logger.info("Previous request now closed, so create a new one")
                        self.create_update_record(vbi_1099_data.employee_id, correction_ind, None)
                    else:
                        logger.info("There is a open request, overwrite")
                        self.create_update_record(
                            vbi_1099_data.employee_id,
                            correction_ind,
                            existing_record.pfml_1099_request_id,
                        )
            else:
                logger.info("This is a new request")
                self.create_update_record(vbi_1099_data.employee_id, correction_ind, None)
            reference_file.processed_import_log_id = self.get_import_log_id()

    def map_request_type(self, reqType: str) -> bool:

        logger.info("Request type is %s", reqType)
        if reqType == REQUEST_TYPE_TWO or reqType == REQUEST_TYPE_THREE:
            logger.info("Regenerate request type", extra={"reason_type": reqType})
            return True
        else:
            logger.info("Reprint request type", extra={"reason_type": reqType})
            return False

    def create_update_record(
        self, emp_id: uuid.UUID, correction_ind: bool, existing_id: Optional[uuid.UUID]
    ) -> int:
        self.increment(self.Metrics.PROCESSED_REQUESTS)
        if not existing_id:
            logger.info("Request is new", extra={"existing_id": "None"})
            self.increment(self.Metrics.NEW_REQUESTS)
            pfmlRequest = Pfml1099Request(pfml_1099_request_id=uuid.uuid4())
            pfmlRequest.employee_id = emp_id
            pfmlRequest.correction_ind = correction_ind
            self.db_session.add(pfmlRequest)
            return 1

        else:
            logger.info("There is a open request, updating", extra={"existing_id": existing_id})
            self.increment(self.Metrics.DUPLICATE_REQUESTS)
            self.db_session.query(Pfml1099Request).filter(
                Pfml1099Request.pfml_1099_batch_id == existing_id
            ).update({Pfml1099Request.correction_ind: correction_ind})
            return 2

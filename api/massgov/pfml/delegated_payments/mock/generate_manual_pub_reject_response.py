from dataclasses import asdict, dataclass
from typing import List, Optional

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import PaymentMethod
from massgov.pfml.delegated_payments.mock.scenario_data_generator import ScenarioData
from massgov.pfml.delegated_payments.pub.manual_pub_reject_file_parser import (
    ManualPubRejectFileParser,
)
from massgov.pfml.util.files import create_csv_from_list

logger = logging.get_logger(__name__)


@dataclass
class ManualPubRejectData:
    record_id: Optional[str] = None
    notes: Optional[str] = None


MANUAL_PUB_REJECT_DATA_FIELDS = ManualPubRejectData(
    record_id=ManualPubRejectFileParser.RECORD_ID_COLUMN,
    notes=ManualPubRejectFileParser.NOTES_COLUMN,
)


class ManualPubRejectResponseGenerator:
    def __init__(self, scenario_dataset: List[ScenarioData], folder_path: str):
        self.scenario_dataset = scenario_dataset
        self.folder_path = folder_path

        self.responses: List[ManualPubRejectData] = []

    def run(self) -> None:
        for scenario_data in self.scenario_dataset:
            self.add_response_entry_for_scenario(scenario_data)

        self.write_files()

    def add_response_entry_for_scenario(self, scenario_data: ScenarioData) -> None:
        scenario_descriptor = scenario_data.scenario_descriptor
        payment = scenario_data.payment

        # Only ACH would be relevant
        if scenario_descriptor.payment_method != PaymentMethod.ACH:
            return

        # Only add if configured, not expected for most scenarios
        if not scenario_descriptor.manual_pub_reject_response:
            return

        if not payment:
            raise Exception(
                "No payment found for scenario %s that is configured to do manual PUB reject"
                % scenario_descriptor.scenario_name
            )

        individual_id = f"P{payment.pub_individual_id}"
        notes = scenario_descriptor.manual_pub_reject_notes

        self.responses.append(ManualPubRejectData(record_id=individual_id, notes=notes))

    def write_files(self) -> None:
        if len(self.responses) > 0:
            self.write_csv(
                self.responses,
                MANUAL_PUB_REJECT_DATA_FIELDS,
                f"2022-01-01-12-00-00-{payments_util.Constants.FILE_NAME_MANUAL_PUB_REJECT}",
            )

    def write_csv(
        self,
        entries_list: List[ManualPubRejectData],
        fieldnames: ManualPubRejectData,
        file_name: str,
    ) -> None:
        fieldname_by_key = {key: value for key, value in asdict(fieldnames).items()}

        response_csv_data = []
        for entry in entries_list:
            _data = asdict(entry)

            data = {}
            for key, value in _data.items():
                fieldname = fieldname_by_key.get(key, None)
                if fieldname:
                    data[fieldname] = value

            response_csv_data.append(data)

        create_csv_from_list(
            data=response_csv_data,
            fieldnames=list(asdict(fieldnames).values()),
            file_name=file_name,
            folder_path=self.folder_path,
        )

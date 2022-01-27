import argparse
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

from dateutil.parser import isoparse

import massgov.pfml.db as db
import massgov.pfml.dua.demographics as demographics
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import ReferenceFile
from massgov.pfml.dua.config import get_moveit_config, get_transfer_config
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)

MOVEIT = "MOVEIT"
FILE = "FILE"
IMPORT_MODE_ALLOWED_VALUES = [MOVEIT, FILE]

IMPORT_DEMOGRAPHICS_FILE = "import-demographics-file"
SET_ORG_UNIT_ID = "set-org-unit-id"
ALL = "ALL"
ALLOWED_STEPS = [ALL, IMPORT_DEMOGRAPHICS_FILE, SET_ORG_UNIT_ID]


@dataclass
class Configuration:
    import_mode: str
    file_path: str

    import_demographics_file: bool
    set_org_unit_id: bool
    set_org_unit_id_start_date: Optional[datetime] = None

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Process DUA Demographics file")
        parser.add_argument(
            "--import-mode",
            choices=IMPORT_MODE_ALLOWED_VALUES,
            default=FILE,
            help="Indicate which mode to process: MOVEIT scans MOVEit, FILE takes a direct path. FILE must be "
            "accompanies by --file arg",
        )

        parser.add_argument(
            "--file",
            help="Path to DUA_DFML_CLM_DEM_YYYYMMDDHHMM file to process. Must be used with --mode FILE argument",
        )

        parser.add_argument(
            "--start-date",
            help="Specifies a start date when set-org-unit-id is run. Must be in ISO-8601 format. If not set, "
            "start time of run will be used if also importing a file, otherwise will process all records.",
        )

        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_STEPS,
            default=[IMPORT_DEMOGRAPHICS_FILE],
            help="Indicate which steps of the process to run",
        )

        args = parser.parse_args(input_args)
        self.import_mode = args.import_mode

        steps = set(args.steps)
        if ALL in steps:
            self.import_demographics_file = True
            self.set_org_unit_id = True
        else:
            self.import_demographics_file = IMPORT_DEMOGRAPHICS_FILE in steps
            self.set_org_unit_id = SET_ORG_UNIT_ID in steps

        if args.start_date is not None:
            self.set_org_unit_id_start_date = isoparse(args.start_date)
        elif self.import_demographics_file:
            self.set_org_unit_id_start_date = datetime_util.utcnow()

        if self.import_demographics_file and self.import_mode == FILE and args.file is None:
            raise Exception("File is required when in FILE mode.")

        self.file_path = args.file


@background_task("dua-import-employee-demographics")
def main():
    config = Configuration(sys.argv[1:])
    logger.info("Starting dua-import-employee-demographics with config", extra=asdict(config))

    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with LogEntry(log_entry_db_session, "DUA import_demographics_file") as log_entry:

            if config.import_demographics_file:
                transfer_config = get_transfer_config()

                if config.import_mode == MOVEIT:
                    moveit_config = get_moveit_config()
                    reference_files = demographics.download_demographics_file_from_moveit(
                        db_session,
                        log_entry,
                        transfer_config=transfer_config,
                        moveit_config=moveit_config,
                    )

                    for file in reference_files:
                        demographics.load_demographics_file(
                            db_session,
                            file,
                            log_entry,
                            move_files=True,
                            transfer_config=transfer_config,
                        )

                elif config.import_mode == FILE:
                    demographics.load_demographics_file(
                        db_session,
                        ReferenceFile(file_location=config.file_path),
                        log_entry,
                        transfer_config=transfer_config,
                    )

            if config.set_org_unit_id:
                demographics.set_employee_occupation_from_demographic_data(
                    db_session, log_entry, config.set_org_unit_id_start_date
                )

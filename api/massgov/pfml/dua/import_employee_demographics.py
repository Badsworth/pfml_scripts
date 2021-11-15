import argparse
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

import massgov.pfml.db as db
import massgov.pfml.dua.demographics as demographics
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import ReferenceFile
from massgov.pfml.dua.config import get_moveit_config, get_s3_config
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)

MOVEIT = "MOVEIT"
FILE = "FILE"
ALLOWED_VALUES = [MOVEIT, FILE]

IMPORT_DEMOGRAPHICS_FILE = "import-demographics-file"
SET_ORG_UNIT_ID = "set-org-unit-id"
ALL = "ALL"
ALLOWED_STEPS = [ALL, IMPORT_DEMOGRAPHICS_FILE, SET_ORG_UNIT_ID]


@dataclass
class Configuration:
    mode: str
    file_path: str

    import_demographics_file: bool
    set_org_unit_id: bool
    set_org_unit_id_start_date: Optional[datetime]

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Process DUA Demographics file")
        parser.add_argument(
            "--mode",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=FILE,
            help="Indicate which mode to process: MOVEIT scans MOVEit, FILE takes a direct path. FILE must be accompanies by --file arg",
        )

        parser.add_argument(
            "--file",
            help="Path to DUA_DFML_CLM_DEM_YYYYMMDDHHMM file to process. Must be used with --mode FILE argument",
        )

        parser.add_argument(
            "--startdate",
            help="Specifies a start date when set-org-unit-id is run. Must be in `%Y-%m-%d %H:%M:%S` format. If not set, all records will be set if applicable.",
        )

        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_STEPS,
            default=[IMPORT_DEMOGRAPHICS_FILE],
            help="Indicate which steps of the process to run",
        )

        args = parser.parse_args(input_args)
        self.mode = args.mode

        steps = set(args.steps)
        if ALL in steps:
            self.import_demographics_file = True
            self.set_org_unit_id = True
        else:
            self.import_demographics_file = IMPORT_DEMOGRAPHICS_FILE in steps
            self.set_org_unit_id = SET_ORG_UNIT_ID in steps

        if args.startdate is not None:
            self.set_org_unit_id_start_date = datetime.strptime(args.startdate, "%Y-%m-%d %H:%M:%S")
        else:
            self.set_org_unit_id_start_date = datetime_util.utcnow()

        if self.mode == FILE and args.file is None:
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
            s3_config = get_s3_config()
            if config.import_demographics_file:
                if config.mode == MOVEIT:
                    moveit_config = get_moveit_config()
                    reference_files = demographics.download_demographics_file_from_moveit(
                        db_session, log_entry, s3_config=s3_config, moveit_config=moveit_config
                    )

                    for file in reference_files:
                        demographics.load_demographics_file(
                            db_session, file, log_entry, move_files=True, s3_config=s3_config
                        )

                elif config.mode == FILE:
                    demographics.load_demographics_file(
                        db_session,
                        ReferenceFile(file_location=config.file_path),
                        log_entry,
                        s3_config=s3_config,
                    )
            if config.set_org_unit_id:
                demographics.set_employee_occupation_from_demographic_data(
                    db_session, log_entry, config.set_org_unit_id_start_date
                )

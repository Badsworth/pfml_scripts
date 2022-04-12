import argparse
import sys
from dataclasses import asdict, dataclass
from typing import List

import massgov.pfml.db as db
import massgov.pfml.dua.employer as employer
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import ReferenceFile
from massgov.pfml.dua.config import get_moveit_config, get_transfer_config
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task, get_current_task_name

logger = logging.get_logger(__name__)

MOVEIT = "MOVEIT"
FILE = "FILE"
IMPORT_MODE_ALLOWED_VALUES = [MOVEIT, FILE]

IMPORT_EMPLOYER_FILE = "import-employer-file"


@dataclass
class Configuration:
    import_mode: str
    file_path: str

    import_employer_file: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Process DUA Employer file")
        parser.add_argument(
            "--import-mode",
            choices=IMPORT_MODE_ALLOWED_VALUES,
            default=FILE,
            help="Indicate which mode to process: MOVEIT scans MOVEit, FILE takes a direct path. FILE must be accompanies by --file arg",
        )

        parser.add_argument(
            "--file",
            help="Path to DUA_DFML_EMP_YYYYMMDDHHMM file to process. Must be used with --mode FILE argument",
        )

        args = parser.parse_args(input_args)
        self.import_mode = args.import_mode
        self.import_employer_file = True

        if self.import_mode == FILE and args.file is None:
            raise Exception("File is required when in FILE mode.")

        self.file_path = args.file


@background_task("dua-import-employer")
def main():
    config = Configuration(sys.argv[1:])
    logger.info("Starting dua-import-employer with config", extra=asdict(config))

    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with LogEntry(
            log_entry_db_session, get_current_task_name(), "DUA import_employer_file"
        ) as log_entry:

            if config.import_employer_file:
                transfer_config = get_transfer_config()

                if config.import_mode == MOVEIT:
                    moveit_config = get_moveit_config()
                    reference_files = employer.download_employer_file_from_moveit(
                        db_session,
                        log_entry,
                        transfer_config=transfer_config,
                        moveit_config=moveit_config,
                    )

                    for file in reference_files:
                        employer.load_employer_file(
                            db_session,
                            file,
                            log_entry,
                            move_files=True,
                            transfer_config=transfer_config,
                        )

                elif config.import_mode == FILE:
                    employer.load_employer_file(
                        db_session,
                        ReferenceFile(file_location=config.file_path),
                        log_entry,
                        transfer_config=transfer_config,
                    )

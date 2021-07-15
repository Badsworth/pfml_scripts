import enum
import os
from typing import List, Optional

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)

FILE_NAME_FORMAT = "{}-{}"
OK_FILE_SUFFIX = ".OK"


class PickupResponseFilesStep(Step):
    """
    This moves all files from the incoming directories that are populated by
    either Sharepoint or MoveIT to our archive folders for processing.

    Note that this method does not create reference files and leaves that to
    the processes that consume the files.
    """

    class Metrics(str, enum.Enum):
        FILES_MOVED_COUNT = "files_moved_count"
        UNKNOWN_FILES_COUNT = "unknown_files_count"

    def run_step(self):
        s3_config = payments_config.get_s3_config()

        # Move audit report from the DFML folder populated by Sharepoint
        payment_reject_received_folder = os.path.join(
            s3_config.pfml_payment_rejects_archive_path,
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
        )
        self.move_files(
            s3_config.dfml_response_inbound_path,
            payment_reject_received_folder,
            payments_util.Constants.FILE_NAME_PAYMENT_AUDIT_REPORT,
        )

        # Move check return files from the DFML folder populated by MoveIt
        # We expect this to copy both the Paid & Outstanding files
        pub_check_received_folder = os.path.join(
            s3_config.pfml_pub_check_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
        )
        self.move_files(
            s3_config.pub_moveit_inbound_path,
            pub_check_received_folder,
            payments_util.Constants.FILE_NAME_PUB_POSITIVE_PAY,
        )

        # Move ACH return files from the DFML folder populated by MoveIt
        pub_ach_received_folder = os.path.join(
            s3_config.pfml_pub_ach_archive_path, payments_util.Constants.S3_INBOUND_RECEIVED_DIR
        )
        self.move_files(
            s3_config.pub_moveit_inbound_path,
            pub_ach_received_folder,
            payments_util.Constants.FILE_NAME_PUB_NACHA,
        )

        # Check if anything else is present in the directories that we don't expect
        # This won't error, just updates metrics and logs a warning.
        self.check_dir_after(s3_config.dfml_response_inbound_path)
        self.check_dir_after(s3_config.pub_moveit_inbound_path, [OK_FILE_SUFFIX])

    def move_files(
        self, source_directory: str, destination_directory: str, expected_file_name: str
    ) -> None:
        logger.info("Looking in %s for files with name %s", source_directory, expected_file_name)
        file_names = file_util.list_files(source_directory)
        logger.info("Found files %s in %s", file_names, source_directory)

        files_to_move = []
        for file_name in file_names:
            if expected_file_name.lower() in file_name.lower():
                files_to_move.append(file_name)

        now = payments_util.get_now()
        for file_to_move in files_to_move:
            source_path = os.path.join(source_directory, file_to_move)

            # In case we ever need to process more than one file of a name
            # add a timestamp to the filename so each file is named uniquely
            timestamped_file = FILE_NAME_FORMAT.format(
                now.strftime("%Y-%m-%d-%H-%M-%S"), file_to_move
            )
            destination_path = os.path.join(destination_directory, timestamped_file)

            logger.info(
                "Moving %s file from %s to %s", expected_file_name, source_path, destination_path
            )
            file_util.rename_file(source_path, destination_path)

        num_files_to_move = len(files_to_move)
        if num_files_to_move == 0:
            logger.info(
                "No files found in %s for expected name %s", source_directory, expected_file_name
            )

        self.increment(expected_file_name + "_file_moved_count", num_files_to_move)
        self.increment(self.Metrics.FILES_MOVED_COUNT, num_files_to_move)

    def check_dir_after(
        self, source_directory: str, expected_misc_files: Optional[List[str]] = None
    ) -> None:
        """
        As a sanity test, check the directories after we've processed to verify
        that no files are present in the inbound directories that we don't expect to be there
        """
        file_names = file_util.list_files(source_directory)

        for file_name in file_names:
            lower_file_name = file_name.lower()

            file_is_expected = False
            if expected_misc_files:
                for expected_misc_file in expected_misc_files:
                    if expected_misc_file.lower() in lower_file_name:
                        file_is_expected = True
                        break

            if file_is_expected:
                logger.info(
                    "Found file %s in directory %s which is expected", file_name, source_directory
                )

            else:
                logger.warning(
                    "Found file %s in directory %s and was not expecting it",
                    file_name,
                    source_directory,
                )
                self.increment(self.Metrics.UNKNOWN_FILES_COUNT)

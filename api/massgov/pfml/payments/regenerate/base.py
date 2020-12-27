#
# Regenerate payments files - common code to all types of files.
#

import abc
import os.path

import massgov.pfml.db
import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import ReferenceFile

logger = massgov.pfml.util.logging.get_logger(__name__)


class ReferenceFileRegenerator(abc.ABC, metaclass=abc.ABCMeta):
    """Base class to regenerate a reference file."""

    reference_file: ReferenceFile
    outbound_path: str
    db_session: massgov.pfml.db.Session
    directory_name: str  # Directory for this batch, e.g. "EOL20201216GAX10"

    def __init__(
        self, reference_file: ReferenceFile, outbound_path: str, db_session: massgov.pfml.db.Session
    ):
        self.reference_file = reference_file
        self.outbound_path = outbound_path
        self.db_session = db_session
        self.directory_name = os.path.basename(reference_file.file_location.rstrip("/"))

    def run(self):
        logger.info("move to error directory")
        self.move_to_error_directory()
        logger.info("update entries")
        self.update_entries()
        logger.info("create new file")
        self.create_new_file()
        logger.info("upload to MoveIT")
        self.upload_to_moveit()
        logger.info("send BIE")
        self.send_bie()

    def move_to_error_directory(self):
        source_path = self.reference_file.file_location
        destination_path = f"{self.outbound_path}/error/{self.directory_name}"

        logger.info("move %s to %s", source_path, destination_path)
        if source_path == destination_path:
            logger.info("already in error directory - skipping rename")
            return

        massgov.pfml.util.files.rename_recursive(source_path, destination_path)

        self.reference_file.file_location = destination_path
        self.db_session.commit()

    @abc.abstractmethod
    def update_entries(self):
        raise NotImplementedError

    @abc.abstractmethod
    def create_new_file(self):
        raise NotImplementedError

    def upload_to_moveit(self):
        pass

    @abc.abstractmethod
    def send_bie(self):
        raise NotImplementedError

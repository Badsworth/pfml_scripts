import os
from dataclasses import dataclass

from sqlalchemy.orm.exc import MultipleResultsFound
from tenacity import retry, stop_after_attempt

import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import ReferenceFile

logger = logging.get_logger(__name__)


@dataclass
class SftpS3TransferConfig:
    # S3 bucket without any path to directory (s3://bucket_name/).
    s3_bucket_uri: str
    # URI for SFTP server with user and port information included (sftp://user@example.com:2222/).
    sftp_uri: str
    # Paths to various directories (path/to/dir). Paths here can apply to either S3 or SFTP.
    source_dir: str
    dest_dir: str
    archive_dir: str
    # String representation of the password of the SSH key (my_str0ng_pa$$word).
    ssh_key_password: str
    # String representation of the private key.
    ssh_key: str


def copy_to_sftp_and_archive_s3_files(
    config: SftpS3TransferConfig, db_session: db.Session,
) -> None:
    source_dir_path = os.path.join(config.s3_bucket_uri, config.source_dir)
    s3_filenames = file_util.list_files(source_dir_path)
    if len(s3_filenames) == 0:
        # If there are no new files in S3 return early to avoid the overhead of an SFTP connection.
        return

    sftp_client = file_util.get_sftp_client(
        uri=config.sftp_uri, ssh_key_password=config.ssh_key_password, ssh_key=config.ssh_key,
    )

    # List files so we can avoid overwriting a file in the destination directory.
    dest_dir_filenames = sftp_client.listdir(config.dest_dir)
    for filename in s3_filenames:
        if filename in dest_dir_filenames:
            logger.error(
                "Skipping file named '{}' because it already exists in destination directory '{}'".format(
                    filename, config.dest_dir
                ),
            )
            continue

        source_filepath = os.path.join(source_dir_path, filename)
        dest_filepath = os.path.join(config.dest_dir, filename)

        try:
            reference_file = (
                db_session.query(ReferenceFile)
                .filter(ReferenceFile.file_location == source_filepath)
                .one_or_none()
            )
        except MultipleResultsFound:
            logger.error(
                "Found more than one ReferenceFile with the same file_location:", source_filepath,
            )
            continue
        except Exception as e:
            raise e

        if not reference_file:
            logger.info(
                "Could not find ReferenceFile record in database for file in S3 named:",
                source_filepath,
            )
            continue

        # TODO: Create state_log entry.

        try:
            # Copy to MoveIt.
            _copy_file_from_s3_to_sftp_with_retry(
                source=source_filepath, dest=dest_filepath, sftp=sftp_client
            )
        except Exception as e:
            # Capture and re-raise exceptions so we can update the database before allowing
            # calling code to respond to unexpected failure.

            # TODO: Update state_log entry to note failure to copy file from S3 to MoveIt.
            raise e

        # TODO: Update state_log entry to note successful transfer of file to MoveIt.

        try:
            # Move from ready directory to sent directory.
            archive_filepath = os.path.join(config.s3_bucket_uri, config.archive_dir, filename)
            file_util.rename_file(source_filepath, archive_filepath)
        except Exception as e:
            # Capture and re-raise exceptions so we can update the database before allowing
            # calling code to respond to unexpected failure.

            # "Roll back" the copy from S3 to MoveIt by removing the copied file from MoveIt if
            # archiving the file in S3 fails.
            sftp_client.remove(dest_filepath)

            # TODO: Update state_log entry to note failure to archive file in S3.
            raise e

        # Update the filepath for the reference file since we moved it.
        reference_file.file_location = archive_filepath
        db_session.commit()


@retry(stop=stop_after_attempt(3))
def _copy_file_from_s3_to_sftp_with_retry(source, dest, sftp):
    file_util.copy_file_from_s3_to_sftp(source=source, dest=dest, sftp=sftp)


def copy_from_sftp_to_s3_and_archive_files(
    config: SftpS3TransferConfig, db_session: db.Session
) -> None:
    sftp_client = file_util.get_sftp_client(
        uri=config.sftp_uri, ssh_key_password=config.ssh_key_password, ssh_key=config.ssh_key,
    )

    source_filenames = sftp_client.listdir(config.source_dir)
    if len(source_filenames) == 0:
        # TODO: Create a row in state_log noting that we did not find any files.
        logger.info("Did not find any files in source SFTP directory:", config.source_dir)
        return

    for filename in source_filenames:
        source_filepath = os.path.join(config.source_dir, filename)
        dest_filepath = os.path.join(config.s3_bucket_uri, config.dest_dir, filename)
        archive_filepath = os.path.join(config.archive_dir, filename)

        # If there is already a row in ReferenceFile for this file then skip it.
        # We may have retrieved it earlier but failed to move it to the archive directory in SFTP
        # or the folks on the other end may have accidentally re-uploaded a file with a previously
        # used filename.
        try:
            existing_reference_file = (
                db_session.query(ReferenceFile)
                .filter(ReferenceFile.file_location == dest_filepath)
                .one_or_none()
            )
        except MultipleResultsFound:
            logger.error(
                "Found more than one ReferenceFile with the same file_location:", source_filepath,
            )
            continue
        except Exception as e:
            raise e

        if existing_reference_file:
            logger.info(
                "ReferenceFile record already exists for in S3 named '{}'. Skipping SFTP to S3 transfer for this file.".format(
                    source_filepath
                )
            )
            continue

        # Copy from SFTP to S3.
        # Not currently implementing any error handling here because we haven't done any work on
        # the file at this point. Exceptions will bubble up to calling code.
        _copy_file_from_sftp_to_s3_with_retry(source_filepath, dest_filepath, sftp_client)

        try:
            # Record this action in our database.
            reference_file = ReferenceFile(file_location=dest_filepath)
            db_session.add(reference_file)
            db_session.commit()
            # TODO: Add row in StateLog table.
        except Exception as e:
            logger.error(
                "Saved file '{}' into S3 but could not create a ReferenceFile record in database.".format(
                    dest_filepath
                )
            )
            raise e

        # Move file to archive dir in SFTP
        try:
            sftp_client.rename(source_filepath, archive_filepath)
        except Exception as e:
            logger.info("Failed to archive file '{}' in SFTP server.".format(source_filepath))
            raise e


@retry(stop=stop_after_attempt(3))
def _copy_file_from_sftp_to_s3_with_retry(source, dest, sftp):
    file_util.copy_file_from_sftp_to_s3(source=source, dest=dest, sftp=sftp)

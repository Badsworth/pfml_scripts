import os
from dataclasses import dataclass
from re import Pattern
from typing import List, Optional

import paramiko
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
    ssh_key_password: Optional[str]
    # String representation of the private key.
    ssh_key: str
    regex_filter: Optional[Pattern] = None


def copy_to_sftp_and_archive_s3_files(
    config: SftpS3TransferConfig, db_session: db.Session,
) -> List[ReferenceFile]:
    copied_reference_files: List[ReferenceFile] = []

    source_dir_path = os.path.join(config.s3_bucket_uri, config.source_dir)
    s3_filenames = file_util.list_s3_files_and_directories_by_level(source_dir_path)
    if len(s3_filenames.keys()) == 0:
        logger.info("No files found to move to SFTP")
        # If there are no new files in S3 return early to avoid the overhead of an SFTP connection.
        return copied_reference_files

    logger.info("Copying files to SFTP server: %s", ", ".join(s3_filenames))

    sftp_client = file_util.get_sftp_client(
        uri=config.sftp_uri, ssh_key_password=config.ssh_key_password, ssh_key=config.ssh_key,
    )

    # List files so we can avoid overwriting a file in the destination directory.
    dest_dir_filenames = sftp_client.listdir(config.dest_dir)
    for local_filename, files_in_set in s3_filenames.items():
        source_file_location = os.path.join(source_dir_path, local_filename)

        try:
            reference_file = (
                db_session.query(ReferenceFile)
                .filter(ReferenceFile.file_location == source_file_location)
                .one_or_none()
            )
        except MultipleResultsFound:
            # TODO - API-1311 - Extend this method to have a flag that determines whether
            #                   to error out entirely here or to continue
            logger.exception(
                "Found more than one ReferenceFile with the same file_location. Skipping",
                extra={"file_location": source_file_location},
            )
            continue
        except Exception as e:
            raise e

        if not reference_file:
            logger.warning(
                "Could not find ReferenceFile with file_location matching S3 file name. Skipping",
                extra={"file_location": source_file_location},
            )
            continue

        copied_reference_file = _copy_files_in_set_for_reference_file(
            reference_file, files_in_set, dest_dir_filenames, config, sftp_client, db_session
        )
        if copied_reference_file:
            copied_reference_files.append(copied_reference_file)

    return copied_reference_files


def _copy_files_in_set_for_reference_file(
    reference_file: ReferenceFile,
    files_in_set: List[str],
    dest_dir_filenames: List[str],
    config: SftpS3TransferConfig,
    sftp_client: paramiko.SFTPClient,
    db_session: db.Session,
) -> Optional[ReferenceFile]:
    if reference_file.reference_file_type_id is None:
        logger.error(
            "ReferenceFile does not have associated ReferenceFileType",
            extra={
                "reference_file_id": reference_file.reference_file_id,
                "reference_file_location": reference_file.file_location,
            },
        )
        return None

    if not reference_file.reference_file_type.num_files_in_set == len(files_in_set):
        logger.error(
            "Incorrect number of files in set. Skipping",
            extra={
                "reference_file_id": reference_file.reference_file_id,
                "correct_num_files_in_set": reference_file.reference_file_type.num_files_in_set,
                "actual_num_files_in_set": len(files_in_set),
                "reference_file_type": reference_file.reference_file_type.reference_file_type_description,
                "reference_file_location": reference_file.file_location,
            },
        )
        return None

    source_dir_path = os.path.join(config.s3_bucket_uri, config.source_dir)

    sftp_files_to_rollback = []
    s3_files_to_return = []
    for subfile in files_in_set:
        source_filepath = os.path.join(source_dir_path, subfile)

        basename = os.path.basename(subfile)
        dest_filepath = os.path.join(config.dest_dir, basename)

        if basename in dest_dir_filenames:
            logger.warning(
                "File already exists in destination directory. Skipping",
                extra={"file_name": basename, "destination_directory": config.dest_dir},
            )
            return None

        try:
            # Copy to MoveIt.
            _copy_file_from_s3_to_sftp_with_retry(
                source=source_filepath, dest=dest_filepath, sftp=sftp_client
            )
            sftp_files_to_rollback.append(dest_filepath)

            # Move from ready directory to sent directory.
            archive_filepath = os.path.join(config.s3_bucket_uri, config.archive_dir, subfile)

            logger.info(
                "Copying file to archive folder - source: %s, destination: %s",
                source_filepath,
                archive_filepath,
            )
            file_util.rename_file(source_filepath, archive_filepath)

            # Flip the arguments here to prepare for a potential rename back the other way.
            s3_files_to_return.append((archive_filepath, source_filepath))
        except Exception as e:
            # Capture and re-raise exceptions so we can update the database before allowing
            # calling code to respond to unexpected failure.

            for s3_rename_args in s3_files_to_return:
                file_util.rename_file(*s3_rename_args)

            # "Roll back" the copy from S3 to MoveIt by removing the copied file from MoveIt if
            # archiving the file in S3 fails.
            for file_to_rollback in sftp_files_to_rollback:
                sftp_client.remove(file_to_rollback)

            raise e

        # Update the filepath for the reference file since we moved it.
        local_filename = os.path.basename(reference_file.file_location)
        archive_file_location = os.path.join(
            config.s3_bucket_uri, config.archive_dir, local_filename
        )
        reference_file.file_location = archive_file_location
        db_session.add(reference_file)
        db_session.commit()

    return reference_file


@retry(stop=stop_after_attempt(3))
def _copy_file_from_s3_to_sftp_with_retry(source, dest, sftp):
    try:
        logger.info("Copying file from S3 to SFTP - source: %s, destination: %s", source, dest)
        file_util.copy_file_from_s3_to_sftp(source=source, dest=dest, sftp=sftp)
    except Exception:
        # Add additional logging when we encounter an SFTP error because tenacity's retry
        # appears to be eating the original Exception.
        logger.exception(
            "Failed to copy_file_from_s3_to_sftp",
            extra={"s3_source": source, "sftp_destination": dest},
        )
        raise


def filter_filenames(source_filenames: List[str], filename_regex: Pattern) -> List[str]:
    original_filenames = source_filenames
    source_filenames = [filename for filename in source_filenames if filename_regex.match(filename)]
    logger.info(
        "Filtered files retrieved from source SFTP directory",
        extra={
            "original_filenames": ", ".join(original_filenames),
            "filtered_filenames": ", ".join(source_filenames),
        },
    )

    return source_filenames


def copy_from_sftp_to_s3_and_archive_files(
    config: SftpS3TransferConfig, db_session: db.Session
) -> List[ReferenceFile]:
    sftp_client = file_util.get_sftp_client(
        uri=config.sftp_uri, ssh_key_password=config.ssh_key_password, ssh_key=config.ssh_key,
    )

    source_filenames = sftp_client.listdir(config.source_dir)

    if config.regex_filter is not None:
        source_filenames = filter_filenames(source_filenames, config.regex_filter)

    if len(source_filenames) == 0:
        logger.info("Did not find any files in source SFTP directory: %s", config.source_dir)
        return []

    # Remove any leading (and trailing) slashes so that we include the config.s3_bucket_uri when
    # constructing the dest_filepath. If the dest_dir has a leading slash os.path.join() will
    # ignore config.s3_bucket_uri and start the path at dest_dir.
    dest_dir = config.dest_dir.strip("/")

    reference_files = []

    for filename in source_filenames:
        source_filepath = os.path.join(config.source_dir, filename)
        dest_filepath = os.path.join(config.s3_bucket_uri, dest_dir, filename)
        archive_filepath = os.path.join(config.archive_dir, filename)

        logger.info(
            "Copying file from SFTP to S3 - source: %s, destination: %s, archive: %s",
            source_filepath,
            dest_filepath,
            archive_filepath,
        )

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
            # TODO - API-1311 - Extend this method to have a flag that determines whether
            #                   to error out entirely here or to continue
            logger.exception(
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
            reference_files.append(reference_file)
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
            logger.exception("Failed to archive file '{}' in SFTP server.".format(source_filepath))
            raise e

    return reference_files


@retry(stop=stop_after_attempt(3))
def _copy_file_from_sftp_to_s3_with_retry(source, dest, sftp):
    try:
        file_util.copy_file_from_sftp_to_s3(source=source, dest=dest, sftp=sftp)
    except Exception:
        # Add additional logging when we encounter an SFTP error because tenacity's retry
        # appears to be eating the original Exception.
        logger.exception(
            "Failed to copy_file_from_sftp_to_s3",
            extra={"sftp_source": source, "s3_destination": dest},
        )
        raise

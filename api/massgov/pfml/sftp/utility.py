import argparse
import os
import sys
import tempfile
from typing import Any, List, Optional, Tuple

from paramiko import SFTPClient
from pydantic import Field

import massgov.pfml.util.files as file_util
from massgov.pfml.util import logging
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.pydantic import PydanticBaseSettings

logger = logging.get_logger(__name__)


@background_task("sftp-tool")
def main() -> None:
    sftp_config = SftpConfig()
    sftp_client = file_util.get_sftp_client(
        uri=sftp_config.sftp_uri,
        ssh_key_password=sftp_config.ssh_key_password,
        ssh_key=sftp_config.ssh_key,
    )

    run_tool(sftp_client, sys.argv[1:])


def parse_args(args: Any) -> Any:
    parser = argparse.ArgumentParser(description="List/modify files or copy to S3 from MOVEit")
    parser.add_argument("--list", type=str, help="List objects in path")
    parser.add_argument("--rename", type=str, help="Rename object")
    parser.add_argument("--copy", type=str, help="Copy object")
    parser.add_argument("--to", type=str, help="Copy object new name")
    parser.add_argument("--copy_dir", type=str, help="Copy multiple objs")
    parser.add_argument("--to_dir", type=str, help="New dest for copied objs")

    parsed_args = parser.parse_args(args)
    validate_args(parsed_args)
    return parsed_args


def validate_args(args: Any) -> None:
    exclusive_args = [args.list, args.copy, args.copy_dir]
    if sum(map(bool, exclusive_args)) > 1:
        raise RuntimeError(
            "Only one of the following can be specified: --list, --copy, --delete, --copy_dir"
        )

    if ((args.copy or args.rename) and not args.to) or (args.to and not (args.copy or args.rename)):
        raise RuntimeError("Must specify --to with --copy")

    if (args.copy_dir and not args.to_dir) or (args.to_dir and not args.copy_dir):
        raise RuntimeError("Must specify --to_dir with --copy_dir")


class SftpConfig(PydanticBaseSettings):
    sftp_uri: str = Field(..., env="SFTP_URI")
    ssh_key: str = Field(..., env="SFTP_SSH_KEY")
    ssh_key_password: Optional[str] = Field(..., env="SFTP_SSH_KEY_PASSWORD")


def run_tool(sftp_client: SFTPClient, raw_args: Any) -> Tuple[bool, Any]:
    args = parse_args(raw_args)

    if args.list:
        return True, sftp_ls(sftp_client, args.list)

    if args.rename:
        sftp_rename(sftp_client, args.rename, args.to)
        return True, None

    # Operations involving S3
    if args.copy:
        sftp_cp(sftp_client, args.copy, args.to)
        return True, None

    elif args.copy_dir and args.to_dir:
        sftp_copy_dir(sftp_client, args.copy_dir, args.to_dir)
        return True, None

    return False, None


def _unsupported_feature_error(
    from_path: str, to_path: str, msg: str = "Unsupported feature"
) -> None:
    logger.error("Unsupported rename feature:", extra={"from_path": from_path, "to_path": to_path})
    raise RuntimeError(msg)


def sftp_ls(sftp_client: SFTPClient, path: str) -> List[str]:
    if not file_util.is_s3_path(path):
        files = sftp_client.listdir(path)
        logger.info(f"{len(files)} file(s) found in path: {path}")
        for file in files:
            print(file)
        if len(files) == 0:
            print(f"<0 files in {path}>")
        return files
    else:
        logger.error("Listing S3 bucket contents is not supported", extra={"path": path})
        raise RuntimeError("Unsupported feature: Listing S3 bucket contents")


def sftp_rename(sftp_client: SFTPClient, from_path: str, to_path: str) -> None:
    if file_util.is_s3_path(from_path) or file_util.is_s3_path(to_path):
        _unsupported_feature_error(
            from_path, to_path, msg="Unsupported feature: Can only rename between two sftp paths"
        )
    sftp_client.rename(from_path, to_path)


def sftp_cp(sftp_client: SFTPClient, from_path: str, to_path: str) -> None:
    if file_util.is_s3_path(from_path):
        if file_util.is_s3_path(to_path):
            _unsupported_feature_error(
                from_path, to_path, msg="Unsupported feature: Copying/moving from s3 to s3"
            )

        else:
            file_util.copy_file_from_s3_to_sftp(from_path, to_path, sftp_client)

    else:
        if not file_util.is_s3_path(to_path):
            logger.info(
                "Renaming files on SFTP server", extra={"from_path": from_path, "to_path": to_path}
            )
            _handle, tempfile_path = tempfile.mkstemp()
            sftp_client.get(from_path, tempfile_path)
            sftp_client.put(tempfile_path, to_path, confirm=False)
            os.close(_handle)
        elif file_util.is_s3_path(to_path):
            file_util.copy_file_from_sftp_to_s3(from_path, to_path, sftp_client)


def sftp_copy_dir(sftp_client: SFTPClient, from_dir: str, to_dir: str) -> None:
    if file_util.is_s3_path(from_dir):
        if file_util.is_s3_path(to_dir):
            _unsupported_feature_error(
                from_dir, to_dir, msg="Unsupported feature: Copying/moving from s3 to s3"
            )
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info("copy started")
                files = file_util.list_files_without_folder(from_dir)
                for file in files:
                    file_from_path = f"{from_dir}/{file}"
                    file_temp_path = f"{temp_dir}/{file}"
                    file_to_path = f"{to_dir}/{file}"

                    file_util.download_from_s3(file_from_path, file_temp_path)
                    logger.info("download done")
                    sftp_client.put(file_temp_path, file_to_path, confirm=False)
                    logger.info("upload done")
    else:
        if not file_util.is_s3_path(to_dir):
            logger.info(
                "Renaming files on SFTP server", extra={"from_path": from_dir, "to_path": to_dir}
            )

            with tempfile.TemporaryDirectory() as directory:
                temp_dir = directory + "/copy"
                logger.info("copy started")
                sftp_client.get(from_dir, temp_dir)
                logger.info("download done")
                sftp_client.put(temp_dir, to_dir, confirm=False)
                logger.info("upload done")

        else:
            # copy sftp to s3
            with tempfile.TemporaryDirectory() as directory:
                temp_dir = directory + "/copy"
                logger.info("copy started")
                sftp_client.get(from_dir, temp_dir)
                files = file_util.list_files_without_folder(temp_dir)
                for file in files:
                    target_path = f"{to_dir}/{file}"
                    logger.info("download done")
                    file_util.upload_to_s3(f"{temp_dir}/{file}", target_path)
                    logger.info("upload done")

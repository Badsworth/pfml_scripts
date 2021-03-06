#
# FINEOS bucket access tool.
#

import argparse
import re
import sys
import tempfile

import boto3
from pydantic import BaseSettings, Field

import massgov.pfml.util.aws.sts
import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.util.bg import background_task

logger = massgov.pfml.util.logging.get_logger(__name__)


class BucketConfig(BaseSettings):
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)


def parse_args(args):
    parser = argparse.ArgumentParser(description="List or modify a bucket")
    parser.add_argument("--list", type=str, help="List objects in path")
    parser.add_argument("--copy", type=str, help="Copy object")
    parser.add_argument("--to", type=str, help="Copy object new name")
    parser.add_argument("--delete", type=str, help="Delete object")
    parser.add_argument("--delsize", type=int, help="Size of object to delete")
    parser.add_argument("--copy_dir", type=str, help="Copy multiple objs")
    parser.add_argument("--to_dir", type=str, help="New dest for copied objs")
    parser.add_argument(
        "--archive_dir", type=str, help="Absolute s3:// path of archived, previously-copied objs"
    )
    parser.add_argument(
        "--file_prefixes", type=str, help="List of file prefixes. Default: copy all files"
    )
    parser.add_argument("--recursive", dest="recursive", action="store_true")
    parser.add_argument("--dated-folders", dest="dated_folders", action="store_true")
    parser.set_defaults(recursive=False, dated_folders=False, file_prefixes="all")

    return parser.parse_args(args)


@background_task("fineos-bucket-tool")
def main():
    """Main entry point."""
    run_tool(sys.argv[1:])


def run_tool(raw_args):
    args = parse_args(raw_args)

    exclusive_args = [args.list, args.copy, args.delete, args.copy_dir]
    if sum(map(bool, exclusive_args)) > 1:
        raise RuntimeError(
            "Only one of the following can be specified: --list, --copy, --delete, --copy_dir"
        )

    if args.archive_dir and not all([args.archive_dir, args.copy_dir, args.to_dir]):
        raise RuntimeError("Must specify --archive_dir with both --copy_dir and --to_dir")

    if (args.copy and not args.to) or (args.to and not args.copy):
        raise RuntimeError("Must specify --to with --copy")

    if (args.delete and not args.delsize) or (args.delsize and not args.delete):
        raise RuntimeError("Must specify --delsize with --delete")

    if (args.copy_dir and not args.to_dir) or (args.to_dir and not args.copy_dir):
        raise RuntimeError("Must specify --to_dir with --copy_dir")

    # Error out if one of the flags for copy_dir is used for another option.
    # file_prefixes always defaults to "all" so we have to check the value against that default.
    if not args.copy_dir and (args.recursive or args.dated_folders or args.file_prefixes != "all"):
        raise RuntimeError(
            "The following options are only valid when using copy_dir: [--recursive, --dated-folders, --file_prefixes]"
        )

    fineos_boto_session = None
    if any(
        is_fineos_bucket(arg)
        for arg in [args.list, args.copy, args.to, args.delete, args.copy_dir, args.to_dir]
    ):
        logger.info("FINEOS bucket detected; starting a cross-account session to access it")
        config = BucketConfig()
        fineos_boto_session = massgov.pfml.util.aws.sts.assume_session(
            role_arn=config.fineos_aws_iam_role_arn,
            external_id=config.fineos_aws_iam_role_external_id,
            role_session_name="bucket_tool",
            region_name="us-east-1",
        )

    s3 = boto3.resource("s3")
    s3_fineos = fineos_boto_session.resource("s3") if fineos_boto_session else boto3.resource("s3")

    bucket_tool(args, s3, s3_fineos, boto3, fineos_boto_session)


def is_fineos_bucket(path):
    return False if path is None else path.startswith("s3://fin-som")


def bucket_tool(args, s3, s3_fineos, boto3, fineos_boto_session):
    if args.list:
        bucket_ls(args.list, s3_fineos if is_fineos_bucket(args.list) else s3)

    elif args.copy:
        bucket_cp(
            args.copy,
            args.to,
            s3_fineos if is_fineos_bucket(args.copy) else s3,
            s3_fineos if is_fineos_bucket(args.to) else s3,
        )

    elif args.delete:
        bucket_delete(args.delete, args.delsize, s3_fineos if is_fineos_bucket(args.delete) else s3)

    elif args.copy_dir and args.to_dir:
        if args.file_prefixes == "all":
            files_to_list = args.file_prefixes
        else:
            files_to_list = args.file_prefixes.split(",")

        copy_dir(
            source=args.copy_dir,
            dest=args.to_dir,
            s3_source=s3_fineos if is_fineos_bucket(args.copy_dir) else s3,
            s3_dest=s3_fineos if is_fineos_bucket(args.to_dir) else s3,
            boto_source=fineos_boto_session if is_fineos_bucket(args.copy_dir) else boto3,
            boto_dest=fineos_boto_session if is_fineos_bucket(args.to_dir) else boto3,
            file_prefixes=files_to_list,
            recursive=args.recursive,
            dated_folders=args.dated_folders,
            archive_dir=args.archive_dir,
        )


def bucket_ls(path, s3):
    bucket_name, prefix = massgov.pfml.util.files.split_s3_url(path)
    bucket = s3.Bucket(bucket_name)

    logger.info("ls %s", path)
    for obj in bucket.objects.filter(Prefix=prefix):
        logger.info("object %15s  %s  %s", format(obj.size, ","), obj.last_modified, obj.key)


def bucket_cp(source, dest, s3_source, s3_dest):
    logger.info("CP %s %s", source, dest)

    source_bucket_name, source_prefix = massgov.pfml.util.files.split_s3_url(source)
    source_object = s3_source.Object(source_bucket_name, source_prefix)
    logger.info(
        "SOURCE %15s  %s  %s",
        format(source_object.content_length, ","),
        source_object.last_modified,
        source_object.key,
    )

    dest_bucket_name, dest_prefix = massgov.pfml.util.files.split_s3_url(dest)
    dest_object = s3_dest.Object(dest_bucket_name, dest_prefix)

    with tempfile.TemporaryDirectory() as directory:
        temp_path = directory + "/copy"
        logger.info("copy started")
        source_object.download_file(temp_path)
        logger.info("download done")
        dest_object.upload_file(temp_path)
        logger.info("upload done")

    logger.info(
        "DEST   %15s  %s  %s",
        format(dest_object.content_length, ","),
        dest_object.last_modified,
        dest_object.key,
    )


def bucket_delete(delete, delsize, s3):
    logger.info("DELETE %s", delete)

    bucket_name, prefix = massgov.pfml.util.files.split_s3_url(delete)
    del_object = s3.Object(bucket_name, prefix)
    logger.info(
        "DELETE %15s  %s  %s",
        format(del_object.content_length, ","),
        del_object.last_modified,
        del_object.key,
    )

    if delsize != del_object.content_length:
        raise RuntimeError("--delsize does not match real size, aborting delete")

    del_object.delete()
    logger.info("delete done")


def file_name_contains_prefix(file_prefixes, file_name):
    if file_prefixes == "all":
        return True

    for prefix in file_prefixes:
        if prefix.lower() in file_name.lower():
            return True
    return False


def copy_dir(
    source,
    dest,
    s3_source,
    s3_dest,
    boto_source,
    boto_dest,
    file_prefixes,
    recursive,
    dated_folders,
    archive_dir,
):
    if not source.endswith("/"):
        source = source + "/"

    if not dest.endswith("/"):
        dest = dest + "/"

    if archive_dir and not archive_dir.endswith("/"):
        archive_dir = archive_dir + "/"

    # get list of all files in source prefix
    source_files = massgov.pfml.util.files.list_files(
        path=source, recursive=recursive, boto_session=boto_source
    )

    # get list of all files in dest prefix
    dest_files = massgov.pfml.util.files.list_files(
        path=dest, recursive=recursive, boto_session=boto_dest
    )

    # get list of all files in the provided S3 archival path, or empty list if no prefix was given
    archive_files = (
        massgov.pfml.util.files.list_files(
            path=archive_dir, recursive=recursive, boto_session=boto_dest
        )
        if archive_dir
        else []
    )

    for file in source_files:
        # copy select files that don???t already exist in the destination or in the destination's archival S3 path
        file_contains_prefix = file_name_contains_prefix(file_prefixes, file)
        if file_contains_prefix and file not in dest_files and file not in archive_files:
            source_file = source + file

            if dated_folders and "/" not in file:
                match = re.match(r"(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})", file)

                if match:
                    date = match.group()
                    dest_file = f"{dest}{date}/{file}"
                else:
                    logger.warning(f"File '{file}' was found without a date; copying normally")
                    dest_file = dest + file
            else:
                dest_file = dest + file

            bucket_cp(source_file, dest_file, s3_source, s3_dest)
        elif not file_contains_prefix:
            logger.info(f"File '{file}' doesn't match any prefixes; skipping it")
        elif file in dest_files or file in archive_files:
            logger.info(f"File '{file}' already exists or is already archived; skipping it")
        else:
            logger.info(f"File '{file}' won't be copied; skipping it")
            continue

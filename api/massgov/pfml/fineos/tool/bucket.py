#
# FINEOS bucket access tool.
#

import argparse
import tempfile

import boto3
from pydantic import BaseSettings, Field

import massgov.pfml.util.aws.sts
import massgov.pfml.util.files
import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit

logger = massgov.pfml.util.logging.get_logger(__name__)


class BucketConfig(BaseSettings):
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)


def main():
    """Main entry point."""
    massgov.pfml.util.logging.audit.init_security_logging()
    massgov.pfml.util.logging.init(__name__)

    config = BucketConfig()

    parser = argparse.ArgumentParser(description="List or modify a bucket")
    parser.add_argument("--list", type=str, help="List objects in path")
    parser.add_argument("--copy", type=str, help="Copy object")
    parser.add_argument("--to", type=str, help="Copy object new name")
    parser.add_argument("--delete", type=str, help="Delete object")
    parser.add_argument("--delsize", type=int, help="Size of object to delete")
    parser.add_argument("--copy_dir", type=str, help="Copy multiple objs")
    parser.add_argument("--to_dir", type=str, help="New dest for copied objs")
    parser.add_argument("--file_prefixes", type=str, help="List of file prefixes")

    args = parser.parse_args()

    if args.copy and not args.to:
        raise RuntimeError("Must specify --to with --copy")

    if args.delete and not args.delsize:
        raise RuntimeError("Must specify --delsize with --delete")

    fineos_boto_session = None
    if (
        is_fineos_bucket(args.list)
        or is_fineos_bucket(args.copy)
        or is_fineos_bucket(args.to)
        or is_fineos_bucket(args.delete)
        or is_fineos_bucket(args.copy_dir)
        or is_fineos_bucket(args.to_dir)
    ):
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
    if path is None:
        return False
    return path.startswith("s3://fin-som")


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
        copy_dir(
            args.copy_dir,
            args.to_dir,
            s3_fineos if is_fineos_bucket(args.copy_dir) else s3,
            s3_fineos if is_fineos_bucket(args.to_dir) else s3,
            fineos_boto_session if is_fineos_bucket(args.copy_dir) else boto3,
            fineos_boto_session if is_fineos_bucket(args.to_dir) else boto3,
            args.file_prefixes.split(","),
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
    for prefix in file_prefixes:
        if prefix in file_name:
            return True
    return False


def copy_dir(source, dest, s3_source, s3_dest, boto_source, boto_dest, file_prefixes):
    if not source.endswith("/"):
        source = source + "/"

    if not dest.endswith("/"):
        dest = dest + "/"

    # get list of all files in source prefix
    source_files = massgov.pfml.util.files.list_files(source, boto_session=boto_source)

    # get list of all files in dest prefix
    dest_files = massgov.pfml.util.files.list_files(dest, boto_session=boto_dest)

    for file in source_files:
        # copy select files that don’t already exist in the destination
        if file_name_contains_prefix(file_prefixes, file) and (file not in dest_files):
            source_file = source + file
            dest_file = dest + file
            bucket_cp(source_file, dest_file, s3_source, s3_dest)

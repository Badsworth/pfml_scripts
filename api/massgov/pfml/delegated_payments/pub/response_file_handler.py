import massgov.pfml.db as db


def copy_response_files_to_s3(db_session: db.Session) -> None:
    # TODO: Copy all files from the source directory to S3 and create ReferenceFiles.
    # s3://massgov-pfml-prod-agency-transfer/pub/inbound/received/

    return None


def process_pending_response_files(db_session: db.Session) -> None:
    # TODO: Loop over all files in the received directory and process them through the functions
    # we'll create as part of PUB-70.

    return None

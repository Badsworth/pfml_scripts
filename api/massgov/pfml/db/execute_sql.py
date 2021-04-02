#
# Execute an SQL statement on the database.
#
# This is intended to be run as an ECS task with the SQL passed as a command line argument.
# Ex: ./bin/run-ecs-task/run-task.sh <env> execute-sql <firstname>.<lastname> execute-sql \
#     "SELECT COUNT(*) FROM employer" "SELECT * FROM lk_geo_state
#

import argparse
import csv
import os
from datetime import date

import sqlalchemy

import massgov.pfml.db
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit
from massgov.pfml.util.sentry import initialize_sentry

logger = massgov.pfml.util.logging.get_logger(__name__)
S3_BUCKET = os.environ.get("S3_EXPORT_BUCKET", None)


def get_file_target(args, count):
    """ Produce a target based on the parameters provided """
    if args.use_date:
        return f"{args.s3_output}/{date.today()}/query{count}.csv"
    return f"{args.s3_output}-query{count}.csv"


def execute_sql():
    """Execute some SQL against the database."""
    initialize_sentry()
    massgov.pfml.util.logging.audit.init_security_logging()
    massgov.pfml.util.logging.init("execute_sql")

    args = parse_args()
    if args.s3_output and not args.s3_bucket:
        logger.error("S3 Output Requested without S3_EXPORT_BUCKET or --s3_bucket set")
        exit(1)

    s3_mode = bool(args.s3_output)
    db_session = massgov.pfml.db.init()
    count = 0
    try:
        for sql in args.sql:
            count += 1
            if s3_mode:
                target = get_file_target(args, count)
                execute_sql_statement_s3(db_session, sql, args.s3_bucket, target)
            else:
                execute_sql_statement(db_session, sql, args.limit)

    except sqlalchemy.exc.SQLAlchemyError as ex:
        logger.exception("error during execute: %s %s", ex.__class__, str(ex))

    logger.info("done, %i statements executed", count)


def execute_sql_statement_s3(db_session, sql, bucket, file_target):
    """ Export the results of an SQL statement to S3 """
    logger.info("exporting results of %r to %s in %s", sql, file_target, bucket)
    file_path = f"s3://{bucket}/{file_target}"
    execute_sql_statement_file_path(db_session, sql, file_path)
    db_session.commit()


def execute_sql_statement_file_path(db_session, sql, file_path):
    logger.info("exporting results of %r to %s", sql, file_path)
    result = db_session.execute(sql)
    dictwriter = None
    fields = None
    with file_util.open_stream(file_path, mode="w") as open_fh:
        for row in result:
            if not dictwriter:
                fields = row.keys()
                dictwriter = csv.DictWriter(open_fh, fieldnames=fields, restval="")
                dictwriter.writeheader()
            dictwriter.writerow({f: getattr(row, f, "") for f in fields})


def execute_sql_statement(db_session, sql, print_limit):
    """Execute a single SQL statement."""
    logger.info("execute %r", sql)
    result = db_session.execute(sql)
    logger.info("rowcount %i", result.rowcount)
    if result.returns_rows:
        output_result_rows(result, print_limit)
    if result.is_insert:
        logger.info("inserted_primary_key %r", result.inserted_primary_key)
    db_session.commit()


def output_result_rows(result, print_limit):
    """Output result rows to the log."""
    row_count = 0
    for row in result:
        if print_limit <= row_count:
            logger.info("too many rows to print, stopping (use --limit=N to increase)")
            return
        logger.info("row %i %r", row_count, row.items())
        row_count += 1


def parse_args():
    """Parse command line arguments and flags."""
    parser = argparse.ArgumentParser(description="Execute SQL statements on the database",)
    parser.add_argument("sql", nargs="+", help="SQL statements")
    parser.add_argument("--limit", type=int, default=100, help="Row limit when printing output")
    parser.add_argument(
        "--s3_output",
        default=None,
        help=(
            "A file location to export to; bucket is configured in env. "
            "If you run multiple queries with --s3_output, "
            "_query1, _query2, etc will be appended"
        ),
    )
    parser.add_argument(
        "--s3_bucket",
        default=S3_BUCKET,
        help=("An S3 bucket to export query data to; default is set in env"),
    )
    parser.add_argument(
        "--use_date",
        default=False,
        action="store_true",
        help=("Prepend the current date to the folder"),
    )
    args = parser.parse_args()
    if not args.sql:
        parser.print_help()
        exit(1)
    return args

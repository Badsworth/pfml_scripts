#
# Execute an SQL statement on the database.
#
# This is intended to be run as an ECS task with the SQL passed as a command line argument.
# Ex: ./bin/run-ecs-task/run-task.sh <env> execute-sql <firstname>.<lastname> execute-sql \
#     "SELECT COUNT(*) FROM employer" "SELECT * FROM lk_geo_state
#

import argparse

import sqlalchemy

import massgov.pfml.db
import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit

logger = massgov.pfml.util.logging.get_logger(__name__)


def execute_sql():
    """Execute some SQL against the database."""
    massgov.pfml.util.logging.audit.init_security_logging()
    massgov.pfml.util.logging.init("execute_sql")

    args = parse_args()

    db_session = massgov.pfml.db.init()

    count = 0
    try:
        for sql in args.sql:
            count += 1
            execute_sql_statement(db_session, sql, args.limit)
    except sqlalchemy.exc.SQLAlchemyError as ex:
        logger.error("error during execute: %s %s", ex.__class__, str(ex))

    logger.info("done, %i statements executed", count)


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
    args = parser.parse_args()
    if not args.sql:
        parser.print_help()
        exit(1)
    return args

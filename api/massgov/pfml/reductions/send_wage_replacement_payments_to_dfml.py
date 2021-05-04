import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.reductions.dua as dua
import massgov.pfml.reductions.reports.dia_payments.create as dia_payments_reports_create
import massgov.pfml.reductions.reports.dia_payments.send as dia_payments_reports_send
import massgov.pfml.reductions.reports.dua_payments_reports as dua_reports
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit as audit

logger = logging.get_logger(__name__)

ALL = "ALL"
DIA = "DIA"
DUA = "DUA"
ALLOWED_VALUES = [ALL, DIA, DUA]


class Configuration:
    send_dia_report: bool
    send_dua_report: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Create and send reductions reports to DFML")
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=[ALL],
            help="Indicate which agency, DIA or DUA, to create reports for",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        if ALL in steps:
            self.send_dia_report = True
            self.send_dua_report = True
        else:
            self.send_dia_report = DIA in steps
            self.send_dua_report = DUA in steps


def main():
    audit.init_security_logging()
    logging.init("Sending wage replacement payments")

    config = Configuration(sys.argv[1:])

    with db.session_scope(db.init(), close=True) as db_session:
        if config.send_dia_report:
            logger.info("Running DIA steps")
            dia_payments_reports_create.create_report_new_dia_payments_to_dfml(db_session)
            dia_payments_reports_send.send_dia_reductions_report(db_session)

        if config.send_dua_report:
            logger.info("Running DUA steps")
            dua.create_report_new_dua_payments_to_dfml(db_session)
            dua_reports.send_dua_reductions_report(db_session)

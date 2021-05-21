import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.reductions.dia as dia
import massgov.pfml.reductions.dua as dua
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit as audit
from massgov.pfml.util.batch.log import LogEntry

logger = logging.get_logger(__name__)

ALL = "ALL"
DIA = "DIA"
DUA = "DUA"
ALLOWED_VALUES = [ALL, DIA, DUA]


class Configuration:
    get_dia_list: bool
    get_dua_list: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Retrieve and process payment files from agencies"
        )
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=[ALL],
            help="Indicate which agency, DIA or DUA, to grab files for",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        if ALL in steps:
            self.get_dia_list = True
            self.get_dua_list = True
        else:
            self.get_dia_list = DIA in steps
            self.get_dua_list = DUA in steps


def main():
    audit.init_security_logging()
    logging.init("Retrieving payments list")
    config = Configuration(sys.argv[1:])

    with db.session_scope(db.init(), close=True) as db_session:
        if config.get_dia_list:
            with LogEntry(db_session, "DIA retrieve_payment_lists_from_agencies") as log_entry:
                dia_payment_lists_downloaded_count = dia.download_payment_list_from_moveit(
                    db_session
                )
                log_entry.set_metrics(
                    {
                        dia.Metrics.DIA_PAYMENT_LISTS_DOWNLOADED_COUNT: dia_payment_lists_downloaded_count
                    }
                )
                dia.load_new_dia_payments(db_session, log_entry)

        if config.get_dua_list:
            with LogEntry(db_session, "DUA retrieve_payment_lists_from_agencies") as log_entry:
                dua_payment_lists_downloaded_count = dua.download_payment_list_from_moveit(
                    db_session
                )
                log_entry.set_metrics(
                    {
                        dua.Metrics.DUA_PAYMENT_LISTS_DOWNLOADED_COUNT: dua_payment_lists_downloaded_count
                    }
                )
                dua.load_new_dua_payments(db_session, log_entry)

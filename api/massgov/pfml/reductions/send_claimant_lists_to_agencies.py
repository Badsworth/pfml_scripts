import argparse
import sys
from typing import List

import massgov.pfml.db as db
import massgov.pfml.reductions.dia as dia
import massgov.pfml.reductions.dua as dua
import massgov.pfml.util.logging as logging
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task

logger = logging.get_logger(__name__)

ALL = "ALL"
DIA = "DIA"
DUA = "DUA"
ALLOWED_VALUES = [ALL, DIA, DUA]


class Configuration:
    send_dia_list: bool
    send_dua_list: bool

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Send claimant list to agencies")
        parser.add_argument(
            "--steps",
            nargs="+",
            choices=ALLOWED_VALUES,
            default=[ALL],
            help="Indicate which agency, DIA or DUA, to create claimant list for",
        )

        args = parser.parse_args(input_args)
        steps = set(args.steps)

        if ALL in steps:
            self.send_dia_list = True
            self.send_dua_list = True
        else:
            self.send_dia_list = DIA in steps
            self.send_dua_list = DUA in steps


@background_task("reductions-send-claimant-lists-to-agencies")
def main():
    config = Configuration(sys.argv[1:])

    with db.session_scope(db.init(), close=True) as db_session:

        if config.send_dia_list:
            with LogEntry(db_session, "DIA send_claimant_lists_to_agencies") as log_entry:
                dia.create_list_of_claimants(db_session, log_entry)
                dia.upload_claimant_list_to_moveit(db_session)

        if config.send_dua_list:
            with LogEntry(db_session, "DUA send_claimant_lists_to_agencies") as log_entry:
                dua.create_list_of_claimants(db_session, log_entry)
                dua.copy_claimant_list_to_moveit(db_session)

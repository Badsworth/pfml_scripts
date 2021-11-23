#
# Interactive console for using database and services.
#
# Automatically connects to the database and authenticates with a FINEOS API server, then drops
# into a Python interactive prompt.
#
# Use via the `-i` flag to python, for example:
#   poetry run python3 -i -m massgov.pfml.tool.console.interactive
#

import logging  # noqa: B1
import sys
from typing import Union

import rich.pretty
import sqlalchemy.orm

import massgov.pfml.api.services.fineos_actions
import massgov.pfml.db
import massgov.pfml.db.config
import massgov.pfml.db.models
import massgov.pfml.db.models.base
import massgov.pfml.fineos
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger("massgov.pfml.repl")


INTRO = """
PFML Python console

Available objects:

│ db = database session {db}
│ fineos = FINEOS client {fineos}

Examples:

│ db.query(Employer).filter(Employer.employer_name == "Stephens LLC").first()
│ fineos.find_employer("239234683")
│ fineos.read_employer("239234683")
│ user_id = massgov.pfml.api.services.fineos_actions.register_employee(fineos, "693078960", "239234683", db)
│ db.commit()
│ fineos.read_customer_details(user_id)
│ fineos.get_absences(user_id)
│ fineos.get_absence(user_id, "NTN-88808-ABS-01")
│ massgov.pfml.api.services.fineos_actions.get_absence_periods("693078960", "239234683", "NTN-88808-ABS-01", db)

Tips:

★ Tab-completion is available
★ History is available (use ↑↓ keys)
★ Use Ctrl+D to exit
"""


def interactive_console() -> dict:
    """Set up variables and print a introduction message for the interactive console."""
    massgov.pfml.util.logging.init("interactive", develop=True)

    db = connect_to_database()
    fineos = massgov.pfml.fineos.create_client()

    print(INTRO.format(**locals()))

    if type(fineos) == massgov.pfml.fineos.MockFINEOSClient:
        print("WARNING: using mock FINEOS client - set FINEOS_ env vars to use a real client\n")

    sys.ps1 = "\npfml >>> "
    sys.ps2 = "pfml ... "

    variables = locals()
    variables.update(vars(massgov.pfml.db.models.applications))
    variables.update(vars(massgov.pfml.db.models.employees))
    variables.update(vars(massgov.pfml.db.models.industry_codes))
    variables.update(vars(massgov.pfml.db.models.payments))
    variables.update(vars(massgov.pfml.db.models.verifications))

    return variables


def connect_to_database() -> Union[sqlalchemy.orm.scoped_session, Exception]:
    """Connect to database and enable logging of SQL queries."""
    db_config = massgov.pfml.db.config.get_config()
    db_config.hide_sql_parameter_logs = False
    db: Union[sqlalchemy.orm.scoped_session, Exception]
    try:
        db = massgov.pfml.db.init(config=db_config, sync_lookups=True)
    except Exception as err:
        db = err
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)  # noqa: B1
    return db


if __name__ == "__main__":
    interactive_variables = interactive_console()
    globals().update(interactive_variables)
    rich.pretty.install(indent_guides=True, max_length=20, max_string=400)

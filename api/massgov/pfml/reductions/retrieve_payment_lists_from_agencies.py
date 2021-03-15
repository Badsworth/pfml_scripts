import massgov.pfml.db as db
import massgov.pfml.reductions.dua as dua
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit as audit

# import massgov.pfml.reductions.dia as dia

logger = logging.get_logger(__name__)


def main():
    audit.init_security_logging()
    logging.init("Retrieving payments list")

    with db.session_scope(db.init(), close=True) as db_session:
        # Expect retreive_dua_payments_list() to retrieve environment variables set via terraform.

        dua.download_payment_list_if_none_today(db_session)
        dua.load_new_dua_payments(db_session)

        # TODO: Uncomment this once the work in API-475 is complete.
        # dia.retreive_dia_payments_list(db_session)

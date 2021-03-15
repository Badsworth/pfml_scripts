import massgov.pfml.db as db
import massgov.pfml.reductions.dua as dua
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit as audit

# import massgov.pfml.reductions.dia as dia

logger = logging.get_logger(__name__)


def main():
    audit.init_security_logging()
    logging.init("Sending claimant lists")

    with db.session_scope(db.init(), close=True) as db_session:
        # Expect create_list_of_claimants() to retrieve environment variables set via terraform.
        dua.create_list_of_claimants(db_session)
        dua.copy_claimant_list_to_moveit(db_session)

        # TODO: Uncomment this once the work in API-478 is complete and DIA is ready to receive.
        # dia.create_list_of_approved_claimants(db_session)
        # dia.send_dia_claimant_list(db_session)

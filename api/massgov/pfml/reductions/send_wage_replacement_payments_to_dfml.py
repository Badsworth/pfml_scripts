import massgov.pfml.util.logging as logging

# import massgov.pfml.db as db
# import massgov.pfml.reductions.dia as dia
# import massgov.pfml.reductions.dua as dua

logger = logging.get_logger(__name__)


def main():
    logging.audit.init_security_logging()
    logging.init("Sending wage replacement payments")

    # with db.session_scope(db.init(), close=True) as db_session:
    #   Expect create_wage_replacement_payments_list() to retrieve environment variables set via terraform.

    #   dua.create_wage_replacement_payments_list(db_session)
    #   dua.send_wage_replacement_payments_list(db_session)

    #   TODO: Uncomment this once the dependent work has been completed.
    #   dia.create_wage_replacement_payments_list(db_session)
    #   dia.send_wage_replacement_payments_list(db_session)
